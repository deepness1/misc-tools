import sys
import os

import strlib

import tw

scraper = tw.login()


def merge_replies(posts):
    for i in range(len(posts) - 1, -1, -1):
        if not posts[i].reply_of:
            print(posts[i].post_id, "is not reply")
            continue
        posts[i].merged = False
        print(posts[i].post_id, "is reply of ", posts[i].reply_of)

        parent_post = None
        for j in range(i - 1, -1, -1):
            if posts[i].reply_of == posts[j].post_id:
                parent_post = posts[j]
                break
        if not parent_post:
            print("parent post missing, skipping:", posts[i].post_id)
            continue
        print(parent_post.post_id, "is parent")

        parent_post.full_text += "\n" + posts[i].full_text
        parent_post.photos += posts[i].photos
        parent_post.videos += posts[i].videos
        posts[i].merged = True


def update_user(user_id, savedir, recorddir, merge_reply):
    downloaded = strlib.list_downloaded_works(recorddir)
    last_post_id = int(downloaded[-1]) if len(downloaded) != 0 else 0
    posts = tw.list_posts(scraper, user_id, last_post_id)
    if merge_reply:
        merge_replies(posts)
    for post in posts:
        if post.post_id in downloaded:
            continue
        if post.reply_of and post.merged:
            strlib.append_downloaded_works(recorddir, post.post_id)
            continue

        print("*", post.date, post.full_text[:20].replace("\n", ""))
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

    [user_id, rel, merge_reply] = user[:-1].split(",")
    savedir = saveroot + "/" + rel
    recorddir = recordroot + "/" + rel

    print(rel)
    update_user(user_id, savedir, recorddir, merge_reply == "1")
