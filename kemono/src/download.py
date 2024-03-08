import sys
import os
import glob
import threading

import fetch
import strlib

import kemono
import atomic


def download(url, path):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "*/*",
        "Referer": kemono.origin + "/",
    }
    res = fetch.request(url, headers=headers)
    if res == None:
        print("request failed")
        return False
    open(path, "wb").write(res.content)
    return True


def post_to_dirname(post):
    title = strlib.canonicalize_filename(post.title)
    meta_size = len(f"{post.date[:10]}  {post.pid}".encode(encoding="utf-8"))
    title_size = len(title.encode(encoding="utf-8"))
    if meta_size + title_size > 255:
        title = strlib.truncate_by_concating(title, 255 - meta_size)[:-3] + "..."
    return f"{post.date[:10]} {title} {post.pid}"


def is_downloadable_link(link):
    if link.startswith(kemono.origin):
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
