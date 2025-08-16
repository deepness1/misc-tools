import time
import certifi
from io import BytesIO

import pycurl


def contents_to_string(c):
    try:
        s = c.decode("utf-8")
        return s
    except:
        return "(binary)"


# header: list
# cookie: list
# version: 1|2|3
def get_full(url, **kwargs):
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

    headers = {}

    def header_callback(line):
        nonlocal headers

        line = line.decode("iso-8859-1")
        if ":" not in line:
            return

        name, value = line.split(":", 1)

        name = name.strip().lower()
        value = value.strip()
        headers[name] = value

    while True:
        buf = BytesIO()
        curl = pycurl.Curl()
        curl.setopt(curl.URL, url)
        curl.setopt(curl.WRITEDATA, buf)
        curl.setopt(curl.CAINFO, certifi.where())
        curl.setopt(curl.HEADERFUNCTION, header_callback)
        curl.setopt(curl.FOLLOWLOCATION, True)
        # curl.setopt(curl.VERBOSE, 1)
        if "version" in kwargs:
            match kwargs["version"]:
                case 1:
                    curl.setopt(curl.HTTP_VERSION, curl.CURL_HTTP_VERSION_1_1)
                case 2:
                    curl.setopt(curl.HTTP_VERSION, curl.CURL_HTTP_VERSION_2_0)
                case 3:
                    curl.setopt(curl.HTTP_VERSION, curl.CURL_HTTP_VERSION_3_0)
                case _:
                    print("invalid http version", kwargs["version"])
        if "header" in kwargs:
            curl.setopt(curl.HTTPHEADER, kwargs["header"])
        if "cookie" in kwargs:
            s = ""
            for c in kwargs["cookie"]:
                s += c + ";"
            curl.setopt(curl.COOKIE, s)
        try:
            curl.perform()
            code = curl.getinfo(curl.RESPONSE_CODE)
        except pycurl.error as e:
            print(e)
            code = -1

        if code != 200:
            if code == 429:
                print(f"too many requests for {url}")
                time.sleep(30)
                continue

            print(
                "code={} headers={} contents={}".format(
                    code, headers, contents_to_string(buf.getvalue())
                )
            )
            if not retry():
                return None
            continue

        return [headers, buf.getvalue()]


def get(url, **kwargs):
    headers, contents = get_full(url, **kwargs)
    return contents
