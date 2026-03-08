import os
import time
from google import genai
from pydantic import BaseModel, Field

# La API Key se carga desde el entorno o secretos
def get_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        import streamlit as st
        # Intento de carga directa desde secretos si no está en el entorno
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
            os.environ["GEMINI_API_KEY"] = api_key
        else:
            raise ValueError("No se encontró la GEMINI_API_KEY.")
    return genai.Client(api_key=api_key)

# --- 1. ESTRUCTURA DE DATOS (PYDANTIC V2 COMPATIBLE) ---
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

# --- 2. CONFIGURACIÓN GEMINI ---
# NOTA: Si gemini-3.1-pro-preview falla, bajaremos a gemini-1.5-pro que es más estable
# en términos de compatibilidad de tipos de respuesta (Response Schema).
MODEL_ID = 'gemini-1.5-pro' 

def analizar_reporte_tecnico(texto: str, lista_precios: str = "") -> LevantamientoTecnico:
    client = get_client()
    print(f"DEBUG: Procesando texto con {MODEL_ID}")
    
    prompt = f"""
Eres un ingeniero de costos de KVANetworks Chile. Extrae materiales de este reporte técnico.
Calcula precios unitarios CLP NETOS incluyendo materiales y mano de obra.
CATÁLOGO DE REFERENCIA: {lista_precios}
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
    raise Exception(f"Gemini ({MODEL_ID}) no pudo estructurar la información. Respuesta cruda: {response.text}")

def analizar_audio_tecnico(ruta_audio: str, lista_precios: str = "") -> LevantamientoTecnico:
    client = get_client()
    print(f"DEBUG: Subiendo audio para análisis con {MODEL_ID}")
    
    if not os.path.exists(ruta_audio):
        raise FileNotFoundError(f"No se encontró el archivo: {ruta_audio}")

    archivo_google = client.files.upload(file=ruta_audio)
    
    # Espera activa para procesamiento de audio (Polling)
    max_intentos = 30
    intento = 0
    while archivo_google.state.name == "PROCESSING" and intento < max_intentos:
        time.sleep(2)
        archivo_google = client.files.get(name=archivo_google.name)
        intento += 1
    
    if archivo_google.state.name != "ACTIVE":
        raise Exception(f"El procesamiento del audio en Google falló o tardó demasiado (Estado: {archivo_google.state.name})")

    prompt = "Escucha atentamente este audio técnico de KVANetworks Chile. Extrae todos los materiales y servicios mencionados. Calcula precios unitarios CLP NETOS."
    
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
        raise Exception(f"Gemini ({MODEL_ID}) no pudo procesar el contenido del audio. Respuesta cruda: {response.text}")
    finally:
        # Limpieza del archivo en Google para no saturar cuotas
        try:
            client.files.delete(name=archivo_google.name)
        except:
            pass
