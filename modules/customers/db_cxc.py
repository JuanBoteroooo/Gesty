from database.connection import connect

# ====================================================
# SECCIÓN 1: MODELO CLÁSICO (POR FACTURA INDIVIDUAL)
# ====================================================
def obtener_facturas_pendientes():
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cxc.id, cxc.venta_id, c.nombre as cliente_nombre, cxc.monto_total, cxc.saldo_pendiente, v.fecha_hora as fecha_venta, cxc.fecha_vencimiento
        FROM cuentas_por_cobrar cxc
        JOIN clientes c ON cxc.cliente_id = c.id
        JOIN ventas v ON cxc.venta_id = v.id
        WHERE cxc.estado = 'PENDIENTE'
        ORDER BY cxc.fecha_vencimiento ASC
    """)
    res = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return res

def registrar_abono_factura_especifica(cxc_id, monto, metodo_pago_id, sesion_caja_id):
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT saldo_pendiente FROM cuentas_por_cobrar WHERE id = ?", (cxc_id,))
        saldo_actual = float(cursor.fetchone()['saldo_pendiente'])
        monto_pagar = float(monto)

        cursor.execute("INSERT INTO abonos_cxc (cxc_id, monto, metodo_pago_id, sesion_caja_id) VALUES (?, ?, ?, ?)", (cxc_id, monto_pagar, metodo_pago_id, sesion_caja_id))
        
        nuevo_saldo = saldo_actual - monto_pagar
        estado_nuevo = 'PAGADA' if nuevo_saldo <= 0.01 else 'PENDIENTE'
        
        cursor.execute("UPDATE cuentas_por_cobrar SET saldo_pendiente = ?, estado = ? WHERE id = ?", (nuevo_saldo, estado_nuevo, cxc_id))
        
        # Eliminada la actualización a sesiones_caja que causaba el error
        conn.commit()
        return True, "Abono aplicado correctamente a la factura."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()


# ====================================================
# SECCIÓN 2: MODELO CUADERNO (MINI-POS INFINITO)
# ====================================================
def obtener_cuentas_infinitas():
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cxc.id as cxc_id, cxc.venta_id, c.id as cliente_id, c.nombre as cliente_nombre, c.documento, cxc.saldo_pendiente, v.fecha_hora
        FROM cuentas_por_cobrar cxc
        JOIN clientes c ON cxc.cliente_id = c.id
        JOIN ventas v ON cxc.venta_id = v.id
        WHERE cxc.estado = 'CUENTA_ABIERTA'
    """)
    res = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return res

def crear_cuenta_infinita(cliente_id, moneda_id, sesion_caja_id):
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM cuentas_por_cobrar WHERE cliente_id = ? AND estado = 'CUENTA_ABIERTA'", (cliente_id,))
        if cursor.fetchone():
            return False, "Este cliente ya tiene una Cuenta Abierta activa."
        
        cursor.execute("SELECT tasa_cambio FROM monedas WHERE id = ?", (moneda_id,))
        tasa = cursor.fetchone()['tasa_cambio']

        # Crear una venta vacía como ancla
        cursor.execute("INSERT INTO ventas (cliente_id, moneda_id, tasa_cambio_momento, total_venta, sesion_caja_id) VALUES (?, ?, ?, 0, ?)", (cliente_id, moneda_id, tasa, sesion_caja_id))
        venta_id = cursor.lastrowid
        
        # Crear la CxC atada a esa venta en modo INFINITO
        cursor.execute("INSERT INTO cuentas_por_cobrar (venta_id, cliente_id, monto_total, saldo_pendiente, estado) VALUES (?, ?, 0, 0, 'CUENTA_ABIERTA')", (venta_id, cliente_id))
        conn.commit()
        return True, "Cuenta Abierta (Cuaderno) iniciada con éxito."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def obtener_detalle_cuenta_infinita(cxc_id, venta_id):
    """Devuelve los productos llevados y los pagos realizados para armar la tabla del Mini-POS"""
    conn = connect()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 'PRODUCTO' as tipo, dv.id as item_id, p.nombre as descripcion, dv.cantidad, dv.precio_unitario as precio, (dv.cantidad * dv.precio_unitario) as subtotal, '' as fecha
        FROM detalles_venta dv
        JOIN productos p ON dv.producto_id = p.id
        WHERE dv.venta_id = ?
        
        UNION ALL
        
        SELECT 'ABONO' as tipo, a.id as item_id, mp.nombre as descripcion, 1 as cantidad, a.monto as precio, a.monto as subtotal, a.fecha
        FROM abonos_cxc a
        JOIN metodos_pago mp ON a.metodo_pago_id = mp.id
        WHERE a.cxc_id = ?
    """, (venta_id, cxc_id))
    
    res = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return res

def agregar_producto_cuenta(cxc_id, venta_id, producto_id, almacen_id, cantidad, precio, usuario_id):
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT precio_costo FROM productos_proveedores WHERE producto_id = ? LIMIT 1", (producto_id,))
        row = cursor.fetchone()
        costo = row['precio_costo'] if row else 0.0
        
        cursor.execute("UPDATE inventario_almacenes SET cantidad = cantidad - ? WHERE producto_id = ? AND almacen_id = ?", (cantidad, producto_id, almacen_id))
        cursor.execute("INSERT INTO detalles_venta (venta_id, producto_id, almacen_origen_id, cantidad, precio_unitario, precio_costo_momento) VALUES (?, ?, ?, ?, ?, ?)", (venta_id, producto_id, almacen_id, cantidad, precio, costo))
        
        subtotal = float(cantidad) * float(precio)
        cursor.execute("UPDATE ventas SET total_venta = total_venta + ? WHERE id = ?", (subtotal, venta_id))
        cursor.execute("UPDATE cuentas_por_cobrar SET monto_total = monto_total + ?, saldo_pendiente = saldo_pendiente + ? WHERE id = ?", (subtotal, subtotal, cxc_id))
        
        cursor.execute("INSERT INTO movimientos_inventario (producto_id, almacen_origen_id, tipo_movimiento, cantidad, motivo, usuario_id) VALUES (?, ?, 'SALIDA', ?, 'Agregado a Cuaderno', ?)", (producto_id, almacen_id, cantidad, usuario_id))
        
        conn.commit()
        return True, "Producto agregado a la cuenta."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def devolver_producto_cuenta(detalle_id, cxc_id, venta_id, cantidad_a_devolver, usuario_id):
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT producto_id, almacen_origen_id, cantidad, precio_unitario FROM detalles_venta WHERE id = ?", (detalle_id,))
        det = cursor.fetchone()
        if not det: return False, "El producto no existe en la cuenta."
        
        cantidad_original = int(det['cantidad'])
        if cantidad_a_devolver > cantidad_original:
            return False, "No puede devolver más unidades de las que compró."
            
        subtotal_devuelto = float(cantidad_a_devolver) * float(det['precio_unitario'])
        
        # 1. Devolver inventario
        cursor.execute("UPDATE inventario_almacenes SET cantidad = cantidad + ? WHERE producto_id = ? AND almacen_id = ?", (cantidad_a_devolver, det['producto_id'], det['almacen_origen_id']))
        
        # 2. Modificar o eliminar la línea de la factura
        if cantidad_a_devolver == cantidad_original:
            cursor.execute("DELETE FROM detalles_venta WHERE id = ?", (detalle_id,))
        else:
            cursor.execute("UPDATE detalles_venta SET cantidad = cantidad - ? WHERE id = ?", (cantidad_a_devolver, detalle_id))
        
        # 3. Rebajar la deuda
        cursor.execute("UPDATE ventas SET total_venta = total_venta - ? WHERE id = ?", (subtotal_devuelto, venta_id))
        cursor.execute("UPDATE cuentas_por_cobrar SET monto_total = monto_total - ?, saldo_pendiente = saldo_pendiente - ? WHERE id = ?", (subtotal_devuelto, subtotal_devuelto, cxc_id))
        
        # 4. KARDEX
        cursor.execute("INSERT INTO movimientos_inventario (producto_id, almacen_destino_id, tipo_movimiento, cantidad, motivo, usuario_id) VALUES (?, ?, 'ENTRADA', ?, 'Devolución de Cuaderno', ?)", (det['producto_id'], det['almacen_origen_id'], cantidad_a_devolver, usuario_id))
        
        conn.commit()
        return True, f"Se han devuelto {cantidad_a_devolver} unidades. Inventario restaurado y deuda actualizada."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def registrar_abono_cuaderno(cxc_id, monto, metodo_pago_id, sesion_caja_id):
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO abonos_cxc (cxc_id, monto, metodo_pago_id, sesion_caja_id) VALUES (?, ?, ?, ?)", (cxc_id, monto, metodo_pago_id, sesion_caja_id))
        cursor.execute("UPDATE cuentas_por_cobrar SET saldo_pendiente = saldo_pendiente - ? WHERE id = ?", (monto, cxc_id))
        
        # Eliminada la actualización a sesiones_caja
        conn.commit()
        return True, "Abono ingresado a la cuenta."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()