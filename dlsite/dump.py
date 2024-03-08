import sys
import os

import strlib
import fetch

import dlsite


def download(url, path):
    res = fetch.request(url)
    if res == None:
        print("request failed")
        return False
    open(path, "wb").write(res.content)
    return True


def dump_work(work):
    info_dir = "{} {}/info".format(work.date, strlib.canonicalize_filename(work.title))
    if os.path.exists(info_dir):
        print("path exists")
        return

    os.makedirs(info_dir)
    open(info_dir + "/info.txt", "w").write(work.desc.replace("\r", ""))
    if not download(work.samples[0], info_dir + "/cover.jpg"):
        return
    for i in range(len(work.samples) - 1):
        filename = info_dir + f"/sample-{i:03}.jpg"
        download(work.samples[i + 1], filename)


for w in sys.argv[1:]:
    print(w)
    try:
        work = dlsite.Work(w)
        dump_work(work)
    except Exception as e:
        print(e)
        continue
