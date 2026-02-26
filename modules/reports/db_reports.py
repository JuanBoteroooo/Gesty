from database.connection import connect

def obtener_kpis_mes_actual():
    conn = connect()
    cursor = conn.cursor()
    # Calculamos Ventas Totales y Costos Totales del mes actual
    cursor.execute("""
        SELECT 
            COALESCE(SUM(total_venta), 0) as venta_total,
            COALESCE(SUM((SELECT SUM(cantidad * precio_costo_momento) FROM detalles_venta WHERE venta_id = v.id)), 0) as costo_total
        FROM ventas v
        WHERE strftime('%Y-%m', v.fecha_hora) = strftime('%Y-%m', 'now')
    """)
    res = dict(cursor.fetchone())
    conn.close()
    
    venta = float(res['venta_total'])
    costo = float(res['costo_total'])
    ganancia = venta - costo
    
    return {'venta_total': venta, 'costo_total': costo, 'ganancia': ganancia}

def obtener_ingresos_por_metodo():
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT mp.nombre as metodo, m.simbolo, SUM(pv.monto) as total_recaudado
        FROM pagos_venta pv
        JOIN metodos_pago mp ON pv.metodo_pago_id = mp.id
        JOIN monedas m ON mp.moneda_id = m.id
        JOIN ventas v ON pv.venta_id = v.id
        WHERE strftime('%Y-%m', v.fecha_hora) = strftime('%Y-%m', 'now')
        GROUP BY mp.id
        ORDER BY total_recaudado DESC
    """)
    res = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return res

def obtener_top_productos():
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.codigo, p.nombre, SUM(dv.cantidad) as total_vendido, SUM(dv.cantidad * dv.precio_unitario) as dinero_generado
        FROM detalles_venta dv
        JOIN productos p ON dv.producto_id = p.id
        JOIN ventas v ON dv.venta_id = v.id
        WHERE strftime('%Y-%m', v.fecha_hora) = strftime('%Y-%m', 'now')
        GROUP BY p.id 
        ORDER BY total_vendido DESC LIMIT 10
    """)
    res = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return res

def obtener_stock_critico():
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.codigo, p.nombre, SUM(ia.cantidad) as stock_actual, p.stock_minimo as cantidad_minima
        FROM productos p
        LEFT JOIN inventario_almacenes ia ON p.id = ia.producto_id
        GROUP BY p.id
        HAVING stock_actual <= p.stock_minimo
        ORDER BY stock_actual ASC
    """)
    res = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return res

# 🔥 NUEVA FUNCIÓN: TOP CLIENTES 🔥
def obtener_top_clientes():
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.documento, c.nombre, COUNT(v.id) as total_compras, SUM(v.total_venta) as dinero_gastado
        FROM ventas v
        JOIN clientes c ON v.cliente_id = c.id
        WHERE strftime('%Y-%m', v.fecha_hora) = strftime('%Y-%m', 'now') AND c.id != 1
        GROUP BY c.id 
        ORDER BY dinero_gastado DESC LIMIT 10
    """)
    res = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return res