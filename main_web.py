import streamlit as st
import os
from traductor_ia import analizar_reporte_tecnico, analizar_audio_tecnico
from generador_excel import crear_excel_cotizacion
from datetime import datetime
import database as db

# Inicializar DB al arrancar
db.inicializar_db()

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

# --- AUTENTICACIÓN ---
if 'logueado' not in st.session_state:
    st.session_state.logueado = False
    st.session_state.usuario = None
    st.session_state.rol = None

with st.sidebar:
    st.image("https://img.icons8.com/ios-filled/100/04447c/infinity.png", width=100)
    st.title("Acceso KVANetworks")
    
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
        st.write(f"Hola, **{st.session_state.usuario}**")
        st.write(f"Rol: `{st.session_state.rol.upper()}`")
        if st.button("Cerrar Sesión"):
            st.session_state.logueado = False
            st.rerun()
        
        st.divider()
        st.title("Panel de Control")
        opciones_menu = ["📦 Crear Cotización"]
        if st.session_state.rol == "admin":
            opciones_menu += ["🛠️ Inventario & Precios", "👥 Clientes", "📊 Historial"]
        
        opcion = st.radio("Menu", opciones_menu)

# --- MÓDULO PRINCIPAL: CREAR COTIZACIÓN ---
# --- MÓDULO PRINCIPAL: CREAR COTIZACIÓN ---
if not st.session_state.logueado:
    st.warning("🔒 Por favor, inicie sesión en la barra lateral para usar el sistema.")
    st.stop()

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
        if not cliente_nombre:
            st.error("⚠️ El nombre del Cliente/Empresa es OBLIGATORIO para generar la cotización.")
        elif not reporte_texto and not audio_file:
            st.error("⚠️ Por favor, ingrese un reporte de texto o suba un archivo de audio.")
        else:
            with st.spinner("🧠 KVANetworks IA trabajando..."):
                try:
                    # 0. Preparar catálogo de precios para la IA
                    productos = db.listar_productos()
                    contexto_precios = "\n".join([f"- {p['nombre']}: ${p['precio_neto']} por {p['unidad']}" for p in productos])
                    
                    # 1. Ejecutar IA (Texto o Audio)
                    if audio_file:
                        # Guardar temporalmente para que Gemini pueda leerlo
                        temp_path = f"temp_{audio_file.name}"
                        with open(temp_path, "wb") as f:
                            f.write(audio_file.getbuffer())
                        datos = analizar_audio_tecnico(temp_path, lista_precios_actual=contexto_precios)
                        os.remove(temp_path) # Limpiar
                    else:
                        datos = analizar_reporte_tecnico(reporte_texto, lista_precios_actual=contexto_precios)
                    
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
                    
                    # 2. Generar Excel (Usando el margen manual del slider)
                    filename = f"cotizacion_{cliente_nombre.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.xlsx"
                    ruta = crear_excel_cotizacion(datos, filename, margen_override=margen_manual/100)
                    
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

# --- MÓDULO INVENTARIO & PRECIOS ---
elif opcion == "🛠️ Inventario & Precios":
    st.header("🛠️ Gestión de Inventario y Precios Base")
    
    with st.expander("➕ Agregar Nuevo Producto/Servicio"):
        with st.form("nuevo_producto"):
            col1, col2 = st.columns(2)
            with col1:
                p_nombre = st.text_input("Nombre del Producto", placeholder="Ej: Cámara IP Domo 4MP")
                p_unidad = st.selectbox("Unidad", ["unidades", "mt", "puntos", "global", "día/técnico"])
            with col2:
                p_precio = st.number_input("Precio Neto ($)", min_value=0.0, step=100.0)
                p_desc = st.text_input("Descripción Corta")
            
            if st.form_submit_button("Guardar en Catálogo"):
                if p_nombre:
                    db.agregar_producto(p_nombre, p_desc, p_precio, p_unidad)
                    st.success(f"¡{p_nombre} agregado correctamente!")
                    st.rerun()
                else:
                    st.error("El nombre es obligatorio")

    st.write("### Catálogo de Precios Actual")
    productos = db.listar_productos()
    if productos:
        tabla_prod = []
        for p in productos:
            tabla_prod.append({
                "ID": p["id"],
                "Nombre": p["nombre"],
                "Descripción": p["descripcion"],
                "Precio Neto": f"${p['precio_neto']:,.0f}",
                "Unidad": p["unidad"]
            })
        st.table(tabla_prod)
    else:
        st.info("Aún no hay productos cargados. Usa el formulario de arriba para empezar.")

# --- MÓDULO CLIENTES (PRÓXIMAMENTE) ---
elif opcion == "👥 Clientes":
    st.header("👥 Gestión de Clientes")
    st.info("Este módulo estará disponible en la Fase 4 para guardar tu base de datos de clientes.")

# --- MÓDULO HISTORIAL (PRÓXIMAMENTE) ---
elif opcion == "📊 Historial":
    st.header("📊 Historial de Cotizaciones")
    st.write("Aquí podrás ver todas las cotizaciones enviadas anteriormente.")
