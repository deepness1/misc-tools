import sys
import os
import json
import urllib

import fetch
import creds

origin = "https://api.fanbox.cc"


class Session:
    def __init__(self):
        self.session = fetch.Session()
        self.session.headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "ja,en-US;q=0.9,en;q=0.8",
            "origin": "https://www.fanbox.cc",
            "referer": "https://www.fanbox.cc/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
        }
        self.session.cookies.set(
            "FANBOXSESSID", creds.fanbox_session_id, domain=".fanbox.cc"
        )

    def request(self, url, **kwargs):
        return fetch.request(url, self.session, **kwargs)


class Post:
    def __init__(self, post_id):
        self.session = Session()

        url = origin + "/post.info"
        payload = {"postId": post_id}
        info = self.download(url, params=payload).json()
        data = info["body"]

        self.post_id = post_id
        self.title = data["title"]
        self.date = data["publishedDatetime"][:10]
        self.text = ""
        self.images = []
        self.files = []

        body = data["body"]
        if body == None:
            self.visible = False
            return
        else:
            self.visible = True
        if "blocks" in body:
            for b in body["blocks"]:
                match b["type"]:
                    case "p" | "header":
                        self.text += b["text"] + "\n"
                    case "image":
                        self.text += f"(image {len(self.images)})"

                        image_id = b["imageId"]
                        self.images.append(body["imageMap"][image_id]["originalUrl"])
                    case "url_embed":
                        self.text += "(link)"
                    case "file":
                        self.text += f"(file {len(self.files)})"

                        file_id = b["fileId"]
                        m = body["fileMap"][file_id]
                        name = m["name"] + "." + m["extension"]
                        url = body["fileMap"][file_id]["url"]
                        self.files.append({"name": name, "url": url})
                    case _:
                        print(b)
                        print("unknown block type", b["type"])
                        exit(1)

        if "text" in body:
            self.text += body["text"].replace("\\n", "\n")
        if "images" in body:
            for i in body["images"]:
                self.images.append(i["originalUrl"])
        if "files" in body:
            for f in body["files"]:
                name = f["name"]
                if "extension" in f:
                    name += "." + f["extension"]
                self.files.append({"name": name, "url": f["url"]})

    def download(self, url, **kwargs):
        return self.session.request(url, **kwargs)


def list_posts(creator_id):
    session = Session()

    def get_paginate_creator():
        nonlocal session
        url = origin + "/post.paginateCreator"
        payload = {"creatorId": creator_id}

        return session.request(url, params=payload).json()

    def query_parse(url):
        query = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        for k in query:
            query[k] = query[k][0]
        return query

    def get_list_creator(**kwargs) -> dict:
        url = origin + "/post.listCreator"
        payload = kwargs
        return session.request(url, params=payload).json()

    paginate = get_paginate_creator()

    posts = []
    for i in range(len(paginate["body"])):
        param = query_parse(paginate["body"][i])
        for p in get_list_creator(**param)["body"]:
            posts.append(p["id"])

    return posts


def dump_post(post, basedir):
    dirname = f"{post.date} {post.title} {post.post_id}".replace("/", "／")
    path = os.path.join(basedir, dirname)
    os.makedirs(path, exist_ok=True)
    if len(post.text) != 0:
        filepath = os.path.join(path, "description.txt")
        open(filepath, "wt").write(post.text)

    for i, url in enumerate(post.images):
        ext = os.path.splitext(url)[1]
        if ext == ".jpeg":
            ext = ".jpg"
        filepath = os.path.join(path, f"{i:03}{ext}")
        open(filepath, "wb").write(post.download(url).content)

    for file in post.files:
        filepath = os.path.join(path, file["name"])
        open(filepath, "wb").write(post.download(file["url"]).content)


def main():
    for n in sys.argv[1:-1]:
        post = Post(n)
        if not post.visible:
            continue
        print("*", post.title)
        dump_post(post, sys.argv[-1])


if __name__ == "__main__":
    main()
