import streamlit as st
import os
from datetime import datetime
import database as db

# --- CARGAR API KEY DESDE SECRETS ---
if "GEMINI_API_KEY" in st.secrets:
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
elif os.path.exists(".env"):
    from dotenv import load_dotenv
    load_dotenv()

# Importamos las herramientas del motor
from traductor_ia import analizar_reporte_tecnico, analizar_audio_tecnico 
from generador_excel import crear_excel_cotizacion

# Inicializar DB
db.inicializar_db()

# --- CONFIGURACIÓN DE PÁGINA ---
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
                    st.error("Credenciales incorrectas")
    else:
        st.success(f"Hola {st.session_state.usuario}")
        opciones = ["📦 Crear Cotización"]
        if st.session_state.rol == "admin":
            opciones += ["🛠️ Catálogo", "📊 Historial"]
        opcion = st.radio("Menú", opciones)
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
        reporte_texto = st.text_area("Reporte escrito", height=150, placeholder="Escriba aquí si no usa audio...")
        
        st.divider()
        audio_file = st.file_uploader("🎙️ Subir Nota de Voz", type=['mp3', 'wav', 'm4a'], key="audio_uploader")
        
        if audio_file:
            st.success(f"✅ ARCHIVO DETECTADO: {audio_file.name}")
            st.audio(audio_file)
        else:
            st.info("💡 Consejo: Asegúrate de ver el mensaje verde 'ARCHIVO DETECTADO' antes de procesar.")

    with col_config:
        st.subheader("2. Configuración")
        cliente = st.text_input("🏢 Empresa/Cliente", placeholder="Ej: Condominio El Roble")
        margen = st.slider("Margen de ganancia (%)", 10, 100, 30)
        
        st.write("---")
        btn_procesar = st.button("🚀 GENERAR COTIZACIÓN", use_container_width=True)
        
        # DEBUG VISUAL PARA EL USUARIO (Solo aparece si hay duda)
        if btn_procesar:
            if not audio_file and not reporte_texto.strip():
                st.error("❌ ERROR: No ingresaste texto ni subiste audio.")
                st.write("**Estado Interno:**")
                st.write(f"- Audio en memoria: {'SÍ' if audio_file else 'NO'}")
                st.write(f"- Texto escrito: {'SÍ' if reporte_texto.strip() else 'NO'}")

    # --- LÓGICA DE PROCESAMIENTO ---
    if btn_procesar and (audio_file or reporte_texto.strip()):
        if not cliente:
            st.warning("⚠️ Ingresa el nombre del cliente.")
        else:
            with st.spinner("⏳ KVANetworks IA Pro analizando..."):
                try:
                    # Determinamos qué procesar (Audio tiene prioridad)
                    if audio_file:
                        st.info(f"🎤 Analizando audio: {audio_file.name}")
                        temp_name = f"temp_{int(datetime.now().timestamp())}.mp3"
                        with open(temp_name, "wb") as f:
                            f.write(audio_file.getbuffer())
                        try:
                            datos = analizar_audio_tecnico(temp_name)
                        finally:
                            if os.path.exists(temp_name): os.remove(temp_name)
                    else:
                        st.info("📝 Analizando reporte de texto...")
                        datos = analizar_reporte_tecnico(reporte_texto)
                    
                    # Generación y DB
                    nombre_xlsx = f"cotizacion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                    ruta_xlsx = crear_excel_cotizacion(datos, nombre_xlsx)
                    db.guardar_cotizacion_en_bd(datos, ruta_xlsx)
                    
                    st.success("✅ ¡Cotización Creada!")
                    st.balloons()
                    with open(ruta_xlsx, "rb") as f:
                        st.download_button("📥 DESCARGAR EXCEL", f, file_name=nombre_xlsx)
                        
                except Exception as e:
                    st.error("❌ ERROR DE PROCESAMIENTO")
                    st.exception(e)
                    # Verificar si la API Key está presente en el error
                    if "401" in str(e) or "API_KEY" in str(e):
                        st.error("⚠️ Tu GEMINI_API_KEY parece no ser válida o no estar configurada.")