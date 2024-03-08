import os

import pixivpy3 as ppy
import creds
import strlib

import retry


class APIs:
    def login(self):
        self.api = ppy.api
        self.aapi = ppy.AppPixivAPI()
        self.aapi.auth(refresh_token=creds.pixiv_refresh_token)


def build_dirname(module, work):
    title = strlib.canonicalize_filename(work.title)
    date = work.create_date[:10]
    dirname = f"{date} {title} {work.id}"
    if len(dirname.encode(encoding="utf-8")) > 255:
        reserved = f"{date} ... {work.id}".encode(encoding="utf-8")
        trtitle = strlib.truncate_by_concating(title, 255 - len(reserved)) + "..."
        dirname = f"{date} {trtitle} {work.id}"
    return dirname


def dump_work(apis, module, work, savedir):
    dirname = build_dirname(module, work)
    basedir = savedir + "/" + dirname
    os.makedirs(basedir, exist_ok=True)
    if work.caption != None and len(work.caption) != 0:
        cappath = basedir + "/" + "caption.txt"
        caption = work.caption.replace("<br />", "\n")
        open(cappath, "w", encoding="utf-8").write(caption)

    def download():
        try:
            return module.dump_work(apis, work, basedir)
        except ppy.PixivError:
            print("connection closed, retrying...")
            return False

    retry.until_success(download)
