import sys

import strlib

import fanbox


def update_user(cid, savedir, recorddir):
    downloaded = strlib.list_downloaded_works(recorddir)
    for post_id in fanbox.list_posts(cid):
        if post_id in downloaded:
            continue

        post = fanbox.Post(post_id)
        if post.title == None:
            continue
        print("*", post.title)
        fanbox.dump_post(post, savedir)
        strlib.append_downloaded_works(recorddir, post_id)


if len(sys.argv) != 4:
    print("usage dump.py users.csv saveroot recordroot")
    exit(1)

users_file = sys.argv[1]
saveroot = sys.argv[2]
recordroot = sys.argv[3]

for user in open(users_file).readlines():
    if len(user) == 0 or user[0] == "#":
        continue

    [cid, rel] = user[:-1].split(",")
    savedir = saveroot + "/" + rel
    recorddir = recordroot + "/" + rel

    print(rel)
    update_user(cid, savedir, recorddir)
