import os
import time
from google import genai
from pydantic import BaseModel, Field

# La API Key se carga desde el entorno (gestionado por main_web.py)
def get_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        import streamlit as st
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
            os.environ["GEMINI_API_KEY"] = api_key
        else:
            raise ValueError("No se encontró la GEMINI_API_KEY en secretos ni entorno.")
    return genai.Client(api_key=api_key)

# --- 1. ESTRUCTURA DE DATOS ---
class ItemMaterial(BaseModel):
    nombre_material: str = Field(description="Nombre del ítem (ej. 'Cámara IP 4MP').")
    descripcion_detallada: str = Field(description="Descripción técnica y servicios incluidos.")
    cantidad: float = Field(description="Cantidad solicitada")
    unidad_medida: str = Field(description="Unidad (puntos, c/u, mt)")
    precio_unitario_neto_estimado: float = Field(description="Precio unitario final CLP NETO calculado por la IA.")
    justificacion_costo: str = Field(description="Breve desglose del precio unitario.")

class LevantamientoTecnico(BaseModel):
    resumen_proyecto: str = Field(description="Resumen breve del objetivo.")
    materiales_y_servicios: list[ItemMaterial] = Field(description="Lista de ítems detectados.")
    notas_adicionales: str = Field(description="Observaciones del técnico.")
    sugerencia_margen: float = Field(description="Margen sugerido (ej: 0.35 para 35%)")
    justificacion_margen: str = Field(description="Por qué sugieres este margen.")

# --- 2. CONFIGURACIÓN GEMINI 3.1 PRO ---
# Usamos el identificador experimental/preview para Gemini 3.1 Pro
MODEL_ID = 'gemini-3.1-pro-preview' 

def analizar_reporte_tecnico(texto: str, lista_precios: str = "") -> LevantamientoTecnico:
    client = get_client()
    print(f"DEBUG: Procesando con {MODEL_ID}")
    
    prompt = f"""
Eres un experto de KVANetworks Chile. Extrae materiales de este reporte.
Calcula precios unitarios CLP NETOS incluyendo mano de obra si es necesario.
CATÁLOGO: {lista_precios}
"""
    
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=texto,
        config={
            'response_mime_type': 'application/json',
            'response_schema': LevantamientoTecnico,
            'system_instruction': prompt,
            'temperature': 0.1
        }
    )
    if response.parsed:
        return response.parsed
    raise Exception("Error al parsear respuesta de Gemini 3.1")

def analizar_audio_tecnico(ruta_audio: str, lista_precios: str = "") -> LevantamientoTecnico:
    client = get_client()
    print(f"DEBUG: Analizando audio con {MODEL_ID}")
    
    archivo_google = client.files.upload(file=ruta_audio)
    
    # Espera activa para procesamiento de audio
    while archivo_google.state.name == "PROCESSING":
        time.sleep(2)
        archivo_google = client.files.get(name=archivo_google.name)
    
    if archivo_google.state.name == "FAILED":
        raise Exception("Google no pudo procesar este archivo de audio.")

    prompt = "Escucha este audio de KVANetworks Chile y genera el JSON del levantamiento técnico. Precios en CLP NETOS."
    
    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=[prompt, archivo_google],
            config={
                'response_mime_type': 'application/json',
                'response_schema': LevantamientoTecnico,
                'temperature': 0.1
            }
        )
        if response.parsed:
            return response.parsed
        raise Exception("Gemini 3.1 no pudo estructurar el audio.")
    finally:
        client.files.delete(name=archivo_google.name)
