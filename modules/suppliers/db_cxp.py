from database.connection import connect

def inicializar_tablas_cxp():
    """Crea las tablas de Cuentas por Pagar si no existen."""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cuentas_por_pagar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proveedor_id INTEGER,
            numero_factura TEXT,
            fecha_emision DATE,
            fecha_vencimiento DATE,
            monto_total REAL,
            saldo_pendiente REAL,
            estado TEXT DEFAULT 'PENDIENTE',
            FOREIGN KEY(proveedor_id) REFERENCES proveedores(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS abonos_cxp (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cxp_id INTEGER,
            monto REAL,
            metodo_pago_id INTEGER,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            usuario_id INTEGER,
            FOREIGN KEY(cxp_id) REFERENCES cuentas_por_pagar(id),
            FOREIGN KEY(metodo_pago_id) REFERENCES metodos_pago(id)
        )
    """)
    conn.commit()
    conn.close()

def registrar_factura_credito(proveedor_id, numero_factura, fecha_emision, fecha_vencimiento, monto_total):
    inicializar_tablas_cxp()
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO cuentas_por_pagar (proveedor_id, numero_factura, fecha_emision, fecha_vencimiento, monto_total, saldo_pendiente)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (proveedor_id, numero_factura, fecha_emision, fecha_vencimiento, monto_total, monto_total))
        conn.commit()
        return True, "Factura a crédito registrada exitosamente."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def registrar_abono(cxp_id, monto_abono, metodo_pago_id, usuario_id):
    inicializar_tablas_cxp()
    conn = connect()
    cursor = conn.cursor()
    try:
        # 1. Verificar saldo actual
        cursor.execute("SELECT saldo_pendiente FROM cuentas_por_pagar WHERE id = ?", (cxp_id,))
        row = cursor.fetchone()
        if not row: return False, "La cuenta por pagar no existe."
        
        saldo_actual = float(row['saldo_pendiente'])
        if monto_abono > saldo_actual:
            return False, f"El monto ingresado (${monto_abono}) es mayor a la deuda actual (${saldo_actual})."

        # 2. Registrar el abono
        cursor.execute("""
            INSERT INTO abonos_cxp (cxp_id, monto, metodo_pago_id, usuario_id)
            VALUES (?, ?, ?, ?)
        """, (cxp_id, monto_abono, metodo_pago_id, usuario_id))

        # 3. Actualizar la deuda
        nuevo_saldo = saldo_actual - monto_abono
        estado = 'PAGADO' if nuevo_saldo <= 0.01 else 'PENDIENTE'
        
        cursor.execute("""
            UPDATE cuentas_por_pagar 
            SET saldo_pendiente = ?, estado = ? 
            WHERE id = ?
        """, (nuevo_saldo, estado, cxp_id))

        conn.commit()
        return True, "Abono registrado correctamente."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def obtener_deudas_activas():
    inicializar_tablas_cxp()
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cxp.id, p.nombre as proveedor, cxp.numero_factura, cxp.fecha_emision, 
               cxp.fecha_vencimiento, cxp.monto_total, cxp.saldo_pendiente, cxp.estado
        FROM cuentas_por_pagar cxp
        JOIN proveedores p ON cxp.proveedor_id = p.id
        WHERE cxp.estado = 'PENDIENTE'
        ORDER BY cxp.fecha_vencimiento ASC
    """)
    res = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return res

def obtener_historial_abonos(cxp_id):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.fecha, a.monto, mp.nombre as metodo, u.usuario
        FROM abonos_cxp a
        JOIN metodos_pago mp ON a.metodo_pago_id = mp.id
        JOIN usuarios u ON a.usuario_id = u.id
        WHERE a.cxp_id = ?
        ORDER BY a.fecha DESC
    """, (cxp_id,))
    res = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return res