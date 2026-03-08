import streamlit as st
import os
from datetime import datetime
import database as db

# Importamos las herramientas del motor
from traductor_ia import analizar_reporte_tecnico
from traductor_ia_audio import analizar_audio_tecnico 
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

# --- ESTILOS PERSONALIZADOS (CSS AVANZADO) ---
st.markdown("""
    <style>
    /* Fondo general más suave */
    .stApp {
        background-color: #f0f4f8;
    }
    
    /* Estilo para los contenedores (Tarjetas) */
    div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    
    /* Botón principal KVANetworks */
    .stButton>button {
        background-color: #04447c;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #03335e;
        box-shadow: 0 4px 12px rgba(4, 68, 124, 0.3);
        transform: translateY(-2px);
    }
    
    /* Títulos corporativos */
    h1, h2, h3 {
        color: #04447c;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Ocultar elementos molestos por defecto de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- AUTENTICACIÓN Y BARRA LATERAL ---
if 'logueado' not in st.session_state:
    st.session_state.logueado = False
    st.session_state.usuario = None
    st.session_state.rol = None

with st.sidebar:
    st.image("https://img.icons8.com/ios-filled/100/04447c/infinity.png", width=80)
    st.title("KVANetworks")
    st.caption("Sistema de Gestión Integrado")
    st.divider()
    
    if not st.session_state.logueado:
        st.subheader("Acceso al Sistema")
        with st.form("login_form"):
            user = st.text_input("Usuario")
            pw = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Ingresar al CRM"):
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
        st.success(f"👋 Hola, **{st.session_state.usuario}**")
        st.caption(f"Nivel de acceso: {st.session_state.rol.upper()}")
        
        st.divider()
        opciones_menu = ["📦 Crear Cotización"]
        if st.session_state.rol == "admin":
            opciones_menu += ["🛠️ Catálogo de Precios", "👥 Clientes", "📊 Historial de Proyectos"]
        
        opcion = st.radio("Navegación", opciones_menu)
        
        st.divider()
        if st.button("🚪 Cerrar Sesión"):
            st.session_state.logueado = False
            st.rerun()

# --- VALIDACIÓN DE ACCESO ---
if not st.session_state.logueado:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.info("🔒 Bienvenido al portal de KVANetworks. Por favor, inicie sesión en el menú lateral izquierdo para acceder a sus herramientas.")
    st.stop()

# --- MÓDULO PRINCIPAL: CREAR COTIZACIÓN ---
if opcion == "📦 Crear Cotización":
    st.title("📝 Nuevo Levantamiento Técnico")
    st.markdown("Procesa audios de terreno o reportes escritos usando **Inteligencia Artificial**.")
    st.write("") # Espaciador
    
    col_input, col_config = st.columns([1.8, 1.2], gap="large")
    
    with col_input:
        with st.container(border=True):
            st.subheader("1. Ingreso de Datos")
            st.write("Escriba el reporte o suba la nota de voz del técnico:")
            
            reporte_texto = st.text_area(
                "Texto del requerimiento (Opcional si sube audio)", 
                placeholder="Ej: Necesitamos instalar 10 puntos de red cat6...",
                height=150,
                label_visibility="collapsed"
            )
            
            st.divider()
            
            audio_file = st.file_uploader("🎙️ Subir nota de voz (MP3, M4A, WAV)", type=['mp3', 'wav', 'm4a'])
            if audio_file:
                st.success(f"✅ Audio cargado correctamente ({audio_file.size/1024:.0f} KB)")
                st.audio(audio_file)

    with col_config:
        with st.container(border=True):
            st.subheader("2. Parámetros Comerciales")
            cliente_nombre = st.text_input("🏢 Cliente / Empresa", placeholder="Ej: Constructora San José")
            
            st.write("📈 Margen de Utilidad Sugerido")
            margen_manual = st.slider("Porcentaje de recargo sobre el costo neto", min_value=10, max_value=100, value=30, step=5, format="%d%%")
            
            st.write("") # Espaciador
            st.write("")
            btn_procesar = st.button("🚀 PROCESAR Y GENERAR COTIZACIÓN", use_container_width=True)
            
    # Lógica de procesamiento
    if btn_procesar:
        if not cliente_nombre:
            st.error("⚠️ Ingrese el nombre del Cliente para continuar.")
        elif not reporte_texto and not audio_file:
            st.error("⚠️ Debe ingresar un texto o subir un archivo de audio.")
        else:
            with st.spinner("🧠 KVANetworks IA analizando el requerimiento..."):
                try:
                    # IA
                    if audio_file:
                        # Guardar temporalmente para procesar
                        with open("temp_audio.mp3", "wb") as f:
                            f.write(audio_file.getbuffer())
                        datos_estructurados = analizar_audio_tecnico("temp_audio.mp3")
                        os.remove("temp_audio.mp3")
                    else:
                        datos_estructurados = analizar_reporte_tecnico(reporte_texto)
                    
                    # Generar Excel
                    nombre_salida = f"cotizacion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                    ruta_absoluta = crear_excel_cotizacion(datos_estructurados, nombre_salida)
                    
                    # Guardar en DB
                    id_cotizacion = db.guardar_cotizacion_en_bd(datos_estructurados, ruta_absoluta)
                    
                    st.success(f"✅ Cotización #{id_cotizacion} generada con éxito!")
                    st.balloons()
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        with open(ruta_absoluta, "rb") as file:
                            st.download_button(
                                label="📥 Descargar Excel",
                                data=file,
                                file_name=nombre_salida,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                    with col2:
                        st.info(f"📍 Archivo guardado en: {ruta_absoluta}")

                except Exception as e:
                    st.error(f"❌ Error en el procesamiento: {str(e)}")