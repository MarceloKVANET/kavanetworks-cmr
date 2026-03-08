import streamlit as st
import os
from datetime import datetime
import database as db

# --- CARGAR API KEY ---
if "GEMINI_API_KEY" in st.secrets:
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
elif os.path.exists(".env"):
    from dotenv import load_dotenv
    load_dotenv()

from traductor_ia import analizar_reporte_tecnico, analizar_audio_tecnico 
from generador_excel import crear_excel_cotizacion

db.inicializar_db()

st.set_page_config(page_title="KVANetworks CRM", page_icon="📶", layout="wide")

# --- ESTADO DE SESIÓN ---
if 'logueado' not in st.session_state:
    st.session_state.logueado = False
    st.session_state.usuario = None
    st.session_state.rol = None

# --- BARRA LATERAL ---
with st.sidebar:
    st.title("KVANetworks")
    if not st.session_state.logueado:
        with st.form("login_form"):
            user = st.text_input("Usuario")
            pw = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Ingresar"):
                if user == "admin" and pw == "kva2026":
                    st.session_state.logueado = True
                    st.session_state.usuario = "Marcelo"
                    st.session_state.rol = "admin"
                    st.rerun()
                elif user == "tecnico" and pw == "terreno2026":
                    st.session_state.logueado = True
                    st.session_state.usuario = "Técnico"
                    st.session_state.rol = "tecnico"
                    st.rerun()
                else:
                    st.error("Error")
    else:
        st.success(f"Hola {st.session_state.usuario}")
        opciones_menu = ["📦 Crear Cotización"]
        if st.session_state.rol == "admin":
            opciones_menu += ["🛠️ Catálogo", "📊 Historial"]
        opcion = st.radio("Menú", opciones_menu)
        if st.button("Cerrar Sesión"):
            st.session_state.logueado = False
            st.rerun()

if not st.session_state.logueado:
    st.info("🔒 Por favor, inicie sesión.")
    st.stop()

# --- MÓDULO: CREAR COTIZACIÓN ---
if opcion == "📦 Crear Cotización":
    st.title("📝 Nuevo Levantamiento")
    
    col_input, col_config = st.columns([1.5, 1], gap="large")
    
    with col_input:
        st.subheader("1. Ingrese Datos")
        # Widget de texto
        reporte_texto = st.text_area("Reporte escrito", height=150, placeholder="Escriba aquí...", key="txt_input")
        
        st.divider()
        # Uploader
        audio_file = st.file_uploader("🎙️ Subir Nota de Voz", type=['mp3', 'wav', 'm4a'], key="file_input")
        
        # PERSISTENCIA MANUAL: Guardamos en session_state si el archivo existe
        if audio_file is not None:
            st.session_state['last_audio'] = audio_file
            st.session_state['last_audio_bytes'] = audio_file.getvalue()
            st.success(f"✅ ARCHIVO LISTO: {audio_file.name}")
            st.audio(st.session_state['last_audio_bytes'])
        elif 'last_audio' in st.session_state:
            # Si desaparece en el rerun del botón, lo recordamos
            st.info(f"🔄 Usando audio en memoria: {st.session_state['last_audio'].name}")

    with col_config:
        st.subheader("2. Configuración")
        cliente_nombre = st.text_input("🏢 Empresa/Cliente", key="cli_input")
        margen = st.slider("Margen (%)", 10, 100, 30)
        
        st.write("---")
        btn_procesar = st.button("🚀 GENERAR COTIZACIÓN", use_container_width=True)

    # --- LÓGICA DE PROCESAMIENTO ---
    if btn_procesar:
        # Recuperar datos de session_state si el widget falló
        final_audio_bytes = st.session_state.get('last_audio_bytes')
        final_text = reporte_texto.strip()
        
        if not cliente_nombre:
            st.warning("⚠️ Ingresa el nombre del cliente.")
        elif not final_text and final_audio_bytes is None:
            st.error("❌ ERROR: El sistema no detectó ni texto ni audio.")
            st.write("---")
            st.write("**Reporte de Estado:**")
            st.write(f"- Texto: {len(final_text)} caracteres.")
            st.write(f"- Audio: {'Cargado' if final_audio_bytes else 'Vacío'}")
        else:
            with st.spinner("⏳ KVANetworks IA Pro analizando..."):
                try:
                    if final_audio_bytes:
                        st.info("🎤 Procesando Nota de Voz...")
                        temp_path = f"temp_{int(datetime.now().timestamp())}.mp3"
                        with open(temp_path, "wb") as f:
                            f.write(final_audio_bytes)
                        try:
                            datos = analizar_audio_tecnico(temp_path)
                        finally:
                            if os.path.exists(temp_path): os.remove(temp_path)
                    else:
                        st.info("📝 Procesando Reporte de Texto...")
                        datos = analizar_reporte_tecnico(final_text)
                    
                    nombre_xlsx = f"cotizacion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                    ruta = crear_excel_cotizacion(datos, nombre_xlsx)
                    db.guardar_cotizacion_en_bd(datos, ruta)
                    
                    st.success("✅ ¡Cotización Generada!")
                    st.balloons()
                    with open(ruta, "rb") as f:
                        st.download_button("📥 DESCARGAR EXCEL", f, file_name=nombre_xlsx)
                        
                except Exception as e:
                    st.error("❌ ERROR CRÍTICO")
                    st.exception(e)