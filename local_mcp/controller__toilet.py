ENDPOINT_MODULE = 'local_mcp.controller__toilet'
#########################################################################

from fastmcp import FastMCP
import sys, os
import logging
import requests

from utils.find_self_mcp_config import find_instructions
from utils.ip_scanning_op import ip_scanning
from config import config


# URL_PATH = f"/local_mcp/controller__air_conditioner__home_office"
URL_PATH = f"/{ENDPOINT_MODULE.replace('.', '/')}"
LOGGER_NAME = ENDPOINT_MODULE.replace('.', '___')
MCP_NAME = LOGGER_NAME

# 设备字典
DEVICE_IP = None


logger = logging.getLogger(LOGGER_NAME)
# logger.setLevel(logging.INFO)

# Windows控制台UTF8修复
if sys.platform == 'win32':
    sys.stderr.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')

mcp = FastMCP(MCP_NAME)



def find_device_url() -> str | None:
    # 自动扫描局域网寻找ESP32温湿度设备，端口8051
    global DEVICE_IP
    tgt_ip = DEVICE_IP

    if not tgt_ip:
        print('缓存中没有设备链接，开始扫描...')
        tgt_ip = ip_scanning(url_path=URL_PATH, port=config.DEVICE_PORT, max_concurrent=30, timeout_ms=400)

    if not tgt_ip:
        print(f'未扫描到设备链接！')
        return None

    DEVICE_URL = f'http://{tgt_ip}:{config.DEVICE_PORT}{URL_PATH}'
    res = requests.get(url=DEVICE_URL, timeout=1)
    if res.status_code not in [200, 400]:
        print('设备接口有误或设备离线，再次扫描设备！')
        tgt_ip = ip_scanning(url_path=URL_PATH, port=config.DEVICE_PORT, max_concurrent=30, timeout_ms=400)
        if not tgt_ip:
            print(f'还是没扫描到设备链接！')
            return None

    DEVICE_IP = tgt_ip
    return DEVICE_URL


def controller__toilet(cmd: str) -> dict:
    """
    instructions动态插入
    """
    # logger.info(f'mac: {mac}, cmd: {cmd}')
    device_url = find_device_url()
    if not device_url:
        return {
            "success": False,
            "msg": "局域网内未扫描到控制器"
        }
    if cmd == "error":
        return {
            "success": False,
            "msg": "暂时无法处理此命令！"
        }
    try:
        resp = requests.get(device_url, params={"cmd": cmd}, timeout=3)
        resp.raise_for_status()
        return {
            "success": True,
            "msg": f"请求成功！cmd: {cmd}"
        }
    except requests.exceptions.RequestException as e:
        # print(f"设备访问失败：{str(e)}")
        return {
            "success": False,
            "msg": f"设备访问失败：{str(e)}"
        }
device_instructions = find_instructions(ENDPOINT_MODULE, config_path='../../mcp_config.json') if os.path.dirname(__file__) == 'local_mcp' else find_instructions(ENDPOINT_MODULE)
controller__toilet.__doc__ = device_instructions if device_instructions else '用户未配置MCP控制说明'
mcp.add_tool(controller__toilet)



if __name__ == "__main__":
    mcp.run(transport="stdio")