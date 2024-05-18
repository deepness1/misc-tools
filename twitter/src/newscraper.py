# twitter-api-client does not expose cursor, which is needed for query large amount of tweets
# thus, we do not use builtin pagenater
# this is a custom partial reinplementation of scraper.py

import asyncio

import httpx
from twitter.scraper import Scraper
from twitter.util import find_key
from twitter.util import get_headers
from twitter.constants import Operation


async def process(scraper, operation, cursor, **kwargs):
    headers = get_headers(scraper.session)
    cookies = scraper.session.cookies
    async with httpx.AsyncClient(
        limits=httpx.Limits(max_connections=500),
        headers=headers,
        cookies=cookies,
        timeout=20,
    ) as c:
        return await scraper._query(c, operation, cursor=cursor, **kwargs)
        return await paginate(scraper, c, operation, cursor, **kwargs)


def run(scraper, operation, cursor, **kwargs):
    keys, qid, name = operation
    return asyncio.run(process(scraper, operation, cursor, **kwargs))


def get_user_tweets(scraper, cursor, user_id):
    return run(scraper, Operation.UserTweets, cursor, userId=user_id)


def get_tweets(scraper, cursor, post_ids):
    return run(scraper, Operation.TweetResultsByRestIds, cursor, tweetIds=post_ids)
