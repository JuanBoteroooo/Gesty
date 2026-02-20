from database.connection import connect

def obtener_datos_configuracion():
    conn = connect()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, nombre, lista_precio_id FROM clientes ORDER BY nombre")
    clientes = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT id, nombre, simbolo, tasa_cambio, es_principal FROM monedas ORDER BY id")
    monedas = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT id, nombre FROM listas_precios ORDER BY id")
    listas = [dict(row) for row in cursor.fetchall()]
    
    # 🔥 AHORA TRAEMOS EL ID DE LA MONEDA PARA PODER FILTRAR LOS MÉTODOS EN LA INTERFAZ
    cursor.execute("""
        SELECT mp.id, mp.nombre, mp.moneda_id, m.simbolo, m.tasa_cambio, m.es_principal 
        FROM metodos_pago mp
        JOIN monedas m ON mp.moneda_id = m.id
    """)
    metodos_pago = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return clientes, monedas, listas, metodos_pago

def buscar_productos(termino, lista_precio_id):
    conn = connect()
    cursor = conn.cursor()
    termino = f"%{termino.lower()}%"
    cursor.execute("""
        SELECT 
            p.id, p.codigo, p.nombre, 
            COALESCE(ia.cantidad, 0) as stock,
            COALESCE(pp.precio_venta, 0) as precio,
            COALESCE((SELECT precio_costo FROM productos_proveedores WHERE producto_id = p.id ORDER BY fecha_actualizacion DESC LIMIT 1), 0) as costo
        FROM productos p
        LEFT JOIN inventario_almacenes ia ON p.id = ia.producto_id AND ia.almacen_id = 1
        LEFT JOIN precios_producto pp ON p.id = pp.producto_id AND pp.lista_precio_id = ?
        WHERE LOWER(p.nombre) LIKE ? OR LOWER(p.codigo) LIKE ?
        LIMIT 20
    """, (lista_precio_id, termino, termino))
    res = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return res

def procesar_venta_completa(cliente_id, moneda_id, tasa_cambio, total_base, carrito, pagos):
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO ventas (cliente_id, moneda_id, tasa_cambio_momento, total_venta) VALUES (?, ?, ?, ?)", (cliente_id, moneda_id, tasa_cambio, total_base))
        venta_id = cursor.lastrowid
        
        for item in carrito:
            cursor.execute("INSERT INTO detalles_venta (venta_id, producto_id, almacen_origen_id, cantidad, precio_unitario, precio_costo_momento) VALUES (?, ?, 1, ?, ?, ?)", (venta_id, item['id'], item['cantidad'], item['precio'], item['costo']))
            cursor.execute("UPDATE inventario_almacenes SET cantidad = cantidad - ? WHERE producto_id = ? AND almacen_id = 1", (item['cantidad'], item['id']))
            
        for pago in pagos:
            if pago['monto'] > 0:
                cursor.execute("""
                    INSERT INTO pagos_venta (venta_id, metodo_pago_id, monto, tasa_calculo)
                    VALUES (?, ?, ?, ?)
                """, (venta_id, pago['metodo_id'], pago['monto'], pago['tasa']))
            
        conn.commit()
        return True, venta_id 
    except Exception as e:
        conn.rollback() 
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def obtener_datos_ticket(venta_id):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT v.id, v.fecha_hora, v.total_venta, c.nombre as cliente_nombre, c.documento as cliente_doc FROM ventas v JOIN clientes c ON v.cliente_id = c.id WHERE v.id = ?", (venta_id,))
    venta = dict(cursor.fetchone())
    cursor.execute("SELECT p.nombre, d.cantidad, d.precio_unitario, (d.cantidad * d.precio_unitario) as subtotal FROM detalles_venta d JOIN productos p ON d.producto_id = p.id WHERE d.venta_id = ?", (venta_id,))
    detalles = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return venta, detalles