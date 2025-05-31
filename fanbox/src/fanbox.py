import sys
import os
import json
import urllib

import curl
import creds

origin = "https://api.fanbox.cc"


def get(url):
    return curl.get(
        url,
        header=[
            "accept: application/json, text/plain, */*",
            "accept-language: ja,en-US;q=0.9,en;q=0.8",
            "origin: https://www.fanbox.cc",
            "referer: https://www.fanbox.cc/",
            "user-agent: Mozilla/5.0 (X11; Linux x86_64; rv:139.0) Gecko/20100101 Firefox/139.0",
        ],
        cookie=[
            "FANBOXSESSID={}".format(creds.fanbox_session_id),
            "cf_clearance={}".format(creds.fanbox_cf_clearance),
        ],
    )


class Post:
    def __init__(self, post_id):
        info = json.loads(get(f"{origin}/post.info?postId={post_id}"))
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


def list_posts(creator_id):
    posts = []
    pages_url = f"{origin}/post.paginateCreator?creatorId={creator_id}"
    for url in json.loads(get(pages_url))["body"]:
        for p in json.loads(get(url))["body"]:
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
        if os.path.exists(filepath):
            continue
        file = get(url)
        open(filepath, "wb").write(file)

    for file in post.files:
        filepath = os.path.join(path, file["name"])
        if os.path.exists(filepath):
            continue
        file = get(file["url"])
        open(filepath, "wb").write(file)


def main():
    for n in sys.argv[1:-1]:
        post = Post(n)
        if not post.visible:
            continue
        print("*", post.title)
        dump_post(post, sys.argv[-1])


if __name__ == "__main__":
    main()
