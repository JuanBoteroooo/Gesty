from database.connection import connect

def inicializar_tabla_gastos():
    """Garantiza que la tabla de gastos operativos exista en la base de datos"""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gastos_operativos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            categoria TEXT,
            descripcion TEXT,
            monto REAL,
            metodo_pago_id INTEGER,
            usuario_id INTEGER,
            FOREIGN KEY(metodo_pago_id) REFERENCES metodos_pago(id)
        )
    """)
    conn.commit()
    conn.close()

def registrar_gasto(categoria, descripcion, monto_usd, metodo_pago_id, usuario_id):
    inicializar_tabla_gastos()
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO gastos_operativos (categoria, descripcion, monto, metodo_pago_id, usuario_id)
            VALUES (?, ?, ?, ?, ?)
        """, (categoria, descripcion, monto_usd, metodo_pago_id, usuario_id))
        conn.commit()
        return True, "Gasto operativo registrado exitosamente."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def obtener_historial_gastos():
    inicializar_tabla_gastos()
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT g.id, g.fecha, g.categoria, g.descripcion, g.monto, mp.nombre as metodo_pago
        FROM gastos_operativos g
        JOIN metodos_pago mp ON g.metodo_pago_id = mp.id
        ORDER BY g.fecha DESC LIMIT 100
    """)
    res = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return res

def obtener_saldos_cuentas():
    """
    ¡MAGIA FINANCIERA!
    Calcula cuánto dinero hay en cada cuenta sumando (Ventas + Abonos CxC) y restando (Gastos)
    """
    inicializar_tabla_gastos()
    conn = connect()
    cursor = conn.cursor()
    
    query = """
        SELECT mp.id, mp.nombre as metodo, m.simbolo, m.tasa_cambio,
               COALESCE((SELECT SUM(monto / tasa_calculo) FROM pagos_venta pv WHERE pv.metodo_pago_id = mp.id), 0) +
               COALESCE((SELECT SUM(monto) FROM abonos_cxc ac WHERE ac.metodo_pago_id = mp.id), 0) -
               COALESCE((SELECT SUM(monto) FROM gastos_operativos go WHERE go.metodo_pago_id = mp.id), 0) as saldo_usd
        FROM metodos_pago mp
        JOIN monedas m ON mp.moneda_id = m.id
    """
    cursor.execute(query)
    res = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return res