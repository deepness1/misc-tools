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
    return strlib.build_dirname_from_parts(work.create_date[:10], title, work.id)


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
