import sys
import os

import strlib

import fantia


def update_user(fanclub, savedir, recorddir):
    downloaded = strlib.list_downloaded_works(recorddir)
    # if os.path.isfile('/tmp/cache'):
    #    works = open("/tmp/cache", "rt").read()[1:-1].replace(',','').replace("'",'').split(' ')
    # else:
    #    works = fantia.list_posts(fanclub)
    #    open("/tmp/cache", "wt").write(str(works))
    # for post_id in works:
    for post_id in fantia.list_posts(fanclub):
        if post_id in downloaded:
            continue

        post = fantia.Post(post_id)
        if post.title == None:
            continue
        print("*", post.title)
        fantia.dump_post(post, savedir)
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

    [fanclub, rel] = user[:-1].split(",")
    savedir = saveroot + "/" + rel
    recorddir = recordroot + "/" + rel

    print(rel)
    update_user(fanclub, savedir, recorddir)
