from database.connection import connect

def verificar_caja_abierta():
    """Verifica si hay una sesión de caja activa. Retorna los datos o None."""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sesiones_caja WHERE estado = 'ABIERTA' ORDER BY id DESC LIMIT 1")
    sesion = cursor.fetchone()
    conn.close()
    return dict(sesion) if sesion else None

def abrir_caja(monto_inicial, usuario_id=1):
    """Abre un nuevo turno de caja"""
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO sesiones_caja (monto_inicial, estado, usuario_id) VALUES (?, 'ABIERTA', ?)", (monto_inicial, usuario_id))
        conn.commit()
        return True, "Caja abierta exitosamente."
    except Exception as e:
        return False, f"Error al abrir caja: {e}"
    finally:
        conn.close()

def cerrar_caja(sesion_id):
    """Cierra el turno actual registrando la hora de salida"""
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE sesiones_caja SET estado = 'CERRADA', fecha_cierre = CURRENT_TIMESTAMP WHERE id = ?", (sesion_id,))
        conn.commit()
        return True, "Turno de caja cerrado correctamente."
    except Exception as e:
        return False, f"Error al cerrar caja: {e}"
    finally:
        conn.close()

def obtener_resumen_caja(sesion_id):
    """Suma todos los pagos agrupados por método durante esta sesión específica"""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT mp.nombre as metodo, m.simbolo, SUM(p.monto) as total
        FROM pagos_venta p
        JOIN ventas v ON p.venta_id = v.id
        JOIN metodos_pago mp ON p.metodo_pago_id = mp.id
        JOIN monedas m ON mp.moneda_id = m.id
        WHERE v.sesion_caja_id = ?
        GROUP BY mp.id
    """, (sesion_id,))
    res = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return res

def obtener_datos_configuracion():
    """Trae clientes, monedas, listas, métodos de pago y almacenes"""
    conn = connect()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, nombre, lista_precio_id FROM clientes ORDER BY nombre")
    clientes = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT id, nombre, simbolo, tasa_cambio, es_principal FROM monedas ORDER BY id")
    monedas = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT id, nombre FROM listas_precios ORDER BY id")
    listas = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("""
        SELECT mp.id, mp.nombre, mp.moneda_id, m.simbolo, m.tasa_cambio, m.es_principal 
        FROM metodos_pago mp
        JOIN monedas m ON mp.moneda_id = m.id
    """)
    metodos_pago = [dict(row) for row in cursor.fetchall()]

    cursor.execute("SELECT id, nombre FROM almacenes ORDER BY id")
    almacenes = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return clientes, monedas, listas, metodos_pago, almacenes

def buscar_productos(termino, lista_precio_id, almacen_id):
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
        LEFT JOIN inventario_almacenes ia ON p.id = ia.producto_id AND ia.almacen_id = ?
        LEFT JOIN precios_producto pp ON p.id = pp.producto_id AND pp.lista_precio_id = ?
        WHERE LOWER(p.nombre) LIKE ? OR LOWER(p.codigo) LIKE ?
        LIMIT 20
    """, (almacen_id, lista_precio_id, termino, termino))
    res = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return res

def procesar_venta_completa(cliente_id, moneda_id, tasa_cambio, total_base, carrito, pagos, almacen_id, sesion_id):
    conn = connect()
    cursor = conn.cursor()
    try:
        # 1. Guardar la Factura (Vinculada a la sesión de caja)
        cursor.execute("""
            INSERT INTO ventas (cliente_id, moneda_id, tasa_cambio_momento, total_venta, sesion_caja_id) 
            VALUES (?, ?, ?, ?, ?)
        """, (cliente_id, moneda_id, tasa_cambio, total_base, sesion_id))
        venta_id = cursor.lastrowid
        
        # 2. Guardar Detalles, Descontar Stock y Registrar en KARDEX
        for item in carrito:
            cursor.execute("""
                INSERT INTO detalles_venta (venta_id, producto_id, almacen_origen_id, cantidad, precio_unitario, precio_costo_momento) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, (venta_id, item['id'], almacen_id, item['cantidad'], item['precio'], item['costo']))
            
            cursor.execute("""
                UPDATE inventario_almacenes SET cantidad = cantidad - ? 
                WHERE producto_id = ? AND almacen_id = ?
            """, (item['cantidad'], item['id'], almacen_id))
            
            # 🔥 REGISTRO EN EL KARDEX AUTOMÁTICO
            cursor.execute("""
                INSERT INTO movimientos_inventario (producto_id, almacen_origen_id, tipo_movimiento, cantidad, motivo, usuario_id)
                VALUES (?, ?, 'SALIDA', ?, ?, 1)
            """, (item['id'], almacen_id, item['cantidad'], f"Venta #{venta_id:06d}"))
            
        # 3. Guardar Pagos
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
    cursor.execute("""
        SELECT v.id, v.fecha_hora, v.total_venta, c.nombre as cliente_nombre, c.documento as cliente_doc 
        FROM ventas v JOIN clientes c ON v.cliente_id = c.id WHERE v.id = ?
    """, (venta_id,))
    venta = dict(cursor.fetchone())
    
    cursor.execute("""
        SELECT p.nombre, d.cantidad, d.precio_unitario, (d.cantidad * d.precio_unitario) as subtotal 
        FROM detalles_venta d JOIN productos p ON d.producto_id = p.id WHERE d.venta_id = ?
    """, (venta_id,))
    detalles = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return venta, detalles

# ==========================================
# 🔥 NUEVO: GESTIÓN DE PRESUPUESTOS (COTIZACIONES)
# ==========================================

def guardar_presupuesto(cliente_id, moneda_id, total_base, carrito):
    """Guarda un carrito como presupuesto válido por 3 días sin restar stock"""
    conn = connect()
    cursor = conn.cursor()
    try:
        # Se guarda con vencimiento a 3 días
        cursor.execute("""
            INSERT INTO presupuestos (cliente_id, moneda_id, total_presupuesto, fecha_vencimiento, estado) 
            VALUES (?, ?, ?, date('now', '+3 days'), 'ACTIVO')
        """, (cliente_id, moneda_id, total_base))
        presupuesto_id = cursor.lastrowid
        
        for item in carrito:
            cursor.execute("""
                INSERT INTO detalles_presupuesto (presupuesto_id, producto_id, cantidad, precio_unitario) 
                VALUES (?, ?, ?, ?)
            """, (presupuesto_id, item['id'], item['cantidad'], item['precio']))
            
        conn.commit()
        return True, presupuesto_id 
    except Exception as e:
        conn.rollback() 
        return False, f"Error al guardar presupuesto: {str(e)}"
    finally:
        conn.close()

def obtener_presupuestos_activos():
    """Trae la lista de presupuestos que aún no han sido facturados"""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.id, p.fecha_hora, p.total_presupuesto, c.nombre as cliente_nombre 
        FROM presupuestos p 
        JOIN clientes c ON p.cliente_id = c.id 
        WHERE p.estado = 'ACTIVO' 
        ORDER BY p.id DESC
    """)
    res = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return res

def cargar_detalle_presupuesto(presupuesto_id):
    """Trae los items de un presupuesto para meterlos al carrito de ventas"""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT dp.producto_id as id, prod.nombre, dp.cantidad, dp.precio_unitario as precio, 
               (SELECT cantidad FROM inventario_almacenes WHERE producto_id = prod.id LIMIT 1) as stock_max,
               (SELECT precio_costo FROM productos_proveedores WHERE producto_id = prod.id LIMIT 1) as costo
        FROM detalles_presupuesto dp
        JOIN productos prod ON dp.producto_id = prod.id
        WHERE dp.presupuesto_id = ?
    """, (presupuesto_id,))
    res = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return res

def marcar_presupuesto_procesado(presupuesto_id):
    """Cambia el estado a FACTURADO para que no vuelva a salir en la lista"""
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE presupuestos SET estado = 'FACTURADO' WHERE id = ?", (presupuesto_id,))
        conn.commit()
    except:
        pass
    finally:
        conn.close()

def obtener_datos_ticket_presupuesto(presupuesto_id):
    """Obtiene los datos formateados para imprimir el PDF/HTML del presupuesto"""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.id, p.fecha_hora, p.fecha_vencimiento, p.total_presupuesto, c.nombre as cliente_nombre, c.documento as cliente_doc 
        FROM presupuestos p JOIN clientes c ON p.cliente_id = c.id WHERE p.id = ?
    """, (presupuesto_id,))
    presupuesto = dict(cursor.fetchone())
    
    cursor.execute("""
        SELECT prod.nombre, d.cantidad, d.precio_unitario, (d.cantidad * d.precio_unitario) as subtotal 
        FROM detalles_presupuesto d JOIN productos prod ON d.producto_id = prod.id WHERE d.presupuesto_id = ?
    """, (presupuesto_id,))
    detalles = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return presupuesto, detalles