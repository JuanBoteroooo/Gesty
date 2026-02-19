# database_setup.py
import sqlite3
import os

DB_NAME = "ferreteria_inventario.db"

def inicializar_db():
    """Crea las tablas si no existen."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Habilitar Foreign Keys (Claves foráneas)
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. Tabla PRODUCTOS (Solo cantidades e info básica)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT UNIQUE NOT NULL,      -- Código manual (ej: TORN-001)
        nombre TEXT NOT NULL,
        cantidad_actual INTEGER NOT NULL DEFAULT 0,
        cantidad_minima INTEGER NOT NULL DEFAULT 5 -- Para la alerta
    );
    """)

    # 2. Tabla DESPACHOS (Encabezado del Ticket)
    # Aquí guardamos los datos del cliente "al vuelo"
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS despachos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
        cliente_nombre TEXT,
        cliente_telefono TEXT,
        cliente_direccion TEXT
    );
    """)

    # 3. Tabla DETALLES (Qué se llevó en cada despacho)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS detalles_despacho (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        despacho_id INTEGER NOT NULL,
        producto_id INTEGER NOT NULL,
        cantidad INTEGER NOT NULL,
        FOREIGN KEY(despacho_id) REFERENCES despachos(id) ON DELETE CASCADE,
        FOREIGN KEY(producto_id) REFERENCES productos(id)
    );
    """)

    conn.commit()
    conn.close()
    print(f"Base de datos '{DB_NAME}' inicializada correctamente.")

if __name__ == "__main__":
    inicializar_db()