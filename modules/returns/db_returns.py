from database.connection import connect

def buscar_facturas(termino=""):
    conn = connect()
    cursor = conn.cursor()
    query = """
        SELECT v.id, v.fecha_hora, c.nombre as cliente_nombre, c.documento as cliente_doc, m.simbolo as moneda_simbolo, v.total_venta
        FROM ventas v
        JOIN clientes c ON v.cliente_id = c.id
        JOIN monedas m ON v.moneda_id = m.id
        WHERE v.id LIKE ? OR c.nombre LIKE ? OR c.documento LIKE ?
        ORDER BY v.fecha_hora DESC LIMIT 50
    """
    param = f"%{termino}%"
    cursor.execute(query, (param, param, param))
    res = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return res

def obtener_detalles_factura(venta_id):
    conn = connect()
    cursor = conn.cursor()
    # 🔥 AÑADIMOS dv.id PARA PODER IDENTIFICAR LA LÍNEA EXACTA A DEVOLVER 🔥
    cursor.execute("""
        SELECT dv.id, p.codigo, p.nombre, dv.cantidad, dv.precio_unitario, (dv.cantidad * dv.precio_unitario) as subtotal
        FROM detalles_venta dv
        JOIN productos p ON dv.producto_id = p.id
        WHERE dv.venta_id = ?
    """, (venta_id,))
    res = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return res

def procesar_devolucion(venta_id):
    """Anula la factura completa (Todas las unidades)"""
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT producto_id, almacen_origen_id, cantidad FROM detalles_venta WHERE venta_id = ?", (venta_id,))
        detalles = cursor.fetchall()
        
        # 1. Regresar todo el stock
        for d in detalles:
            cursor.execute("UPDATE inventario_almacenes SET cantidad = cantidad + ? WHERE producto_id = ? AND almacen_id = ?", (d['cantidad'], d['producto_id'], d['almacen_origen_id']))
        
        # 2. Borrar las cuentas por cobrar si era a crédito
        cursor.execute("DELETE FROM cuentas_por_cobrar WHERE venta_id = ?", (venta_id,))
        
        # 3. Borrar la venta (la cascada borrará los detalles y pagos atados)
        cursor.execute("DELETE FROM ventas WHERE id = ?", (venta_id,))
        
        conn.commit()
        return True, "Factura anulada. Todo el stock ha sido devuelto."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

# ====================================================
# 🔥 NUEVA FUNCIÓN: DEVOLUCIÓN PARCIAL DE PRODUCTO 🔥
# ====================================================
def procesar_devolucion_parcial(venta_id, detalle_id, cantidad_devuelta, usuario_id):
    conn = connect()
    cursor = conn.cursor()
    try:
        # 1. Buscar los datos exactos del producto en esa factura
        cursor.execute("SELECT producto_id, almacen_origen_id, cantidad, precio_unitario FROM detalles_venta WHERE id = ?", (detalle_id,))
        det = cursor.fetchone()
        if not det: return False, "Línea de factura no encontrada."
        
        cant_original = int(det['cantidad'])
        if cantidad_devuelta > cant_original: 
            return False, "No puedes devolver más unidades de las que se compraron."
            
        subtotal_devuelto = float(cantidad_devuelta) * float(det['precio_unitario'])
        
        # 2. Restaurar el stock al almacén
        cursor.execute("UPDATE inventario_almacenes SET cantidad = cantidad + ? WHERE producto_id = ? AND almacen_id = ?", (cantidad_devuelta, det['producto_id'], det['almacen_origen_id']))
        
        # 3. Si devuelve todo el producto, borramos la línea. Si devuelve una parte, restamos la cantidad.
        if cantidad_devuelta == cant_original:
            cursor.execute("DELETE FROM detalles_venta WHERE id = ?", (detalle_id,))
        else:
            cursor.execute("UPDATE detalles_venta SET cantidad = cantidad - ? WHERE id = ?", (cantidad_devuelta, detalle_id))
            
        # 4. Descontar el dinero del total de la factura
        cursor.execute("UPDATE ventas SET total_venta = total_venta - ? WHERE id = ?", (subtotal_devuelto, venta_id))
        
        # 5. Si la factura estaba a crédito, le descontamos la deuda al cliente
        cursor.execute("SELECT id, saldo_pendiente FROM cuentas_por_cobrar WHERE venta_id = ?", (venta_id,))
        cxc = cursor.fetchone()
        if cxc:
            nuevo_saldo = max(0, float(cxc['saldo_pendiente']) - subtotal_devuelto)
            estado = 'PAGADA' if nuevo_saldo <= 0.01 else 'PENDIENTE'
            cursor.execute("UPDATE cuentas_por_cobrar SET monto_total = monto_total - ?, saldo_pendiente = ?, estado = ? WHERE id = ?", (subtotal_devuelto, nuevo_saldo, estado, cxc['id']))
            
        # 6. Registrar en Kardex el movimiento
        cursor.execute("INSERT INTO movimientos_inventario (producto_id, almacen_destino_id, tipo_movimiento, cantidad, motivo, usuario_id) VALUES (?, ?, 'ENTRADA', ?, 'Devolución de mercancía Fac #' || ?, ?)", (det['producto_id'], det['almacen_origen_id'], cantidad_devuelta, venta_id, usuario_id))

        # 7. Si la factura se quedó sin productos (devolvió el último que quedaba), la borramos por completo
        cursor.execute("SELECT COUNT(*) as cant FROM detalles_venta WHERE venta_id = ?", (venta_id,))
        if cursor.fetchone()['cant'] == 0:
            cursor.execute("DELETE FROM ventas WHERE id = ?", (venta_id,))

        conn.commit()
        return True, f"Se devolvieron {cantidad_devuelta} unidades exitosamente."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()