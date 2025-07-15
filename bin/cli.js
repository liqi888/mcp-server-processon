#!/usr/bin/env node

const { spawn } = require('child_process');
const path = require('path');

// 启动 Python 脚本
const py = spawn('python', [path.join(__dirname, '../py/processon.py'), '--transport', 'stdio'], {
    stdio: 'inherit', // 关键：让 MCP 和 Studio 建立 I/O 通道
    env: process.env
});

py.on('exit', (code) => {
    process.exit(code);
});
