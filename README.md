# mcp-server-processon

🚀 基于 MCP 协议的 Markdown → ProcessOn 思维导图生成工具。

该工具可将结构化 Markdown 内容转化为符合 ProcessOn 要求的树状图结构，并通过 API 创建思维导图文件，适用于大模型 Agent、Cherry Studio 等场景。

---

## ✨ 功能特性

- ✅ 支持结构化 Markdown 转思维导图
- ✅ 自动调用 [ProcessOn](https://www.processon.com) API 创建文件
- ✅ 基于 MCP 协议，可直接集成大模型工具链
- ✅ 支持 `check()` 工具验证密钥与服务连通性
- ✅ 支持 `npx` 运行，无需全局安装

---

## 📦 安装方式

> 首次运行时会自动安装 Python 依赖。请确保系统已安装 Python（推荐 3.8+）并添加到 PATH。


### ✅ 方式一：使用 `npx`（推荐）

```bash
npx mcp-server-processon
```


---

### ✅ 方式二：全局安装

```bash
npm install -g mcp-server-processon
```

运行服务：

```bash
mcp-server-processon
```

---

## 🔧 环境变量配置

服务通过环境变量读取 ProcessOn 配置信息：

| 变量名               | 是否必须 | 说明                                                                                     |
|----------------------|----------|----------------------------------------------------------------------------------------|
| `PROCESSON_API_KEY`  | ✅ 是     | 你的 ProcessOn API 密钥（可在 [www.processon.com](https://www.processon.com/setting) 账户中心 获取） |
| `BASE_URL`           | ❌ 否     | 自定义 API 地址（默认使用官方地址）                                                                   |

### 设置示例

#### macOS / Linux

```bash
export PROCESSON_API_KEY=YOU PROCESSON_API_KEY
```

#### Windows（CMD）

```cmd
set PROCESSON_API_KEY="YOU PROCESSON_API_KEY"
```

#### Windows（PowerShell）

```powershell
$env:PROCESSON_API_KEY="YOU PROCESSON_API_KEY"
```

---

## 🚀 使用说明

### 启动服务

```bash
npx mcp-server-processon
```

或（已全局安装）：

```bash
mcp-server-processon
```

默认以 `stdio` 模式启动 MCP 服务。

---

### 查看版本

```bash
npx mcp-server-processon --version
```

---

## 🛠 MCP 工具接口

本服务通过 MCP 协议提供以下两个方法：

---

### 🧪 `check()`

用于验证 API KEY 是否已配置，并返回当前连接的 API 地址。

#### 请求示例：

```json
{
  "tool": "check",
  "args": {}
}
```

#### 返回示例：

```json
"https://www.processon.com:your_api_key"
```

---

### 🧠 `createProcessOnMind(title, content)`

根据 Markdown 内容生成思维导图。

#### 请求参数：

| 参数名     | 类型   | 必填 | 说明               |
|------------|--------|------|--------------------|
| title  | string | ✅   | 思维导图文件名     |
| content    | string | ✅   | Markdown 内容       |

#### Markdown 内容格式要求：

- `# 一级标题`：作为导图根节点
- `## 二级标题`及以下：作为子节点，支持到 `######`

#### 示例请求：

```json
{
  "tool": "createProcessOnMind",
  "args": {
    "title": "项目计划",
    "content": "# 项目计划\n## 阶段一\n### 任务 1\n### 任务 2\n## 阶段二\n### 任务 3"
  }
}
```

#### 返回示例：

```json
{
  "code": 0,
  "msg": "成功",
  "chartId": "abc123def456",
  "fileUrl": "https://www.processon.com/mindmap/abc123def456"
}
```

---

## 🐍 Python 依赖说明

系统将自动安装以下依赖：

- [`httpx`](https://www.python-httpx.org/) >= 0.24.0
- [`pydantic`](https://docs.pydantic.dev/) >= 1.10.0
- [`fastmcp`](https://github.com/lqez/mcp) >= 0.1.3
- 更多依赖包请参考requirements.txt文件

如需手动安装：

```bash
pip install -r requirements.txt
```

---

## 🧑‍💻 本地调试方式

你也可以在本地手动启动 MCP 服务：

```bash
cd py
export PROCESSON_API_KEY=your_token
python processon.py --transport stdio
```

---

## 🍒 在 Cherry Studio 中使用本 MCP 服务

打开`Cherry Studio`，左下角的`设置`，选择`MCP服务器`，右上角`添加服务器`，选择`从JSON导入`

在文件中添加如下内容后保存

```json
"processon_mind": {
  "name": "ProcessOn_CreateMind",
  "type": "stdio",
  "description": "ProcessOn创建思维导图",
  "isActive": true,
  "registryUrl": "",
  "command": "npx",
  "args": [
    "mcp-server-processon"
  ],
  "env": {
    "PROCESSON_API_KEY": "{YOU PROCESSON_API_KEY}"
  }
}

```

---

## 📁 项目结构说明

```
mcp-server-processon/
├── bin/
│   └── cli.js              # Node 启动脚本，供 npx 使用
├── py/
│   └── processon.py        # Python 实现的 MCP Server
├── requirements.txt        # Python 依赖清单
├── package.json            # npm 包配置
└── README.md               # 使用说明文档
```

---

## 📄 协议 License

MIT License © 2025 [琪天大圣](https://github.com/liqi888/mcp-server-processon)
