import streamlit as st
import os
from datetime import datetime
import database as db

# --- CARGAR API KEY DESDE SECRETS ---
# Hacemos esto antes de importar traductor_ia para que ya esté disponible
if "GEMINI_API_KEY" in st.secrets:
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
elif os.path.exists(".env"):
    from dotenv import load_dotenv
    load_dotenv()

# Importamos las herramientas del motor
from traductor_ia import analizar_reporte_tecnico, analizar_audio_tecnico 
from generador_excel import crear_excel_cotizacion

# Inicializar DB al arrancar
db.inicializar_db()

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="KVANetworks CRM",
    page_icon="📶",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILOS PERSONALIZADOS ---
st.markdown("""
    <style>
    .stApp { background-color: #f0f4f8; }
    div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    .stButton>button {
        background-color: #04447c;
        color: white;
        border-radius: 8px;
        font-weight: 600;
        width: 100%;
    }
    h1, h2, h3 { color: #04447c; }
    </style>
""", unsafe_allow_html=True)

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
            opciones_menu += ["🛠️ Catálogo de Precios", "📊 Historial"]
        opcion = st.radio("Navegación", opciones_menu)
        if st.button("Cerrar Sesión"):
            st.session_state.logueado = False
            st.rerun()

if not st.session_state.logueado:
    st.info("🔒 Inicie sesión para continuar")
    st.stop()

# --- MÓDULO: CREAR COTIZACIÓN ---
if opcion == "📦 Crear Cotización":
    st.title("📝 Nuevo Levantamiento")
    
    col_input, col_config = st.columns([1.5, 1], gap="large")
    
    with col_input:
        with st.container(border=True):
            st.subheader("1. Ingrese Datos")
            reporte_texto = st.text_area("Texto del reporte (opcional)", height=150)
            
            st.divider()
            # Usar una key para el uploader ayuda a la persistencia en Streamlit
            audio_file = st.file_uploader("🎙️ Subir Audio", type=['mp3', 'wav', 'm4a'], key="audio_uploader")
            
            if audio_file:
                st.success(f"✅ Archivo '{audio_file.name}' detectado y listo.")
                st.audio(audio_file)

    with col_config:
        with st.container(border=True):
            st.subheader("2. Configuración")
            cliente_nombre = st.text_input("🏢 Cliente", placeholder="Nombre del cliente")
            margen = st.slider("Margen (%)", 10, 100, 30)
            
            btn_procesar = st.button("🚀 GENERAR COTIZACIÓN", use_container_width=True)

    # --- LÓGICA DE PROCESAMIENTO ---
    if btn_procesar:
        # Debug visual para el usuario si algo falla
        if not cliente_nombre:
            st.warning("⚠️ Falta el nombre del cliente.")
        elif not reporte_texto.strip() and audio_file is None:
            st.error("❌ El sistema no detecta ni texto ni audio. Por favor sube el archivo de nuevo.")
            # Debug oculto
            st.write(f"DEBUG: Texto length={len(reporte_texto)}, Audio={audio_file}")
        else:
            with st.spinner("⏳ Procesando con IA Pro..."):
                try:
                    if audio_file is not None:
                        st.info("🎙️ Procesando Nota de Voz...")
                        # Guardar temporalmente
                        temp_path = f"temp_{datetime.now().timestamp()}.mp3"
                        with open(temp_path, "wb") as f:
                            f.write(audio_file.getbuffer())
                        
                        try:
                            datos = analizar_audio_tecnico(temp_path)
                        finally:
                            if os.path.exists(temp_path):
                                os.remove(temp_path)
                    else:
                        st.info("📝 Procesando Texto...")
                        datos = analizar_reporte_tecnico(reporte_texto)
                    
                    # Generar Excel
                    nombre_salida = f"cotizacion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                    ruta = crear_excel_cotizacion(datos, nombre_salida)
                    db.guardar_cotizacion_en_bd(datos, ruta)
                    
                    st.success("✅ ¡Cotización Generada!")
                    st.balloons()
                    with open(ruta, "rb") as f:
                        st.download_button("📥 Descargar Excel", f, file_name=nombre_salida)
                        
                except Exception as e:
                    st.error("❌ ERROR CRÍTICO")
                    st.warning("Detalle para soporte:")
                    st.exception(e)
                    # Verificar API Key en vivo
                    api_check = os.environ.get("GEMINI_API_KEY")
                    if not api_check:
                        st.error("Error de Configuración: La API Key no está cargada en el servidor.")
                    else:
                        st.write(f"Info Técnica: API Key detectada ({api_check[:4]}...)")