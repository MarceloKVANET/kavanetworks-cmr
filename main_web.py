import streamlit as st
import os
from traductor_ia import analizar_reporte_tecnico, analizar_audio_tecnico
from generador_excel import crear_excel_cotizacion
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="KVANetworks CRM",
    page_icon="📶",
    layout="wide"
)

# --- ESTILOS PERSONALIZADOS (SITEI INSPIRATION) ---
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        background-color: #04447c;
        color: white;
        border-radius: 5px;
        border: none;
        padding: 0.5rem 1rem;
    }
    .stHeader {
        color: #04447c;
    }
    </style>
""", unsafe_allow_html=True)

# --- CABECERA ---
st.title("📶 KVANetworks CRM")
st.subheader("Sistema Inteligente de Cotizaciones: Telecomunicaciones & Electricidad")

# --- BARRA LATERAL (GESTIÓN) ---
with st.sidebar:
    st.image("https://img.icons8.com/ios-filled/100/04447c/infinity.png", width=100) # Placeholder logo
    st.title("Panel de Control")
    opcion = st.radio("Menu", ["📦 Crear Cotización", "👥 Clientes", "📊 Historial"])
    st.divider()
    st.info("Logueado como: Marcelo (Admin)")

# --- MÓDULO PRINCIPAL: CREAR COTIZACIÓN ---
if opcion == "📦 Crear Cotización":
    st.header("📝 Nuevo Levantamiento Técnico")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("Escriba o pegue el reporte enviado por el técnico:")
        reporte_texto = st.text_area(
            "Reporte de Terreno", 
            placeholder="Ej: Instalar 10 puntos de red cat6 en bodega...",
            height=200
        )
        
        # Opción de Audio (Simulada en esta fase de interfaz)
        audio_file = st.file_uploader("📥 O subir nota de voz del técnico", type=['mp3', 'wav', 'm4a'])
        if audio_file:
            st.audio(audio_file)
            st.warning("Módulo de procesamiento de audio cargado. Listo para análisis.")

    with col2:
        st.write("Configuración de Cotización")
        cliente_nombre = st.text_input("Nombre del Cliente/Empresa", placeholder="Ej: Minera San José")
        margen_manual = st.slider("Margen de Utilidad Sugerido (%)", 0, 100, 30)
        
    if st.button("🚀 PROCESAR CON IA Y GENERAR EXCEL"):
            with st.spinner("🧠 KVANetworks IA trabajando..."):
                try:
                    # 1. Ejecutar IA (Texto o Audio)
                    if audio_file:
                        # Guardar temporalmente para que Gemini pueda leerlo
                        temp_path = f"temp_{audio_file.name}"
                        with open(temp_path, "wb") as f:
                            f.write(audio_file.getbuffer())
                        datos = analizar_audio_tecnico(temp_path)
                        os.remove(temp_path) # Limpiar
                    else:
                        datos = analizar_reporte_tecnico(reporte_texto)
                    
                    st.success("¡Análisis completado!")
                    
                    # Mostrar vista previa
                    st.write("### 📋 Vista Previa de la Cotización")
                    st.info(f"**Resumen:** {datos.resumen_proyecto}")
                    
                    # Tabla de materiales
                    st.table([
                        {"Material": m.nombre_material, "Cantidad": m.cantidad, "Neto Est.": m.precio_unitario_neto_estimado}
                        for m in datos.materiales_y_servicios
                    ])
                    
                    st.write(f"**Justificación IA:** {datos.justificacion_margen}")
                    
                    # 2. Generar Excel
                    filename = f"cotizacion_{cliente_nombre.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.xlsx"
                    ruta = crear_excel_cotizacion(datos, filename)
                    
                    # 3. Botón de Descarga
                    with open(ruta, "rb") as file:
                        st.download_button(
                            label="📥 DESCARGAR EXCEL DE COTIZACIÓN",
                            data=file,
                            file_name=filename,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                except Exception as e:
                    st.error(f"Falla en el sistema: {e}")

# --- MÓDULO CLIENTES (PRÓXIMAMENTE) ---
elif opcion == "👥 Clientes":
    st.header("👥 Gestión de Clientes")
    st.info("Este módulo estará disponible en la Fase 4 para guardar tu base de datos de clientes.")

# --- MÓDULO HISTORIAL (PRÓXIMAMENTE) ---
elif opcion == "📊 Historial":
    st.header("📊 Historial de Cotizaciones")
    st.write("Aquí podrás ver todas las cotizaciones enviadas anteriormente.")
