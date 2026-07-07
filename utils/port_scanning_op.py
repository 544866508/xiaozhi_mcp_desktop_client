import re
import subprocess
import platform
import socket
import requests
import threading
import time
from typing import Optional

from utils.thread_op import MyThreadFunc



def get_wifi_prefix_three() -> str | None:
    """自动获取当前局域网 192.168.x.1 中的前三段网段 192.168.x"""
    gw_ip = get_default_gateway()
    if not gw_ip or not gw_ip.startswith("192.168."):
        return None
    parts = gw_ip.split(".")
    # 拼接前三段 a.b.c
    return f"{parts[0]}.{parts[1]}.{parts[2]}"

def get_default_gateway() -> str | None:
    """获取系统默认网关IP"""
    sys = platform.system()
    try:
        if sys == "Windows":
            res = subprocess.check_output(["ipconfig"], encoding="gbk")
            match = re.search(r"默认网关.*?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", res, re.S)
        else:
            res = subprocess.check_output(["route", "-n"], encoding="utf-8")
            match = re.search(r"0\.0\.0\.0\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", res)
        if match:
            return match.group(1)
    except Exception:
        pass
    # 兜底方式：UDP连接虚拟地址拿本机内网IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        if local_ip.startswith("192.168."):
            parts = local_ip.split(".")
            return f"{parts[0]}.{parts[1]}.{parts[2]}.1"
    except Exception:
        pass
    return None



def get_wifi_suffix_one(ip_like: str,
                        url_path: str,
                        port: int = 8051,
                        timeout_ms: int = 300,
                        max_concurrent: int = 30) -> Optional[int]:
    """
    多线程网段端口扫描，只要接口返回200即判定连通
    :param ip_like: 网段模板 "192.168.1.*"
    :param url_path: 接口路径，如 "/sensor"
    :param port: 扫描端口，如 8051
    :param max_concurrent: 最大并发线程数量
    :param timeout_ms: HTTP请求超时时间，单位毫秒
    :return: 第一个连通IP最后一段数字 / None
    """
    seg_prefix = ip_like.rstrip(".*")
    host_suffix_list = list(range(2, 255))
    total = len(host_suffix_list)
    req_timeout = timeout_ms / 1000

    found_result: Optional[int] = None
    finished_count = 0
    thread_pool: list[MyThreadFunc] = []
    pool_lock = threading.Lock()

    def scan_task(suffix: int):
        nonlocal found_result, finished_count
        with pool_lock:
            if found_result is not None:
                return
        current_ip = f"{seg_prefix}.{suffix}"

        full_url = f"http://{current_ip}:{port}{url_path}"
        try:
            resp = requests.get(full_url, timeout=req_timeout)
            # 仅判断状态码200，连通即命中
            if resp.status_code == 200:
                with pool_lock:
                    found_result = suffix
                print(f"✅ 连通成功：{full_url}，IP尾段：{suffix}")
                return
        except (requests.exceptions.RequestException, socket.timeout):
            pass

        with pool_lock:
            finished_count += 1
            print(f"【进度 {finished_count}/{total}】完成IP {current_ip}")

    idx = 0
    while idx < len(host_suffix_list):
        if found_result is not None:
            break
        alive_num = sum(1 for t in thread_pool if t.state())
        if alive_num >= max_concurrent:
            time.sleep(0.05)
            continue

        suffix = host_suffix_list[idx]
        t = MyThreadFunc(scan_task, (suffix,))
        thread_pool.append(t)
        t.start()
        idx += 1

    while True:
        all_done = all(not t.state() for t in thread_pool)
        if all_done or found_result is not None:
            break
        time.sleep(0.1)

    if found_result is not None:
        print(f"检测到可连通地址，IP尾段：{found_result}，终止全部扫描线程...")
        for t in thread_pool:
            if t.state():
                t.stop()
    else:
        print("❌ 全部扫描完成，无200可连通地址")
    return found_result



def ip_scanning(url_path, port=8051, max_concurrent=30, timeout_ms=300):
    '''
    根据端口和url规则扫描ip
    :return:
    '''
    # 确认wifi环境下前三段网段的值
    prefix_three = get_wifi_prefix_three()
    if not prefix_three:
        print("未识别到内网网络！")
        return None

    # 根据端口和url的规则扫描最后一个网段的值
    suffix_one = get_wifi_suffix_one(ip_like=f"{prefix_three}.*", port=port, url_path=url_path, max_concurrent=max_concurrent, timeout_ms=timeout_ms)
    if not suffix_one:
        print("未扫描到对应规则的IP！")
        return None

    return f"{prefix_three}.{suffix_one}"



if __name__ == "__main__":

    port = 8051
    url_path = "/sensor"
    tgt_ip = ip_scanning(url_path, port=port, max_concurrent=30, timeout_ms=300)


    print(tgt_ip)
    url = f'http://{tgt_ip}:{port}{url_path}'
    print(url)




    # port = 8051
    # url_path = "/"
    # tgt_ip = ip_scanning(url_path, port=port, max_concurrent=30, timeout_ms=300)
    #
    #
    # print(tgt_ip)
    # url = f'http://{tgt_ip}:{port}{url_path}'
    # print(url)