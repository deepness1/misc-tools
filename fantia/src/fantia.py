import sys
import os
import json
import urllib
import calendar
import json

from bs4 import BeautifulSoup
import fetch
import strlib
import creds

import mime

domain = "fantia.jp"
origin = "https://" + domain


class Session:
    def __init__(self):
        self.session = fetch.Session()
        self.session.headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "ja,en-US;q=0.9,en;q=0.8",
            "origin": origin,
            "referer": origin,
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
        }
        self.session.cookies.set("_session_id", creds.fantia_session_id, domain=domain)

    def request(self, url, **kwargs):
        return fetch.request(url, self.session, **kwargs)


class PhotoGalleryContent:
    def __init__(self, title, photos):
        self.title = title
        self.photos = photos

    def download(self, session, postdir):
        contentdir = os.path.join(postdir, self.title)
        os.makedirs(contentdir, exist_ok=True)
        for i, url in enumerate(self.photos):
            url_header = session.session.head(url, allow_redirects=True)
            mimetype = url_header.headers["Content-Type"]
            ext = mime.guess_extension(mimetype, url)
            filename = f"{i:03}{ext}"
            path = os.path.join(contentdir, filename)
            if not os.path.exists(path):
                open(path, "wb").write(session.request(url).content)


class FileContent:
    def __init__(self, filename, url):
        self.filename = filename
        self.url = url

    def download(self, session, postdir):
        path = os.path.join(postdir, self.filename)
        if not os.path.exists(path):
            open(path, "wb").write(session.request(self.url).content)


class BlogContent:
    def __init__(self, title, ops):
        self.ops = ops

    def reset_dump_state(self):
        self.bold = False
        self.textsize = None

    def handle_insert_str(self, value):
        if self.textsize:
            match self.textsize:
                case "huge":
                    self.info.write("# ")
                case "large":
                    self.info.write("## ")
                case _:
                    print("unimplemented font size:", self.textsize)
                    exit(1)
        if self.bold:
            self.info.write("**")
        self.info.write(value)
        if self.bold:
            self.info.write("**")
        self.info.write("\n")

        self.reset_dump_state()

    def handle_insert_dict(self, value):
        image = value["fantiaImage"]
        url = image["url"]
        ext = ".jpg"  # FIXME: always jpeg?
        path = os.path.join(self.postdir, f"{self.file_count:03}" + ext)
        self.file_count += 1
        if not os.path.exists(path):
            open(path, "wb").write(self.session.request(url).content)

    def handle_insert(self, value):
        if isinstance(value, str):
            return self.handle_insert_str(value)
        elif isinstance(value, dict):
            return self.handle_insert_dict(value)
        else:
            print("unimplemented insert type: ", type(value))
            exit(1)

    def handle_attr(self, key, value):
        match key:
            case "bold":
                if not isinstance(value, bool):
                    print("bold type must be bool")
                    exit(1)
                self.bold = value
            case "size":
                self.textsize = value
            case "link":
                self.info.write(f"[link]({value})\n")
            case "color":
                pass
            case _:
                print("unimplemented blog attribute:", key)
                exit(1)

    def handle_op(self, key, value):
        match key:
            case "insert":
                self.handle_insert(value)
            case "attributes":
                for attr, flag in value.items():
                    self.handle_attr(attr, flag)

    def download(self, session, postdir):
        info_path = os.path.join(postdir, "info.txt")
        self.session = session
        self.postdir = postdir
        self.info = open(info_path, "wt")
        self.file_count = 1
        self.reset_dump_state()

        for op in self.ops:
            for key, value in op.items():
                self.handle_op(key, value)

        self.info.close()


def parse_content(content):
    title = content["title"] if content["title"] != None else "1"
    match content["category"]:
        case "photo_gallery":
            photos = []
            gallery = content["post_content_photos"]
            for photo in gallery:
                url = photo["url"]["original"]
                photos.append(url)
            return PhotoGalleryContent(title, photos)
        case "file":
            filename = content["filename"]
            url = origin + content["download_uri"]
            return FileContent(filename, url)
        case "blog":
            comment = json.loads(content["comment"])
            return BlogContent(title, comment["ops"])
        case _:
            print("warn: content type", content["category"], "is not implemented")


def get_csrf_token(session, post_id):
    r = session.request(f"https://fantia.jp/posts/{post_id}")
    if r.status_code != 200:
        print(r)
        raise Exception("missing post")

    bs = BeautifulSoup(r.text, "html.parser")

    return bs.select_one('meta[name="csrf-token"]')["content"]


def posted_at_to_date(posted_at):
    elms = posted_at.split(" ")
    year = elms[3]
    month = list(calendar.month_abbr).index(elms[2])
    date = elms[1]
    return f"{year}-{month:02}-{date:02}"


class Post:
    def __init__(self, post_id):
        session = Session()
        self.id = post_id

        response = session.request(
            "https://fantia.jp/api/v1/posts/" + self.id,
            headers={
                "X-CSRF-Token": get_csrf_token(session, post_id),
                "X-Requested-With": "XMLHttpRequest",
            },
        )

        post = json.loads(response.text)["post"]

        self.title = post["title"]
        self.date = posted_at_to_date(post["posted_at"])
        self.description = (
            post["comment"].replace("\r\n", "\n") if post["comment"] != None else ""
        )
        self.contents = []
        for content in post["post_contents"]:
            if content["visible_status"] != "visible":
                print("warn: content is not visible")
                continue
            self.contents.append(parse_content(content))


def list_posts(fanclub):
    session = Session()
    posts = []
    page = 1
    while True:
        res = session.request(f"{origin}/fanclubs/{fanclub}/posts?page={page}")
        bs = BeautifulSoup(res.text, "html.parser")
        posts_bs = bs.select("div.post")
        if not posts_bs:
            return posts
        for post in posts_bs:
            link = post.select_one("a.link-block")["href"]
            post_id = link.lstrip("/posts/")
            posts.append(post_id)
        page += 1


def post_to_dirname(post):
    title = strlib.canonicalize_filename(post.title)
    meta_size = len(f"{post.date[:10]}  {post.id}".encode(encoding="utf-8"))
    title_size = len(title.encode(encoding="utf-8"))
    if meta_size + title_size > 255:
        title = strlib.truncate_by_concating(title, 255 - meta_size)[:-3] + "..."
    return f"{post.date[:10]} {title} {post.id}"


def dump_post(post, basedir):
    session = Session()
    dirname = post_to_dirname(post)
    postdir = os.path.join(basedir, dirname)
    os.makedirs(postdir, exist_ok=True)
    if len(post.description) != 0:
        filepath = os.path.join(postdir, "description.txt")
        open(filepath, "wt").write(post.description)

    for content in post.contents:
        content.download(session, postdir)


def main():
    for post_id in sys.argv[1:]:
        post = Post(post_id)
        dump_post(post, ".")


if __name__ == "__main__":
    main()
