import json

# 新增状态存储
STATUS_FILE = "./mcp_status.json"
status_data = {}

def write_status(target, running: bool, pid=None):
    status_data[target] = {"running": running, "pid": pid}
    try:
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(status_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"写入状态文件失败: {e}")
