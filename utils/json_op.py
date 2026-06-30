import json
from typing import Any

CONFIG_FILE = "./client_config.json"


def get_cfg(key: str, default: Any = None) -> Any:
    """根据key读取配置，不存在返回默认值"""
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    return data.get(key, default)


def set_cfg(key: str, value: Any) -> None:
    """指定key和value保存，存在则覆盖，不存在新增"""
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}

    data[key] = value

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)




if __name__ == '__main__':
    # ========== 使用示例 ==========
    # 写入/修改
    set_cfg("port", 8080)
    set_cfg("debug", True)
    set_cfg("username", "admin")
    set_cfg("timeout", 30.5)

    # 读取
    print(get_cfg("port"))
    print(get_cfg("debug"))
    print(get_cfg("username"))
    # 读不存在的key，给默认值
    print(get_cfg("password", "123456"))