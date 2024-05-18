import sys
import os
import calendar
import re
from urllib.parse import urlparse

import strlib
from twitter.scraper import Scraper
from twitter.util import find_key

import creds
import fetch


def login():
    cookies = {
        "auth_token": creds.twitter_auth_token,
        "ct0": creds.twitter_ct0,
    }
    return Scraper(cookies=cookies, save=False)


def convert_calender(text):
    arr = text.split(" ")
    month = list(calendar.month_abbr).index(arr[1])
    day = int(arr[2])
    time = arr[3]
    year = int(arr[5])
    return f"{year:04}-{month:02}-{day:02} {time}"


class Post:
    def __init__(self, tweet):
        self.post_id = int(tweet["rest_id"])
        legacy = tweet["legacy"]
        self.full_text = legacy["full_text"]
        self.date = convert_calender(legacy["created_at"])

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


def list_posts(scraper, uid):
    # for tweet in scraper.tweets_by_ids([1791768715647922576]):
    #     for result in tweet["data"]["tweetResult"]:
    #         result = result["result"]
    #         print(result)
    #         post = Post(result)
    #         return [post]

    posts = []
    for tweet in find_key(scraper.tweets_and_replies([uid]), "tweet_results"):
        result = tweet.get("result")
        if not result:
            print("unexpected tweet_result")
            exit(1)
        posts.append(Post(result))
    return posts


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

            post = Post(result)
            print("*", post.date, post.full_text)
            dump_post(post, ".")


if __name__ == "__main__":
    main()
