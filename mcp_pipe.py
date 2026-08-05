"""
Simple MCP stdio <-> WebSocket pipe with optional unified config.
Version: 0.2.0
"""

import asyncio
import websockets
import subprocess
import logging
import os
import signal
import sys
import json
import time
from dotenv import load_dotenv
# 仅新增一行导入，所有状态逻辑隔离外部文件
from mcp_status_tracker import (
    status_flush_worker,
    update_target_status,
    parse_websocket_exception,
    parse_subproc_stderr_log,
    get_target_current_state,  # 新增
    STATUS_CONFIG_ERR,
    STATUS_SCRIPT_MISSING,
    STATUS_RECONNECTING,
    STATUS_ONLINE,
    STATUS_PROCESS_EXIT,
    STATUS_AUTH_FAILED,
    STATUS_NOT_FOUND,
    STATUS_SERVER_ERR, heartbeat_refresh_online
)

# Auto-load environment variables from a .env file if present
load_dotenv()

# Configure logging
logging.basicConfig(
    # level=logging.INFO,
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('MCP_PIPE')

# Reconnection settings
INITIAL_BACKOFF = 1  # Initial wait time in seconds
MAX_BACKOFF = 600  # Maximum wait time in seconds

async def connect_with_retry(uri, target):
    """Connect to WebSocket server with retry mechanism for a given server target."""
    reconnect_attempt = 0
    backoff = INITIAL_BACKOFF
    while True:  # Infinite reconnection
        try:
            if reconnect_attempt > 0:
                # 仅新增一行状态更新
                update_target_status(target, STATUS_RECONNECTING, f"Wait {backoff}s retry, attempt:{reconnect_attempt}", reconnect_attempt)
                logger.info(f"[{target}] Waiting {backoff}s before reconnection attempt {reconnect_attempt}...")
                await asyncio.sleep(backoff)

            # Attempt to connect
            await connect_to_server(uri, target)

        except Exception as e:
            reconnect_attempt += 1
            err_state, err_text = parse_websocket_exception(e)
            logger.warning(f"[{target}] Connection closed (attempt {reconnect_attempt}): {err_text}")
            # 仅新增一行状态更新
            update_target_status(target, err_state, err_text, reconnect_attempt)
            # Calculate wait time for next reconnection (exponential backoff)
            backoff = min(backoff * 2, MAX_BACKOFF)

async def connect_to_server(uri, target):
    """Connect to WebSocket server and pipe stdio for the given server target."""
    process = None
    try:
        logger.info(f"[{target}] Connecting to WebSocket server...")
        async with websockets.connect(uri) as websocket:
            logger.info(f"[{target}] Successfully connected to WebSocket server")
            # 仅新增一行：标记在线
            update_target_status(target, STATUS_ONLINE)

            # Start server process (built from CLI arg or config)
            cmd, env = build_server_command(target)
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8',
                text=True,
                env=env
            )
            logger.info(f"[{target}] Started server process: {' '.join(cmd)}")

            # Create two tasks: read from WebSocket and write to process, read from process and write to WebSocket
            await asyncio.gather(
                pipe_websocket_to_process(websocket, process, target),
                pipe_process_to_websocket(process, websocket, target),
                pipe_process_stderr_to_terminal(process, target),
                heartbeat_refresh_online(target)  # 心跳监控，用于mcp状态恢复
            )
    except websockets.exceptions.ConnectionClosed as e:
        raise  # Re-throw exception to trigger reconnection
    except Exception as e:
        raise  # Re-throw exception
        # mcp_pipe.py connect_to_server 函数的 finally 片段
    finally:
        if process is not None:
            logger.info(f"[{target}] Terminating server process")
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            logger.info(f"[{target}] Server process terminated")
            # 关键修改：不强制覆盖状态，仅当当前状态不是故障类时才标记进程退出
            st = get_target_current_state(target)
            current_st = st.get("status", "")
            fault_states = {STATUS_AUTH_FAILED, STATUS_NOT_FOUND, STATUS_SERVER_ERR, STATUS_CONFIG_ERR,
                            STATUS_SCRIPT_MISSING}
            if current_st not in fault_states:
                update_target_status(target, STATUS_PROCESS_EXIT, "MCP subprocess exited")



async def pipe_websocket_to_process(websocket, process, target):
    """Read data from WebSocket and write to process stdin"""
    try:
        while True:
            # Read message from WebSocket
            message = await websocket.recv()
            logger.debug(f"[{target}] << {message}")

            # Write to process stdin (in text mode)
            if isinstance(message, bytes):
                message = message.decode('utf-8')
            process.stdin.write(message + '\n')
            process.stdin.flush()

            # # 新增：收到ws消息并下发进程，证明链路正常，重置在线（避免断连出现的5xx）
            # update_target_status(target, STATUS_ONLINE, "Communication normal")

    except Exception as e:
        logger.error(f"[{target}] Error in WebSocket to process pipe: {e}")
        raise  # Re-throw exception to trigger reconnection
    finally:
        # Close process stdin
        if not process.stdin.closed:
            process.stdin.close()

async def pipe_process_to_websocket(process, websocket, target):
    """Read data from process stdout and send to WebSocket"""
    try:
        while True:
            # Read data from process stdout
            data = await asyncio.to_thread(process.stdout.readline)

            if not data:  # If no data, the process may have ended
                logger.info(f"[{target}] Process has ended output")
                break

            # Send data to WebSocket
            logger.debug(f"[{target}] >> {data}")
            # In text mode, data is already a string, no need to decode
            await websocket.send(data)
    except Exception as e:
        logger.error(f"[{target}] Error in process to WebSocket pipe: {e}")
        raise  # Re-throw exception to trigger reconnection

async def pipe_process_stderr_to_terminal(process, target):
    """Read data from process stderr and print to terminal"""
    try:
        while True:
            # Read data from process stderr
            data = await asyncio.to_thread(process.stderr.readline)

            if not data:  # If no data, the process may have ended
                logger.info(f"[{target}] Process has ended stderr output")
                break

            # Print stderr data to terminal (in text mode, data is already a string)
            sys.stderr.write(data)
            sys.stderr.flush()

            # 新增：解析stderr日志识别业务HTTP错误
            err_match = parse_subproc_stderr_log(data)
            if err_match is not None:
                err_status, err_msg = err_match
                update_target_status(target, err_status, err_msg)

    except Exception as e:
        logger.error(f"[{target}] Error in process stderr pipe: {e}")
        raise  # Re-throw exception to trigger reconnection


def signal_handler(sig, frame):
    """Handle interrupt signals"""
    logger.info("Received interrupt signal, shutting down...")
    # 退出前刷新状态文件
    from mcp_status_tracker import flush_status_to_file
    flush_status_to_file()
    sys.exit(0)

def load_config():
    """Load JSON config from $MCP_CONFIG or ./mcp_config.json. Return dict or {}."""
    path = os.environ.get("MCP_CONFIG") or os.path.join(os.getcwd(), "mcp_config.json")
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load config {path}: {e}")
        return {}


def build_server_command(target=None):
    """Build [cmd,...] and env for the server process for a given target.

    Priority:
    - If target matches a server in config.mcpServers: use its definition
    - Else: treat target as a Python script path (back-compat)
    If target is None, read from sys.argv[1].
    """
    if target is None:
        assert len(sys.argv) >= 2, "missing server name or script path"
        target = sys.argv[1]
    cfg = load_config()
    servers = cfg.get("mcpServers", {}) if isinstance(cfg, dict) else {}

    # （复用主进程python） ----------------------------------------------
    current_python = sys.executable  # 锁定当前运行mcp_pipe的venv Python
    # ----------------------------------------------------------------

    if target in servers:
        entry = servers[target] or {}
        if entry.get("disabled"):
            err_msg = f"Server '{target}' is disabled in config"
            update_target_status(target, STATUS_CONFIG_ERR, err_msg)
            raise RuntimeError(err_msg)
        typ = (entry.get("type") or entry.get("transportType") or "stdio").lower()

        # environment for child process
        child_env = os.environ.copy()
        for k, v in (entry.get("env") or {}).items():
            child_env[str(k)] = str(v)

        if typ == "stdio":
            command = entry.get("command")
            args = entry.get("args") or []

            # 关键修复：如果配置里写的是python/python3，替换成当前venv绝对路径（复用主进程python）
            if command in ("python", "python3", "python.exe"):
                command = current_python
            # ----------------------------------------------------------------

            if not command:
                err_msg = f"Server '{target}' is missing 'command'"
                update_target_status(target, STATUS_CONFIG_ERR, err_msg)
                raise RuntimeError(err_msg)
            return [command, *args], child_env

        if typ in ("sse", "http", "streamablehttp"):
            url = entry.get("url")
            if not url:
                err_msg = f"Server '{target}' (type {typ}) is missing 'url'"
                update_target_status(target, STATUS_CONFIG_ERR, err_msg)
                raise RuntimeError(err_msg)
            # Unified approach: always use current Python to run mcp-proxy module
            cmd = [sys.executable, "-m", "mcp_proxy"]
            if typ in ("http", "streamablehttp"):
                cmd += ["--transport", "streamablehttp"]
            # optional headers: {"Authorization": "Bearer xxx"}
            headers = entry.get("headers") or {}
            for hk, hv in headers.items():
                cmd += ["-H", hk, str(hv)]
            cmd.append(url)
            return cmd, child_env

        err_msg = f"Unsupported server type: {typ}"
        update_target_status(target, STATUS_CONFIG_ERR, err_msg)
        raise RuntimeError(err_msg)

    # Fallback to script path (back-compat)
    script_path = target
    if not os.path.exists(script_path):
        err_msg = f"'{target}' script file not found"
        update_target_status(target, STATUS_SCRIPT_MISSING, err_msg)
        raise RuntimeError(
            f"'{target}' is neither a configured server nor an existing script"
        )
    return [sys.executable, script_path], os.environ.copy()

if __name__ == "__main__":

    from utils import json_op

    # print('自动配置环境变量')
    os.environ["MCP_ENDPOINT"] = json_op.get_cfg('MCP_WSS')

    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)

    # Get token from environment variable or command line arguments
    endpoint_url = os.environ.get('MCP_ENDPOINT')
    if not endpoint_url:
        logger.error("Please set the `MCP_ENDPOINT` environment variable")
        sys.exit(1)

    # Determine target: default to all if no arg; single target otherwise
    target_arg = sys.argv[1] if len(sys.argv) >= 2 else None

    async def _main():
        # 启动独立定时刷盘协程
        asyncio.create_task(status_flush_worker())

        if not target_arg:
            cfg = load_config()
            servers_cfg = (cfg.get("mcpServers") or {})
            all_servers = list(servers_cfg.keys())
            enabled = [name for name, entry in servers_cfg.items() if not (entry or {}).get("disabled")]
            skipped = [name for name in all_servers if name not in enabled]
            if skipped:
                logger.info(f"Skipping disabled servers: {', '.join(skipped)}")
            if not enabled:
                raise RuntimeError("No enabled mcpServers found in config")
            logger.info(f"Starting servers: {', '.join(enabled)}")
            tasks = [asyncio.create_task(connect_with_retry(endpoint_url, t)) for t in enabled]
            # Run all forever; if any crashes it will auto-retry inside
            await asyncio.gather(*tasks)
        else:
            if os.path.exists(target_arg):
                await connect_with_retry(endpoint_url, target_arg)
            else:
                err_msg = f"Script path {target_arg} does not exist"
                update_target_status(target_arg, STATUS_SCRIPT_MISSING, err_msg)
                logger.error("Argument must be a local Python script path. To run configured servers, run without arguments.")
                sys.exit(1)


    try:
        asyncio.run(_main())
    except KeyboardInterrupt:
        logger.info("Program interrupted by user")
    except Exception as e:
        logger.error(f"Program execution error: {e}")
    finally:
        # 程序最终退出强制写状态
        from mcp_status_tracker import flush_status_to_file
        flush_status_to_file()
