from database.connection import connect

def obtener_cuentas_por_cobrar():
    """Trae la lista de clientes que tienen deudas pendientes"""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cxc.id, cxc.venta_id, cl.nombre as cliente_nombre, 
               cxc.monto_total, cxc.saldo_pendiente, cxc.fecha_vencimiento,
               v.fecha_hora as fecha_venta
        FROM cuentas_por_cobrar cxc
        JOIN clientes cl ON cxc.cliente_id = cl.id
        JOIN ventas v ON cxc.venta_id = v.id
        WHERE cxc.estado = 'PENDIENTE'
        ORDER BY cxc.fecha_vencimiento ASC
    """)
    res = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return res

def registrar_abono(cxc_id, monto, metodo_pago_id, sesion_caja_id):
    """Registra un pago parcial o total de una deuda"""
    conn = connect()
    cursor = conn.cursor()
    try:
        # 1. Insertar el abono
        cursor.execute("""
            INSERT INTO abonos_cxc (cxc_id, monto, metodo_pago_id, sesion_caja_id)
            VALUES (?, ?, ?, ?)
        """, (cxc_id, monto, metodo_pago_id, sesion_caja_id))

        # 2. Actualizar el saldo en la tabla CxC
        cursor.execute("""
            UPDATE cuentas_por_cobrar 
            SET saldo_pendiente = saldo_pendiente - ?
            WHERE id = ?
        """, (monto, cxc_id))

        # 3. Si el saldo llega a 0, marcar como PAGADA
        cursor.execute("""
            UPDATE cuentas_por_cobrar 
            SET estado = 'PAGADA'
            WHERE id = ? AND saldo_pendiente <= 0.01
        """, (cxc_id,))

        conn.commit()
        return True, "Abono registrado correctamente."
    except Exception as e:
        conn.rollback()
        return False, f"Error: {str(e)}"
    finally:
        conn.close()