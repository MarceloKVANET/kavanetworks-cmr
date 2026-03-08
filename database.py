import sqlite3
import os
from datetime import datetime

DB_PATH = "kvanetworks_crm.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def inicializar_db():
    """Crea las tablas necesarias de forma segura."""
    # El uso de 'with' garantiza que la base de datos se cierre siempre, evitando bloqueos.
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Tabla de Usuarios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                rol TEXT CHECK(rol IN ('admin', 'tecnico')) NOT NULL
            )
        ''')
        
        # Tabla de Productos/Servicios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                descripcion TEXT,
                precio_neto REAL NOT NULL,
                unidad TEXT DEFAULT 'unidades'
            )
        ''')
        
        # Tabla de Clientes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_empresa TEXT UNIQUE NOT NULL,
                contacto TEXT,
                email TEXT
            )
        ''')
        
        # Tabla de Cotizaciones (Historial)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cotizaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER,
                fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                resumen TEXT,
                total_neto REAL,
                ruta_archivo TEXT,
                FOREIGN KEY (cliente_id) REFERENCES clientes(id)
            )
        ''')
        
        # Insertar usuario admin por defecto si no existe
        cursor.execute("SELECT * FROM usuarios WHERE username='admin'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO usuarios (username, password, rol) VALUES (?, ?, ?)", 
                           ('admin', 'kva2026', 'admin'))
        
        conn.commit()

# --- FUNCIONES DE PRODUCTOS ---

def listar_productos():
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM productos ORDER BY nombre ASC")
        return cursor.fetchall()

def agregar_producto(nombre, descripcion, precio, unidad):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO productos (nombre, descripcion, precio_neto, unidad) VALUES (?, ?, ?, ?)",
                       (nombre, descripcion, precio, unidad))
        conn.commit()

def eliminar_producto(id_producto):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM productos WHERE id = ?", (id_producto,))
        conn.commit()

# --- NUEVA FUNCIÓN: EL PUENTE CON LA IA ---

def guardar_cotizacion_en_bd(datos_estructurados, ruta_archivo=""):
    """
    Guarda el resumen del levantamiento técnico generado por la IA en el historial.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            resumen = datos_estructurados.resumen_proyecto
            
            # Guardamos el resumen de la IA. Más adelante conectaremos el cliente_id y el total_neto.
            cursor.execute('''
                INSERT INTO cotizaciones (resumen, ruta_archivo) 
                VALUES (?, ?)
            ''', (resumen, ruta_archivo))
            
            conn.commit()
            print(f"💾 Registro guardado en BD con ID: {cursor.lastrowid}")
            return cursor.lastrowid
    except Exception as e:
        print(f"❌ Error al guardar en base de datos: {str(e)}")
        return None

if __name__ == "__main__":
    inicializar_db()
    print("✅ Base de datos inicializada y asegurada correctamente.")