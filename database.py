import sqlite3
import os
from datetime import datetime

DB_PATH = "kvanetworks_crm.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def inicializar_db():
    """Crea las tablas necesarias si no existen."""
    conn = get_connection()
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
    
    # Insertar usuario admin por defecto si no existe (pass simple para MVP)
    cursor.execute("SELECT * FROM usuarios WHERE username='admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO usuarios (username, password, rol) VALUES (?, ?, ?)", 
                       ('admin', 'kva2026', 'admin'))
    
    conn.commit()
    conn.close()

# --- FUNCIONES DE PRODUCTOS ---

def listar_productos():
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM productos ORDER BY nombre ASC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def agregar_producto(nombre, descripcion, precio, unidad):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO productos (nombre, descripcion, precio_neto, unidad) VALUES (?, ?, ?, ?)",
                   (nombre, descripcion, precio, unidad))
    conn.commit()
    conn.close()

def eliminar_producto(id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM productos WHERE id = ?", (id,))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    inicializar_db()
    print("Base de datos inicializada correctamente.")
