import os
import csv
import time
import requests
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# =========================
#   CONFIG & CATEGORIES
# =========================

CATEGORIES = {
    # --- ספות וכורסאות ---
    "Sofa 3-seat": "https://www.ikea.com/il/he/cat/three-seat-sofas-10670/",
    "Sofa corner": "https://www.ikea.com/il/he/cat/corner-sofas-10670/",
    "Sofa bed": "https://www.ikea.com/il/he/cat/sofa-beds-10663/",
    "Armchair": "https://www.ikea.com/il/he/cat/armchairs-fu006/",

    # --- כיסאות ---
    "Chair dining": "https://www.ikea.com/il/he/cat/dining-chairs-25219/",
    "Chair office": "https://www.ikea.com/il/he/cat/desk-chairs-20653/",
    "Bar chair": "https://www.ikea.com/il/he/cat/bar-chairs-stools-20864/",

    # --- מיטות ---
    "Bed double": "https://www.ikea.com/il/he/cat/double-beds-16284/",
    "Bed single": "https://www.ikea.com/il/he/cat/single-beds-16285/",
    "Bed frame": "https://www.ikea.com/il/he/cat/bed-frames-bm004/",

    # --- שולחנות ---
    "Table dining": "https://www.ikea.com/il/he/cat/dining-tables-21825/",
    "Table coffee": "https://www.ikea.com/il/he/cat/coffee-side-tables-10705/",
    "Desk": "https://www.ikea.com/il/he/cat/desks-20649/",
    "Bedside table": "https://www.ikea.com/il/he/cat/bedside-tables-20656/",

    # --- תאורה ---
    "Lamp floor": "https://www.ikea.com/il/he/cat/floor-lamps-10731/",
    "Lamp table": "https://www.ikea.com/il/he/cat/table-lamps-10732/",

    # --- אחסון ---
    "Chest of drawers": "https://www.ikea.com/il/he/cat/chests-of-drawers-10451/",
    "TV bench": "https://www.ikea.com/il/he/cat/tv-benches-10475/",
    "Wardrobe": "https://www.ikea.com/il/he/cat/wardrobes-19053/",
    "Bookcase": "https://www.ikea.com/il/he/cat/bookcases-10382/",
    "Sideboard": "https://www.ikea.com/il/he/cat/sideboards-buffets-console-tables-30454/",

    # --- חוץ וגינה ---
    "Outdoor chair": "https://www.ikea.com/il/he/cat/outdoor-dining-chairs-benches-25224/",
    "Outdoor table": "https://www.ikea.com/il/he/cat/outdoor-dining-tables-25225/",
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
IMAGE_DIR = os.path.join(DATA_DIR, "ikea_il_images")
CSV_PATH = os.path.join(DATA_DIR, "ikea_il.csv")

os.makedirs(IMAGE_DIR, exist_ok=True)


def get_driver():
    options = Options()
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)


def clean_price(price_text):
    """מנקה את המחיר ומשאיר רק מספרים"""
    if not price_text: return "0"
    return "".join(filter(str.isdigit, price_text))


def scroll_to_bottom(driver):
    """גולל את העמוד עד הסוף כדי לטעון את כל המוצרים"""
    print("   ...Scrolling to load all products...")
    last_height = driver.execute_script("return document.body.scrollHeight")

    # גלילה אגרסיבית יותר
    for _ in range(30):  # הגבלת גלילות למקרה שזה נתקע, אבל מספיק לרוב הקטגוריות
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        try:
            # לחיצה על כפתור "הצג עוד" אם קיים
            show_more = driver.find_elements(By.CSS_SELECTOR, ".plp-btn--secondary")
            if show_more:
                driver.execute_script("arguments[0].click();", show_more[0])
                time.sleep(2)
        except:
            pass

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


def run_smart_scraper():
    driver = get_driver()
    all_rows = []
    seen_urls = set()
    row_id = 0

    print("🚀 Starting NUCLEAR PRICE Scraper...")

    try:
        for cat_key, url in CATEGORIES.items():
            print(f"\n📂 Scanning: {cat_key}...")
            driver.get(url)
            time.sleep(3)

            scroll_to_bottom(driver)

            soup = BeautifulSoup(driver.page_source, "lxml")
            cards = soup.select(".plp-fragment-wrapper, .pip-product-compact")

            print(f"   Found {len(cards)} items. Extracting...")

            for card in cards:
                try:
                    # 1. תמונה
                    img_tag = card.find("img")
                    if not img_tag: continue
                    img_url = img_tag.get("src") or img_tag.get("data-src") or img_tag.get("srcset", "").split(" ")[0]
                    if not img_url or "base64" in img_url: continue

                    # 2. לינק
                    link_tag = card.find("a")
                    if not link_tag: continue
                    p_url = link_tag.get("href")
                    if p_url in seen_urls: continue
                    seen_urls.add(p_url)

                    # 3. שם
                    name = "Unknown"
                    name_tag = card.select_one(".pip-header-section__title--small, .header-section__title--small")
                    if name_tag: name = name_tag.get_text(strip=True)

                    desc_tag = card.select_one(
                        ".pip-header-section__description-text, .header-section__description-text")
                    desc = desc_tag.get_text(strip=True) if desc_tag else ""

                    if name == "Unknown":
                        name = img_tag.get("alt", "Unknown")

                    full_name = f"{name} {desc}".strip()

                    # 4. מחיר - השיטה הגרעינית (Regex)
                    price = "0"

                    # קודם כל ננסה למצוא בצורה מסודרת
                    price_text_elements = card.select(".pip-price__integer, .price__integer, .pip-temp-price__integer")
                    for el in price_text_elements:
                        temp_price = clean_price(el.get_text())
                        if temp_price != "0":
                            price = temp_price
                            break

                    # אם לא מצאנו, נחפש בכל הטקסט של הכרטיס את הסימן ₪
                    if price == "0":
                        card_text = card.get_text()
                        # מחפש את הסימן שקל ואחריו מספרים (עם או בלי פסיקים)
                        # דוגמה: ₪ 2,495 או ₪2495
                        match = re.search(r'₪\s*([\d,]+)', card_text)
                        if match:
                            price = clean_price(match.group(1))
                        else:
                            # ניסיון נואש: חפש מספרים גדולים מ-50 בטקסט (בדרך כלל המחיר הוא המספר הכי בולט)
                            # נזהר לא לקחת מידות (כמו 200x150)
                            all_nums = re.findall(r'\d+', card_text)
                            candidates = [int(n) for n in all_nums if len(n) >= 2]  # רק מספרים עם 2 ספרות ומעלה
                            if candidates:
                                # נניח שהמחיר הוא לא קטן מדי (כמו מידה)
                                candidates = [c for c in candidates if c > 40]
                                if candidates:
                                    price = str(candidates[0])  # לוקח את הראשון שנראה כמו מחיר

                    # בדיקת שפיות
                    if price == "0":
                        continue

                    # שמירה
                    row_id += 1
                    img_name = f"{row_id}.jpg"
                    img_path = os.path.join(IMAGE_DIR, img_name)

                    try:
                        resp = requests.get(img_url, timeout=5)
                        if resp.status_code == 200:
                            with open(img_path, "wb") as f:
                                f.write(resp.content)
                        else:
                            continue
                    except:
                        continue

                    all_rows.append({
                        "item_id": row_id,
                        "item_name": full_name,
                        "item_price": price,
                        "item_cat": cat_key,
                        "image_url": img_url,
                        "product_link": p_url,
                        "image_file": img_name
                    })

                    if len(all_rows) % 20 == 0:
                        print(f"   ---> Collected {len(all_rows)} items... (Last: {full_name[:15]} | ₪{price})")

                except Exception as e:
                    continue

            # שמירת ביניים
            if all_rows:
                with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=all_rows[0].keys())
                    writer.writeheader()
                    writer.writerows(all_rows)

    finally:
        driver.quit()
        print(f"\n🏆 DONE! Total valid items: {len(all_rows)}")


if __name__ == "__main__":
    run_smart_scraper()