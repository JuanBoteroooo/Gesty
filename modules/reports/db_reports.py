from database.connection import connect

def obtener_kpis_mes_actual():
    """Calcula Ventas Totales, Costos y Ganancia Neta del mes en curso"""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            COALESCE(SUM(d.cantidad * d.precio_unitario), 0) as venta_total,
            COALESCE(SUM(d.cantidad * d.precio_costo_momento), 0) as costo_total
        FROM detalles_venta d
        JOIN ventas v ON d.venta_id = v.id
        WHERE strftime('%Y-%m', v.fecha_hora) = strftime('%Y-%m', 'now', 'localtime')
    """)
    res = dict(cursor.fetchone())
    res['ganancia'] = res['venta_total'] - res['costo_total']
    conn.close()
    return res

def obtener_ingresos_por_metodo():
    """Suma cuánto dinero ha entrado por cada método de pago (Zelle, Pago Móvil, etc) este mes"""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            mp.nombre as metodo, 
            m.simbolo, 
            SUM(p.monto) as total_recaudado
        FROM pagos_venta p
        JOIN ventas v ON p.venta_id = v.id
        JOIN metodos_pago mp ON p.metodo_pago_id = mp.id
        JOIN monedas m ON mp.moneda_id = m.id
        WHERE strftime('%Y-%m', v.fecha_hora) = strftime('%Y-%m', 'now', 'localtime')
        GROUP BY mp.id
        ORDER BY total_recaudado DESC
    """)
    res = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return res

def obtener_top_productos():
    """Los 10 productos más vendidos del mes"""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            p.codigo, 
            p.nombre, 
            SUM(d.cantidad) as total_vendido,
            SUM(d.cantidad * d.precio_unitario) as dinero_generado
        FROM detalles_venta d
        JOIN ventas v ON d.venta_id = v.id
        JOIN productos p ON d.producto_id = p.id
        WHERE strftime('%Y-%m', v.fecha_hora) = strftime('%Y-%m', 'now', 'localtime')
        GROUP BY p.id
        ORDER BY total_vendido DESC
        LIMIT 10
    """)
    res = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return res

def obtener_stock_critico():
    """Productos que están por debajo de su stock mínimo sumando todos los almacenes"""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            p.codigo, 
            p.nombre, 
            COALESCE(SUM(ia.cantidad), 0) as stock_actual,
            p.stock_minimo as cantidad_minima
        FROM productos p
        LEFT JOIN inventario_almacenes ia ON p.id = ia.producto_id
        GROUP BY p.id
        HAVING stock_actual <= p.stock_minimo
        ORDER BY stock_actual ASC
    """)
    res = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return res