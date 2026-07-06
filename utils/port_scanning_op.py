import re
import subprocess
import platform
import socket
import requests
import threading
import time

from utils.thread_op import MyThreadFunc


def get_wifi_third_segment() -> int | None:
    """自动获取当前局域网 192.168.x.1 中的 x"""
    gw_ip = get_default_gateway()
    if not gw_ip or not gw_ip.startswith("192.168."):
        return None
    parts = gw_ip.split(".")
    return int(parts[2])

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






def port_scanning(ip_like: str,
                  url_path_list: list[str],
                  port_list: list[int],
                  max_concurrent: int,
                  timeout_ms: int) -> str | None:
    """
    多线程网段端口扫描，只要接口返回200即判定连通
    :param ip_like: 网段模板 "192.168.1.*"
    :param url_path_list: 接口路径列表 ["/sensor","/data"]
    :param port_list: 端口列表 [80,8051]
    :param max_concurrent: 最大并发线程数量
    :param timeout_ms: HTTP请求超时时间，单位毫秒
    :return: 第一个连通的url / None
    """
    seg_prefix = ip_like.rstrip(".*")
    host_suffix_list = list(range(2, 255))
    total = len(host_suffix_list)
    req_timeout = timeout_ms / 1000

    found_result: str | None = None
    finished_count = 0
    thread_pool: list[MyThreadFunc] = []
    pool_lock = threading.Lock()

    def scan_task(suffix: int):
        nonlocal found_result, finished_count
        with pool_lock:
            if found_result is not None:
                return
        current_ip = f"{seg_prefix}.{suffix}"

        for p in port_list:
            for path in url_path_list:
                full_url = f"http://{current_ip}:{p}{path}"
                try:
                    resp = requests.get(full_url, timeout=req_timeout)
                    # 仅判断状态码200，不校验页面内容，连通即命中
                    if resp.status_code == 200:
                        with pool_lock:
                            found_result = full_url
                        print(f"✅ 连通成功：{full_url}")
                        return
                except (requests.exceptions.RequestException, socket.timeout):
                    continue
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
        print("检测到可连通地址，终止全部扫描线程...")
        for t in thread_pool:
            if t.state():
                t.stop()
    else:
        print("❌ 全部扫描完成，无200可连通地址")
    return found_result



if __name__ == "__main__":

    # 确认wifi环境下第三段网段的值
    seg_x = get_wifi_third_segment()
    if seg_x is None:
        print("未识别到192.168.x.x局域网！")

    # ip_like = f"192.168.{seg_x}.*"
    # port_list = [8051]
    # url_path_list = ["/sensor", "/data"]
    # target_url = port_scanning(ip_like=ip_like, port_list=port_list, url_path_list=url_path_list, max_concurrent=5, timeout_ms=300)
    # print(target_url)

    ip_like = f"192.168.{seg_x}.*"
    port_list = [8051]
    url_path_list = ["/"]
    target_url = port_scanning(ip_like=ip_like, port_list=port_list, url_path_list=url_path_list, max_concurrent=30, timeout_ms=300)
    print(target_url)