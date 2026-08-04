import threading

import webview
import subprocess
import os

from utils import json_op
import sys
import json

from utils.device_scanning_op import find_new_device
from utils.exp_generation import validate_ir_ctl_cfg, render_esp32_ino_from_irctl, write_mcp_py_file


class Api:
    def __init__(self):
        self.proc = None  # 纯粹用来保存后台子进程
        self.is_mcp_running = False
        self.mcp_config_path = os.path.join(os.getcwd(), "mcp_config.json")
        self.mcp_status_path = os.path.join(os.getcwd(), "mcp_status.json")

        # 文件不存在则初始化默认模板
        if not os.path.exists(self.mcp_config_path):
            default_data = {
                "mcpServers": {}
            }
            with open(self.mcp_config_path, "w", encoding="utf-8") as f:
                json.dump(default_data, f, ensure_ascii=False, indent=2)

    def get_mcp_status(self):
        if not os.path.exists(self.mcp_status_path):
            return []
        try:
            # 读取mcp状态文件
            with open(self.mcp_status_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                return []

            # 读取mcp配置信息
            mcp_servers = {}
            if os.path.exists(self.mcp_config_path):
                try:
                    with open(self.mcp_config_path, "r", encoding="utf-8") as cfg_f:
                        cfg_raw = json.load(cfg_f)
                    mcp_servers = cfg_raw.get("mcpServers", {})
                except Exception as cfg_err:
                    print("读取mcp配置文件失败", cfg_err)

            # 为每条状态补充配置信息
            for item in data:
                target_name = item.get("target", "")
                server_info = mcp_servers.get(target_name, {})
                item["type"] = server_info.get("type", "")
                item["description"] = server_info.get("description", "")
                item["url"] = server_info.get("url", "")

            return data
        except Exception as e:
            print("读取状态文件失败", e)
            return []


    def read_mcp_config(self):
        with open(self.mcp_config_path, "r", encoding="utf-8") as f:
            return f.read()

    def write_mcp_config(self, json_text):
        # 1. 先校验一下是不是合法的 JSON，防止存进去坏数据导致程序起不来
        try:
            json.loads(json_text)
        except Exception as e:
            print(f"JSON 格式错误，拒绝保存: {e}")
            return
        with open(self.mcp_config_path, "w", encoding="utf-8") as f:
            f.write(json_text)

    def save_mcp_addr(self, addr):
        json_op.set_cfg('MCP_WSS', addr.strip())

    def get_mcp_addr(self):
        return json_op.get_cfg('MCP_WSS')

    def start_mcp(self):
        if self.proc is not None and self.proc.poll() is None:
            print("MCP 已经在运行中...")
            return

        # # 更新所有设备的控制信号
        # send_ir_map()

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

    # 查询后台进程是否存活，前端用来真实判断服务启停
    def is_mcp_service_alive(self):
        if self.proc is None:
            return False
        return self.proc.poll() is None

    # # 扫描本地设备
    # def scanning_local_mcp_device(self):
    #     new_device_list = find_new_device()
    #     return new_device_list

    def gen_terminal_ir_code(self, edit_json_str: str):
        try:
            wrap_obj = json.loads(edit_json_str)
            keys = list(wrap_obj.keys())
            if len(keys) != 1:
                return {"ok": False, "msg": "外层必须只有一个MCP配置key", "ino_code": ""}
            mcp_cfg = wrap_obj[keys[0]]

            # 校验args数组
            args_arr = mcp_cfg.get("args", [])
            if not isinstance(args_arr, list) or len(args_arr) == 0:
                return {"ok": False, "msg": "该MCP配置args数组不存在或为空，无法生成脚本文件名", "ino_code": ""}
            module_name = args_arr[-1]

            # 1.校验irCtl配置
            valid_ok, valid_msg, ir_ctl = validate_ir_ctl_cfg(mcp_cfg)
            if not valid_ok:
                return {"ok": False, "msg": valid_msg, "ino_code": ""}

            # 2.渲染ino模板
            render_ok, render_msg, ino_code = render_esp32_ino_from_irctl(mcp_cfg, ir_ctl)
            if not render_ok:
                return {"ok": False, "msg": render_msg, "ino_code": ""}

            # 3.输出py文件（你原有业务逻辑不动）
            rel_py_path = module_name.replace(".", os.sep) + ".py"
            full_py_file = os.path.join(os.getcwd(), rel_py_path)
            py_ok, py_msg = write_mcp_py_file(mcp_cfg, full_py_file)
            if not py_ok:
                return {"ok": False, "msg": py_msg, "ino_code": ""}

            # 4.输出ino文件
            rel_ino_path = module_name.replace(".", os.sep) + ".ino"
            full_ino_file = os.path.join(os.getcwd(), rel_ino_path)
            dir_ino = os.path.dirname(full_ino_file)
            os.makedirs(dir_ino, exist_ok=True)
            with open(full_ino_file, "w", encoding="utf-8") as fw:
                fw.write(ino_code)

            return {
                "ok": True,
                "msg": f"{py_msg} ; ino脚本已生成",
                "ino_code": ino_code
            }

        except Exception as e:
            return {"ok": False, "msg": f"异常:{str(e)}", "ino_code": ""}


if __name__ == "__main__":

    # # 启动后端服务 --------------------------------------------------
    # from backend_server import run_backend_server
    # t = threading.Thread(target=run_backend_server, daemon=True)
    # t.start()
    # # -------------------------------------------------------------

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
    webview.start(gui="edgechromium", icon=icon_file)