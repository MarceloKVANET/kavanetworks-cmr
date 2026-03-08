import streamlit as st
import os
from datetime import datetime
import database as db

# --- SETUP INICIAL ---
if "GEMINI_API_KEY" in st.secrets:
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]

from traductor_ia import analizar_reporte_tecnico, analizar_audio_tecnico 
from generador_excel import crear_excel_cotizacion

db.inicializar_db()

st.set_page_config(page_title="KVANetworks CRM", page_icon="📶", layout="wide")

# --- LOGIN & SESIÓN ---
if 'logueado' not in st.session_state:
    st.session_state.logueado = False

with st.sidebar:
    st.title("KVANetworks")
    if not st.session_state.logueado:
        with st.form("login"):
            u = st.text_input("Usuario")
            p = st.text_input("Clave", type="password")
            if st.form_submit_button("Entrar"):
                if (u == "admin" and p == "kva2026") or (u == "tecnico" and p == "terreno2026"):
                    st.session_state.logueado = True
                    st.session_state.rol = "admin" if u == "admin" else "tecnico"
                    st.rerun()
    else:
        st.write(f"Conectado como {st.session_state.rol}")
        if st.button("Salir"):
            st.session_state.logueado = False
            st.rerun()

if not st.session_state.logueado:
    st.info("🔒 Inicie sesión")
    st.stop()

# --- MÓDULO COTIZACIÓN ---
st.title("📝 Generador de Cotizaciones Pro (Gemini 3.1)")

# PERSISTENCIA DE DATOS (Solución al error de 'borrado')
if 'audio_buffer' not in st.session_state:
    st.session_state.audio_buffer = None
if 'audio_name' not in st.session_state:
    st.session_state.audio_name = None

col1, col2 = st.columns([1.5, 1])

with col1:
    st.subheader("Entrada de Datos")
    texto_tecnico = st.text_area("Descripción del trabajo", height=150, key="texto_input")
    
    uploaded_file = st.file_uploader("🎙️ Subir Audio", type=['mp3', 'wav', 'm4a'])
    if uploaded_file:
        # Guardamos inmediatamente en la sesión para que no se pierda al pulsar el botón
        st.session_state.audio_buffer = uploaded_file.getvalue()
        st.session_state.audio_name = uploaded_file.name
        st.success(f"✅ Audio grabado en memoria: {uploaded_file.name}")
        st.audio(st.session_state.audio_buffer)

with col2:
    st.subheader("Parámetros")
    cliente = st.text_input("🏢 Empresa/Cliente", placeholder="Nombre del cliente")
    margen = st.slider("Margen de ganancia (%)", 10, 100, 30)
    
    st.write("---")
    if st.button("🚀 PROCESAR CON GEMINI 3.1 PRO", use_container_width=True, type="primary"):
        txt = texto_tecnico.strip()
        aud = st.session_state.audio_buffer
        
        if not cliente:
            st.warning("Escriba el nombre del cliente.")
        elif not txt and not aud:
            st.error("Error: No hay texto ni audio cargado.")
            # Diagnóstico visual
            st.write("---")
            st.write("**Estado de Memoria:**")
            st.write(f"Texto: {'SÍ' if txt else 'NO'}")
            st.write(f"Audio: {'SÍ' if aud else 'NO'}")
        else:
            with st.spinner("🧠 Gemini 3.1 Pro analizando el requerimiento..."):
                try:
                    if aud:
                        tmp = f"temp_{int(datetime.now().timestamp())}.mp3"
                        with open(tmp, "wb") as f: f.write(aud)
                        try:
                            datos = analizar_audio_tecnico(tmp)
                        finally:
                            if os.path.exists(tmp): os.remove(tmp)
                    else:
                        datos = analizar_reporte_tecnico(txt)
                    
                    # Generar y Guardar
                    file_name = f"cotiz_{datetime.now().strftime('%d%m_%H%M')}.xlsx"
                    path = crear_excel_cotizacion(datos, file_name, margen_override=(margen/100))
                    db.guardar_cotizacion_en_bd(datos, path)
                    
                    st.success("¡Éxito! Cotización generada con IA 3.1")
                    st.balloons()
                    with open(path, "rb") as f:
                        st.download_button("📥 DESCARGAR EXCEL", f, file_name=file_name)
                    
                    # Limpiar buffer tras éxito
                    st.session_state.audio_buffer = None
                    
                except Exception as e:
                    st.error("Error en el procesamiento de IA")
                    st.exception(e)