import os
from google import genai
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Cargamos las variables de entorno
load_dotenv()

# --- 1. DEFINICIÓN DE ESTRUCTURA ---
class ItemMaterial(BaseModel):
    nombre_material: str = Field(description="Nombre descriptivo del material, equipo o servicio solicitado")
    cantidad: float = Field(description="Cantidad solicitada. Si no se especifica, usar 1.0")
    unidad_medida: str = Field(description="Unidad (ej: unidades, metros, cajas, rollos, horas). Si no se infiere, usar 'unidades'")

class LevantamientoTecnico(BaseModel):
    resumen_proyecto: str = Field(description="Un resumen de 1 oración describiendo el objetivo general de la visita")
    materiales_y_servicios: list[ItemMaterial] = Field(description="Lista detallada de todo lo que solicitó el técnico")
    notas_adicionales: str = Field(description="Cualquier otra observación importante que mencionó el técnico. Dejar vacío si no hay.")

# --- 2. CONFIGURAR EL MOTOR DE IA PARA AUDIO ---
def analizar_audio_tecnico(ruta_audio: str) -> LevantamientoTecnico:
    """
    Sube un archivo de audio a Gemini, extrae los materiales, y luego borra el archivo de la nube.
    """
    print(f"\n[KVANetworks CRM] Procesando audio ({ruta_audio}) con Inteligencia Artificial...\n")
    
    # Seguro anti-errores: Verificar que el archivo realmente exista en tu PC
    if not os.path.exists(ruta_audio):
        raise FileNotFoundError(f"No se encontró el archivo de audio. Revisa que '{ruta_audio}' esté en la carpeta correcta.")

    client = genai.Client()
    archivo_subido = None
    
    try:
        # Paso A: Subir el archivo de audio
        print("📡 Subiendo audio de forma segura...")
        archivo_subido = client.files.upload(file=ruta_audio)
        print("✅ Audio subido correctamente. Escuchando y analizando...")
        
        prompt_sistema = """
        Eres un asistente experto en redes, electricidad y sistemas CCTV. 
        Trabajas para la empresa KVANetworks.
        Tu trabajo es escuchar la nota de voz del técnico en terreno y extraer de forma 
        ordenada y precisa todos los materiales y servicios solicitados para armar una cotización formal.
        Asegúrate de deducir unidades lógicas si el técnico es ambiguo.
        """
        
        # Paso B: Usar el modelo PRO para máxima precisión
        respuesta = client.models.generate_content(
            model='gemini-2.5-pro',
            contents=["Por favor extrae los materiales mencionados en este audio:", archivo_subido],
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
            raise Exception("La IA no pudo estructurar la respuesta del audio")

    finally:
        # Paso C: LIMPIEZA OBLIGATORIA (Se ejecuta siempre, incluso si hay un error)
        if archivo_subido:
            print("🧹 Limpiando servidores: Borrando audio temporal de la nube...")
            client.files.delete(name=archivo_subido.name)

if __name__ == "__main__":
    if not os.environ.get("GEMINI_API_KEY"):
        print("⚠️ ERROR: Falta configurar tu 'GEMINI_API_KEY' en el archivo .env")
    else:
        print("💡 El módulo de audio está listo y optimizado.")
        print("Para probarlo, llama a la función analizar_audio_tecnico('nombre_del_audio.mp3')")