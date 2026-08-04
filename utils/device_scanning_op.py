import requests
from config import config
from urllib.parse import urlparse
from utils.ip_scanning_op import ip_scanning
import json


def get_device_mac_by_ip(tgt_ip):
    "获取设备mac地址"
    mac_url = f'http://{tgt_ip}:{config.DEVICE_PORT}/get_mac'
    res = requests.get(mac_url, timeout=3)
    res.raise_for_status()
    data = res.json()
    return data['mac']


def device_scanning():
    '''设备扫描'''
    device_list = []
    for url_path in config.DEVICE_PATH_LIST:
        tgt_ip = ip_scanning(url_path, port=config.DEVICE_PORT, max_concurrent=30, timeout_ms=500)
        # print(tgt_ip)
        if not tgt_ip:
            print(f'未扫描到相关设备，跳过 url_path ：{url_path}')
            continue
        # 控制url
        op_url = f'http://{tgt_ip}:{config.DEVICE_PORT}{url_path}'
        print(f'op_url: {op_url}')
        # 获取mac
        # print(mac_url)
        mac_path = get_device_mac_by_ip(tgt_ip)
        device = {'op_url': op_url, 'mac_path': mac_path}
        device_list.append(device)

    return device_list


def build_mcp_config(input_list: list[dict]) -> list[dict]:
    """
    转换输入设备列表为MCP配置结构
    :param input_list: 输入 [{'op_url': 'http://xxx', 'mac_path': 'xx'}]
    :return: MCP配置数组
    """
    result = []
    for idx, item in enumerate(input_list):
        op_url = item["op_url"]
        mac_path = item["mac_path"]
        # 解析url路径
        url_path = urlparse(op_url).path
        # 拼接本地py文件路径
        script_path = f".{url_path}.py"
        # 生成key，序号从00001开始
        key_name = f"local-stdio-air-controller-{idx + 1:05d}"

        config_item = {
            key_name: {
                "type": "stdio",
                "command": "python",
                "description": "新设备",
                "args": [
                    script_path
                ],
                "disabled": False,
                "controller": {
                    "mac_path": mac_path,
                    "instruction": "",
                    "cmd-ir": {}
                }
            }
        }
        result.append(config_item)
    return result


def filter_new_mcp_config(exist_full_config: dict, new_server_list: list[dict]) -> list[dict]:
    """
    根据mac_path过滤新增MCP服务，剔除和已有配置重复设备
    :param exist_full_config: 完整配置 {"mcpServers": {...}}
    :param new_server_list: build_mcp_config输出的数组 [{"key": {...}}, ...]
    :return: 过滤后不重复的新增服务数组
    """
    # 收集已有所有mac（统一大写去空格）
    exist_macs = set()
    mcp_servers = exist_full_config.get("mcpServers", {})
    for server_cfg in mcp_servers.values():
        controller = server_cfg.get("controller")
        if controller and "mac_path" in controller:
            mac = controller["mac_path"].strip().upper()
            exist_macs.add(mac)

    result = []
    for item in new_server_list:
        # item: {"local-stdio-air-controller-00001": {...}}
        for server_cfg in item.values():
            controller = server_cfg.get("controller")
            if not controller or "mac_path" not in controller:
                # 没有mac_path，默认保留
                result.append(item)
                continue
            current_mac = controller["mac_path"].strip().upper()
            if current_mac not in exist_macs:
                result.append(item)
    return result


def find_new_device(mcp_config_path='./mcp_config.json'):
    # 扫描设备
    device_list = device_scanning()
    # print(device_list)

    # 转换成mcp固定格式
    device_list = build_mcp_config(device_list)
    print(device_list)

    # 剔除重复设备
    with open(f'{mcp_config_path}', 'r', encoding='utf-8') as f:
        mcp_config = json.load(f)

    new_device_list = filter_new_mcp_config(mcp_config, device_list)

    return new_device_list



if __name__ == '__main__':

    # # 扫描ip
    # port = 8051
    # url_path = "/local_mcp/controller/common"
    # tgt_ip = ip_scanning(url_path, port=port, max_concurrent=30, timeout_ms=500)
    # print(tgt_ip)
    # url = f'http://{tgt_ip}:{port}{url_path}'
    # print(url)
    #
    # # 获取mac
    # mac_url = f'http://{tgt_ip}:{port}/get_mac'
    # print(mac_url)
    # mac_path = get_device_mac(mac_url)
    # print(mac_path)

    mcp_config_path = '../mcp_config.json'
    new_device_list = find_new_device(mcp_config_path)
    print(new_device_list)