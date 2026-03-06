import os
import sys
from traductor_ia import analizar_reporte_tecnico
from generador_excel import crear_excel_cotizacion
from dotenv import load_dotenv

load_dotenv()

def ejecutar_flujo_completo(texto_tecnico):
    """
    Coordina todo el proceso: IA + Excel
    """
    print("\n" + "="*60)
    print("🚀 INICIANDO PROCESAMIENTO KVANetworks CRM")
    print("="*60)

    try:
        # 1. PASO IA: Analizar el mensaje
        datos_estructurados = analizar_reporte_tecnico(texto_tecnico)
        
        # 2. PASO EXCEL: Generar el archivo
        nombre_salida = f"cotizacion_{datetime_filename()}.xlsx"
        ruta_absoluta = crear_excel_cotizacion(datos_estructurados, nombre_salida)
        
        print("\n" + "✅" + " PROCESO COMPLETADO CON ÉXITO")
        print(f"📄 Archivo generado: {nombre_salida}")
        print(f"📍 Ubicación: {ruta_absoluta}")
        print("="*60)
        
        return ruta_absoluta

    except Exception as e:
        print(f"\n❌ ERROR EN EL SISTEMA: {str(e)}")
        return None

def datetime_filename():
    from datetime import datetime
    return datetime.now().strftime("%Y%m%d_%H%M%S")

if __name__ == "__main__":
    # Si el usuario no pasó texto, usamos uno por defecto para demostrar
    if len(sys.argv) > 1:
        entrada = sys.argv[1]
    else:
        print("💡 TIP: Puedes pasar el reporte del técnico entre comillas después del comando.")
        print("   Ejemplo: python app_kvanetworks.py 'Necesitamos 10 cámaras...'")
        print("\nEjecutando prueba de demostración...")
        entrada = """
        Hola Marcelo, para el cliente de la calle San Diego, necesitamos hacer
        la mantención de las 8 cámaras. Además quieren agregar 2 cámaras nuevas
        en el patio trasero, ahí se van como 50 metros de cable y tubos PVC.
        Estaríamos unos 2 días ahí. El trabajo está difícil porque el techo está alto.
        """
    
    ejecutar_flujo_completo(entrada)
