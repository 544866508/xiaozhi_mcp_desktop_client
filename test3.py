import os
import sys
import subprocess

def run_child_python():
    # 1. sys.executable：当前运行脚本的Python解释器
    python_bin = sys.executable
    # 2. os.environ.copy()：完整复制父进程全部环境变量
    child_env = os.environ.copy()

    # 子任务：打印当前使用的python路径、环境变量PATH
    cmd = [
        python_bin,
        "-c",
        "import sys, os;print('子进程Python路径：', sys.executable);print('子进程PATH：', os.environ.get('PATH'))"
    ]

    # 拉起子进程，环境完全继承父进程
    subprocess.run(
        cmd,
        env=child_env,
        text=True
    )

if __name__ == "__main__":
    print("主进程Python路径：", sys.executable)
    print("主进程PATH：", os.environ.get("PATH"))
    print("-" * 60)
    run_child_python()