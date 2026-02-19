import sqlite3
import os
import sys

DB_FILENAME = "gesty_erp.db"

def get_db_path():
    if sys.platform == "win32":
        app_data = os.getenv('LOCALAPPDATA')
        data_folder = os.path.join(app_data, "GestyERP")
    else:
        data_folder = os.path.join(os.path.expanduser("~"), ".gesty_erp")

    if not os.path.exists(data_folder):
        os.makedirs(data_folder)
    
    return os.path.join(data_folder, DB_FILENAME)

def connect():
    """Devuelve la conexión a la BD con Foreign Keys y acceso por nombre de columna."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row # Permite hacer: fila['nombre'] en lugar de fila[1]
    
    # Habilitar claves foráneas
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    return conn