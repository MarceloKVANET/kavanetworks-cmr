from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from datetime import datetime
import os

def crear_excel_cotizacion(datos, nombre_archivo="cotizacion_kvanetworks.xlsx"):
    """
    Toma los datos extraídos por la IA y crea un archivo Excel profesional.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Cotización"

    # --- CONFIGURACIÓN DE ESTILOS ---
    azul_kvanetworks = "003366"
    gris_claro = "F2F2F2"
    
    fuente_titulo = Font(name="Arial", size=16, bold=True, color="FFFFFF")
    fuente_negrita = Font(bold=True)
    relleno_azul = PatternFill(start_color=azul_kvanetworks, end_color=azul_kvanetworks, fill_type="solid")
    relleno_gris = PatternFill(start_color=gris_claro, end_color=gris_claro, fill_type="solid")
    
    borde_fino = Border(
        left=Side(style='thin'), 
        right=Side(style='thin'), 
        top=Side(style='thin'), 
        bottom=Side(style='thin')
    )

    # --- ENCABEZADO ---
    ws.merge_cells('A1:E2')
    ws['A1'] = "KVANetworks - COTIZACIÓN TÉCNICA"
    ws['A1'].font = fuente_titulo
    ws['A1'].fill = relleno_azul
    ws['A1'].alignment = Alignment(horizontal="center", vertical="center")

    # Información básica
    ws['A4'] = "Fecha:"
    ws['B4'] = datetime.now().strftime("%d/%m/%Y")
    ws['A5'] = "Proyecto:"
    ws['B5'] = datos.resumen_proyecto
    
    # --- TABLA DE MATERIALES ---
    ws['A7'] = "Ítem"
    ws['B7'] = "Descripción"
    ws['C7'] = "Cantidad"
    ws['D7'] = "Unidad"
    ws['E7'] = "Neto Unitario ($)"
    ws['F7'] = "Margen (%)"
    ws['G7'] = "Total Neto ($)"

    # Aplicar estilos al encabezado de la tabla
    for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
        celda = ws[f'{col}7']
        celda.font = fuente_negrita
        celda.fill = relleno_gris
        celda.border = borde_fino
        celda.alignment = Alignment(horizontal="center")

    # Margen global sugerido por la IA
    margen_base = datos.sugerencia_margen

    # Llenar la tabla
    fila_actual = 8
    for i, item in enumerate(datos.materiales_y_servicios, 1):
        ws[f'A{fila_actual}'] = i
        ws[f'B{fila_actual}'] = f"{item.nombre_material} - {item.descripcion_detallada}"
        ws[f'C{fila_actual}'] = item.cantidad
        ws[f'D{fila_actual}'] = item.unidad_medida
        ws[f'E{fila_actual}'] = item.precio_unitario_neto_estimado
        ws[f'F{fila_actual}'] = margen_base 
        
        # Fórmula de Excel para calcular el total con margen incluido: (Cantidad * Precio) / (1 - Margen)
        # O si el margen es un recargo directo: (Cantidad * Precio * (1 + Margen))
        # Usaremos el recargo directo por simplicidad: =C8*E8*(1+F8)
        ws[f'G{fila_actual}'] = f"=C{fila_actual}*E{fila_actual}*(1+F{fila_actual})"
        
        # Formato moneda para precios
        ws[f'E{fila_actual}'].number_format = '#,##0'
        ws[f'F{fila_actual}'].number_format = '0%'
        ws[f'G{fila_actual}'].number_format = '#,##0'

        # Aplicar bordes
        for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
            ws[f'{col}{fila_actual}'].border = borde_fino
        
        fila_actual += 1

    # --- TOTALES FINALES ---
    fila_actual += 1
    ws[f'F{fila_actual}'] = "Subtotal Neto:"
    ws[f'G{fila_actual}'] = f"=SUM(G8:G{fila_actual-2})"
    ws[f'F{fila_actual}'].font = fuente_negrita
    
    fila_actual += 1
    ws[f'F{fila_actual}'] = "IVA (19%):"
    ws[f'G{fila_actual}'] = f"=G{fila_actual-1}*0.19"
    
    fila_actual += 1
    ws[f'F{fila_actual}'] = "TOTAL FINAL ($):"
    ws[f'G{fila_actual}'] = f"=G{fila_actual-2}+G{fila_actual-1}"
    ws[f'F{fila_actual}'].font = fuente_negrita
    ws[f'G{fila_actual}'].font = Font(bold=True, size=12)

    # --- SECCIÓN DE INTELIGENCIA COMERCIAL (IA) ---
    fila_actual += 2
    ws.merge_cells(f'A{fila_actual}:G{fila_actual}')
    ws[f'A{fila_actual}'] = "💡 Justificación Técnica de la IA"
    ws[f'A{fila_actual}'].font = fuente_negrita
    
    fila_actual += 1
    ws.merge_cells(f'A{fila_actual}:G{fila_actual + 1}')
    ws[f'A{fila_actual}'] = datos.justificacion_margen
    ws[f'A{fila_actual}'].alignment = Alignment(wrap_text=True, vertical="top")

    # Ajustar ancho de columnas
    ws.column_dimensions['B'].width = 60
    ws.column_dimensions['G'].width = 20

    # Guardar archivo
    wb.save(nombre_archivo)
    return os.path.abspath(nombre_archivo)

if __name__ == "__main__":
    # Prueba rápida con datos simulados
    print("Este archivo es un módulo. Úsalo importándolo desde app_kvanetworks.py")
