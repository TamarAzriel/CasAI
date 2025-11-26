from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import json
import os
import time
from pathlib import Path

# הגדרות כלליות
BASE_URL = "https://www.ikea.com.hk"

def getdetails(soup):
    """
    מחלץ את פרטי המוצרים מה-HTML של העמוד הנוכחי.
    """
    items_data = []
    
    products = soup.find_all(class_="card px-0 px-md-4")
    
    for item in products:
        try:
            item_info_element = item.find(class_='itemInfo')
            if not item_info_element:
                continue
                
            json_data = json.loads(item_info_element.input['value'])
            
            item_name = json_data.get('name')
            item_price = json_data.get('price')
            item_cat = json_data.get('category')
            
            img_tag = item.find(class_='productImg').find('img')
            item_url = img_tag['src'] if img_tag else None
            
            link_tag = item.find(class_='card-header').find('a')
            prod_url = BASE_URL + link_tag['href'] if link_tag else None

            if item_name and item_url:
                items_data.append({
                    "item_name": item_name,
                    "item_price": item_price,
                    "item_cat": item_cat,
                    "item_url": item_url,
                    "prod_url": prod_url
                })
                
        except Exception as e:
            print(f"Error parsing item: {e}")
            continue

    return pd.DataFrame(items_data)

def ikeascrape(productlist):
    """
    הפונקציה הראשית לסריקת המוצרים וניהול הדפדפן.
    """
    all_products_df = pd.DataFrame()
    
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=service, options=options)

    try:
        for product_category in productlist:
            url = f"{BASE_URL}/en/products/{product_category}"
            driver.get(url)
            print(f"Scraping category: {product_category}")
            
            while True:
                time.sleep(1) 
                
                soup = BeautifulSoup(driver.page_source, "html.parser")
                
                current_page_df = getdetails(soup)
                all_products_df = pd.concat([all_products_df, current_page_df], ignore_index=True)
                
                print(f"Collected {len(current_page_df)} items from page.")

                nextlink = soup.find(class_='page-item next')
                
                if nextlink and 'disabled' not in nextlink.get('class', []):
                    link_element = nextlink.find('a', {'class': "page-link"})
                    if link_element and link_element.get('data-sitemap-url'):
                        newurl = link_element['data-sitemap-url']
                        driver.get(newurl)
                    else:
                        print("No link found in next button, stopping category.")
                        break
                else:
                    print("End of pages for this category.")
                    break
                    
    except Exception as e:
        print(f"Critical Error: {e}")
    finally:
        driver.quit()
        
    return all_products_df
    
def cleansing(df):
    """
    ניקוי הנתונים, הסרת כפילויות ואיחוד קטגוריות.
    """
    if df.empty:
        return df

    # רשימת החרגות
    excludeli = ['0126 Footstools', '0917 Baby highchairs', "0951 Children's beds (8-14)", "1233 Chairpads", "0211 Living room storage"]
    dfclean = df[~df["item_cat"].isin(excludeli)].copy() # שימוש ב-copy למניעת אזהרות

    # הסרת כפילויות לפי URL של התמונה
    dfclean.drop_duplicates(subset="item_url", keep=False, inplace=True) 

    # מיפוי קטגוריות
    category_map = {
        '0113 Sofa beds': 'sofas', 
        '0111 Sofas': 'sofas',
        '0125 Armchairs': 'chairs',
        '0521 Bed frames..': 'beds',
        '0423 Wardrobes': 'dressers',
        '0212 Living room cabinets': 'dressers',
        '0811 Dining tables': 'tables',
        '0822 Dining stools': 'chairs',
        '0821 Dining chairs and folding chairs': 'chairs',
        '0823 Bar stools': 'chairs',
        '1012 Table lamps': 'lamps',
        '1011 Floor lamps': 'lamps',
        '1016 Wall lamps and wall spotlights': 'lamps'
    }
    
    dfclean['item_cat'] = dfclean['item_cat'].replace(category_map)
    
    return dfclean.reset_index(drop=True)

def savecleandf(df, folder="ikeadata"):
    if not os.path.exists(folder):
        os.makedirs(folder)
    df.to_csv(f"{folder}/ikea_scrape.csv", index=False)
    print(f"Data saved to {folder}/ikea_scrape.csv")

def getscrapeimage(newdf, base_folder="ikeadata"):
    """
    הורדת התמונות ושמירתן בתיקיות לפי קטגוריה.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    print(f"Starting image download for {len(newdf)} items...")
    
    for index, row in newdf.iterrows():
        category_dir = Path(base_folder) / str(row['item_cat'])
        
        category_dir.mkdir(parents=True, exist_ok=True)
        
        image_path = category_dir / f"{index}.jpg"
        
        if image_path.exists():
            continue

        try:
            response = requests.get(row['item_url'], headers=headers, timeout=10)
            if response.status_code == 200:
                with open(image_path, 'wb') as f:
                    f.write(response.content)
            else:
                print(f"Failed to download image for index {index}: Status {response.status_code}")
        except Exception as e:
            print(f"Error downloading image {index}: {e}")

    print("Image download process completed.")

if __name__ == "__main__":
    products_to_scrape = ["sofas-and-armchairs/sofas", "beds/double-beds"] 
    
    df = ikeascrape(products_to_scrape)
    
    clean_df = cleansing(df)
    print(f"Total clean items: {len(clean_df)}")
    
    savecleandf(clean_df)

    getscrapeimage(clean_df)