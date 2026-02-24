import sqlite3
import os
import sys

DB_FILENAME = "gesty_erp.db"

def obtener_ruta_db():
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
    print(f"Inicializando Base de Datos MAESTRA Gesty ERP en:\n{DB_NAME}\n")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    # ==========================================
    # 1. TABLAS PADRE Y CATÁLOGOS
    # ==========================================
    cursor.execute("CREATE TABLE IF NOT EXISTS roles (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT UNIQUE NOT NULL);")
    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL, usuario TEXT UNIQUE NOT NULL, password TEXT NOT NULL, rol_id INTEGER NOT NULL, estado BOOLEAN DEFAULT 1, FOREIGN KEY(rol_id) REFERENCES roles(id));")
    
    cursor.execute("CREATE TABLE IF NOT EXISTS monedas (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT UNIQUE NOT NULL, simbolo TEXT NOT NULL, tasa_cambio REAL NOT NULL, es_principal BOOLEAN DEFAULT 0);")
    cursor.execute("CREATE TABLE IF NOT EXISTS departamentos (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT UNIQUE NOT NULL, descripcion TEXT);")
    cursor.execute("CREATE TABLE IF NOT EXISTS almacenes (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT UNIQUE NOT NULL, ubicacion TEXT);")
    cursor.execute("CREATE TABLE IF NOT EXISTS proveedores (id INTEGER PRIMARY KEY AUTOINCREMENT, documento TEXT UNIQUE NOT NULL, nombre TEXT NOT NULL, telefono TEXT, direccion TEXT);")
    cursor.execute("CREATE TABLE IF NOT EXISTS listas_precios (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT UNIQUE NOT NULL);")

    # ==========================================
    # 2. PRODUCTOS, CLIENTES Y MÉTODOS
    # ==========================================
    cursor.execute("CREATE TABLE IF NOT EXISTS clientes (id INTEGER PRIMARY KEY AUTOINCREMENT, documento TEXT UNIQUE NOT NULL, nombre TEXT NOT NULL, telefono TEXT, direccion TEXT, lista_precio_id INTEGER NOT NULL DEFAULT 1, FOREIGN KEY(lista_precio_id) REFERENCES listas_precios(id));")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT UNIQUE,
        nombre TEXT NOT NULL,
        departamento_id INTEGER,
        proveedor_id INTEGER,
        stock_minimo REAL DEFAULT 5.0,  -- 🔥 ESTA ES LA LÍNEA NUEVA
        FOREIGN KEY(departamento_id) REFERENCES departamentos(id),
        FOREIGN KEY(proveedor_id) REFERENCES proveedores(id)
    )
    ''')
    cursor.execute("CREATE TABLE IF NOT EXISTS metodos_pago (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL, moneda_id INTEGER NOT NULL, FOREIGN KEY(moneda_id) REFERENCES monedas(id) ON DELETE CASCADE);")

    # ==========================================
    # 3. INTERMEDIAS (INVENTARIO Y PRECIOS)
    # ==========================================
    cursor.execute("CREATE TABLE IF NOT EXISTS inventario_almacenes (id INTEGER PRIMARY KEY AUTOINCREMENT, producto_id INTEGER NOT NULL, almacen_id INTEGER NOT NULL, cantidad INTEGER NOT NULL DEFAULT 0, UNIQUE(producto_id, almacen_id), FOREIGN KEY(producto_id) REFERENCES productos(id) ON DELETE CASCADE, FOREIGN KEY(almacen_id) REFERENCES almacenes(id) ON DELETE CASCADE);")
    cursor.execute("CREATE TABLE IF NOT EXISTS productos_proveedores (id INTEGER PRIMARY KEY AUTOINCREMENT, producto_id INTEGER NOT NULL, proveedor_id INTEGER NOT NULL, precio_costo REAL NOT NULL, fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP, UNIQUE(producto_id, proveedor_id), FOREIGN KEY(producto_id) REFERENCES productos(id) ON DELETE CASCADE, FOREIGN KEY(proveedor_id) REFERENCES proveedores(id) ON DELETE CASCADE);")
    cursor.execute("CREATE TABLE IF NOT EXISTS precios_producto (id INTEGER PRIMARY KEY AUTOINCREMENT, producto_id INTEGER NOT NULL, lista_precio_id INTEGER NOT NULL, precio_venta REAL NOT NULL, UNIQUE(producto_id, lista_precio_id), FOREIGN KEY(producto_id) REFERENCES productos(id) ON DELETE CASCADE, FOREIGN KEY(lista_precio_id) REFERENCES listas_precios(id) ON DELETE CASCADE);")

    # 🔥 NUEVO: KARDEX (HISTORIAL DE MOVIMIENTOS Y TRASPASOS)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS movimientos_inventario (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
        producto_id INTEGER NOT NULL,
        almacen_origen_id INTEGER,
        almacen_destino_id INTEGER,
        tipo_movimiento TEXT NOT NULL, -- 'ENTRADA', 'SALIDA', 'TRASPASO', 'AJUSTE'
        cantidad REAL NOT NULL,
        motivo TEXT,
        usuario_id INTEGER,
        FOREIGN KEY(producto_id) REFERENCES productos(id),
        FOREIGN KEY(almacen_origen_id) REFERENCES almacenes(id),
        FOREIGN KEY(almacen_destino_id) REFERENCES almacenes(id),
        FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
    );
    """)

    # ==========================================
    # 4. CAJA Y FINANZAS
    # ==========================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sesiones_caja (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha_apertura DATETIME DEFAULT CURRENT_TIMESTAMP,
        fecha_cierre DATETIME,
        monto_inicial REAL NOT NULL DEFAULT 0,
        estado TEXT DEFAULT 'ABIERTA',
        usuario_id INTEGER,
        FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
    );
    """)

    # 🔥 NUEVO: GASTOS DE CAJA CHICA
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS gastos_caja (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sesion_caja_id INTEGER NOT NULL,
        descripcion TEXT NOT NULL,
        monto REAL NOT NULL,
        moneda_id INTEGER NOT NULL,
        fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(sesion_caja_id) REFERENCES sesiones_caja(id),
        FOREIGN KEY(moneda_id) REFERENCES monedas(id)
    );
    """)

    # ==========================================
    # 5. VENTAS, COMPRAS Y PRESUPUESTOS
    # ==========================================
    cursor.execute("CREATE TABLE IF NOT EXISTS ventas (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha_hora DATETIME DEFAULT CURRENT_TIMESTAMP, cliente_id INTEGER NOT NULL, moneda_id INTEGER NOT NULL, tasa_cambio_momento REAL NOT NULL, total_venta REAL NOT NULL, sesion_caja_id INTEGER NOT NULL, FOREIGN KEY(cliente_id) REFERENCES clientes(id), FOREIGN KEY(moneda_id) REFERENCES monedas(id), FOREIGN KEY(sesion_caja_id) REFERENCES sesiones_caja(id));")
    cursor.execute("CREATE TABLE IF NOT EXISTS detalles_venta (id INTEGER PRIMARY KEY AUTOINCREMENT, venta_id INTEGER NOT NULL, producto_id INTEGER NOT NULL, almacen_origen_id INTEGER NOT NULL, cantidad INTEGER NOT NULL, precio_unitario REAL NOT NULL, precio_costo_momento REAL NOT NULL, FOREIGN KEY(venta_id) REFERENCES ventas(id) ON DELETE CASCADE, FOREIGN KEY(producto_id) REFERENCES productos(id), FOREIGN KEY(almacen_origen_id) REFERENCES almacenes(id));")
    cursor.execute("CREATE TABLE IF NOT EXISTS pagos_venta (id INTEGER PRIMARY KEY AUTOINCREMENT, venta_id INTEGER NOT NULL, metodo_pago_id INTEGER NOT NULL, monto REAL NOT NULL, tasa_calculo REAL NOT NULL, FOREIGN KEY(venta_id) REFERENCES ventas(id) ON DELETE CASCADE, FOREIGN KEY(metodo_pago_id) REFERENCES metodos_pago(id));")

    # 🔥 NUEVO: COMPRAS A PROVEEDORES
    cursor.execute("CREATE TABLE IF NOT EXISTS compras (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha_hora DATETIME DEFAULT CURRENT_TIMESTAMP, proveedor_id INTEGER NOT NULL, nro_factura_prov TEXT, total_compra REAL, FOREIGN KEY(proveedor_id) REFERENCES proveedores(id));")
    cursor.execute("CREATE TABLE IF NOT EXISTS detalles_compra (id INTEGER PRIMARY KEY AUTOINCREMENT, compra_id INTEGER NOT NULL, producto_id INTEGER NOT NULL, almacen_destino_id INTEGER NOT NULL, cantidad INTEGER NOT NULL, costo_unitario REAL NOT NULL, FOREIGN KEY(compra_id) REFERENCES compras(id) ON DELETE CASCADE, FOREIGN KEY(producto_id) REFERENCES productos(id), FOREIGN KEY(almacen_destino_id) REFERENCES almacenes(id));")

    # 🔥 NUEVO: PRESUPUESTOS (COTIZACIONES)
    cursor.execute("CREATE TABLE IF NOT EXISTS presupuestos (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha_hora DATETIME DEFAULT CURRENT_TIMESTAMP, fecha_vencimiento DATETIME, cliente_id INTEGER NOT NULL, moneda_id INTEGER NOT NULL, total_presupuesto REAL NOT NULL, estado TEXT DEFAULT 'ACTIVO', FOREIGN KEY(cliente_id) REFERENCES clientes(id), FOREIGN KEY(moneda_id) REFERENCES monedas(id));")
    cursor.execute("CREATE TABLE IF NOT EXISTS detalles_presupuesto (id INTEGER PRIMARY KEY AUTOINCREMENT, presupuesto_id INTEGER NOT NULL, producto_id INTEGER NOT NULL, cantidad INTEGER NOT NULL, precio_unitario REAL NOT NULL, FOREIGN KEY(presupuesto_id) REFERENCES presupuestos(id) ON DELETE CASCADE, FOREIGN KEY(producto_id) REFERENCES productos(id));")

    # 🔥 NUEVO: CUENTAS POR COBRAR (CRÉDITOS)
    cursor.execute("CREATE TABLE IF NOT EXISTS cuentas_por_cobrar (id INTEGER PRIMARY KEY AUTOINCREMENT, venta_id INTEGER UNIQUE NOT NULL, cliente_id INTEGER NOT NULL, monto_total REAL NOT NULL, saldo_pendiente REAL NOT NULL, estado TEXT DEFAULT 'PENDIENTE', fecha_vencimiento DATETIME, FOREIGN KEY(venta_id) REFERENCES ventas(id) ON DELETE CASCADE, FOREIGN KEY(cliente_id) REFERENCES clientes(id));")
    cursor.execute("CREATE TABLE IF NOT EXISTS abonos_cxc (id INTEGER PRIMARY KEY AUTOINCREMENT, cxc_id INTEGER NOT NULL, fecha DATETIME DEFAULT CURRENT_TIMESTAMP, monto REAL NOT NULL, metodo_pago_id INTEGER NOT NULL, sesion_caja_id INTEGER NOT NULL, FOREIGN KEY(cxc_id) REFERENCES cuentas_por_cobrar(id) ON DELETE CASCADE, FOREIGN KEY(metodo_pago_id) REFERENCES metodos_pago(id), FOREIGN KEY(sesion_caja_id) REFERENCES sesiones_caja(id));")

    # ==========================================
    # 6. POBLAR DATOS BÁSICOS
    # ==========================================
    cursor.execute("INSERT OR IGNORE INTO roles (id, nombre) VALUES (1, 'Administrador'), (2, 'Gerente'), (3, 'Cajero')")
    cursor.execute("INSERT OR IGNORE INTO usuarios (id, nombre, usuario, password, rol_id) VALUES (1, 'Admin Gesty', 'admin', 'admin123', 1)")
    
    cursor.execute("INSERT OR IGNORE INTO monedas (id, nombre, simbolo, tasa_cambio, es_principal) VALUES (1, 'Dólar', '$', 1.0, 1)")
    cursor.execute("INSERT OR IGNORE INTO monedas (id, nombre, simbolo, tasa_cambio, es_principal) VALUES (2, 'Bolívar', 'Bs', 40.0, 0)")
    
    cursor.execute("INSERT OR IGNORE INTO listas_precios (id, nombre) VALUES (1, 'Detal'), (2, 'Mayorista')")
    cursor.execute("INSERT OR IGNORE INTO departamentos (id, nombre, descripcion) VALUES (1, 'General', 'Categoría por defecto')")
    cursor.execute("INSERT OR IGNORE INTO almacenes (id, nombre, ubicacion) VALUES (1, 'Principal', 'Tienda')")
    cursor.execute("INSERT OR IGNORE INTO clientes (id, documento, nombre, lista_precio_id) VALUES (1, '0000', 'Cliente Mostrador', 1)")

    cursor.execute("INSERT OR IGNORE INTO metodos_pago (id, nombre, moneda_id) VALUES (1, 'Zelle', 1), (2, 'Efectivo Divisas', 1), (3, 'Pago Móvil', 2), (4, 'Punto de Venta', 2), (5, 'Efectivo Bs', 2)")

    conn.commit()
    conn.close()
    print("¡Base de Datos MAESTRA Gesty ERP creada exitosamente! Lista para todos los módulos.")

if __name__ == "__main__":
    inicializar_db()