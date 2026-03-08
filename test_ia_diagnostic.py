import os
from traductor_ia import analizar_reporte_tecnico
from dotenv import load_dotenv

# Asegurar carga de API Key
load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    print("❌ ERROR: GEMINI_API_KEY no encontrada.")
else:
    print(f"✅ API Key detectada: {api_key[:5]}...")
    
    test_text = "Necesitamos instalar 5 puntos de red Cat6 en la oficina central y un rack de 12U."
    
    try:
        print("🚀 Probando conexión con Gemini 1.5 Pro...")
        resultado = analizar_reporte_tecnico(test_text)
        print("\n🏆 ¡ÉXITO! La IA Pro respondió correctamente:")
        print(f"Resumen: {resultado.resumen_proyecto}")
        for item in resultado.materiales_y_servicios:
            print(f"- {item.cantidad} x {item.nombre_material} ({item.precio_unitario_neto_estimado} CLP)")
    except Exception as e:
        print(f"❌ FALLO EN LA PRUEBA IA: {str(e)}")
