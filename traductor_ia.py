import os
from google import genai
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Cargaremos las variables de entorno (como tu contraseña o llave de API) del archivo .env
load_dotenv()

# --- 1. DEFINIR LA ESTRUCTURA DE LOS DATOS ---
# Usamos Pydantic para decirle a la IA exactamente qué información queremos extraer y en qué formato.
class ItemMaterial(BaseModel):
    nombre_material: str = Field(description="Nombre del ítem (ej. 'Punto de red Cat.6 completo').")
    descripcion_detallada: str = Field(description="Descripción técnica completa que incluye los servicios (ej. tendido, punchado, certificado)")
    cantidad: float = Field(description="Cantidad total del ítem")
    unidad_medida: str = Field(description="Unidad (ej. puntos, unidades, mt)")
    precio_unitario_neto_estimado: float = Field(description="Precio unitario final calculado internamente por la IA sumando todos los componentes necesarios para UN SOLO ítem de este tipo.")
    justificacion_costo: str = Field(description="Desglose de cómo la IA llegó a ese precio unitario (ej. calculando metros de cable + conectores + horas de técnico)")

class LevantamientoTecnico(BaseModel):
    resumen_proyecto: str = Field(description="Un resumen de 1 oración describiendo el objetivo general de la visita")
    materiales_y_servicios: list[ItemMaterial] = Field(description="Lista detallada de todo lo que solicitó el técnico")
    notas_adicionales: str = Field(description="Cualquier otra observación importante que mencionó el técnico. Dejar vacío si no hay.")
    sugerencia_margen: float = Field(description="Porcentaje de margen de utilidad sugerido (ej: 0.3 para 30%) basado en la complejidad del trabajo")
    justificacion_margen: str = Field(description="Breve explicación de por qué sugieres ese margen (riesgo, dificultad, tiempo)")

# --- 2. CONFIGURAR EL MOTOR DE IA ---
# Para usar esto en la vida real, necesitarás una API Key de Google (es gratis para empezar).
def analizar_reporte_tecnico(texto_del_tecnico: str) -> LevantamientoTecnico:
    """
    Toma el texto desordenado del técnico, consulta a Gemini, y devuelve un objeto estructurado.
    """
    print("\n[KVANetworks CRM] Procesando reporte con Inteligencia Artificial...\n")
    
    # Inicializa el cliente usando la variable de entorno GEMINI_API_KEY
    client = genai.Client()
    
    prompt_sistema = """
Eres un asistente experto en redes, electricidad y sistemas CCTV. 
Trabajas para la empresa KVANetworks.
Tu trabajo es leer los apuntes informales de los técnicos en terreno y extraer de forma 
ordenada y precisa todos los materiales y servicios solicitados para armar una cotización formal.

**CEREBRO DE COSTOS (CRITICAL)**: 
Si el técnico menciona un sistema compuesto (ej. 'Punto de red' o 'Punto de Cámara'), la IA DEBE:
1. Identificar componentes base: metros de cable (según la distancia que diga el técnico), conectores, faceplates, patchcords, mano de obra proporcional por punto.
2. Calcular el costo TOTAL para completar UN SOLO punto (Precio Unitario).
3. En el campo 'nombre_material', poner el sistema completo.
4. En 'descripcion_detallada', listar: 'tendido, punchado, accesorios completo y certificado'.

Asegúrate de deducir unidades lógicas. Todos los cálculos en CLP NETOS.
También debes sugerir un margen de utilidad comercial (ej. 30% para KVANetworks).
"""
    
    # Llamamos a Gemini (usaremos el modelo flash, que es rapidísimo y muy bueno para texto lógico)
    respuesta = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=texto_del_tecnico,
        config={
            'response_mime_type': 'application/json',
            'response_schema': LevantamientoTecnico,
            'system_instruction': prompt_sistema,
            'temperature': 0.1 # Para que sea preciso y no "invente" cosas
        },
    )
    
    # La respuesta ya viene en el formato estructurado de nuestra clase Pydantic!!
    if respuesta.parsed:
      return respuesta.parsed
    else:
        raise Exception("La IA no pudo estructurar la respuesta")

# --- 3. PRUEBA DEL SISTEMA ---
# Este es un texto de ejemplo, como si tu técnico te hubiera mandado un Whatsapp
texto_prueba = """
Jefe, acabo de terminar la visita en la oficina del cliente nuevo. 
Necesitan cablear el segundo piso. A simple vista van a ser como 20 puntos de red cat 6 completos.
También pidieron que pongamos 4 cámaras domo IP en los pasillos, revisar bien que sean POE.
Vamos a necesitar un rack mural, yo creo que uno de 9U o 12U anda bien. 
Ah, y separar unos 3 rollos de cable UTP para exterior por si las moscas, y canaletas para tapar todo.
Para la mano de obra calcúlale unos 3 días de trabajo para 2 técnicos.
"""

def analizar_audio_tecnico(ruta_audio: str) -> LevantamientoTecnico:
    """
    Sube un archivo de audio a Gemini y extrae los materiales con el cerebro de costos.
    """
    client = genai.Client()
    
    # Subir archivo
    archivo_subido = client.files.upload(file=ruta_audio)
    
    prompt_audio = """
    Escucha atentamente este audio del técnico en terreno.
    Debes identificar el proyecto y desglosar todos los puntos de red, cámaras o servicios mencionados.
    Usa el CEREBRO DE COSTOS para calcular los precios unitarios compuestos.
    """
    
    respuesta = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=[prompt_audio, archivo_subido],
        config={
            'response_mime_type': 'application/json',
            'response_schema': LevantamientoTecnico,
            'system_instruction': """
Eres un asistente experto en redes, electricidad y sistemas CCTV. 
Trabajas para la empresa KVANetworks.
Tu trabajo es escuchar la nota de voz del técnico y extraer la información estructurada.
**CEREBRO DE COSTOS (CRITICAL)**: 
Si menciona 'Puntos de red' o similar, calcula el costo total (cable + conectores + mano de obra + certificación) y ponlo como Precio Unitario.
""",
            'temperature': 0.1
        },
    )
    
    if respuesta.parsed:
        return respuesta.parsed
    else:
        raise Exception("La IA no pudo procesar el audio correctamente")

if __name__ == "__main__":
    # Solo ejecutamos esto si tenemos la llave configurada
    if not os.environ.get("GEMINI_API_KEY"):
        print("⚠️ ERROR: Falta configurar tu 'GEMINI_API_KEY'.")
        print("Para probarlo, primero debes obtener una llave gratuita en Google AI Studio.")
    else:
        # Ejecutamos la función
        resultado = analizar_reporte_tecnico(texto_prueba)
        
        # Mostramos los resultados hermosamente por pantalla
        print("="*50)
        print(f"📊 RESUMEN: {resultado.resumen_proyecto}")
        print("="*50)
        print("🛠️ LISTA DE MATERIALES / SERVICIOS:")
        for articulo in resultado.materiales_y_servicios:
            print(f"  - [{articulo.cantidad} {articulo.unidad_medida}] {articulo.nombre_material}")
            
        if resultado.notas_adicionales:
            print("-"*50)
            print(f"📝 NOTAS DEL TÉCNICO: {resultado.notas_adicionales}")
        print("="*50)
        print("\n¡Traducción exitosa! Listo para enviar a formato Excel en la Fase 2.")
