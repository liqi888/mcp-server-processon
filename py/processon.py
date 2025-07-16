# coding: utf-8
"""
ProcessOn MCP Server
"""
import argparse
import json
import logging
import os
import re
import traceback
import uuid
from typing import Dict, Any

import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import Field, BaseModel, validator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建MCP服务器实例
mcp = FastMCP("ProcessOn Server", log_level="INFO", port=int(os.getenv("PORT", "9000")))

# ProcessOn API Base URL
API_BASE = "https://www.processon.com"
BASE_URL = os.getenv('BASE_URL')
if BASE_URL:
    API_BASE = BASE_URL

class ImportRequest(BaseModel):
    """思维导图导入请求模型"""
    title: str = Field(description="文件名称")
    content: str = Field(description="markdown形式的内容")

    @validator('title')
    def validate_title(cls, value):
        if not value.strip():
            raise ValueError("文件名称不能为空")
        return value


def check_api_key() -> str:
    """
    检查 PROCESSON_API_KEY 是否已设置
    :return: API KEY
    """
    api_key = os.getenv('PROCESSON_API_KEY')
    if not api_key:
        raise ValueError("PROCESSON_API_KEY 环境变量未设置")
    return api_key

def generate_random_id():
    return str(uuid.uuid4())[:20]  # ProcessOn的ID通常是20位字符

def parse_content_to_tree(lines):
    """
    解析Markdown内容为树结构，支持标题(## ~ ######)和列表项(-)
    """
    stack = []
    virtual_root = {"id": "virtual-root", "children": [], "depth": 0}
    current_parent = virtual_root
    last_level = 1  # 默认从1开始

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 处理标题
        heading_match = re.match(r'^(#{2,6})\s+(.*)', line)
        if heading_match:
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()

            node = {
                "id": generate_random_id(),
                "title": title,
                "depth": level,
                "children": []
            }

            # 找到当前标题应挂靠的父节点
            while stack and stack[-1]["depth"] >= level:
                stack.pop()

            parent = stack[-1] if stack else virtual_root
            parent["children"].append(node)
            stack.append(node)
            current_parent = node
            last_level = level
            continue

        # 处理列表项
        list_match = re.match(r'^-\s+(.*)', line)
        if list_match:
            content = list_match.group(1).strip()

            node = {
                "id": generate_random_id(),
                "title": content,
                "depth": last_level + 1,  # 列表项比当前标题低一级
                "children": []
            }

            current_parent["children"].append(node)
            continue

        # 处理其他内容（可以作为当前节点的补充说明）
        if stack and current_parent:
            current_parent["title"] += "\n" + line

    return virtual_root["children"]

def encode_mind(markdown_content: str) -> str:
    """
    支持符合ProcessOn树格式的Markdown思维导图
    现在支持标题(## ~ ######)和列表项(-)
    """
    lines = [line for line in markdown_content.split('\n') if line.strip()]
    if not lines:
        raise ValueError("Markdown内容不能为空")

    # 取首个#作为根标题
    root_title = "未命名思维导图"
    content_lines = []

    for line in lines:
        if line.startswith("# "):
            root_title = line[2:].strip()
        else:
            content_lines.append(line)

    # 构建子树结构
    children = parse_content_to_tree(content_lines)

    # 思维导图主题配置
    base_theme = {
        "background": "#ffffff",
        "version": "v6.1.1",
        "common": {"bold": False, "italic": False, "textAlign": "left"},
        "connectionStyle": {"lineWidth": 2, "lineColor": "#C7654E", "color": "#ffffff", "lineType": "dashed"},
        "summaryTopic": {"font-size": "14px", "summaryLineColor": "#C7654E", "summaryLineWidth": 2, "summaryLineType": "curve_complex"},
        "boundaryStyle": {"lineColor": "#C7654E", "lineWidth": 2, "lineType": 2, "dasharray": "6,3", "fill": "#C7654E", "opacity": "0.1"},
        "centerTopic": {"font-size": 30, "lineStyle": {"lineType": "curve", "lineWidth": 3}, "shape": "radiansRectangle", "background": "#C7654E", "border-color": "#C7654E", "font-weight": "bold"},
        "secTopic": {"font-size": 18, "lineStyle": {"lineType": "roundBroken", "lineWidth": 2}, "shape": "radiansRectangle", "background": "autoColor", "border-color": "autoColor"},
        "childTopic": {"font-size": 14, "lineStyle": {"lineType": "roundBroken", "lineWidth": 2}, "shape": "underline", "border-width": 2, "border-color": "autoColor", "childBgOpacity": "0.16", "anticipateBackground": "autoColor"},
        "w1": 1,
        "w2": 12,
        "autoColor": True,
        "colorList": ["#729B8D", "#EED484", "#E19873", "#DFE8D7"],
        "skeletonId": "mindmap_curve_green-default",
        "colorCardId": "system",
        "colorMinorId": "mind-style1"
    }

    # 构建思维导图JSON
    flow_structure = {
        "root": "true",
        "showWatermark": False,
        "structure": "mind_free",
        "theme": json.dumps(base_theme),
        "title": root_title,
        "depth": 1,
        "id": "root",
        "children": children
    }

    return json.dumps(flow_structure, ensure_ascii=False)


@mcp.tool()
async def check() -> str:
    """查询用户当前配置apiKey"""
    api_key = check_api_key()
    return API_BASE + ":" + api_key

# 创建思维导图
@mcp.tool()
async def createProcessOnMind(
        title: str = Field(description="文件名称"),
        content: str = Field(description="markdown形式的内容"),
) -> Dict[str, Any]:
    """
    创建（生成）思维导图。创建ProcessOn思维导图时调用：根据markdown内容创建思维导图并返回ProcessOn文件链接。
    """
    try:
        # 参数校验
        request = ImportRequest(title=title, content=content)

        # 对用户输入的内容进行URL转码处理
        encoded_content = encode_mind(request.content)

        # 检查API密钥
        api_key = check_api_key()

        url = f"{API_BASE}/api/activity/mcp/chart/create/mind"
        request_data = {
            'file_type': 'mind',
            'folder': 'root',  # 目标文件夹ID
            'category': 'mind',
            'file_name': request.title,
            'def': encoded_content  # 使用转码后的内容
        }

        logger.info(f"开始调用ProcessOn API，URL: {url}")
        logger.debug(f"请求数据: {request_data}")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                data=request_data,
                headers={'X-Mcp-ApiKey': api_key},
                timeout=30
            )
            response.raise_for_status()

            result = response.json()
            logger.info(f"API调用成功，返回结果: {result}")

            code = result.get("code") or result.get("result", {}).get("code")
            msg = result.get("msg") or result.get("result", {}).get("msg")
            data = result.get("data") or result.get("result", {}).get("data")

            chartId = None
            if isinstance(data, dict):
                chartId = data.get("chartId")
            elif isinstance(data, str):
                chartId = data
            else:
                logger.warning(f"data字段类型异常: {type(data)}, 内容: {data}")

            if not chartId:
                # 将完整返回结果记录下来，方便模型/用户排查
                logger.error(f"API调用成功，但未提取到chartId，返回内容: {json.dumps(result, ensure_ascii=False)}")
                raise Exception(f"API返回格式异常，未提取到chartId。完整返回内容: {json.dumps(result, ensure_ascii=False)}")


            fileUrl = f"{API_BASE}/mindmap/{chartId}"
            logger.info(f"文件地址: {fileUrl}")

            return {
                "code": code,
                "msg": msg,
                "chartId": chartId,
                "fileUrl": fileUrl
            }

    except ImportRequest.ValidationError as e:
        logger.error(f"参数验证失败: {str(e)}")
        raise ValueError(f"参数验证失败: {str(e)}") from e

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP请求失败，状态码: {e.response.status_code}")
        logger.error(f"响应内容: {e.response.text}")
        raise Exception(f"API请求失败，状态码: {e.response.status_code}") from e

    except httpx.RequestError as e:
        logger.error(f"请求发送失败: {str(e)}")
        raise Exception(f"请求发送失败: {str(e)}") from e

    except ValueError as e:
        logger.error(f"值错误: {str(e)}")
        raise

    except Exception as e:
        logger.error(f"思维导图生成失败: {str(e)}")
        logger.error(traceback.format_exc())
        raise Exception(f"思维导图生成失败: {str(e)}") from e


def main():
    """MCP Processon Server - HTTP call Processon API for MCP"""
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description="Run the ProcessOn MCP Server")

    # 添加传输协议参数
    parser.add_argument(
        "--transport",
        "-t",
        choices=["sse", "stdio"],
        default="stdio",
        help="Transport protocol to use (sse or stdio)"
    )

    # 解析命令行参数
    args = parser.parse_args()

    # 记录启动信息
    logger.info(f"Starting server with transport: {args.transport}")
    logger.info(f"API base URL: {API_BASE}")

    # 启动服务器
    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()