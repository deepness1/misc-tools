import os

import retry


def paginate(apis, uid):
    json = None

    def update_json(**kwargs):
        nonlocal json
        json = apis.aapi.user_novels(**kwargs)
        return json.novels != None

    retry.until_success(update_json, user_id=uid)
    works = []
    while True:
        works += json.novels
        if json.next_url == None:
            break

        next_qs = apis.aapi.parse_qs(json.next_url)
        retry.until_success(update_json, **next_qs)

    return works


def list_works(apis, uid):
    return paginate(apis, uid)


def dump_work(apis, work, basedir):
    image_url = work.image_urls.large
    apis.aapi.download(image_url, "", basedir, "cover" + os.path.splitext(image_url)[1])

    json = apis.aapi.webview_novel(novel_id=work.id, raw=False)
    text = json.text
    if text == None:
        print("empty novel text")
        return False

    novelpath = basedir + "/novel.txt"
    open(novelpath, "w", encoding="utf-8").write(text)
    return True
