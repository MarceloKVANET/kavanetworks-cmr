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
    
    # 1. Widgets principales FUERA de columnas para máxima compatibilidad
    st.subheader("1. Ingrese Datos")
    
    # Reporte de texto
    reporte_texto = st.text_area("Reporte escrito", height=150, placeholder="Escriba aquí...", key="txt_input")
    
    st.divider()
    
    # Uploader
    audio_file = st.file_uploader("🎙️ Subir Nota de Voz", type=['mp3', 'wav', 'm4a'], key="file_input")
    
    # Lógica de persistencia de audio inmediata
    if audio_file is not None:
        st.session_state['audio_data'] = audio_file.getvalue()
        st.session_state['audio_name'] = audio_file.name
        st.success(f"✅ ARCHIVO LISTO PARA PROCESAR: {audio_file.name}")
        st.audio(st.session_state['audio_data'])

    st.divider()
    
    st.subheader("2. Configuración")
    col1, col2 = st.columns(2)
    with col1:
        cliente_nombre = st.text_input("🏢 Empresa/Cliente", key="cli_input")
    with col2:
        margen = st.slider("Margen (%)", 10, 100, 30)
    
    st.write("---")
    btn_procesar = st.button("🚀 GENERAR COTIZACIÓN", type="primary", use_container_width=True)

    # --- LÓGICA DE PROCESAMIENTO ---
    if btn_procesar:
        # Recuperamos datos
        final_text = reporte_texto.strip() if reporte_texto else ""
        final_audio = st.session_state.get('audio_data')
        
        # DEBUG PARA EL USUARIO
        st.write("---")
        st.write("**🔍 Debug de Entrada:**")
        st.write(f"- Texto escrito: {'SÍ' if final_text else 'NO'}")
        st.write(f"- Audio en sesión: {'SÍ' if final_audio else 'NO'}")
        
        if not cliente_nombre:
            st.warning("⚠️ Ingresa el nombre del cliente.")
        elif not final_text and final_audio is None:
            st.error("❌ ERROR: El sistema no detectó datos de entrada.")
        else:
            with st.spinner("⏳ KVANetworks IA Pro analizando..."):
                try:
                    if final_audio:
                        st.info(f"🎤 Procesando Audio: {st.session_state.get('audio_name')}")
                        temp_path = f"temp_{int(datetime.now().timestamp())}.mp3"
                        with open(temp_path, "wb") as f:
                            f.write(final_audio)
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
                    st.error("❌ ERROR DE PROCESAMIENTO")
                    st.exception(e)