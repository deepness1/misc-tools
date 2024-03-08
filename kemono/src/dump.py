import sys

import strlib

import download
import kemono


def update_user(site, uid, savedir, recorddir):
    downloaded = strlib.list_downloaded_works(recorddir)
    for pid in kemono.list_post_urls(site, uid):
        if pid in downloaded:
            continue

        post = kemono.Post(site, uid, pid)
        if kemono.save_post(post, savedir):
            strlib.append_downloaded_works(recorddir, pid)


if len(sys.argv) != 4:
    print("usage dump.py users.csv saveroot recordroot")
    exit(1)

users_file = sys.argv[1]
saveroot = sys.argv[2]
recordroot = sys.argv[3]

for user in open(users_file).readlines():
    if len(user) == 0 or user[0] == "#":
        continue

    [site, uid, rel] = user[0:-1].split(",")
    savedir = saveroot + "/" + rel
    recorddir = recordroot + "/" + rel

    print(rel)
    update_user(site, uid, savedir, recorddir)
