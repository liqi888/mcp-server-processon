#!/usr/bin/env node

const { spawn, spawnSync } = require('child_process');
const path = require('path');
const pkg = require(path.join(__dirname, '..', 'package.json'));

// 支持 --version 和 -v 参数，打印版本号后退出
if (process.argv.includes('--version') || process.argv.includes('-v')) {
    console.log(pkg.version);
    process.exit(0);
}

function findPythonCommand() {
    const candidates = ['python', 'python3'];

    for (const cmd of candidates) {
        try {
            const res = spawnSync(cmd, ['--version'], { encoding: 'utf-8' });
            if (res.status === 0 && res.stdout.toLowerCase().includes('python')) {
                return cmd;
            }
        } catch (e) {
            // 忽略异常，尝试下一个
        }
    }
    return null;
}

function installPythonDeps(pythonCmd) {
    const reqFile = path.join(__dirname, '../requirements.txt');

    console.log(`Using Python command: ${pythonCmd}`);
    console.log('Checking and installing Python dependencies...');

    const pipInstall = spawnSync(pythonCmd, ['-m', 'pip', 'install', '-r', reqFile], {
        stdio: 'inherit',
        env: process.env,
    });

    if (pipInstall.error) {
        console.error('Error executing pip install:', pipInstall.error);
        process.exit(1);
    }

    if (pipInstall.status !== 0) {
        console.error('Failed to install Python dependencies, exit code:', pipInstall.status);
        process.exit(pipInstall.status);
    }

    console.log('Python dependencies installed successfully.');
}

function startPythonProcess(pythonCmd) {
    const pyScript = path.join(__dirname, '../py/processon.py');

    console.log('Starting Python MCP server...');
    const py = spawn(pythonCmd, [pyScript, '--transport', 'stdio'], {
        stdio: 'inherit',
        env: process.env,
    });

    py.on('exit', (code) => {
        console.log(`Python MCP server exited with code ${code}`);
        process.exit(code);
    });
}

function main() {
    const pythonCmd = findPythonCommand();
    if (!pythonCmd) {
        console.error('Cannot find Python interpreter. Please install Python and ensure "python" or "python3" is in your PATH.');
        process.exit(1);
    }
    installPythonDeps(pythonCmd);
    startPythonProcess(pythonCmd);
}

main();
