import sqlite3
import os
import sys

# Nombre del archivo de la base de datos
DB_FILENAME = "gesty_erp.db"

def obtener_ruta_db():
    """Determina la ruta segura para guardar la base de datos y evitar que se borre con el .exe"""
    if sys.platform == "win32":
        app_data = os.getenv('LOCALAPPDATA')
        carpeta_datos = os.path.join(app_data, "GestyERP")
    else:
        carpeta_datos = os.path.join(os.path.expanduser("~"), ".gesty_erp")

    if not os.path.exists(carpeta_datos):
        os.makedirs(carpeta_datos)
    
    return os.path.join(carpeta_datos, DB_FILENAME)

DB_NAME = obtener_ruta_db()

def inicializar_db():
    print(f"Inicializando Base de Datos Gesty ERP en:\n{DB_NAME}\n")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Activar el soporte para Claves Foráneas (Obligatorio para SQLite relacional)
    cursor.execute("PRAGMA foreign_keys = ON;")

    # ==========================================
    # 1. TABLAS PADRE (Catálogos Base)
    # ==========================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS monedas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE NOT NULL,    
        simbolo TEXT NOT NULL,          
        tasa_cambio REAL NOT NULL,      
        es_principal BOOLEAN DEFAULT 0  
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS departamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE NOT NULL,
        descripcion TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS almacenes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE NOT NULL,
        ubicacion TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS proveedores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        documento TEXT UNIQUE NOT NULL,
        nombre TEXT NOT NULL,
        telefono TEXT,
        direccion TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS listas_precios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE NOT NULL 
    );
    """)

    # ==========================================
    # 2. TABLAS DE SEGUNDO NIVEL (Dependen de las Padre)
    # ==========================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        documento TEXT UNIQUE NOT NULL,
        nombre TEXT NOT NULL,
        telefono TEXT,
        direccion TEXT,
        lista_precio_id INTEGER NOT NULL DEFAULT 1,
        FOREIGN KEY(lista_precio_id) REFERENCES listas_precios(id)
    );
    """)

    # La tabla maestra de productos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT UNIQUE NOT NULL,
        nombre TEXT NOT NULL,
        departamento_id INTEGER,
        cantidad_minima INTEGER NOT NULL DEFAULT 5,
        FOREIGN KEY(departamento_id) REFERENCES departamentos(id) ON DELETE SET NULL
    );
    """)

    # 🔥 NUEVA TABLA: Métodos de Pago asociados a su moneda correspondiente
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS metodos_pago (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        moneda_id INTEGER NOT NULL,
        FOREIGN KEY(moneda_id) REFERENCES monedas(id) ON DELETE CASCADE
    );
    """)

    # ==========================================
    # 3. TABLAS INTERMEDIAS (El cerebro del sistema)
    # ==========================================

    # Stock por Almacén
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventario_almacenes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        producto_id INTEGER NOT NULL,
        almacen_id INTEGER NOT NULL,
        cantidad INTEGER NOT NULL DEFAULT 0,
        UNIQUE(producto_id, almacen_id),
        FOREIGN KEY(producto_id) REFERENCES productos(id) ON DELETE CASCADE,
        FOREIGN KEY(almacen_id) REFERENCES almacenes(id) ON DELETE CASCADE
    );
    """)

    # Costos por Proveedor
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS productos_proveedores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        producto_id INTEGER NOT NULL,
        proveedor_id INTEGER NOT NULL,
        precio_costo REAL NOT NULL, 
        fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(producto_id, proveedor_id),
        FOREIGN KEY(producto_id) REFERENCES productos(id) ON DELETE CASCADE,
        FOREIGN KEY(proveedor_id) REFERENCES proveedores(id) ON DELETE CASCADE
    );
    """)

    # Precios de Venta por Lista
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS precios_producto (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        producto_id INTEGER NOT NULL,
        lista_precio_id INTEGER NOT NULL,
        precio_venta REAL NOT NULL, 
        UNIQUE(producto_id, lista_precio_id),
        FOREIGN KEY(producto_id) REFERENCES productos(id) ON DELETE CASCADE,
        FOREIGN KEY(lista_precio_id) REFERENCES listas_precios(id) ON DELETE CASCADE
    );
    """)

    # ==========================================
    # 4. TABLAS DE TRANSACCIONES (Ventas y Facturación)
    # ==========================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ventas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
        cliente_id INTEGER NOT NULL,
        moneda_id INTEGER NOT NULL,
        tasa_cambio_momento REAL NOT NULL,
        total_venta REAL NOT NULL,
        FOREIGN KEY(cliente_id) REFERENCES clientes(id),
        FOREIGN KEY(moneda_id) REFERENCES monedas(id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS detalles_venta (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        venta_id INTEGER NOT NULL,
        producto_id INTEGER NOT NULL,
        almacen_origen_id INTEGER NOT NULL,
        cantidad INTEGER NOT NULL,
        precio_unitario REAL NOT NULL,
        precio_costo_momento REAL NOT NULL,
        FOREIGN KEY(venta_id) REFERENCES ventas(id) ON DELETE CASCADE,
        FOREIGN KEY(producto_id) REFERENCES productos(id),
        FOREIGN KEY(almacen_origen_id) REFERENCES almacenes(id)
    );
    """)

    # 🔥 NUEVA TABLA: Registro exacto de cómo pagó el cliente (Soporta pagos mixtos)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pagos_venta (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        venta_id INTEGER NOT NULL,
        metodo_pago_id INTEGER NOT NULL,
        monto REAL NOT NULL,
        tasa_calculo REAL NOT NULL,
        FOREIGN KEY(venta_id) REFERENCES ventas(id) ON DELETE CASCADE,
        FOREIGN KEY(metodo_pago_id) REFERENCES metodos_pago(id)
    );
    """)

    # ==========================================
    # 5. POBLAR DATOS POR DEFECTO (Para evitar errores iniciales)
    # ==========================================
    
    # Monedas (Ejemplo adaptado a USD y Bs)
    cursor.execute("INSERT OR IGNORE INTO monedas (id, nombre, simbolo, tasa_cambio, es_principal) VALUES (1, 'Dólar', '$', 1.0, 1)")
    cursor.execute("INSERT OR IGNORE INTO monedas (id, nombre, simbolo, tasa_cambio, es_principal) VALUES (2, 'Bolívar', 'Bs', 40.0, 0)")
    
    # Listas de Precios
    cursor.execute("INSERT OR IGNORE INTO listas_precios (id, nombre) VALUES (1, 'Detal')")
    cursor.execute("INSERT OR IGNORE INTO listas_precios (id, nombre) VALUES (2, 'Mayorista')")
    
    # Categorías y Almacenes Básicos
    cursor.execute("INSERT OR IGNORE INTO departamentos (id, nombre, descripcion) VALUES (1, 'General', 'Categoría por defecto')")
    cursor.execute("INSERT OR IGNORE INTO almacenes (id, nombre, ubicacion) VALUES (1, 'Principal', 'Tienda')")
    
    # Cliente Genérico
    cursor.execute("INSERT OR IGNORE INTO clientes (id, documento, nombre, lista_precio_id) VALUES (1, '0000', 'Cliente Mostrador', 1)")

    # 🔥 MÉTODOS DE PAGO POR DEFECTO ASOCIADOS A SU MONEDA
    cursor.execute("INSERT OR IGNORE INTO metodos_pago (id, nombre, moneda_id) VALUES (1, 'Zelle', 1)")
    cursor.execute("INSERT OR IGNORE INTO metodos_pago (id, nombre, moneda_id) VALUES (2, 'Efectivo Divisas', 1)")
    cursor.execute("INSERT OR IGNORE INTO metodos_pago (id, nombre, moneda_id) VALUES (3, 'Pago Móvil', 2)")
    cursor.execute("INSERT OR IGNORE INTO metodos_pago (id, nombre, moneda_id) VALUES (4, 'Punto de Venta', 2)")
    cursor.execute("INSERT OR IGNORE INTO metodos_pago (id, nombre, moneda_id) VALUES (5, 'Efectivo Bs', 2)")

    conn.commit()
    conn.close()
    print("¡Base de Datos Gesty ERP creada/actualizada exitosamente y lista para usar!")

if __name__ == "__main__":
    inicializar_db()