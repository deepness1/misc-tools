import time
import certifi
from io import BytesIO

import pycurl


# header: list
# cookie: list
# version: 1|2|3
def get(url, **kwargs):
    # print(f"curl get {url} {kwargs}")
    retry_count = 0

    def retry():
        nonlocal retry_count

        if retry_count == 99:
            print(f"request failed to {url}")
            return False
        retry_count += 1
        print(f"fail {url} {kwargs}")
        time.sleep(5)
        return True

    while True:
        buf = BytesIO()
        curl = pycurl.Curl()
        curl.setopt(curl.URL, url)
        curl.setopt(curl.WRITEDATA, buf)
        curl.setopt(curl.CAINFO, certifi.where())
        if "version" in kwargs:
            match kwargs["version"]:
                case 1:
                    curl.setopt(curl.HTTP_VERSION, curl.HTTP_VERSION_1_1)
                case 2:
                    curl.setopt(curl.HTTP_VERSION, curl.HTTP_VERSION_2_0)
                case 3:
                    curl.setopt(curl.HTTP_VERSION, curl.HTTP_VERSION_3_0)
                case _:
                    print("invalid http version", kwargs["version"])
        if "header" in kwargs:
            curl.setopt(curl.HTTPHEADER, kwargs["header"])
        if "cookie" in kwargs:
            s = ""
            for c in kwargs["cookie"]:
                s += c + ";"
            curl.setopt(curl.COOKIE, s)
        curl.perform()

        code = curl.getinfo(curl.RESPONSE_CODE)
        if code != 200:
            if code == 429:
                print(f"too many requests for {url}")
                time.sleep(30)
                continue

            if not retry():
                return None
            continue

        return buf.getvalue()
