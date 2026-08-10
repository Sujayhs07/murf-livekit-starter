import os
from dotenv import load_dotenv
# pyrefly: ignore [missing-import]
import google.generativeai as genai

load_dotenv(".env.local")

api_key = os.getenv("GOOGLE_API_KEY")
print(f"GOOGLE_API_KEY starts with: {api_key[:10] if api_key else 'None'}")

try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Hello")
    print("Response:", response.text)
except Exception as e:
    print("Error:", e)
