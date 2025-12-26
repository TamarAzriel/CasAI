from google import genai
from google.genai import types
from PIL import Image
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

client = genai.Client(api_key=os.getenv("NanoBanana_API_KEY"))

prompt = (
    "Create an image of my room, but replace the current sofa with a black one. Only change the sofa so it fits and blends into the room, while keeping the rest of the room exactly the same."
)

image = Image.open("C:\\Users\\תמר\\Desktop\\IMG_4265.jpeg")

response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=[prompt, image],
)

for part in response.parts:
    if part.text is not None:
        print(part.text)
    elif part.inline_data is not None:
        image = part.as_image()
        image.save("generated_image.png")