import webview
import subprocess
import os
from utils import json_op
import sys
import json


class Api:
    def __init__(self):
        self.proc = None
        self.is_mcp_running = False
        self.mcp_config_path = os.path.join(os.getcwd(), "mcp_config.json")
        self.mcp_status_path = os.path.join(os.getcwd(), "mcp_status.json")

        # 初始化空配置文件
        if not os.path.exists(self.mcp_config_path):
            default_data = {
                "mcpServers": {}
            }
            with open(self.mcp_config_path, "w", encoding="utf-8") as f:
                json.dump(default_data, f, ensure_ascii=False, indent=2)

    # 前端读取标准状态数组（适配mcp_pipe输出）
    def get_mcp_status(self):
        if not os.path.exists(self.mcp_status_path):
            return []
        try:
            with open(self.mcp_status_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # 确保是数组格式
            if not isinstance(data, list):
                return []
            return data
        except Exception as e:
            print("读取状态文件失败", e)
            return []

    def read_mcp_config(self):
        with open(self.mcp_config_path, "r", encoding="utf-8") as f:
            return f.read()

    def write_mcp_config(self, json_text):
        data = json.loads(json_text)
        with open(self.mcp_config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def save_mcp_addr(self, addr):
        json_op.set_cfg('MCP_WSS', addr.strip())

    def get_mcp_addr(self):
        return json_op.get_cfg('MCP_WSS')

    def start_mcp(self):
        if self.proc is not None and self.proc.poll() is None:
            print("MCP 已经在运行中...")
            return

        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(sys.executable)
            cmd = [os.path.join(exe_dir, "mcp_pipe.exe")]
        else:
            cmd = [sys.executable, "mcp_pipe.py"]

        print(f"🚀 正在拉起独立后台进程: {' '.join(cmd)}")
        self.proc = subprocess.Popen(cmd)
        self.is_mcp_running = True

    def stop_mcp(self):
        if self.proc is None or self.proc.poll() is not None:
            print("MCP 未运行")
            return

        try:
            print('🛑 正在关闭 MCP 进程...')
            self.proc.terminate()
            self.proc.wait(timeout=3)
        except Exception as e:
            print("关闭异常：", e)
        finally:
            self.proc = None
            self.is_mcp_running = False
            print('MCP 后台已彻底关闭！')

    # 新增接口：查询后台进程是否存活（前端用来真实判断服务启停，抛弃localStorage缓存）
    def is_mcp_service_alive(self):
        if self.proc is None:
            return False
        return self.proc.poll() is None


if __name__ == "__main__":
    icon_file = './pkg/favicon.ico'
    api = Api()
    win_width = 1000
    win_height = 700

    screen = webview.screens[0]
    x_pos = (screen.width - win_width) // 2
    y_pos = (screen.height - win_height) // 2

    window = webview.create_window(
        "MCP客户端控制器",
        url='html/index.html',
        js_api=api,
        width=win_width,
        height=win_height,
        x=x_pos,
        y=y_pos
    )

    window.events.closed += api.stop_mcp
    webview.start(gui="edgechromium", icon=icon_file)