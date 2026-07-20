import time

count = 0
while True:
    print(f"计时运行中，已过 {count} 秒")
    count += 1
    time.sleep(1)