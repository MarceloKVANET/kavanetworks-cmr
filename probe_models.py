import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    print("❌ API KEY NO ENCONTRADA")
else:
    client = genai.Client(api_key=api_key)
    models_to_test = [
        'gemini-1.5-flash',
        'gemini-1.5-pro',
        'gemini-2.0-flash',
        'gemini-2.0-flash-lite',
        'gemini-1.5-flash-latest',
        'gemini-1.5-pro-latest',
        'gemini-2.0-flash-exp'
    ]
    
    for m in models_to_test:
        print(f"Testing {m}...")
        try:
            response = client.models.generate_content(
                model=m,
                contents="test"
            )
            print(f"✅ {m} WORKS!")
            break
        except Exception as e:
            print(f"❌ {m} FAIL: {str(e)[:50]}...")
