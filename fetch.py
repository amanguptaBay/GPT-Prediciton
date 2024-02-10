import asyncio
import aiohttp
import time
import logging
import pandas as pd
import bs4
import base64

#Modified from https://stackoverflow.com/a/57129241
async def get_url(url, session):
    try:
        async with session.get(url=url, allow_redirects = True) as response:
            resp = await response.read()
            resp =  str(resp, encoding='ascii', errors='replace')
            return bs4.BeautifulSoup(resp, "html.parser").get_text(strip=True)
    except Exception as e:
        logging.info("Unable to get url {} due to {}.".format(url, e.__class__))


async def __get_url_bodies(urls):
    async with aiohttp.ClientSession() as session:
        ret = await asyncio.gather(*[get_url(url, session) for url in urls])
    return ret

def get_url_bodies(urls):
    return asyncio.run(__get_url_bodies(urls))



organized_news = pd.read_csv("temp/organized_news.csv")
bodies = get_url_bodies(list(organized_news["proper_link"]))
organized_news["bodies"] = bodies
organized_news.to_csv("temp/organized_news_with_article_bodies.csv")
end = time.time()

