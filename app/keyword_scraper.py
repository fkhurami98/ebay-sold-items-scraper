import csv
import os
import random
import re
import time
import urllib.parse
from datetime import datetime
import pika
from bs4 import BeautifulSoup
import requests
from fake_useragent import UserAgent

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from db.db_utils import insert_data


def get_number_of_search_results(soup: BeautifulSoup) -> int:
    """
    Extracts the number of search results from the eBay page's soup object.
    """
    # Find the correct <script> tag - adjust the criteria as needed for your specific case
    script_tag = soup.find("script", string=re.compile(r'"text":"\d+ results"'))
    if script_tag:
        script_content = script_tag.string
        results_pattern = re.compile(r'"text":"(\d+) results"')
        match = results_pattern.search(script_content)
        if match:
            return int(match.group(1))
    return None


def extract_data(soup: BeautifulSoup) -> list:
    listings = []

    for listing in soup.select(".s-item__wrapper"):
        item_condition = (
            listing.select_one(".s-item__subtitle .SECONDARY_INFO").text.strip()
            if listing.select_one(".s-item__subtitle .SECONDARY_INFO")
            else "Not specified"
        )
        listing_type = (
            listing.select_one(".s-item__detail .BOLD").text.strip()
            if listing.select_one(".s-item__detail .BOLD")
            else "Not specified"
        )
        shipping_detail = (
            listing.select_one(".s-item__logisticsCost").text.strip()
            if listing.select_one(".s-item__logisticsCost")
            else "Shipping details not specified"
        )
        price = (
            listing.select_one(".s-item__price").text.strip()
            if listing.select_one(".s-item__price")
            else "Price not specified"
        )
        seller_info = (
            listing.select_one(".s-item__seller-info-text").text.strip()
            if listing.select_one(".s-item__seller-info-text")
            else "Seller ID not specified"
        )

        # Find the element that contains the sold date
        sold_date_element = listing.select_one(".s-item__title--tag .POSITIVE")

        # Check if the element exists and extract the text
        if sold_date_element:
            sold_date_text = sold_date_element.text.strip().replace("Sold", "").strip()
            try:
                sold_date = datetime.strptime(sold_date_text, "%d %b %Y").strftime(
                    "%Y-%m-%d"
                )
            except ValueError:
                sold_date = "Invalid date format"
        else:
            sold_date = "Not specified"

        title = (
            listing.select_one(".s-item__image img")["alt"].strip()
            if listing.select_one(".s-item__image img")
            else "Title not specified"
        )

        # Append the extracted data to the listings list
        listings.append(
            {
                "title": title,
                "seller_info": seller_info,
                "price": price,
                "shipping_detail": shipping_detail,
                "listing_type": listing_type,
                "item_condition": item_condition,
                "sold_date": sold_date,
            }
        )
    return listings


def save_to_csv(data: list, filename: str, include_headers: bool = True) -> None:
    file_exists: bool = os.path.isfile(filename)

    with open(filename, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        if include_headers and not file_exists:
            writer.writerow(
                [
                    "Title",
                    "Price",
                    "Seller Info",
                    "Shipping Detail",
                    "Listing Type",
                    "Item Condition",
                    "Sold Date",
                ]
            )
        for item in data:
            writer.writerow(
                [
                    item["title"],
                    item["price"],
                    item["seller_info"],
                    item["shipping_detail"],
                    item["listing_type"],
                    item["item_condition"],
                    item["sold_date"],
                ]
            )


def start_scraping(keyword):
    print(f"[STARTING] scraping for: {keyword}")

    user_agent = UserAgent()

    max_pages: int = 1
    items_per_page: int = 120  # 60, 120, 240

    date: str = datetime.now().strftime("%Y-%m-%d")

    filename: str = f"ebay_data_{keyword.replace(' ', '_')}_{date}.csv"

    encoded_keyword: str = urllib.parse.quote_plus(keyword)

    base_url: str = f"https://www.ebay.co.uk/sch/i.html?_from=R40&_nkw={encoded_keyword}&_sacat=0&LH_Sold=1&LH_Complete=1&LH_ItemCondition=1000&_pgn=1&_ipg={items_per_page}"

    headers = {"User-Agent": user_agent.random}

    response = requests.get(url=base_url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")

    number_of_searches: int = get_number_of_search_results(soup)

    if number_of_searches is not None:
        max_pages = min(number_of_searches // items_per_page, max_pages)
        for page_number in range(1, max_pages + 1):
            print(f"[WORKING] Scraping page {page_number} for {keyword}...")
            base_url = f"https://www.ebay.co.uk/sch/i.html?_from=R40&_nkw={encoded_keyword}&_sacat=0&LH_Sold=1&LH_Complete=1&LH_ItemCondition=1000&rt=nc&_pgn={page_number}&_ipg={items_per_page}"
            headers = {"User-Agent": user_agent.random}
            response = requests.get(url=base_url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            listings = extract_data(soup)
            # insert_data(listings)
            if page_number == 1:
                save_to_csv(listings, filename, include_headers=True)
            else:
                save_to_csv(listings, filename, include_headers=False)
            print(
                f"[SUCCESS] Data from page {page_number} for {keyword} saved to '{filename}'.\n"
            )

            time.sleep(random.uniform(1, 10))
    else:
        print(
            f"[FINISHED] Couldn't determine the number of searches for '{keyword}'. Skipping..."
        )


def callback(ch, method, properties, body):
    keyword = body.decode()
    print(f"\n[RECEIVED] keyword: {keyword}")
    try:
        start_scraping(keyword)
    except Exception as e:
        print(f"Error during scraping for keyword '{keyword}': {e}")


def main():
    # Use the below connection object if running locally without docker
    # connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))

    rabbitmq_host = os.getenv("RABBITMQ_HOST", "localhost")
    rabbitmq_user = "user"  # Username as set in docker-compose
    rabbitmq_password = "password"  # Password as set in docker-compose

    credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_password)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=rabbitmq_host, credentials=credentials)
    )

    channel = connection.channel()

    channel.queue_declare(queue="ebay_keyword_queue")

    channel.basic_consume(
        queue="ebay_keyword_queue", on_message_callback=callback, auto_ack=True
    )

    print("Waiting for messages. To exit press CTRL+C")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
