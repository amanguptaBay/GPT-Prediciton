import typing
import yfinance as yf
from gnews import GNews
import pandas as pd
import logging
import multiprocessing as mp
from datetime import datetime, timedelta
import dateutil.parser
import os
import collections

def get_ticker_data(ticker, start_date, end_date):
    #Get Company stock data and ensure its not corrupted
    stock_data = yf.Tickers(ticker).history(period = "1d", start=start_date, end=end_date)

    #Cleans up the date column
    stock_data = stock_data.reset_index()
    stock_data["Date"] = stock_data["Date"].dt.date
    stock_data.set_index("Date")
    return stock_data

def list_bulk_delete(indices, list):
    """
        :arg indices: List of indexes to be removed from the list
        :arg list: List which is to be operated on
        Function removes the indices from the list, in place on the list object
    """
    for idx in sorted(indices, reverse=True):
        del list[idx]
    

def fetch_news(search_topic,start_date, end_date, max_results):
    google_news = GNews(language = "en", max_results=max_results, start_date=(start_date.year, start_date.month, start_date.day), end_date=(end_date.year, end_date.month, end_date.day))
    apple_news = google_news.get_news(search_topic)

    indices_to_delete = []
    logging.info(f"Succesfully retrieved {start_date} to {end_date}")
    for index, article in enumerate(apple_news):
        retrieved_article = google_news.get_full_article(article["url"])
        if retrieved_article is None:
            indices_to_delete.append(index)
            continue
        article["fetched_title"] = retrieved_article.title 
        article["fetched_body"] = retrieved_article.text 
    list_bulk_delete(indices_to_delete, apple_news)
    return pd.DataFrame(apple_news)

def parallel_fetch_news_runner(search_topic, start, end, max_results, queue):
    queue.put(fetch_news(search_topic, start, end, max_results))

def parallel_fetch_news(search_topic: str, bins:typing.List[typing.Tuple[datetime, datetime]], results_per_bin = 10):
    output = mp.Queue()
    processes = [mp.Process(target=parallel_fetch_news_runner, args = (search_topic, start, end, results_per_bin, output)) for start, end in bins]
    for p in processes:
        p.start()
    for p in processes:
        p.join(1)
    out = [output.get() for p in processes]
    return pd.concat(out, ignore_index=True)

def split_weeks(start_date, end_date):
    """
        From GPT, tested and works correctly
        From start_date to end_date splits the week into bins from Sunday to Saturday
    """
    current_date = start_date

    while current_date <= end_date:
        week_start = current_date - timedelta(days=current_date.weekday() + 1)  # Adjust to start from Sunday
        week_end = week_start + timedelta(days=6)  # Saturday
        if week_end > end_date:
            week_end = end_date
        yield (week_start, week_end)
        current_date = week_end + timedelta(days=2)  # Start next range from next day

def batched(iter, batch_size):
    temp = []
    for i in iter:
        temp.append(i)
        if len(temp) == batch_size:
            yield temp
            temp = []
    yield temp

def main():
    os.makedirs("./.data", exist_ok=True)
    STOCK_DATA_FILE_PATH = ".data/stock_data.pickle"
    NEWS_ARTICLE_FILE_PATH = ".data/organized_news.pickle"
    logging.basicConfig(filename='fetch.log', encoding='utf-8', level=logging.DEBUG)
    if not os.path.isfile(STOCK_DATA_FILE_PATH):
        logging.info("Starting script to get Apple stock data")
        start_date, end_date = "2017-6-12", "2023-6-4"
        stock_data = get_ticker_data("AAPL MSFT AMZN GOOGL ^NDX ^GSPC", start_date, end_date)
        logging.info("Retrieved ticker data")
        stock_data.to_pickle(STOCK_DATA_FILE_PATH)
        logging.debug("Retrieved Stock Data")
    else:
        stock_data = pd.read_pickle(STOCK_DATA_FILE_PATH)
        stock_data["Date"] = pd.to_datetime(stock_data["Date"])
    
    logging.debug(stock_data)
    crawl_start, crawl_end = stock_data["Date"].min(), stock_data["Date"].max()
    if os.path.isfile(NEWS_ARTICLE_FILE_PATH):
        logging.info("Building on existing news csv")
        existing_news = pd.read_pickle(NEWS_ARTICLE_FILE_PATH)
        last_date_with_news = max(existing_news["published date"])
        logging.info(f"Last Date We Have News From is {last_date_with_news}")
        crawl_start = max(last_date_with_news.tz_localize(None), crawl_start)
    else:
        existing_news = pd.DataFrame()

    for binSet in batched(split_weeks(crawl_start, crawl_end), 20):
        for topic in stock_data["Close"].columns:
            update = parallel_fetch_news(search_topic=topic, bins = binSet, results_per_bin=5)
            update["Topic"] = topic
            update["published date"] = update["published date"].apply(dateutil.parser.parse)
            new_news = pd.concat([existing_news, update],ignore_index=True)
            logging.info(f"Wrote batch from {binSet[0][0]} to {binSet[-1][-1]} to file system")
            new_news.to_pickle(NEWS_ARTICLE_FILE_PATH)
            existing_news = new_news
    return existing_news

if __name__ == "__main__":
    main()
