import sys
import os
import calendar
import re
import time
import html
from urllib.parse import urlparse

import strlib
from twitter.scraper import Scraper
from twitter.util import find_key
from twitter.util import get_cursor
from twitter.util import batch_ids
from twitter.constants import Operation

import creds
import fetch

import newscraper


def login():
    cookies = {
        "auth_token": creds.twitter_auth_token,
        "ct0": creds.twitter_ct0,
    }
    return Scraper(cookies=cookies, save=False, debug=False)


def convert_calender(text):
    arr = text.split(" ")
    month = list(calendar.month_abbr).index(arr[1])
    day = int(arr[2])
    time = arr[3]
    year = int(arr[5])
    return f"{year:04}-{month:02}-{day:02} {time}"


class Post:
    def __init__(self, tweet):
        self.post_id = tweet["rest_id"]
        legacy = tweet["legacy"]
        self.full_text = html.unescape(legacy["full_text"])
        self.date = convert_calender(legacy["created_at"])
        self.reply_of = legacy.get("in_reply_to_status_id_str")

        self.photos = []
        self.videos = []

        for key, value in legacy["entities"].items():
            match key:
                case "media":
                    self.parse_medias(value)
                case "urls":
                    self.parse_urls(value)
            if key != "media":
                continue

    def parse_medias(self, medias):
        for media in medias:
            match media["type"]:
                case "photo":
                    self.photos.append(media["media_url_https"] + "?name=orig")
                case "video":
                    url = None
                    max_bitrate = 0
                    for v in media["video_info"]["variants"]:
                        bitrate = v.get("bitrate")
                        if not bitrate:
                            continue
                        if bitrate > max_bitrate:
                            url = v["url"]
                    if not url:
                        print("no url available in video")
                        exit(1)
                    self.videos.append(url)
                case _:
                    print("unknown media type")
                    print(media)
                    exit(1)
            # remove short url from text
            short_url = media["url"]
            self.full_text = self.full_text.replace(short_url, "")

    def parse_urls(self, urls):
        for node in urls:
            short_url = node["url"]
            full_url = node["expanded_url"]
            self.full_text = self.full_text.replace(short_url, full_url)


def wait_until_rate_unlimit(scraper, operation):
    limits = scraper.rate_limits[operation[2]]
    duration = int(limits["x-rate-limit-reset"] - time.time()) + 1
    print(f"resuming in {duration} secs...")
    time.sleep(duration)


def complete_missing_reply_parents(scraper, posts):
    # collect missing posts
    post_ids = set()
    for post_id, post in posts.items():
        if not post.reply_of:
            continue

        parent_post = posts.get(int(post.reply_of))
        if parent_post:
            continue

        print(post.reply_of, " parent post missing")
        post_ids.add(int(post.reply_of))

    if len(post_ids) == 0:
        return posts

    # fetch them
    cursor = None
    batches = batch_ids(post_ids)
    prev_posts_size = len(posts)
    for batch in batches:
        data = newscraper.get_tweets(scraper, cursor, batch)
        if not data or data.status_code != 200:
            wait_until_rate_unlimit(scraper, Operation.TweetResultsByRestIds)
            continue
        json = data.json()
        for tweet in json["data"]["tweetResult"]:
            result = tweet.get("result")
            post = Post(result)
            posts[int(post.post_id)] = post

    if prev_posts_size != len(posts):
        # collected posts may also refer to missing posts
        posts = complete_missing_reply_parents(scraper, posts)

    return posts


def list_posts(scraper, user_id, post_id_min):
    posts = {}
    cursor = None
    while True:
        data = newscraper.get_user_tweets(scraper, cursor, user_id)
        if not data or data.status_code != 200:
            wait_until_rate_unlimit(scraper, Operation.UserTweets)
            continue
        json = data.json()

        cursor = get_cursor(json)

        post_id_min_reached = False
        results = find_key(json, "tweet_results")
        if len(results) == 0:
            break
        for tweet in results:
            post = Post(tweet["result"])
            key = int(post.post_id)
            if key <= post_id_min:
                post_id_min_reached = True
                break
            posts[key] = post

        if post_id_min_reached:
            break

    return complete_missing_reply_parents(scraper, posts)


def post_to_dirname(post):
    text = post.full_text
    text = text.replace("\n", "")  # delete line breaks
    text = re.sub(r"https?:\/\/([^ \n])*", "", text, flags=re.MULTILINE)  # delete links
    text = re.sub(r"#\w\w+", "", text)  # delete hashtags
    text = strlib.canonicalize_filename(text)
    return strlib.build_dirname_from_parts(post.date, text, post.post_id)


def dump_post(post, basedir):
    dirname = post_to_dirname(post)
    postdir = os.path.join(basedir, dirname)
    os.makedirs(postdir, exist_ok=True)
    if len(post.full_text) != 0:
        filepath = os.path.join(postdir, "post.txt")
        open(filepath, "wt").write(post.full_text)
    if post.reply_of:
        filepath = os.path.join(postdir, "reply-of.txt")
        open(filepath, "wt").write(post.reply_of)

    for i in range(len(post.photos)):
        url = post.photos[i]
        res = fetch.request(url)
        ext = os.path.splitext(urlparse(url).path)[1]
        savepath = postdir + f"/photo-{i:03}{ext}"
        open(savepath, "wb").write(res.content)

    for i in range(len(post.videos)):
        url = post.videos[i]
        res = fetch.request(url)
        ext = os.path.splitext(urlparse(url).path)[1]
        savepath = postdir + f"/video-{i:03}{ext}"
        open(savepath, "wb").write(res.content)


def main():
    scraper = login()

    for tweet in scraper.tweets_by_ids(sys.argv[1:]):
        for result in tweet["data"]["tweetResult"]:
            result = result["result"]
            print(result)

            post = Post(result)
            print("*", post.date, post.full_text)
            dump_post(post, ".")


if __name__ == "__main__":
    main()
