# server.py
import json

from fastmcp import FastMCP
import sys, os
import logging
import requests
import socket

from utils.port_scanning_op import ip_scanning




# def find_config():
#     with open('./mcp_config.json', 'r', encoding='utf-8') as f:
#         config = json.load(f)
#         print(f'config: {config}')
#         for key, value in config['mcpServers'].items():
#             if 'args' in value and os.path.basename(__file__) in value['args']:
#                 return value
#     return None
#
# def find_position():
#     config_dict = find_config()
#     if not config_dict: return None
#     if not 'device' in config_dict:
#         print('设备未配置！')
#         return None
#     return config_dict['device']
#
# DEVICE_CONFIG = find_position()


# 设备URL
DEVICE_URL = None


logger = logging.getLogger('AirConditioningController')

# Windows控制台UTF8修复
if sys.platform == 'win32':
    sys.stderr.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')

mcp = FastMCP("AirConditioningController")


def find_esp32_ac_controller() -> str | None:
    # 自动扫描局域网寻找ESP32温湿度设备，端口8051

    global DEVICE_URL
    if DEVICE_URL:
        print(f'加载缓存中的设备链接：{DEVICE_URL}')
        return DEVICE_URL

    print('缓存中没有设备链接，开始扫描...')
    port = 8051
    url_path = f"/controller/air_conditioning"
    tgt_ip = ip_scanning(url_path=url_path, port=port, max_concurrent=30, timeout_ms=300)
    if tgt_ip:
        DEVICE_URL = f'http://{tgt_ip}:{port}{url_path}'
        print(f'扫描到设备链接: {DEVICE_URL}')
        return DEVICE_URL

    print(f'未扫描到设备链接！')
    return None


@mcp.tool()
def air_conditioning_controller(cmd: str) -> dict:
    """
    使用这个方法控制我家空调，cmd传入控制命令，允许传入 start、close、up、down、cool、heat，如果用户的命令不在其中，传入 error
    """
    esp32_url = find_esp32_ac_controller()
    if not esp32_url:
        return {
            "success": False,
            "msg": "局域网内未扫描到空调控制器"
        }
    if cmd == "error":
        return {
            "success": False,
            "msg": "暂时无法处理此命令！"
        }
    try:
        resp = requests.get(esp32_url, params={"cmd": cmd}, timeout=3)
        resp.raise_for_status()
        return {
            "success": True,
            "msg": "请求成功！"
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "msg": f"设备访问失败：{str(e)}"
        }




if __name__ == "__main__":
    mcp.run(transport="stdio")