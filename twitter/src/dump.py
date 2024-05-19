import sys
import os

import strlib

import tw

scraper = tw.login()


# add required fields for construct_reply_tree
def append_post_fields(posts):
    for post_id, post in posts.items():
        post.merged = False
        post.replies = []


def construct_reply_tree(posts):
    for post_id, post in posts.items():
        if not post.reply_of:
            print(post.post_id, "is not reply")
            continue
        print(post.post_id, "is reply of ", post.reply_of)

        parent_post = posts.get(int(post.reply_of))
        if not parent_post:
            print("parent post missing, skipping:", post.post_id)
            continue
        print(parent_post.post_id, "is parent")

        parent_post.replies.append(int(post_id))


def merge_replies(posts, post):
    current_node = post
    while True:
        match len(current_node.replies):
            case 0:
                break
            case 1:
                current_node = posts[current_node.replies[0]]
            case _:
                print(current_node.post_id, " has multiple replies, cannot merge")
                return

    current_node = post
    while True:
        if len(current_node.replies) == 0:
            break
        current_node = posts[current_node.replies[0]]
        post.full_text += "\n" + current_node.full_text
        post.photos += current_node.photos
        post.videos += current_node.videos
        current_node.merged = True


def update_user(user_id, savedir, recorddir, merge_reply):
    downloaded = strlib.list_downloaded_works(recorddir)
    last_post_id = int(downloaded[-1]) if len(downloaded) != 0 else 0
    posts = tw.list_posts(scraper, user_id, last_post_id)
    append_post_fields(posts)
    if merge_reply:
        construct_reply_tree(posts)
    posts_list = sorted(list(posts.values()), key=lambda post: int(post.post_id))
    for post in posts_list:
        if post.post_id in downloaded:
            continue
        if post.merged:
            strlib.append_downloaded_works(recorddir, post.post_id)
            continue

        print("*", post.date, post.full_text[:20].replace("\n", ""))
        merge_replies(posts, post)
        tw.dump_post(post, savedir)
        continue
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
