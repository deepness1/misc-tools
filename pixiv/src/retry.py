import time

interval = 5


def until_success(func, **kwargs):
    cnt = 0
    while True:
        if func(**kwargs):
            return
        print("function", func, "failed, retrying")
        time.sleep(interval +  cnt)
        cnt += 1
