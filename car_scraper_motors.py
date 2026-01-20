import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from pymongo import MongoClient
import time
import re

# MongoDB Setup
client = MongoClient("mongodb://localhost:27017/")
db = client["Raava_Sales"]
collection = db["Motors_Cars"]

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


def get_car_links_from_slider(driver, base_url):
    """Extract car links from the slider widget"""
    print("Fetching car links from slider...")

    driver.get(base_url)
    time.sleep(4)

    car_links = []

    try:
        # Find all car elements in the slider
        car_elements = driver.find_elements(
            By.CSS_SELECTOR, "a.motors-widget-car-element"
        )

        for element in car_elements:
            href = element.get_attribute("href")
            if href and "motors.co.uk/car-" in href:
                # Clean the URL to get the base car URL
                clean_url = href.split("?")[0]
                if clean_url not in car_links:
                    car_links.append(clean_url)

        print(f"Found {len(car_links)} car links from slider")

    except Exception as e:
        print(f"Error extracting slider links: {str(e)}")

    return car_links


def scrape_car_details(driver, car_url):
    """Scrape detailed car information from individual car page"""
    print(f"\nScraping: {car_url}")

    driver.get(car_url)
    time.sleep(4)

    car_data = {
        "url": car_url,
        "title": "",
        "year": "",
        "doors": "",
        "fuel_type": "",
        "price": "",
        "images": [],
        "ev_information": {},
        "specifications": {},
    }

    try:
        # Extract Title
        try:
            title_element = driver.find_element(By.CSS_SELECTOR, "h1")
            car_data["title"] = title_element.text.strip()
            print(f"  ✓ Title: {car_data['title']}")
        except:
            pass

        # Extract Price
        try:
            price_element = driver.find_element(
                By.CSS_SELECTOR, "span.price, div.price, p.price"
            )
            car_data["price"] = price_element.text.strip()
            print(f"  ✓ Price: {car_data['price']}")
        except:
            # Try alternative price selector
            try:
                price_scripts = driver.find_elements(By.TAG_NAME, "script")
                for script in price_scripts:
                    script_text = script.get_attribute("innerHTML")
                    if "price" in script_text.lower():
                        price_match = re.search(r"£[\d,]+", script_text)
                        if price_match:
                            car_data["price"] = price_match.group(0)
                            break
            except:
                pass

        # Extract Images from Gallery
        try:
            # Find all gallery images
            gallery_images = driver.find_elements(
                By.CSS_SELECTOR,
                "img.vip-gallery-image, img.vip-gallery-thumbnail__image",
            )

            for img in gallery_images:
                img_src = img.get_attribute("src")
                if img_src and "autoexposure.co.uk" in img_src:
                    # Get high quality version
                    high_quality_url = (
                        img_src.replace("_1e.jpg", "_1.jpg")
                        .replace("_2e.jpg", "_2.jpg")
                        .replace("_3e.jpg", "_3.jpg")
                    )
                    if high_quality_url not in car_data["images"]:
                        car_data["images"].append(high_quality_url)

            print(f"  ✓ Found {len(car_data['images'])} images")
        except Exception as e:
            print(f"  ✗ Error extracting images: {str(e)}")

        # Extract EV Information
        try:
            ev_section = driver.find_element(
                By.CSS_SELECTOR, "div.ev-section, section.ev-section"
            )

            # Battery warranty
            try:
                battery_warranty = ev_section.find_element(
                    By.XPATH,
                    ".//p[contains(text(), 'Battery warranty')]/following-sibling::span",
                )
                car_data["ev_information"][
                    "battery_warranty"
                ] = battery_warranty.text.strip()
            except:
                pass

            # Rapid charge option
            try:
                rapid_charge = ev_section.find_element(
                    By.XPATH,
                    ".//p[contains(text(), 'Rapid charge option')]/following-sibling::span",
                )
                car_data["ev_information"]["rapid_charge"] = rapid_charge.text.strip()
            except:
                pass

            # Connector type
            try:
                connector = ev_section.find_element(
                    By.XPATH,
                    ".//p[contains(text(), 'Connector type')]/following-sibling::span",
                )
                car_data["ev_information"]["connector_type"] = connector.text.strip()
            except:
                pass

            # Time to charge
            try:
                charge_time = ev_section.find_element(By.CSS_SELECTOR, "p.title")
                if "minutes" in charge_time.text or "hours" in charge_time.text:
                    car_data["ev_information"]["charge_time"] = charge_time.text.strip()
            except:
                pass

            print(
                f"  ✓ EV information extracted ({len(car_data['ev_information'])} items)"
            )
        except Exception as e:
            print(f"  ✗ Error extracting EV info: {str(e)}")

        # Extract Additional Specifications
        try:
            spec_items = driver.find_elements(
                By.CSS_SELECTOR, "div.specification-item, li.spec-item"
            )

            for item in spec_items:
                try:
                    label = item.find_element(
                        By.CSS_SELECTOR, "span.label, dt"
                    ).text.strip()
                    value = item.find_element(
                        By.CSS_SELECTOR, "span.value, dd"
                    ).text.strip()
                    car_data["specifications"][label] = value
                except:
                    pass

            if car_data["specifications"]:
                print(
                    f"  ✓ Specifications extracted ({len(car_data['specifications'])} items)"
                )
        except:
            pass

    except Exception as e:
        print(f"  ✗ Error scraping car details: {str(e)}")

    return car_data


def main():
    # Base URL with Tesla cars slider
    base_url = "https://www.thecarexpert.co.uk/car-brands/tesla/"

    driver = init_driver()

    try:
        print("=" * 60)
        print("STEP 1: Extracting car links from slider...")
        print("=" * 60)

        car_links = get_car_links_from_slider(driver, base_url)

        if not car_links:
            print("No car links found. Exiting...")
            return

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

                # Store in MongoDB if we got meaningful data
                if car_data["images"] or car_data["price"]:
                    result = collection.insert_one(car_data)
                    print(
                        f"  ✓ Successfully saved to MongoDB with ID: {result.inserted_id}"
                    )
                    success_count += 1
                else:
                    print(f"  ⚠ Skipped - No meaningful data extracted")
                    error_count += 1

                # Be respectful with requests
                time.sleep(2)

            except Exception as e:
                print(f"  ✗ Error processing {link}: {str(e)}")
                error_count += 1

        # Final Summary
        print("\n" + "=" * 60)
        print("SCRAPING COMPLETE!")
        print("=" * 60)
        print(f"✓ Successfully fetched and stored: {success_count} cars")
        print(f"✗ Errors/Skipped: {error_count} cars")
        print(f"Database: Raava_Sales")
        print(f"Collection: Motors_Cars")
        print(f"Total documents in collection: {collection.count_documents({})}")
        print("=" * 60)

    finally:
        driver.quit()
        client.close()


if __name__ == "__main__":
    main()
