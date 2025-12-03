import os
from google import genai
from google.genai.errors import APIError


def generate_image_with_gemini_api(prompt: str, output_filename: str):
    """
    מייצר תמונה באמצעות Gemini API ושומר אותה כקובץ.

    Args:
        prompt: ההנחיה הטקסטואלית ליצירת התמונה.
        output_filename: שם הקובץ לשמירת התמונה.
    """
    # 1. יצירת לקוח - הלקוח קורא אוטומטית את מפתח ה-API ממשתנה הסביבה
    try:
        client = genai.Client()
    except Exception as e:
        print("שגיאה בהפעלת הלקוח. ודא שמפתח ה-API מוגדר כראוי.")
        print(e)
        return

    # 2. הגדרת המודל וההנחיה
    # משתמשים במודל המיועד ליצירת תמונות (Nano Banana)
    MODEL_NAME = "gemini-3-pro-image-preview"  # ניתן לשנות ל- gemini-2.5-flash-image

    print(f"שולח בקשה למודל: {MODEL_NAME}...")

    try:
        # 3. קריאה ל-API
        # ההנחיה נשלחת כתוכן יחיד ל-generate_content
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[prompt]
        )

        # 4. חילוץ התמונה מהתגובה
        # התמונה נמצאת בתוך parts[0].inline_data
        image_part = response.candidates[0].content.parts[0].inline_data

        # 5. שמירת הנתונים הבינאריים של התמונה לקובץ
        with open(output_filename, "wb") as f:
            f.write(image_part.data)

        print(f"\n✅ התמונה נוצרה בהצלחה ונשמרה כקובץ: {output_filename}")

    except APIError as e:
        print(f"\n❌ שגיאת API: ודא שיש לך הרשאה וחיוב פעיל עבור המודל ({MODEL_NAME}).")
        print(f"פרטי השגיאה: {e}")
    except IndexError:
        print("\n❌ שגיאה: המודל לא הצליח ליצור תמונה עבור ההנחיה הזו (ייתכן שהיא נחסמה).")
    except Exception as e:
        print(f"\n❌ אירעה שגיאה בלתי צפויה: {e}")


# --- הפעלה ---
if __name__ == "__main__":
    # ההנחיה ליצירת תמונה
    my_prompt = "A high-resolution, cinematic photo of a nano banana wearing sunglasses and flying a spaceship in a purple galaxy."

    # שם הקובץ לשמירה
    output_file = "nano_banana_spaceship.jpg"

    generate_image_with_gemini_api(my_prompt, output_file)