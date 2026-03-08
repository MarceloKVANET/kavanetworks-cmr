import os
import json
from google import genai
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Re-definir esquema para la prueba
class Item(BaseModel):
    nombre: str
    precio: float

class Reporte(BaseModel):
    items: list[Item]
    total: float

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    print("❌ API KEY NO ENCONTRADA")
else:
    client = genai.Client(api_key=api_key)
    print("🚀 Probando Gemini 1.5 Pro con Response Schema...")
    
    try:
        response = client.models.generate_content(
            model='gemini-1.5-pro',
            contents="Cámara 100, Cable 50. Total 150.",
            config={
                'response_mime_type': 'application/json',
                'response_schema': Reporte,
            }
        )
        print("✅ RESPUESTA PARSED EXITOSA:")
        print(response.parsed)
    except Exception as e:
        print(f"❌ ERROR EN SDK/ESQUEMA: {str(e)}")
        
        print("\n🔍 Probando sin Esquema Pydantic (JSON Plan):")
        try:
            response = client.models.generate_content(
                model='gemini-1.5-pro',
                contents="Genera un JSON con {items: [{nombre, precio}], total} para: Cámara 100, Cable 50.",
                config={'response_mime_type': 'application/json'}
            )
            print("✅ RESPUESTA JSON PLANA EXITOSA:")
            print(response.text)
        except Exception as e2:
            print(f"❌ ERROR INCLUSO EN JSON PLANO: {str(e2)}")
