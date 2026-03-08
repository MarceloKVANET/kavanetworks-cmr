import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Importaciones de tus otros módulos
from traductor_ia import analizar_reporte_tecnico
from generador_excel import crear_excel_cotizacion
from database import guardar_cotizacion_en_bd # <-- ¡Puente activado!

load_dotenv()

def datetime_filename():
    """Genera un texto con la fecha y hora actual para el nombre del archivo"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def ejecutar_flujo_completo(texto_tecnico):
    """
    Coordina todo el proceso del CRM: IA -> Excel -> Base de Datos
    """
    print("\n" + "="*60)
    print("🚀 INICIANDO PROCESAMIENTO KVANetworks CRM")
    print("="*60)

    try:
        # 1. PASO IA: Analizar el mensaje del técnico
        datos_estructurados = analizar_reporte_tecnico(texto_tecnico)
        
        # 2. PASO EXCEL: Generar el archivo físico primero
        nombre_salida = f"cotizacion_{datetime_filename()}.xlsx"
        ruta_absoluta = crear_excel_cotizacion(datos_estructurados, nombre_salida)
        
        # 3. PASO BASE DE DATOS: Guardar registro con la ruta del Excel
        print("💾 Guardando cotización en el historial...")
        id_cotizacion = guardar_cotizacion_en_bd(datos_estructurados, ruta_absoluta)
        
        print("\n✅ PROCESO COMPLETADO CON ÉXITO")
        print(f"📄 Archivo generado: {nombre_salida}")
        print(f"📍 Ubicación: {ruta_absoluta}")
        print(f"🗄️ ID en Base de Datos: {id_cotizacion}")
        print("="*60)
        
        return ruta_absoluta

    except Exception as e:
        print(f"\n❌ ERROR EN EL SISTEMA: {str(e)}")
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        entrada = sys.argv[1]
    else:
        print("💡 TIP: Puedes pasar el reporte del técnico entre comillas después del comando.")
        print("   Ejemplo: python app_kvanetworks.py 'Necesitamos 10 puntos de red...'")
        print("\nEjecutando prueba de demostración...")
        entrada = """
        Hola Marcelo, para el cliente de la calle San Diego, necesitamos hacer
        la mantención de las 8 cámaras. Además quieren agregar 2 cámaras nuevas
        en el patio trasero, ahí se van como 50 metros de cable y tubos PVC.
        Estaríamos unos 2 días ahí. El trabajo está difícil porque el techo está alto.
        """
    
    ejecutar_flujo_completo(entrada)