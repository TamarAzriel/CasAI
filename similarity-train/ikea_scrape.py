import os
import csv
import re
import requests
from bs4 import BeautifulSoup

# =========================
#   CONFIG - EXPANDED
# =========================

# כאן הוספנו תתי-קטגוריות כדי להגדיל את כמות המוצרים
# המפתחות (למשל Sofa) חייבים להכיל את שם הקטגוריה שהמודל מזהה כדי שהסינון באפליקציה יעבוד
CATEGORIES = {
    # --- ספות וכורסאות ---
    "Sofa 2-seat": "https://www.ikea.com/il/he/cat/2-seat-sofas-10667/",
    "Sofa 3-seat": "https://www.ikea.com/il/he/cat/3-seat-sofas-10669/",
    "Sofa corner": "https://www.ikea.com/il/he/cat/corner-sofas-10670/",
    "Sofa bed": "https://www.ikea.com/il/he/cat/sofa-beds-10663/",
    "Armchair": "https://www.ikea.com/il/he/cat/armchairs-fu006/",

    # --- כיסאות ---
    "Chair dining": "https://www.ikea.com/il/he/cat/dining-chairs-25219/",
    "Chair office": "https://www.ikea.com/il/he/cat/desk-chairs-20653/",
    "Chair stool": "https://www.ikea.com/il/he/cat/stools-benches-10728/",

    # --- מיטות ---
    "Bed double": "https://www.ikea.com/il/he/cat/double-beds-16284/",
    "Bed single": "https://www.ikea.com/il/he/cat/single-beds-16285/",
    "Bed frame": "https://www.ikea.com/il/he/cat/bed-frames-bm004/",

    # --- שולחנות ---
    "Table dining": "https://www.ikea.com/il/he/cat/dining-tables-21825/",
    "Table coffee": "https://www.ikea.com/il/he/cat/coffee-side-tables-10705/",
    "Table desk": "https://www.ikea.com/il/he/cat/desks-20649/",
    "Table bedside": "https://www.ikea.com/il/he/cat/bedside-tables-20656/",

    # --- תאורה ---
    "Lamp floor": "https://www.ikea.com/il/he/cat/floor-lamps-10731/",
    "Lamp table": "https://www.ikea.com/il/he/cat/table-lamps-10732/",
    "Lamp pendant": "https://www.ikea.com/il/he/cat/pendant-lamps-18750/",
    "Lamp work": "https://www.ikea.com/il/he/cat/work-lamps-20502/",

    # --- אחסון (מזוהה כ-Dresser או Cabinetry) ---
    "Dresser chest": "https://www.ikea.com/il/he/cat/chests-of-drawers-10451/",
    "Dresser tv": "https://www.ikea.com/il/he/cat/tv-benches-10475/",
    "Dresser wardrobe": "https://www.ikea.com/il/he/cat/wardrobes-19053/",
    "Dresser cabinet": "https://www.ikea.com/il/he/cat/cabinets-10385/"
}

# תיקיות
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
IMAGE_DIR = os.path.join(DATA_DIR, "ikea_il_images")
CSV_PATH = os.path.join(DATA_DIR, "ikea_il.csv")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}

os.makedirs(IMAGE_DIR, exist_ok=True)


# =========================
#   HELPERS
# =========================

def extract_image(tag):
    if tag.get("src"): return tag["src"]
    if tag.get("data-src"): return tag["data-src"]
    if tag.get("srcset"):
        return tag["srcset"].split(",")[-1].split()[0]
    return None


def clean_price(text):
    if not text:
        return None
    numbers = re.findall(r"[\d,]+", text)
    if numbers:
        return f"₪ {numbers[0]}"
    return None


# =========================
#   SCRAPER
# =========================

def scrape_category(cat_key, url):
    print(f"\n📸 Scraping {cat_key}...")
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Error fetching {url}: {e}")
        return []

    soup = BeautifulSoup(response.text, "lxml")
    products = []

    # חיפוש כרטיסי מוצר
    cards = soup.find_all("div", {"class": "plp-fragment-wrapper"})
    if not cards:
        cards = soup.find_all("article")

    for card in cards:
        # תמונה
        img_tag = card.find("img")
        if not img_tag: continue
        img_url = extract_image(img_tag)
        if not img_url: continue

        # שם ומחיר
        name_tag = card.find("span", {"data-testid": "product-title"})
        if not name_tag: name_tag = card.find("h3")

        price_tag = card.find("span", {"data-testid": "product-price"})
        if not price_tag: price_tag = card.find("span", {"class": "plp-price__integer"})

        name = name_tag.get_text(strip=True) if name_tag else "Unknown"
        price = clean_price(price_tag.get_text(strip=True)) if price_tag else "N/A"

        # קישור
        link_tag = card.find("a")
        product_link = link_tag.get("href") if link_tag else None

        products.append({
            "category": cat_key,
            "name": name,
            "price": price,
            "image_url": img_url,
            "product_link": product_link
        })

    print(f"✔ Found {len(products)} products in {cat_key}")
    return products


def download_and_save_csv():
    all_rows = []
    row_id = 0

    print("🚀 Starting Extended Scraper...")

    for cat_key, url in CATEGORIES.items():
        items = scrape_category(cat_key, url)

        for item in items:
            row_id += 1
            img_name = f"{row_id}.jpg"
            img_path = os.path.join(IMAGE_DIR, img_name)

            # שמירת תמונה מקומית
            try:
                # מדלגים אם התמונה כבר קיימת כדי לחסוך זמן בריצות חוזרות
                if not os.path.exists(img_path):
                    img_data = requests.get(item["image_url"], headers=HEADERS, timeout=10).content
                    with open(img_path, "wb") as f:
                        f.write(img_data)
            except:
                pass

            all_rows.append({
                "item_id": row_id,
                "item_name": item["name"],
                "item_price": item["price"],
                "item_cat": item["category"],  # נשמור את שם הקטגוריה המורחב (למשל Sofa bed)
                "image_url": item["image_url"],
                "product_link": item["product_link"],
                "image_file": img_name
            })

    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["item_id", "item_name", "item_price", "item_cat", "image_url", "product_link", "image_file"]
        )
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\n✅ Saved CSV with {len(all_rows)} products → {CSV_PATH}")


if __name__ == "__main__":
    download_and_save_csv()