import os
import sys
import threading
import urllib
import json

from bs4 import BeautifulSoup
from bs4.element import NavigableString
import strlib
import curl

import atomic

origin = "https://kemono.su"


def get(url):
    return curl.get(url)


def build_full_url(path):
    if path.startswith("https://") or path.startswith("http://"):
        return path
    else:
        return origin + path


class Post:
    def __init__(self, site, uid, pid):
        self.pid = pid

        url = f"{origin}/api/v1/{site}/user/{uid}/post/{pid}"
        root = json.loads(get(url))
        # TODO: support multiple revisions
        # props = root["props"]
        # for num, r in props["revisions"]:
        #     if num == int(props["flagged"]):
        #         rev = r
        rev = root["post"]
        self.title = rev["title"]
        self.date = rev["published"][:10]

        if "url" in rev["embed"] and rev["embed"]["url"] != None:
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
                filename = file["name"] if "name" in file else os.path.basename(url)
                self.files.append([url, filename])

        bs = BeautifulSoup(rev["content"], "html.parser")
        self.description = self.parse_content(bs)

    def parse_content(self, bs):
        if isinstance(bs, NavigableString):
            return str(bs).strip()
        string = ""
        for node in bs.contents:
            pre = ""
            post = ""
            match node.name:
                case "p":
                    post = "\n"
                case "strong" | "b":
                    pre = post = "__"
                case "h1":
                    pre = "# "
                    post = "\n"
                case "h2":
                    pre = "## "
                    post = "\n"
                case "h3":
                    pre = "### "
                    post = "\n"
                case "h4":
                    pre = "#### "
                    post = "\n"
                case "h5":
                    pre = "##### "
                    post = "\n"
                case "h6":
                    pre = "###### "
                    post = "\n"
                case "em" | "i":
                    pre = post = "_"
                case None | "span" | "pre" | "ul" | "blockquote" | "div":
                    pass
                case "li":
                    pre = "- "
                    post = "\n"
                case "a":
                    link = build_full_url(node["href"])
                    pre = "["
                    post = f"]({link})"
                case "iframe":
                    link = build_full_url(node["src"])
                    string += f"[iframe]({link})"
                case "br":
                    string += "\n"
                case "img":
                    link = build_full_url(node["src"])
                    if self.find_file(link) == None:
                        self.files.append([link, None])
                    ext = os.path.splitext(link)[1]
                    index = self.find_file(link)
                    string += f"[img]({index:03}{ext})"
                case _:
                    print("error: unknown element", node)
                    exit(1)
            content = self.parse_content(node)
            if len(content) > 0:
                string += pre + content + post
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
        arr = json.loads(get(url + f"?o={o}"))
        if len(arr) == 0:
            return result
        result += [post["id"] for post in arr]
        o += 50


def download(url, path):
    res = curl.get(
        url,
        header=[
            "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept: */*",
            f"Referer: {origin}/",
        ],
    )
    if res == None:
        print("request failed: ", url)
        return False
    open(path, "wb").write(res)
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
        subject = post.embed["subject"].replace("/", "-")
        description = post.embed["description"]
        text = f"[{description}]({url})"
        open(postdir + f"/{subject}.txt", mode="w").write(text)

    def download_file(post, i):
        link, name = post.files[i]
        print(i + 1, "/", len(post.files), link)
        savepath = postdir + f"/{i:03}"
        if name != None:
            # sometimes name contains a full url
            name = os.path.basename(name)
            if len(name) > 64:
                name = name[-64:]
            savepath += "-" + os.path.splitext(name)[0]
        if not is_downloadable_link(link):
            print("warn: unhandled link type, saving url")
            savepath += ".txt"
            open(savepath, "w").write(link)
            return True

        ext = os.path.splitext(link)[1]
        if ext == ".jpe" or ext == ".jpeg":
            ext = ".jpg"
        savepath += ext
        if os.path.exists(savepath):
            return True
        return download(link, savepath)

    job_index = atomic.AtomicInt()

    failed = False

    def worker_main():
        nonlocal failed

        i = job_index.fetch_add()
        while i < len(post.files):
            failed |= not download_file(post, i)
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
