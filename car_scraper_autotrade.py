import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from pymongo import MongoClient
import time
import json
from urllib.parse import urljoin
import re

# MongoDB Setup
client = MongoClient(
    "mongodb+srv://yuva2:yuva123@cluster0.lujyqyz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
db = client["Raava_Sales"]
collection = db["Scraped_Cars"]

# Selenium Setup
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
)


def init_driver():
    """Initialize Selenium WebDriver"""
    driver = webdriver.Chrome(options=chrome_options)
    return driver


def get_car_links(driver, search_url, max_pages=5):
    """Extract all car listing links from search results"""
    car_links = []

    for page in range(1, max_pages + 1):
        page_url = f"{search_url}&page={page}"
        print(f"Scraping search page {page}...")

        driver.get(page_url)
        time.sleep(3)

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'a[data-testid="search-listing-title"]')
                )
            )

            listings = driver.find_elements(
                By.CSS_SELECTOR, 'a[data-testid="search-listing-title"]'
            )

            for listing in listings:
                link = listing.get_attribute("href")
                if link and link not in car_links:
                    car_links.append(link)

            print(f"Found {len(listings)} cars on page {page}")

        except Exception as e:
            print(f"Error on page {page}: {str(e)}")
            break

    return car_links


def scrape_car_details(driver, car_url):
    """Scrape detailed information from individual car page"""
    print(f"Scraping: {car_url}")

    driver.get(car_url)
    time.sleep(4)

    car_data = {
        "url": car_url,
        "title": "",
        "subtitle": "",
        "images": [],
        "key_information": {},
        "pricing": {},
        "overview": {},
        "running_costs": {},
        "seller_info": {},
        "before_you_buy": [],
    }

    try:
        # Extract Title and Subtitle from Pricing Section
        try:
            pricing_section = driver.find_element(
                By.CSS_SELECTOR, 'section[id="pricing"]'
            )

            # Main title
            try:
                title = pricing_section.find_element(By.CSS_SELECTOR, "h1").text
                car_data["title"] = title
                print(f"  ✓ Title: {title}")
            except:
                pass

            # Subtitle (performance/variant)
            try:
                subtitle = pricing_section.find_element(
                    By.CSS_SELECTOR, "div.sc-77l6z-4 span"
                ).text
                car_data["subtitle"] = subtitle
                print(f"  ✓ Subtitle: {subtitle}")
            except:
                pass

            # Main price
            try:
                price = pricing_section.find_element(
                    By.CSS_SELECTOR, 'p[data-testid="advert-price"]'
                ).text
                car_data["pricing"]["price"] = price
                print(f"  ✓ Price: {price}")
            except:
                pass

            # RRP and Savings
            try:
                rrp = pricing_section.find_element(
                    By.CSS_SELECTOR, "p.sc-1ki5s6d-2"
                ).text
                car_data["pricing"]["rrp"] = rrp
            except:
                pass

            try:
                savings = pricing_section.find_element(
                    By.CSS_SELECTOR, "p.sc-1ki5s6d-3"
                ).text
                car_data["pricing"]["savings"] = savings
            except:
                pass

            # Status pill (Brand new - In stock)
            try:
                status = pricing_section.find_element(
                    By.CSS_SELECTOR, 'p[data-testid*="pill"]'
                ).text
                car_data["pricing"]["status"] = status
            except:
                pass

        except Exception as e:
            print(f"  ✗ Error extracting pricing: {str(e)}")

        # Extract Gallery Images
        try:
            # Find all images in the gallery
            image_elements = driver.find_elements(
                By.CSS_SELECTOR, "div.sc-1kcxwnk-2 img"
            )

            for img in image_elements:
                img_src = img.get_attribute("src")
                if img_src and "atcdn.co.uk" in img_src:
                    # Get highest quality
                    high_quality_url = re.sub(r"/w\d+/", "/w800/", img_src)
                    if high_quality_url not in car_data["images"]:
                        car_data["images"].append(high_quality_url)

            print(f"  ✓ Found {len(car_data['images'])} images")
        except Exception as e:
            print(f"  ✗ Error extracting images: {str(e)}")

        # Extract Overview Section
        try:
            overview_section = driver.find_element(
                By.CSS_SELECTOR, 'section[id="overview"]'
            )

            # Extract all overview items using the structure: div.sc-tqnfbs-1
            overview_items = overview_section.find_elements(
                By.CSS_SELECTOR, "div.sc-tqnfbs-1"
            )

            for item in overview_items:
                try:
                    # Label with class sc-tqnfbs-5
                    label = item.find_element(By.CSS_SELECTOR, "p.sc-tqnfbs-5").text
                    # Value with class sc-tqnfbs-6
                    value = item.find_element(By.CSS_SELECTOR, "p.sc-tqnfbs-6").text
                    car_data["overview"][label] = value
                except:
                    pass

            print(f"  ✓ Overview extracted ({len(car_data['overview'])} items)")
        except Exception as e:
            print(f"  ✗ Error extracting overview: {str(e)}")

        # Extract Running Costs
        try:
            running_costs_section = driver.find_element(
                By.CSS_SELECTOR, 'section[id="running-costs"]'
            )

            # Extract items using same structure as overview
            cost_items = running_costs_section.find_elements(
                By.CSS_SELECTOR, "div.sc-tqnfbs-1"
            )

            for item in cost_items:
                try:
                    label = item.find_element(By.CSS_SELECTOR, "p.sc-tqnfbs-5").text
                    value = item.find_element(By.CSS_SELECTOR, "p.sc-tqnfbs-6").text
                    car_data["running_costs"][label] = value
                except:
                    pass

            print(
                f"  ✓ Running costs extracted ({len(car_data['running_costs'])} items)"
            )
        except Exception as e:
            print(f"  ✗ Error extracting running costs: {str(e)}")

        # Extract Seller Information
        try:
            seller_section = driver.find_element(
                By.CSS_SELECTOR, 'section[id="meet-seller"]'
            )

            # Seller name
            try:
                seller_name = seller_section.find_element(
                    By.CSS_SELECTOR, "p.sc-fdbzzc-2"
                ).text
                car_data["seller_info"]["name"] = seller_name
            except:
                pass

            # Location and distance
            try:
                location_items = seller_section.find_elements(
                    By.CSS_SELECTOR, "p.sc-fdbzzc-5"
                )
                location_parts = [
                    item.text for item in location_items if item.text != "•"
                ]
                if location_parts:
                    car_data["seller_info"]["location"] = " - ".join(location_parts)
            except:
                pass

            # Seller rating
            try:
                rating = seller_section.find_element(
                    By.CSS_SELECTOR, 'a[data-testid="seller-rating"]'
                ).text
                car_data["seller_info"]["rating"] = rating
            except:
                pass

            # Phone number
            try:
                phone = seller_section.find_element(
                    By.CSS_SELECTOR, 'a[href^="tel:"]'
                ).get_attribute("href")
                car_data["seller_info"]["phone"] = phone.replace("tel:", "")
            except:
                pass

            # Seller logo
            try:
                logo = seller_section.find_element(
                    By.CSS_SELECTOR, 'img[data-testid="dealer-logo"]'
                ).get_attribute("src")
                car_data["seller_info"]["logo"] = logo
            except:
                pass

            print(f"  ✓ Seller info extracted")
        except Exception as e:
            print(f"  ✗ Error extracting seller info: {str(e)}")

        # Extract "Before You Buy" information
        try:
            before_buy_section = driver.find_element(
                By.CSS_SELECTOR, 'section[id="before-you-buy"]'
            )

            # Try to find any content in this section
            before_buy_items = before_buy_section.find_elements(
                By.CSS_SELECTOR, 'li, p, div[class*="sc-"]'
            )
            items_text = []
            for item in before_buy_items:
                text = item.text.strip()
                if text and text not in items_text and text != "Before you buy":
                    items_text.append(text)

            car_data["before_you_buy"] = items_text

            if items_text:
                print(f"  ✓ Before you buy extracted ({len(items_text)} items)")
            else:
                print(f"  ⚠ Before you buy section found but empty")
        except Exception as e:
            print(f"  ✗ Error extracting before you buy: {str(e)}")

    except Exception as e:
        print(f"  ✗ Error scraping car details: {str(e)}")

    return car_data


def main():
    search_url = "https://www.autotrader.co.uk/car-search?channel=cars&keywords=sport&keywords=luxury&make=Vauxhall&postcode=SW1A%201AA&sort=relevance&year-from=new"

    driver = init_driver()

    try:
        print("=" * 60)
        print("STEP 1: Collecting car listing URLs...")
        print("=" * 60)
        car_links = get_car_links(driver, search_url, max_pages=3)
        print(f"\nTotal cars found: {len(car_links)}\n")

        print("=" * 60)
        print("STEP 2: Scraping individual car details...")
        print("=" * 60)

        success_count = 0
        error_count = 0

        for idx, link in enumerate(car_links, 1):
            try:
                print(f"\n[{idx}/{len(car_links)}] Processing car...")
                car_data = scrape_car_details(driver, link)

                # Store in MongoDB
                if car_data["images"] or car_data["overview"]:
                    result = collection.insert_one(car_data)
                    print(
                        f"  ✓ Successfully saved to MongoDB with ID: {result.inserted_id}"
                    )
                    success_count += 1
                else:
                    print(f"  ⚠ Skipped - No meaningful data extracted")
                    error_count += 1

                time.sleep(2)

            except Exception as e:
                print(f"  ✗ Error processing {link}: {str(e)}")
                error_count += 1

        print("\n" + "=" * 60)
        print("SCRAPING COMPLETE!")
        print("=" * 60)
        print(f"✓ Successfully fetched and stored: {success_count} cars")
        print(f"✗ Errors/Skipped: {error_count} cars")
        print(f"Database: Raava_Sales")
        print(f"Collection: Cars")
        print(f"Total documents in collection: {collection.count_documents({})}")
        print("=" * 60)

    finally:
        driver.quit()
        client.close()


if __name__ == "__main__":
    main()
