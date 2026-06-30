import webview
import subprocess
import os
from utils import json_op
import sys
import json


class Api:
    def __init__(self):
        self.proc = None  # 纯粹用来保存后台子进程
        self.is_mcp_running = False  # 保留变量但前端不再读取
        # 配置文件路径：程序同目录 mcp_config.json
        self.mcp_config_path = os.path.join(os.getcwd(), "mcp_config.json")
        self.mcp_status_path = os.path.join(os.getcwd(), "mcp_status.json")

        # 文件不存在则初始化默认模板
        if not os.path.exists(self.mcp_config_path):
            default_data = {
                "mcpServers": {}
            }
            with open(self.mcp_config_path, "w", encoding="utf-8") as f:
                json.dump(default_data, f, ensure_ascii=False, indent=2)

        # 程序启动初始化状态文件，无status则从config生成全离线
        self.init_status_file()

    # 初始化mcp_status.json
    def init_status_file(self):
        if os.path.exists(self.mcp_status_path):
            return
        init_data = {}
        if os.path.exists(self.mcp_config_path):
            try:
                with open(self.mcp_config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                servers = cfg.get("mcpServers", {})
                for name in servers:
                    init_data[name] = {"running": False, "pid": None}
            except Exception as e:
                print("初始化状态文件读取config失败", e)
        with open(self.mcp_status_path, "w", encoding="utf-8") as f:
            json.dump(init_data, f, indent=2, ensure_ascii=False)

    # 前端读取MCP服务文件状态
    def get_mcp_status(self):
        if not os.path.exists(self.mcp_status_path):
            self.init_status_file()
        try:
            with open(self.mcp_status_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print("读取状态文件失败", e)
            return {}

    # 读取完整mcp_config.json
    def read_mcp_config(self):
        with open(self.mcp_config_path, "r", encoding="utf-8") as f:
            return f.read()

    # 写入完整json到mcp_config.json
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

        # 核心：根据环境，决定是调用 .py 还是调用 .exe
        if getattr(sys, 'frozen', False):
            # 打包后：主程序和后台后台可执行文件在同一个目录下
            exe_dir = os.path.dirname(sys.executable)
            cmd = [os.path.join(exe_dir, "mcp_pipe.exe")]
        else:
            # 开发环境：直接用当前的 python 解释器去运行独立的 mcp_pipe.py
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


if __name__ == "__main__":
    icon_file = './pkg/favicon.ico'
    api = Api()
    win_width = 1000
    win_height = 700

    # 获取主屏尺寸计算居中坐标
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

    # 窗口关闭时顺手关掉后台
    window.events.closed += api.stop_mcp
    # webview.start(gui="edgechromium", debug=True)
    webview.start(gui="edgechromium", icon=icon_file)