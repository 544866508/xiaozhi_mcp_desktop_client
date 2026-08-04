import threading
import uvicorn
from fastapi import FastAPI
import webview

app = FastAPI()

@app.get("/")
def hello():
    return {"msg": "后台接口服务"}


@app.get("/upload_mac_and_ip")
def upload_mac_and_ip(mac, ip, d_type):
    print(mac, ip, d_type)
    return {"msg": "请求成功！"}


def run_backend_server():
    uvicorn.run(app, host="0.0.0.0", port=8051)



if __name__ == '__main__':
    # # 线程运行
    # t = threading.Thread(target=run_backend_server, daemon=True)
    # t.start()
    # # 前端窗口访问 http://0.0.0.0:12301
    # webview.create_window("客户端", "http://127.0.0.1:12301")
    # webview.start()

    # 直接运行
    uvicorn.run(app, host="0.0.0.0", port=8051)