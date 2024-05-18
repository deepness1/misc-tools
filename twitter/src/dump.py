import sys
import os

import strlib

import tw

scraper = tw.login()


def update_user(uid, savedir, recorddir):
    downloaded = strlib.list_downloaded_works(recorddir)
    for post in tw.list_posts(scraper, uid):
        if post.post_id in downloaded:
            continue

        print("*", post.date, post.full_text)
        tw.dump_post(post, savedir)
        strlib.append_downloaded_works(recorddir, post.post_id)


if len(sys.argv) != 4:
    print("usage dump.py users.csv saveroot recordroot")
    exit(1)

users_file = sys.argv[1]
saveroot = sys.argv[2]
recordroot = sys.argv[3]

for user in open(users_file).readlines():
    if len(user) == 0 or user[0] == "#":
        continue

    [uid, rel] = user[:-1].split(",")
    savedir = saveroot + "/" + rel
    recorddir = recordroot + "/" + rel

    print(rel)
    update_user(uid, savedir, recorddir)
