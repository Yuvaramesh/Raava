import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# ---------------- SETUP ----------------
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--disable-notifications")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()), options=options
)
SEARCH_URL = "https://www.autotrader.co.uk/car-search?keywords=peugeot&keywords=new%20car&keywords=sports%20car&keywords=luxury&postcode=SW1A%201AA&sort=relevance"
driver.get(SEARCH_URL)
time.sleep(6)

# ---------------- GET ALL CAR LINKS ----------------
car_links = set()
elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='/car-details/']")
for el in elements:
    car_links.add(el.get_attribute("href"))

print(f"Total Cars Found: {len(car_links)}")

all_cars = []


# ---------------- HELPER FUNCTIONS ----------------
def scroll_to_id(section_id):
    try:
        section = driver.find_element(By.ID, section_id)
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", section)
        time.sleep(2)
        return section.text.strip()
    except:
        return ""


def safe_text(xpath):
    try:
        return driver.find_element(By.XPATH, xpath).text.strip()
    except:
        return ""


def extract_images():
    images = set()

    # scroll to top where image carousel is
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(2)

    img_elements = driver.find_elements(
        By.XPATH, "//img[contains(@src,'m.atcdn.co.uk')]"
    )

    for img in img_elements:
        src = img.get_attribute("src")
        if src and "media" in src:
            images.add(src)

    return list(images)


# ---------------- SCRAPE EACH CAR ----------------
for index, link in enumerate(car_links, start=1):
    print(f"Scraping {index}/{len(car_links)}")
    driver.get(link)
    time.sleep(5)

    car_data = {
        "url": link,
        "key_information": {"title": safe_text("//h1"), "make": "Ferrari"},
        "images": extract_images(),
        "pricing": scroll_to_id("pricing"),
        "overview": scroll_to_id("overview"),
        "running_costs": scroll_to_id("running-costs"),
        "vehicle_history": scroll_to_id("vehicle-history"),
        "meet_seller": scroll_to_id("meet-seller"),
    }

    all_cars.append(car_data)

driver.quit()

# ---------------- SAVE JSON ----------------
with open("autotrader_peugeot_all_section.json", "w", encoding="utf-8") as f:
    json.dump(all_cars, f, indent=4, ensure_ascii=False)

print("✅ All car data + images extracted successfully")
