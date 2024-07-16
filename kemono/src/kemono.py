import os
import sys
import threading

from bs4 import BeautifulSoup
import strlib
import fetch

import atomic

origin = "https://kemono.su"


def build_full_url(path):
    if path.startswith("https://"):
        return path
    else:
        return origin + path


def make_abs_link(link):
    if link[0] == "/":
        link = "https://kemono.su" + link
    return link


class Post:
    def __init__(self, site, uid, pid):
        self.pid = pid

        url = f"{origin}/{site}/user/{uid}/post/{pid}"
        res = fetch.request(url)
        bs = BeautifulSoup(res.text, "html.parser")
        section = bs.body.main.section
        post_info = section.header.find("div", class_="post__info")
        self.title = post_info.find("h1", class_="post__title").find_all("span")[0].text
        info_time = post_info.find("time")
        if info_time != None:
            self.date = info_time.text.strip()
        else:
            published = bs.head.find("meta", attrs={"name": "published"})
            self.date = published.get("content")[:10]

        post_body = section.find("div", class_="post__body")
        content = post_body.find("div", class_="post__content")
        self.files = []
        if content != None:
            if content.string != None:
                self.description = content.string
            else:
                self.description = ""
                pre = content.find("pre")
                if pre != None:
                    self.description += pre.text.strip()
                ps = content.find_all(["p", "h3"])
                if len(ps) == 0:
                    ps = [content]
                for p in ps:
                    for e in p:
                        text = str(e.string).strip()
                        match e.name:
                            case None | "strong" | "span" | "pre" | "em":
                                self.description += text
                            case "a":
                                link = make_abs_link(e["href"])
                                self.description += f"[{text}]({link})"
                            case "br":
                                self.description += "\n"
                            case "img":
                                link = make_abs_link(e["src"])
                                if not link in self.files:
                                    self.files.append(link)
                                ext = os.path.splitext(link)[1]
                                index = self.files.index(link)
                                self.description += f"[img]({index:03}{ext})"
                            case _:
                                print("error: unknown element name")
                                print(e)
                                exit(1)
                    self.description += "\n"
        else:
            self.description = None

        post_files = post_body.find("div", class_="post__files")
        if post_files != None:
            for thumbnail in post_files.find_all("div", class_="post__thumbnail"):
                file = thumbnail.find("a", class_="fileThumb")
                self.files.append(build_full_url(file["href"]))
            for link in post_files.find_all("a", recursive=False):
                self.files.append(link["href"])

        self.attachments = []
        post_attachments = post_body.find("ul", class_="post__attachments")
        if post_attachments != None:
            for attachment in post_attachments.find_all(
                "a", class_="post__attachment-link"
            ):
                self.attachments.append(
                    [build_full_url(attachment["href"]), attachment.text.strip()[9:]]
                )


def list_post_urls(site, uid):
    url = f"{origin}/{site}/user/{uid}/"
    result = []
    while True:
        res = fetch.request(url)
        bs = BeautifulSoup(res.text, "html.parser")
        section = bs.body.main.section

        items = section.find("div", class_="card-list__items")
        for post in items.find_all("article", class_="post-card"):
            result.append(post.find("a")["href"].split("/")[-1])

        paginator = section.find("div", id="paginator-top")
        next_page = (
            paginator.menu.find("a", class_="next") if paginator.menu != None else None
        )
        if next_page == None:
            break
        url = build_full_url(origin + next_page["href"])

    return result


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
    if link.startswith(origin):
        return True

    for i in range(1, 10):
        domain = f"https://c{i}.kemono.su"
        if link.startswith(domain):
            return True

    return False


def save_post(post, path):
    if post.description == None and len(post.files) == 0 and len(post.attachments) == 0:
        return True

    postdir = path + "/" + post_to_dirname(post)
    os.makedirs(postdir, exist_ok=True)
    if post.description != None:
        text = post.description.strip()
        if len(text) != 0:
            open(postdir + "/info.txt", mode="w").write(text)

    print("*", post.title, len(post.files))

    failed = False

    def run_workers(fn, n):
        workers = []
        for i in range(n):
            thread = threading.Thread(target=fn)
            thread.start()
            workers.append(thread)
        for w in workers:
            w.join()

    job_index = atomic.AtomicInt()

    def worker_main():
        nonlocal failed

        i = job_index.fetch_add()
        while i < len(post.files):
            while True:
                link = post.files[i]
                print(i + 1, "/", len(post.files), link)
                if is_downloadable_link(link):
                    ext = os.path.splitext(link)[1]
                    if ext == ".jpe" or ext == ".jpeg":
                        ext = ".jpg"
                    savepath = postdir + f"/{i:03}{ext}"
                    if os.path.exists(savepath):
                        break
                    if not download(link, savepath):
                        failed = True
                else:
                    print("warn: unhandled link type, saving url")
                    ext = ".txt"
                    open(postdir + f"/{i:03}{ext}", "w").write(link)
                break
            i = job_index.fetch_add()

    run_workers(worker_main, 4)

    job_index = atomic.AtomicInt()

    def worker_main():
        nonlocal failed

        i = job_index.fetch_add()
        while i < len(post.attachments):
            while True:
                attachment = post.attachments[i]
                savepath = postdir + "/" + attachment[1]
                print(attachment[0])
                if os.path.exists(savepath):
                    break
                # print(attachment[0], attachment[1])
                if not download(attachment[0], savepath):
                    failed = True
            i = job_index.fetch_add()

    run_workers(worker_main, 4)

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
