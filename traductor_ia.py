import os
import time
import json
from google import genai
from pydantic import BaseModel, Field

def get_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        import streamlit as st
        # Carga forzosa desde secrets en producción
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
            os.environ["GEMINI_API_KEY"] = api_key
        else:
            raise ValueError("LLAVE API NO CONFIGURADA")
    return genai.Client(api_key=api_key)

# Esqueleto de datos
class ItemMaterial(BaseModel):
    nombre_material: str = Field(description="Nombre")
    descripcion_detallada: str = Field(description="Detalle")
    cantidad: float = Field(description="Cant")
    unidad_medida: str = Field(description="Unidad")
    precio_unitario_neto_estimado: float = Field(description="Precio")
    justificacion_costo: str = Field(description="Justificación")

class LevantamientoTecnico(BaseModel):
    resumen_proyecto: str = Field(description="Resumen")
    materiales_y_servicios: list[ItemMaterial] = Field(description="Items")
    notas_adicionales: str = Field(description="Notas")
    sugerencia_margen: float = Field(description="Margen")
    justificacion_margen: str = Field(description="Justificación")

# USAMOS FLASH PORQUE PRO DA 404 EN ESTE SDK/ENTORNO
MODEL_ID = 'gemini-1.5-flash' 

def analizar_reporte_tecnico(texto: str, lista_precios: str = "") -> LevantamientoTecnico:
    client = get_client()
    print(f"DEBUG: Enviando a {MODEL_ID}")
    
    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=texto,
            config={
                'response_mime_type': 'application/json',
                'response_schema': LevantamientoTecnico,
                'system_instruction': f"Experto KVANetworks Chile. CLP NETO. {lista_precios}",
                'temperature': 0.1
            }
        )
        if response.parsed: return response.parsed
        # Fallback si .parsed falla
        return LevantamientoTecnico(**json.loads(response.text))
    except Exception as e:
        print(f"ERROR TEXTO: {e}")
        raise e

def analizar_audio_tecnico(ruta_audio: str, lista_precios: str = "") -> LevantamientoTecnico:
    client = get_client()
    print(f"DEBUG: Subiendo audio a {MODEL_ID}")
    
    try:
        archivo_google = client.files.upload(file=ruta_audio)
        
        while archivo_google.state.name == "PROCESSING":
            time.sleep(2)
            archivo_google = client.files.get(name=archivo_google.name)
            
        if archivo_google.state.name != "ACTIVE":
            raise Exception("Archivo fallido en Google")

        response = client.models.generate_content(
            model=MODEL_ID,
            contents=["Extrae JSON del audio:", archivo_google],
            config={
                'response_mime_type': 'application/json',
                'response_schema': LevantamientoTecnico,
                'temperature': 0.1
            }
        )
        
        # Limpieza
        try: client.files.delete(name=archivo_google.name)
        except: pass

        if response.parsed: return response.parsed
        return LevantamientoTecnico(**json.loads(response.text))
    except Exception as e:
        print(f"ERROR AUDIO: {e}")
        raise e
