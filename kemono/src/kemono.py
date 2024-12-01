import os
import sys
import threading
import urllib
import json

from bs4 import BeautifulSoup
import strlib
import fetch

import atomic

origin = "https://kemono.su"


def build_full_url(path):
    if path.startswith("https://") or path.startswith("http://"):
        return path
    else:
        return origin + path


class Post:
    def __init__(self, site, uid, pid):
        self.pid = pid

        url = f"{origin}/api/v1/{site}/user/{uid}/post/{pid}"
        res = fetch.request(url)
        root = json.loads(res.text)
        # TODO: support multiple revisions
        # props = root["props"]
        # for num, r in props["revisions"]:
        #     if num == int(props["flagged"]):
        #         rev = r
        rev = root["post"]
        self.title = rev["title"]
        self.date = rev["published"][:10]

        if "url" in rev["embed"]:
            self.embed = rev["embed"]
        else:
            self.embed = None

        self.files = []
        if "path" in rev["file"]:
            file = rev["file"]
            url = build_full_url(file["path"])
            if self.find_file(url) == None:
                self.files.append([url, file["name"]])
        for file in rev["attachments"]:
            url = build_full_url(file["path"])
            if self.find_file(url) == None:
                self.files.append([url, file["name"]])

        bs = BeautifulSoup(rev["content"], "html.parser")
        self.description = self.parse_content(bs)

    def parse_content(self, bs):
        string = bs.string
        if string != None:
            return string

        string = ""
        pre = bs.find("pre")
        if pre != None:
            string += pre.text.strip()
        ps = bs.find_all(["p", "h3"])
        if len(ps) == 0:
            ps = [bs]
        for p in ps:
            for e in p:
                text = str(e.string).strip()
                match e.name:
                    case None | "strong" | "span" | "pre" | "em":
                        string += text
                    case "i":
                        string += f"_{text}_"
                    case "b":
                        string += f"__{text}__"
                    case "a":
                        link = build_full_url(e["href"])
                        string += f"[{text}]({link})"
                    case "br":
                        string += "\n"
                    case "img":
                        link = build_full_url(e["src"])
                        if self.find_file(link) == None:
                            self.files.append([link, None])
                        ext = os.path.splitext(link)[1]
                        index = self.find_file(link)
                        string += f"[img]({index:03}{ext})"
                    case _:
                        print("error: unknown element name")
                        print(e)
                        exit(1)
            string += "\n"
        return string

    def find_file(self, url):
        for i in range(len(self.files)):
            if self.files[i][0] == url:
                return i
        return None


def list_post_urls(site, uid):
    url = f"{origin}/api/v1/{site}/user/{uid}"
    result = []

    o = 0
    while True:
        res = fetch.request(url + f"?o={o}")
        arr = json.loads(res.text)
        if len(arr) == 0:
            return result
        result += [post["id"] for post in arr]
        o += 50


def download(url, path):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "*/*",
        "Referer": origin + "/",
    }
    res = fetch.request(url, headers=headers)
    if res == None:
        print("request failed")
        return False
    open(path, "wb").write(res.content)
    return True


def post_to_dirname(post):
    title = strlib.canonicalize_filename(post.title)
    return strlib.build_dirname_from_parts(post.date[:10], title, post.pid)


def is_downloadable_link(link):
    hostname = urllib.parse.urlparse(link).hostname
    return hostname.endswith("kemono.su")


def save_post(post, path):
    if post.description == None and len(post.files) == 0:
        return True

    print("*", post.title, len(post.files))

    postdir = path + "/" + post_to_dirname(post)
    os.makedirs(postdir, exist_ok=True)
    if post.description != None:
        text = post.description.strip()
        if len(text) != 0:
            open(postdir + "/info.txt", mode="w").write(text)
    if post.embed != None:
        url = post.embed["url"]
        subject = post.embed["subject"]
        description = post.embed["description"]
        text = f"[{description}]({url})"
        open(postdir + f"/{subject}.txt", mode="w").write(text)

    failed = False

    def download_file(post, i):
        link, name = post.files[i]
        print(i + 1, "/", len(post.files), link)
        savepath = postdir + f"/{i:03}-{name}"
        if not is_downloadable_link(link):
            print("warn: unhandled link type, saving url")
            savepath += ".txt"
            open(savepath, "w").write(link)
            return

        ext = os.path.splitext(link)[1]
        if ext == ".jpe" or ext == ".jpeg":
            ext = ".jpg"
        savepath += ext
        if os.path.exists(savepath):
            return
        if not download(link, savepath):
            failed = True

    job_index = atomic.AtomicInt()

    def worker_main():
        nonlocal failed

        i = job_index.fetch_add()
        while i < len(post.files):
            download_file(post, i)
            i = job_index.fetch_add()

    workers = []
    for i in range(4):
        thread = threading.Thread(target=worker_main)
        thread.start()
        workers.append(thread)
    for w in workers:
        w.join()

    return not failed


def main():
    if len(sys.argv) < 4:
        print("site uid pid...")
        exit(1)

    site = sys.argv[1]
    uid = sys.argv[2]
    for pid in sys.argv[3:]:
        post = Post(site, uid, pid)
        save_post(post, ".")


if __name__ == "__main__":
    main()
