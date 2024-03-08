import requests
import time

Session = requests.Session


def request(url, session=None, **kwargs):
    retry_count = 0

    if session == None:
        session = requests

    def retry():
        nonlocal retry_count

        if retry_count == 99:
            print(f"request failed to {url}")
            return False
        retry_count += 1
        time.sleep(5)
        return True

    while True:
        try:
            res = session.get(url, **kwargs)
            # print(res.request.headers)
        except (
            requests.exceptions.ConnectTimeout,
            requests.exceptions.ConnectionError,
        ) as e:
            print(e)
            if not retry():
                return None
            continue

        if res.status_code != 200:
            if res.status_code == 429:
                print(f"too many requests for {url}")
                time.sleep(30)
                continue

            if not retry():
                return None
            continue

        return res
