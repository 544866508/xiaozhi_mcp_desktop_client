import requests
import time

# 请求地址
url = "http://192.168.1.53:8051/controller/air_conditioning?cmd=start"


def loop_request_air():
    while True:
        try:
            # 发送GET请求，设置超时3秒
            resp = requests.get(url, timeout=3)
            print(f"【请求成功】状态码：{resp.status_code}，返回内容：{resp.text}")
        except requests.exceptions.Timeout:
            print("【请求失败】连接超时，设备无响应")
        except requests.exceptions.ConnectionError:
            print("【请求失败】无法连接设备，请检查IP、端口、网络是否通畅")
        except Exception as e:
            print(f"【请求失败】未知异常：{str(e)}")

        # 间隔5秒再发起下一次请求
        time.sleep(5)


if __name__ == "__main__":
    print("开始循环请求空调启动接口，每5秒一次，按Ctrl+C停止程序")
    try:
        loop_request_air()
    except KeyboardInterrupt:
        print("\n程序已手动停止")