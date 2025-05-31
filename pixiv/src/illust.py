import os
import subprocess
import shutil

import urllib3
import pixivpy3 as ppy

import retry


def paginate(apis, uid, category):
    json = None

    def update_json(**kwargs):
        nonlocal json
        try:
            json = apis.aapi.user_illusts(**kwargs)
        except ppy.utils.PixivError:
            return False
        return json.illusts != None

    retry.until_success(update_json, user_id=uid, type=category)
    works = []
    while True:
        works += json.illusts
        if json.next_url == None:
            break

        next_qs = apis.aapi.parse_qs(json.next_url)
        retry.until_success(update_json, **next_qs)

    return works


def list_works(apis, uid):
    return paginate(apis, uid, "illust") + paginate(apis, uid, "manga")


def dump_ugoira_as_movie(apis, work, basedir):
    tmpdir = "/tmp/pixiv"
    os.makedirs(tmpdir, exist_ok=True)
    ugoira = apis.aapi.ugoira_metadata(work.id).ugoira_metadata
    url = work.meta_single_page.original_image_url.rsplit("0", 1)

    with open("/tmp/pixiv/files", "w") as files:
        for frame in ugoira.frames:
            frame_number = int(frame.file.rsplit(".", 1)[0])
            frame_url = f"{url[0]}{frame_number}{url[1]}"
            apis.aapi.download(frame_url, "", tmpdir, frame.file)
            files.write(f"file '{frame.file}'\n")
            files.write(f"duration 0.0{frame.delay}\n")
        files.write(f"file '{ugoira.frames[-1].file}'\n")

    savename = os.path.abspath(os.path.join(basedir, "ugoira.mp4"))
    r = subprocess.run(
        [
            "ffmpeg",
            "-f",
            "concat",
            "-i",
            "files",
            "-vsync",
            "vfr",
            "-c",
            "copy",
            str(savename),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=tmpdir,
    )

    shutil.rmtree(tmpdir)
    return True


def aapi_download(apis, url, basedir, savename):
    while True:
        try:
            apis.aapi.download(url, "", basedir, savename)
            break
        except urllib3.exceptions.IncompleteRead:
            print("failed to download image, retrying")
            sleep(1)


def dump_work(apis, work, basedir):
    if work.type == "ugoira":
        return dump_ugoira_as_movie(apis, work, basedir)

    if work.page_count == 1:
        url = work.meta_single_page.original_image_url
        savename = "001" + os.path.splitext(url)[1]
        aapi_download(apis, url, basedir, savename)
    else:
        page = 1
        for img in work.meta_pages:
            url = img.image_urls.original
            savename = f"{page:03d}" + os.path.splitext(url)[1]
            aapi_download(apis, url, basedir, savename)
            page += 1
    return True
