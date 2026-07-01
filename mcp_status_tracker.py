import time
import json
import os
from typing import Optional, Tuple

# 状态常量，全部隔离在此
STATUS_ONLINE = "online"
STATUS_RECONNECTING = "reconnecting"
STATUS_PROCESS_EXIT = "process_exit"
STATUS_AUTH_FAILED = "auth_401"
STATUS_NOT_FOUND = "url_404"
STATUS_SERVER_ERR = "server_5xx"
STATUS_CONN_FAILED = "conn_failed"
STATUS_CONFIG_ERR = "config_error"
STATUS_SCRIPT_MISSING = "script_missing"

# 配置参数隔离
STATUS_FILE = os.path.join(os.getcwd(), "mcp_status.json")
STATUS_FLUSH_INTERVAL = 2

# 全局状态池，仅本模块持有
_mcp_global_status: dict[str, dict] = {}


def init_target_status(target: str):
    """初始化单个服务状态"""
    _mcp_global_status[target] = {
        "target": target,
        "status": STATUS_CONN_FAILED,
        "reconnect_attempt": 0,
        "last_online_ts": 0,
        "last_error": "",
        "last_error_ts": 0,
        "last_update_ts": time.time()
    }


def flush_status_to_file():
    """持久化全部状态到 mcp_status.json"""
    try:
        now = time.time()
        for item in _mcp_global_status.values():
            item["last_update_ts"] = now
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(list(_mcp_global_status.values()), f, ensure_ascii=False, indent=2)
    except Exception:
        # 不抛异常污染主程序，仅静默失败
        pass


def update_target_status(target: str, status: str, err_msg: str = "", reconnect_cnt: Optional[int] = None):
    """更新单实例状态并立即落盘"""
    if target not in _mcp_global_status:
        init_target_status(target)
    st = _mcp_global_status[target]
    st["status"] = status
    now = time.time()

    if reconnect_cnt is not None:
        st["reconnect_attempt"] = reconnect_cnt

    if err_msg:
        st["last_error"] = err_msg
        st["last_error_ts"] = now
    else:
        st["last_error"] = ""

    if status == STATUS_ONLINE:
        st["last_online_ts"] = now

    flush_status_to_file()


def parse_websocket_exception(exc: Exception) -> Tuple[str, str]:
    """解析WebSocket异常，输出对应状态+错误文本"""
    from websockets.exceptions import InvalidStatusCode, ConnectionClosed, WebSocketException
    if isinstance(exc, InvalidStatusCode):
        code = exc.status_code
        msg = f"HTTP {code}"
        if code == 401:
            return STATUS_AUTH_FAILED, msg
        elif code == 404:
            return STATUS_NOT_FOUND, msg
        # 全覆盖所有标准5xx服务异常码
        elif code in (500, 501, 502, 503, 504, 505, 506, 507, 508, 510, 511):
            return STATUS_SERVER_ERR, msg
        else:
            return STATUS_CONN_FAILED, msg
    elif isinstance(exc, ConnectionClosed):
        return STATUS_RECONNECTING, f"WebSocket closed: {exc}"
    elif isinstance(exc, WebSocketException):
        return STATUS_CONN_FAILED, f"WebSocket connect fail: {exc}"
    else:
        return STATUS_CONN_FAILED, str(exc)


async def status_flush_worker():
    """后台定时刷新协程，独立任务"""
    import asyncio
    while True:
        flush_status_to_file()
        await asyncio.sleep(STATUS_FLUSH_INTERVAL)


# mcp_status_tracker.py 底部新增
def parse_subproc_stderr_log(log_text: str) -> tuple[str, str] | None:
    """
    解析mcp_proxy子进程stderr日志，识别业务HTTP错误
    返回(状态标识, 错误文案)，无匹配返回None
    """
    if "401 Unauthorized" in log_text:
        return STATUS_AUTH_FAILED, "子进程业务请求401鉴权失败，检查API Key"
    if "404 Not Found" in log_text:
        return STATUS_NOT_FOUND, "子进程请求地址404，URL配置错误"
    if any(code in log_text for code in ("500", "502", "503", "504", "507")):
        return STATUS_SERVER_ERR, "子进程收到5xx服务端异常"
    return None


def get_target_current_state(target: str) -> dict:
    """对外获取指定target当前状态字典"""
    if target not in _mcp_global_status:
        init_target_status(target)
    return _mcp_global_status[target]