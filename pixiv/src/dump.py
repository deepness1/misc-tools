import sys
import time

import strlib

import pixiv


def check_tag(whitelist_tags, blacklist_tags, tags):
    for tag in whitelist_tags:
        if not tag in tags:
            return False
    for tag in blacklist_tags:
        if tag in tags:
            return False
    return True


def update_user(apis, module, uid, whitelist_tags, blacklist_tags, savedir, recorddir):
    downloaded = strlib.list_downloaded_works(recorddir)
    for work in module.list_works(apis, uid):
        if str(work.id) in downloaded:
            continue
        if not check_tag(whitelist_tags, blacklist_tags, [tag.name for tag in work.tags]):
            continue

        print("*", work.title)
        pixiv.dump_work(apis, module, work, savedir)
        strlib.append_downloaded_works(recorddir, work.id)
        time.sleep(10)


if len(sys.argv) != 5:
    print("usage dump.py illust|novel users.csv saveroot recordroot")
    exit(1)

match sys.argv[1]:
    case "illust":
        import illust as module
    case "novel":
        import novel as module
    case _:
        print("unknown module", sys.argv[1])
        exit(1)
users_file = sys.argv[2]
saveroot = sys.argv[3]
recordroot = sys.argv[4]

apis = pixiv.APIs()
apis.login()

for user in open(users_file).readlines():
    if len(user) == 0 or user[0] == "#":
        continue

    elms = user[:-1].split(",")
    match len(elms):
        case 2:
            [uid, rel] = elms
            strwtags = ""
            strbtags = ""
        case 3:
            [uid, rel, strwtags] = elms
            strbtags = ""
        case 4:
            [uid, rel, strwtags, strbtags] = elms
        case _:
            print("invalid line in csv")

    savedir = saveroot + "/" + rel
    recorddir = recordroot + "/" + rel

    print(rel)
    wtags = strwtags.split(":") if len(strwtags) != 0 else []
    btags = strbtags.split(":") if len(strbtags) != 0 else []
    update_user(apis, module, uid, wtags, btags, savedir, recorddir)
