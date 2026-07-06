# server.py
from fastmcp import FastMCP
import sys
import logging
import requests
import socket

logger = logging.getLogger('TemperatureHumidityMonitor')

# Windows控制台UTF8修复
if sys.platform == 'win32':
    sys.stderr.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')

mcp = FastMCP("TemperatureHumidityMonitor")

# 自动扫描局域网寻找ESP32温湿度设备，端口8051
def find_esp32_sensor(segment: str = "192.168.1") -> str | None:
    for i in range(2, 255):
        ip = f"{segment}.{i}"
        url = f"http://{ip}:8051/sensor"
        try:
            resp = requests.get(url, timeout=0.25)
            if resp.status_code == 200 and "temperature" in resp.text:
                return url
        except (requests.exceptions.RequestException, socket.timeout):
            continue
    return None

@mcp.tool()
def temperature_humidity_monitor(position: str) -> dict:
    """
    获取家中指定房间温湿度
    :param position: 房间名称，可选：卧室 / 书房
    """
    print(f"查询房间：{position}")

    if position == "书房":
        return {
            "success": True,
            "result": {"temperature": "35℃", "humidity": "25%"}
        }
    elif position == "卧室":
        esp32_url = find_esp32_sensor()
        if not esp32_url:
            return {
                "success": False,
                "msg": "局域网内未扫描到卧室ESP32温湿度设备（端口8051）"
            }
        try:
            resp = requests.get(esp32_url, timeout=3)
            resp.raise_for_status()
            sensor_data = resp.json()
            return {
                "success": True,
                "result": sensor_data
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "msg": f"设备访问失败：{str(e)}"
            }
    else:
        return {
            "success": False,
            "msg": f"不支持房间[{position}]，仅支持：卧室、书房"
        }

if __name__ == "__main__":
    mcp.run(transport="stdio")