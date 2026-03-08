import os
import time
import json
from google import genai
from pydantic import BaseModel, Field

def get_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        import streamlit as st
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
            os.environ["GEMINI_API_KEY"] = api_key
        else:
            raise ValueError("GEMINI_API_KEY NOT FOUND")
    return genai.Client(api_key=api_key)

class ItemMaterial(BaseModel):
    nombre_material: str = Field(description="Nombre del material")
    descripcion_detallada: str = Field(description="Descripción")
    cantidad: float = Field(description="Cantidad")
    unidad_medida: str = Field(description="Unidad")
    precio_unitario_neto_estimado: float = Field(description="Precio CLP")
    justificacion_costo: str = Field(description="Justificación")

class LevantamientoTecnico(BaseModel):
    resumen_proyecto: str = Field(description="Resumen")
    materiales_y_servicios: list[ItemMaterial] = Field(description="Materiales")
    notas_adicionales: str = Field(description="Notas")
    sugerencia_margen: float = Field(description="Margen")
    justificacion_margen: str = Field(description="Justificación margen")

MODEL_ID = 'gemini-1.5-pro'

def analizar_reporte_tecnico(texto: str, lista_precios: str = "") -> LevantamientoTecnico:
    client = get_client()
    print(f"DEBUG: Processing text with {MODEL_ID}")
    
    prompt = f"Extrae materiales de este reporte: {texto}. Responde en JSON basado en el esquema."
    
    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=texto,
            config={
                'response_mime_type': 'application/json',
                'response_schema': LevantamientoTecnico,
                'system_instruction': f"Eres un experto de KVANetworks Chile. Precios en CLP NETOS. CATALOGO: {lista_precios}",
                'temperature': 0.1
            }
        )
        
        if response.parsed:
            return response.parsed
        
        # Fallback manual si .parsed falla (a veces pasa en SDKs antiguos o respuestas raras)
        if response.text:
            cleaned_json = response.text.replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned_json)
            return LevantamientoTecnico(**data)
            
        raise Exception("Sin respuesta de la IA")
    except Exception as e:
        print(f"ERROR IA TEXTO: {str(e)}")
        raise e

def analizar_audio_tecnico(ruta_audio: str, lista_precios: str = "") -> LevantamientoTecnico:
    client = get_client()
    print(f"DEBUG: Uploading audio {ruta_audio}")
    
    try:
        archivo_google = client.files.upload(file=ruta_audio)
        
        while archivo_google.state.name == "PROCESSING":
            time.sleep(2)
            archivo_google = client.files.get(name=archivo_google.name)
            
        if archivo_google.state.name != "ACTIVE":
            raise Exception(f"Fallo carga: {archivo_google.state.name}")

        response = client.models.generate_content(
            model=MODEL_ID,
            contents=["Escucha y extrae materiales en JSON:", archivo_google],
            config={
                'response_mime_type': 'application/json',
                'response_schema': LevantamientoTecnico,
                'temperature': 0.1
            }
        )
        
        client.files.delete(name=archivo_google.name)

        if response.parsed:
            return response.parsed
        
        if response.text:
            cleaned_json = response.text.replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned_json)
            return LevantamientoTecnico(**data)

        raise Exception("IA no pudo procesar el audio")
    except Exception as e:
        print(f"ERROR IA AUDIO: {str(e)}")
        raise e
