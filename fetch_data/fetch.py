import yfinance as yf
from gnews import GNews
import pandas as pd
import logging
import multiprocessing as mp
from datetime import datetime, timedelta
import dateutil.parser
import os


def partition_date_range(start_date, end_date, n):
    """
        From Chat GPT but tested in notebook and modified to work as intended. 
        Partitions date range into n ranges where the ranges are [start_range, end_range) or for a range per day whichever is larger
    """
   
    end_date = end_date + timedelta(days=1)
    
    # Calculate total number of days in the date range
    total_days = (end_date - start_date).days
    n = total_days if n > total_days else n
    # Calculate the number of days for each partition
    days_per_partition = total_days // n
    
    # Calculate the number of remaining days
    remaining_days = total_days % n
    
    # Initialize list to store partition ranges
    partitions = []
    
    # Generate partition ranges
    current_date = start_date
    for _ in range(n):
        # Calculate end date for the current partition
        end_partition_date = current_date + timedelta(days=days_per_partition)
        
        # Adjust end date if there are remaining days
        if remaining_days > 0:
            end_partition_date += timedelta(days=1)
            remaining_days -= 1
        
        # Append the current partition range to the list
        partitions.append((current_date, end_partition_date))
        
        # Move to the start of the next partition
        current_date = end_partition_date
    
    return partitions


def get_ticker_data(ticker):
    #Get Company stock data and ensure its not corrupted
    stock_data = yf.Ticker(ticker).history(period = "5y")
    assert not stock_data.empty

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
    

def fetch_news(search_topic,start_date, end_date):
    google_news = GNews(language = "en", max_results=1000, start_date=(start_date.year, start_date.month, start_date.day), end_date=(end_date.year, end_date.month, end_date.day))
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

def parallel_fetch_news_runner(search_topic, start, end, queue):
    queue.put(fetch_news(search_topic, start, end))

def parallel_fetch_news(search_topic,start_date, end_date):
    n = 100
    output = mp.Queue()
    processes = [mp.Process(target=parallel_fetch_news_runner, args = (search_topic, start, end, output)) for start, end in partition_date_range(start_date, end_date, n)]
    for p in processes:
        p.start()
    for p in processes:
        p.join(10)
    
    out = [output.get() for p in processes]
    return pd.concat(out, ignore_index=True)

def main():
    os.makedirs("./.temp", exist_ok=True)
    STOCK_DATA_FILE_PATH = ".temp/stock_data.csv"
    NEWS_ARTICLE_FILE_PATH = ".temp/organized_news.csv"
    logging.basicConfig(filename='fetch.log', encoding='utf-8', level=logging.DEBUG)
    if not os.path.isfile(STOCK_DATA_FILE_PATH):
        logging.info("Starting script to get Apple stock data")
        stock_data = get_ticker_data("AAPL")
        logging.info("Retrieved Apple ticker data")
        stock_data.to_csv(STOCK_DATA_FILE_PATH)
        logging.debug("Retrieved Stock Data")
    else:
        stock_data = pd.read_csv(STOCK_DATA_FILE_PATH)
        stock_data["Date"] = pd.to_datetime(stock_data["Date"])
    
    logging.debug(stock_data)
    start_date, end_date = stock_data["Date"].min(), stock_data["Date"].max()

    
    if os.path.isfile(NEWS_ARTICLE_FILE_PATH):
        logging.info("Building on existing news csv")
        existing_news = pd.read_csv(NEWS_ARTICLE_FILE_PATH)
        existing_news.drop([existing_news.columns[0]], axis=1, inplace=True)
        min_date = dateutil.parser.parse(existing_news["published date"].min()).replace(tzinfo=None)
        start_date = max(start_date.to_pydatetime(), min_date)
    else:
        existing_news = pd.DataFrame()
    if start_date >= end_date:
        logging.info("No dates left to crawl")
        return None
    logging.info(f"Crawling from {start_date} to {end_date}")
    update = fetch_news("Apple", start_date, start_date+timedelta(days=10))
    new_news = pd.concat([existing_news, update],ignore_index=True)
    new_news.to_csv(NEWS_ARTICLE_FILE_PATH)
    logging.info("Done with Script")

if __name__ == "__main__":
    main()