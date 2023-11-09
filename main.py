import csv
import os
import random
import re
import time
import urllib.parse
from datetime import datetime
from bs4 import BeautifulSoup
import requests
from fake_useragent import UserAgent

search_keywords: list = [
    "Lego 75280",
    "Lego 75309",
    "Lego 75342",
    "Lego 10497",
    "Lego 76193",
    "Lego 75324",
    "Lego 75339",
    "Lego 75331"
]
max_pages: int = 1
items_per_page: int = 120  # 60, 120, 240


def get_number_of_search_results(soup):
    # Find the correct <script> tag - adjust the criteria as needed for your specific case
    script_tag = soup.find("script", string=re.compile(r'"text":"\d+ results"'))
    if script_tag:
        script_content = script_tag.string
        results_pattern = re.compile(r'"text":"(\d+) results"')
        match = results_pattern.search(script_content)
        if match:
            return int(match.group(1))
    return None


def extract_data(soup):
    listings = []
    for listing in soup.select(".s-item__wrapper"):
        # Extract various details from the listing
        item_condition = listing.select_one(".s-item__subtitle .SECONDARY_INFO").text.strip() if listing.select_one(".s-item__subtitle .SECONDARY_INFO") else "Not specified"
        listing_type = listing.select_one(".s-item__detail .BOLD").text.strip() if listing.select_one(".s-item__detail .BOLD") else "Not specified"
        shipping_detail = listing.select_one(".s-item__logisticsCost").text.strip() if listing.select_one(".s-item__logisticsCost") else "Shipping details not specified"
        price = listing.select_one(".s-item__price").text.strip() if listing.select_one(".s-item__price") else "Price not specified"
        seller_info = listing.select_one(".s-item__seller-info-text").text.strip() if listing.select_one(".s-item__seller-info-text") else "Seller ID not specified"

        # Process the sold date, removing the 'Sold' prefix and converting to standard format
        sold_date_text = listing.select_one(".s-item__title--tag .POSITIVE").text.strip().replace("Sold", "").strip()
        try:
            sold_date = datetime.strptime(sold_date_text, "%d %b %Y").strftime("%Y-%m-%d")
        except ValueError:
            sold_date = "Invalid date format"

        title = listing.select_one(".s-item__image img")["alt"].strip() if listing.select_one(".s-item__image img") else "Title not specified"

        # Append the extracted data to the listings list
        listings.append({
            "title": title,
            "seller_info": seller_info,
            "price": price,
            "shipping_detail": shipping_detail,
            "listing_type": listing_type,
            "item_condition": item_condition,
            "sold_date": sold_date,
        })
    return listings


def save_to_csv(data, filename, include_headers=True):
    # Check if file exists to determine whether to write headers
    file_exists = os.path.isfile(filename)

    with open(filename, "a", newline="", encoding="utf-8") as csvfile:

    with open(filename, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        # Write headers only if the file is newly created
        if include_headers and not file_exists:
            writer.writerow(
                [
                    "Title",
                    "Price",
                    "URL",
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
                    item["url"],
                    item["seller_info"],
                    item["shipping_detail"],
                    item["listing_type"],
                    item["item_condition"],
                    item["sold_date"],
                ]
            )


if __name__ == "__main__":
    # Setup fake user agent for HTTP requests
    user_agent = UserAgent()

    # Iterate over each keyword to scrape data
    for keyword in search_keywords:
        date = datetime.now().strftime("%Y-%m-%d")
        filename = f"ebay_data_{keyword.replace(' ', '_')}_{date}.csv"

        # Encode keyword for URL and setup the search URL
        encoded_keyword = urllib.parse.quote_plus(keyword)
        base_url = f"https://www.ebay.co.uk/sch/i.html?_from=R40&_nkw={encoded_keyword}&_sacat=0&LH_Sold=1&LH_Complete=1&LH_ItemCondition=1000&_pgn=1&_ipg={items_per_page}"
        headers = {"User-Agent": user_agent.random}

        # HTTP request and response parsing
        response = requests.get(url=base_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        # Calculate the number of pages to scrape based on the total search results
        number_of_searches = get_number_of_search_results(soup)
        print(f"[INFO] Total number of searches for '{keyword}':", number_of_searches)

        if number_of_searches is not None:
            max_pages = number_of_searches // items_per_page
            max_pages = max(1, max_pages)  # Ensure at least one page
            print(f"[INFO] Total pages to scrape for '{keyword}':", max_pages)

            # Scrape each page and save data to CSV
            for page_number in range(1, max_pages + 1):
                print(f"[WORKING] Scraping page {page_number} for {keyword}...")

                # Generate the URL for the current page
                base_url = f"https://www.ebay.co.uk/sch/i.html?_from=R40&_nkw={encoded_keyword}&_sacat=0&LH_Sold=1&LH_Complete=1&LH_ItemCondition=1000&rt=nc&_pgn={page_number}&_ipg={items_per_page}"
                headers = {"User-Agent": user_agent.random}
                response = requests.get(url=page_url, headers=headers)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, "html.parser")

                # Extract data and save to CSV
                listings = extract_data(soup)
                if page_number == 1:
                    save_to_csv(listings, filename, include_headers=True)
                else:
                    save_to_csv(listings, filename, include_headers=False)

                print(
                    f"[SUCCESS] Data from page {page_number} for {keyword} saved to '{filename}'."
                )
                time.sleep(random.uniform(1, 10))
            print()
        else:
            print(
                f"[FINISHED] Couldn't determine the number of searches for '{keyword}'. Skipping..."
            )
