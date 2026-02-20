from database.connection import connect

def buscar_facturas(termino=""):
    """Busca facturas por ID, Nombre de cliente o Documento"""
    conn = connect()
    cursor = conn.cursor()
    
    termino_sql = f"%{termino.lower()}%"
    
    cursor.execute("""
        SELECT v.id, v.fecha_hora, v.total_venta, c.nombre as cliente_nombre, c.documento as cliente_doc, m.simbolo as moneda_simbolo
        FROM ventas v
        JOIN clientes c ON v.cliente_id = c.id
        JOIN monedas m ON v.moneda_id = m.id
        WHERE CAST(v.id AS TEXT) LIKE ? OR LOWER(c.nombre) LIKE ? OR LOWER(c.documento) LIKE ?
        ORDER BY v.id DESC
        LIMIT 50
    """, (termino_sql, termino_sql, termino_sql))
    
    res = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return res

def obtener_detalles_factura(venta_id):
    """Trae los productos específicos que se vendieron en esa factura"""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.codigo, p.nombre, d.cantidad, d.precio_unitario, (d.cantidad * d.precio_unitario) as subtotal
        FROM detalles_venta d
        JOIN productos p ON d.producto_id = p.id
        WHERE d.venta_id = ?
    """, (venta_id,))
    res = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return res

def procesar_devolucion(venta_id):
    """Devuelve el stock al inventario y elimina la factura por completo"""
    conn = connect()
    cursor = conn.cursor()
    try:
        # 1. Recuperar los productos de la factura para saber qué devolver
        cursor.execute("SELECT producto_id, cantidad FROM detalles_venta WHERE venta_id = ?", (venta_id,))
        detalles = cursor.fetchall()
        
        # 2. Devolver las cantidades al inventario (Almacén 1 por defecto)
        for d in detalles:
            cursor.execute("""
                UPDATE inventario_almacenes 
                SET cantidad = cantidad + ? 
                WHERE producto_id = ? AND almacen_id = 1
            """, (d['cantidad'], d['producto_id']))
        
        # 3. Eliminar la venta 
        # (Nota: SQLite eliminará automáticamente los detalles y los pagos gracias al "ON DELETE CASCADE" que configuramos)
        cursor.execute("DELETE FROM ventas WHERE id = ?", (venta_id,))
        
        conn.commit()
        return True, f"La factura #{venta_id} ha sido anulada y el stock fue devuelto al inventario exitosamente."
    except Exception as e:
        conn.rollback()
        return False, f"Error al procesar la devolución: {e}"
    finally:
        conn.close()