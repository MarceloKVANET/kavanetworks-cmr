import os
import time
from google import genai
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Cargaremos las variables de entorno del archivo .env
load_dotenv()
if not os.environ.get("GEMINI_API_KEY"):
    import streamlit as st
    if "GEMINI_API_KEY" in st.secrets:
        os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]

# --- 1. DEFINIR LA ESTRUCTURA DE LOS DATOS ---
class ItemMaterial(BaseModel):
    nombre_material: str = Field(description="Nombre del ítem (ej. 'Punto de red Cat.6 completo').")
    descripcion_detallada: str = Field(description="Descripción técnica completa que incluye los servicios (ej. tendido, punchado, certificado)")
    cantidad: float = Field(description="Cantidad total del ítem")
    unidad_medida: str = Field(description="Unidad (ej. puntos, unidades, mt)")
    precio_unitario_neto_estimado: float = Field(description="Precio unitario final calculado internamente por la IA sumando todos los componentes necesarios.")
    justificacion_costo: str = Field(description="Desglose de cómo la IA llegó a ese precio unitario.")

class LevantamientoTecnico(BaseModel):
    resumen_proyecto: str = Field(description="Un resumen de 1 oración describiendo el objetivo general de la visita")
    materiales_y_servicios: list[ItemMaterial] = Field(description="Lista detallada de todo lo que solicitó el técnico")
    notas_adicionales: str = Field(description="Cualquier otra observación importante. Dejar vacío si no hay.")
    sugerencia_margen: float = Field(description="Porcentaje de margen de utilidad sugerido (ej: 0.3 para 30%)")
    justificacion_margen: str = Field(description="Breve explicación de por qué sugieres ese margen")

# --- 2. CONFIGURAR EL MOTOR DE IA (GEMINI 1.5 PRO LATEST) ---
MODEL_ID = 'gemini-1.5-pro-latest' # Cambiado de gemini-1.5-pro para evitar 404

def get_client():
    """Inicializa el cliente de GenAI con la API Key."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("No se encontró la variable de entorno GEMINI_API_KEY")
    return genai.Client(api_key=api_key)

def analizar_reporte_tecnico(texto_del_tecnico: str, lista_precios_actual: str = "") -> LevantamientoTecnico:
    """
    Toma el texto del técnico y devuelve un objeto estructurado usando Gemini Pro.
    """
    print(f"\n[KVANetworks CRM] Procesando reporte con {MODEL_ID}...\n")
    client = get_client()
    
    prompt_sistema = f"""
Eres un asistente experto en redes, electricidad y sistemas CCTV para KVANetworks Chile.
Tu trabajo es extraer materiales y servicios de reportes informales.

**CEREBRO DE COSTOS (CRITICAL)**: 
Si se menciona un 'Punto de red' o 'Cámara', calcula el costo TOTAL unitario sumando cable, conectores y mano de obra.

**CATÁLOGO DE PRECIOS REALES**:
{lista_precios_actual}
Usa estos precios si coinciden.

Todos los cálculos en CLP NETOS. Sugiere un margen comercial (ej. 30%).
"""
    
    respuesta = client.models.generate_content(
        model=MODEL_ID,
        contents=texto_del_tecnico,
        config={
            'response_mime_type': 'application/json',
            'response_schema': LevantamientoTecnico,
            'system_instruction': prompt_sistema,
            'temperature': 0.1
        },
    )
    
    if respuesta.parsed:
        return respuesta.parsed
    else:
        raise Exception(f"La IA {MODEL_ID} no pudo estructurar la respuesta")

def analizar_audio_tecnico(ruta_audio: str, lista_precios_actual: str = "") -> LevantamientoTecnico:
    """
    Sube un audio a Gemini Pro y extrae materiales estructurados.
    """
    print(f"\n[KVANetworks CRM] Analizando audio con {MODEL_ID}...\n")
    client = get_client()
    
    if not os.path.exists(ruta_audio):
        raise FileNotFoundError(f"Archivo no encontrado: {ruta_audio}")

    archivo_subido = None
    try:
        # 1. Subir archivo
        print("📡 Subiendo audio...")
        archivo_subido = client.files.upload(file=ruta_audio)
        
        # 2. ESPERAR A QUE ESTÉ ACTIVO
        print("⏳ Esperando que Gemini procese el archivo...")
        max_retries = 30
        for _ in range(max_retries):
            archivo_subido = client.files.get(name=archivo_subido.name)
            if archivo_subido.state.name == "ACTIVE":
                print("✅ Archivo listo.")
                break
            if archivo_subido.state.name == "FAILED":
                raise Exception("El procesamiento del audio falló.")
            time.sleep(2)
        else:
            raise Exception("Tiempo de espera agotado para el audio.")

        prompt_sistema = f"""
Eres un Ingeniero de Costos experto de KVANetworks Chile. Escucha el audio en español (es-CL).
Extrae materiales y servicios. Calcula precio unitario sumando mano de obra.
Resultados en CLP NETOS. Sugiere margen de utilidad.
"""

        respuesta = client.models.generate_content(
            model=MODEL_ID,
            contents=["Extrae el levantamiento técnico de este audio:", archivo_subido],
            config={
                'response_mime_type': 'application/json',
                'response_schema': LevantamientoTecnico,
                'system_instruction': prompt_sistema,
                'temperature': 0.1
            },
        )
        
        if respuesta.parsed:
            return respuesta.parsed
        else:
            raise Exception("La IA no pudo procesar el audio correctamente después de escucharlo")

    finally:
        if archivo_subido:
            try:
                client.files.delete(name=archivo_subido.name)
            except:
                pass

if __name__ == "__main__":
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("⚠️ ERROR: Falta GEMINI_API_KEY.")
    else:
        print(f"Motor {MODEL_ID} listo.")
