import os
import csv
import re
import time
import requests
from bs4 import BeautifulSoup
import mimetypes

def save_image_safe(url, save_path):
    """
    מוריד תמונה בצורה בטוחה ושומר אותה בפורמט הנכון.
    מחזיר את שם הקובץ אם הצליח, אחרת None.
    """
    try:
        img_response = requests.get(url, headers=HEADERS, timeout=10)

        # בדיקה 1: האם הבקשה הצליחה?
        if img_response.status_code != 200:
            print(f"⚠️ Failed to download image (status {img_response.status_code}) → {url}")
            return None

        # בדיקה 2: סוג תוכן
        content_type = img_response.headers.get("Content-Type", "").lower()

        # חובה לוודא שסוג הקובץ הוא תמונה אמיתית
        if not content_type.startswith("image/"):
            print(f"⚠️ Not a real image → {url} (type {content_type})")
            return None

        # גזור סיומת לפי סוג הקובץ
        ext = content_type.split("/")[-1]

        # אם זה לא סיומת מוכרת – דלג
        if ext not in ["jpeg", "jpg", "png", "webp", "avif"]:
            print(f"⚠️ Unsupported image format ({ext}) → {url}")
            return None

        # תיקון: jpg במקום jpeg
        if ext == "jpeg":
            ext = "jpg"

        # החזרת שם קובץ תקין
        save_path = save_path.replace(".jpg", f".{ext}")

        # שמירת הקובץ
        img_data = img_response.content

        # בדיקה 3: האם הקובץ גדול מספיק כדי להיות אמיתי
        if len(img_data) < 1000:
            print(f"⚠️ Image too small → {url}")
            return None
        print(f"✔ Saving image as .{ext} → {save_path}")

        with open(save_path, "wb") as f:
            f.write(img_data)

        return save_path

    except Exception as e:
        print(f"❌ Error downloading image from {url}: {e}")
        return None

# =========================
#   CONFIG
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
    "Chair stool": "https://www.ikea.com/il/he/cat/stools-benches-10728/",

    # --- מיטות ---
    "Bed double": "https://www.ikea.com/il/he/cat/double-beds-16284/",
    "Bed single": "https://www.ikea.com/il/he/cat/single-beds-16285/",
    "Bed frame": "https://www.ikea.com/il/he/cat/bed-frames-bm004/",
    "Bed upholstered": "https://www.ikea.com/il/he/cat/upholstered-beds-49096/",

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

    # --- אחסון ---
    "Dresser chest": "https://www.ikea.com/il/he/cat/chests-of-drawers-10451/",
    "Dresser tv": "https://www.ikea.com/il/he/cat/tv-benches-10475/",
    "Dresser wardrobe": "https://www.ikea.com/il/he/cat/wardrobes-19053/",
    "Dresser cabinet": "https://www.ikea.com/il/he/cat/cabinets-10385/",
    "Wardrobe sliding": "https://www.ikea.com/il/he/cat/sliding-wardrobes-43635/",
    "Wardrobe kids": "https://www.ikea.com/il/he/cat/childrens-wardrobes-18707/",
    "Wardrobe hinged": "https://www.ikea.com/il/he/cat/hinged-wardrobes-48005/"
}

# נתיבים
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
IMAGE_DIR = os.path.join(DATA_DIR, "ikea_il_images")
CSV_PATH = os.path.join(DATA_DIR, "ikea_il.csv")

# כותרות מעודכנות
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Referer": "https://www.ikea.com/"
}

os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)


# =========================
#   HELPERS
# =========================

def extract_image(tag):
    if not tag: return None
    # נסה לשלוף את התמונה האיכותית ביותר
    if tag.get("srcset"):
        # לוקח את ה-URL האחרון ברשימה
        url = tag["srcset"].split(",")[-1].split()[0]
        return url
    if tag.get("src"): return tag["src"]
    if tag.get("data-src"): return tag["data-src"]
    return None


def clean_price(text):
    if not text: return None
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
        time.sleep(1)
        response = requests.get(url, headers=HEADERS, timeout=20)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Error fetching {url}: {e}")
        return []

    soup = BeautifulSoup(response.text, "lxml")
    products = []

    cards = soup.find_all("div", {"class": "plp-fragment-wrapper"})
    if not cards:
        cards = soup.find_all("article")

    for card in cards:
        img_tag = card.find("img")
        img_url = extract_image(img_tag)

        if not img_url or "base64" in img_url:
            continue

        name_tag = card.find("span", {"data-testid": "product-title"})
        if not name_tag: name_tag = card.find("h3")
        name = name_tag.get_text(strip=True) if name_tag else "Unknown"

        price_tag = card.find("span", {"data-testid": "product-price"})
        if not price_tag: price_tag = card.find("span", {"class": "plp-price__integer"})
        price = clean_price(price_tag.get_text(strip=True)) if price_tag else "N/A"

        link_tag = card.find("a")
        product_link = link_tag.get("href") if link_tag else None

        if not product_link:
            continue

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
    seen_urls = set()
    row_id = 0

    print("🚀 Starting Deduplicated Scraper...")

    for cat_key, url in CATEGORIES.items():
        items = scrape_category(cat_key, url)

        for item in items:
            if item["product_link"] in seen_urls:
                continue

            seen_urls.add(item["product_link"])
            row_id += 1

            # שם קובץ ראשוני (יוחלף לסיומת הנכונה בתוך save_image_safe)
            img_name = f"{row_id}.jpg"
            img_path = os.path.join(IMAGE_DIR, img_name)

            # 🔥 כאן מתחיל השינוי הגדול — שימוש בפונקציה החדשה
            saved_file = save_image_safe(item["image_url"], img_path)

            if saved_file:
                all_rows.append({
                    "item_id": row_id,
                    "item_name": item["name"],
                    "item_price": item["price"],
                    "item_cat": item["category"],
                    "image_url": item["image_url"],
                    "product_link": item["product_link"],
                    "image_file": os.path.basename(saved_file)
                })
            else:
                # אם התמונה לא נשמרה — לא נספור את המוצר
                row_id -= 1

    # כתיבת ה־CSV
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["item_id", "item_name", "item_price", "item_cat", "image_url", "product_link", "image_file"]
        )
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\n✅ Saved CSV with {len(all_rows)} unique products → {CSV_PATH}")


if __name__ == "__main__":
    download_and_save_csv()