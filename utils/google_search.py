# utils/google_search.py
import os  # <--- הוספתי את זה, זה היה חסר
import requests
import json
import urllib.parse
from dotenv import load_dotenv  # ספרייה לטעינת משתני סביבה

# טוען את המשתנים מהקובץ .env
load_dotenv()


def search_google_shopping(query):
    """
    Google Shopping search using Serper.dev
    Returns stable, user-safe links
    """

    url = "https://google.serper.dev/shopping"

    # שליפת המפתח מהקובץ הסודי
    api_key = os.getenv("SERPER_API_KEY")

    # בדיקת בטיחות: אם המפתח לא נמצא, מחזירים רשימה ריקה כדי לא לקרוס
    if not api_key:
        print("Error: SERPER_API_KEY not found in .env file.")
        return []

    payload = {
        "q": query,
        "gl": "il",
        "hl": "he"
    }

    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        results = response.json()

        shopping_results = results.get("shopping", [])
        products = []

        for item in shopping_results:
            title = item.get("title", "")
            safe_title = urllib.parse.quote(title)

            # ✅ לינק יציב שתמיד עובד (חיפוש בגוגל שופינג לפי הכותרת)
            stable_link = f"https://www.google.com/search?q={safe_title}&tbm=shop"

            products.append({
                "title": title,
                "price": item.get("price"),
                "source": item.get("source"),
                "image": item.get("imageUrl"),
                "link": stable_link,  # הלינק הזה ייפתח בוודאות
                "raw_link": item.get("link")  # שומרים את המקור למקרה הצורך
            })

        return products

    except Exception as e:
        print(f"Error searching Google Shopping: {e}")
        return []