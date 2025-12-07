import torch
from PIL import Image, ImageDraw
from ultralytics import YOLO
from diffusers import StableDiffusionInpaintPipeline

# הגדרות
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
YOLO_PATH = "yolo-train/best.onnx"  # ודאי שהקובץ הזה קיים בתיקייה!


def get_furniture_mask(image_path):
    """
    מזהה רהיט (ספה/מיטה/כסא) בתמונה ומחזיר את התמונה + מסכה.
    מסנן חלונות, עציצים ושאר דברים לא רלוונטיים.
    """
    print(f"🔍 Loading YOLO model from {YOLO_PATH}...")
    try:
        model = YOLO(YOLO_PATH)
    except Exception as e:
        print(f"❌ Error loading YOLO: {e}")
        return None, None

    results = model(image_path)

    if not results or len(results[0].boxes) == 0:
        print("❌ YOLO לא מצא שום אובייקט בתמונה.")
        return None, None

    # --- התיקון החכם: סינון רהיטים בלבד ---
    target_furniture = ['sofa', 'couch', 'bed', 'chair', 'table']
    best_box = None
    max_area = 0

    print(f"🔎 סורק אובייקטים בתמונה...")

    for box in results[0].boxes:
        # בדיקת שם האובייקט
        class_id = int(box.cls[0])
        class_name = model.names[class_id].lower()

        # חישוב גודל (כדי למצוא את הרהיט הכי דומיננטי)
        x1, y1, x2, y2 = box.xyxy.cpu().numpy()[0]
        area = (x2 - x1) * (y2 - y1)

        print(f"   - נמצא: {class_name} (שטח: {int(area)})")

        # אם זה רהיט מהרשימה שלנו, וגם גדול יותר ממה שמצאנו עד עכשיו
        if class_name in target_furniture and area > max_area:
            max_area = area
            best_box = (x1, y1, x2, y2)

    if best_box is None:
        print(f"⚠️ המודל מצא דברים (כמו חלונות), אבל לא רהיטים מהרשימה: {target_furniture}")
        return None, None

    print(f"✅ נבחר רהיט לצביעה: {best_box}")

    # יצירת המסכה
    img = Image.open(image_path).convert("RGB")
    mask = Image.new("L", img.size, 0)  # רקע שחור
    draw = ImageDraw.Draw(mask)

    x1, y1, x2, y2 = best_box
    # הרחבה קטנה ב-10 פיקסלים כדי שהצבע יכסה את כל הספה
    draw.rectangle((x1 - 10, y1 - 10, x2 + 10, y2 + 10), fill=255)  # מלבן לבן

    return img, mask


def inpaint_room(image_path, style_prompt):
    """
    הפונקציה הראשית: מקבלת תמונה וסגנון, ומחזירה תמונה חדשה.
    """
    # שלב 1: משיגים מסכה אוטומטית מה-YOLO
    original_image, mask_image = get_furniture_mask(image_path)

    if original_image is None:
        return None

    # שלב 2: מציירים מחדש עם Stable Diffusion
    print("🎨 Loading Stable Diffusion...")
    pipe = StableDiffusionInpaintPipeline.from_pretrained(
        "runwayml/stable-diffusion-inpainting",
        torch_dtype=torch.float32,
        safety_checker=None
    ).to(DEVICE)

    # הנחיה מדויקת לבינה המלאכותית
    full_prompt = f"a high quality {style_prompt}, interior design, realistic, 4k, cozy home"
    negative_prompt = "low quality, blurry, distorted, window, messy, bad anatomy, text, watermark"

    print(f"🖌️ Generating: '{full_prompt}'...")

    # שינוי גודל זמני ל-512x512 (שהמודל אוהב)
    w, h = 512, 512
    image_resized = original_image.resize((w, h))
    mask_resized = mask_image.resize((w, h))

    result = pipe(
        prompt=full_prompt,
        negative_prompt=negative_prompt,
        image=image_resized,
        mask_image=mask_resized,
        num_inference_steps=25,  # מספר הצעדים לציור
        strength=0.9,  # כמה חזק לשנות את הספה
        guidance_scale=7.5
    ).images[0]

    # מחזירים לגודל מקורי
    return result.resize(original_image.size)


# --- בדיקה ---
if __name__ == "__main__":
    TEST_IMAGE = "test_room.jpg"
    STYLE = "modern blue velvet sofa"  # נסי צבע בולט כדי לראות שינוי

    print("🚀 מתחיל תהליך עיצוב מחדש...")
    final_image = inpaint_room(TEST_IMAGE, STYLE)

    if final_image:
        final_image.save("final_result.png")
        print("\n🎉 הסתיים בהצלחה! תפתחי את 'final_result.png'")
    else:
        print("\n❌ נכשל. בדקי את ההודעות למעלה.")