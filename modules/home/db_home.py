from database.connection import connect
from datetime import date

def obtener_resumen_dashboard():
    """Trae KPIs financieros y operativos para el Dashboard principal"""
    conn = connect()
    cursor = conn.cursor()
    
    # Fecha de hoy en formato YYYY-MM-DD
    hoy = date.today().strftime('%Y-%m-%d')
    
    # 1. Ingresos generados HOY ($)
    cursor.execute("""
        SELECT COALESCE(SUM(total_venta), 0) as total 
        FROM ventas 
        WHERE date(fecha_hora) = ?
    """, (hoy,))
    ingresos_hoy = cursor.fetchone()['total']
    
    # 2. Cantidad de Facturas HOY
    cursor.execute("""
        SELECT COUNT(id) as cant_facturas 
        FROM ventas 
        WHERE date(fecha_hora) = ?
    """, (hoy,))
    ventas_hoy = cursor.fetchone()['cant_facturas']
    
    # 3. Dinero en la calle (Cuentas por Cobrar Pendientes)
    cursor.execute("""
        SELECT COALESCE(SUM(saldo_pendiente), 0) as deuda 
        FROM cuentas_por_cobrar 
        WHERE estado = 'PENDIENTE'
    """)
    por_cobrar = cursor.fetchone()['deuda']
    
    # 4. Alertas de Stock (Productos que están por debajo de su mínimo)
    cursor.execute("""
        SELECT COUNT(*) as alertas FROM (
            SELECT p.id
            FROM productos p
            LEFT JOIN inventario_almacenes ia ON p.id = ia.producto_id
            GROUP BY p.id
            HAVING COALESCE(SUM(ia.cantidad), 0) <= p.stock_minimo
        )
    """)
    alertas_stock = cursor.fetchone()['alertas']

    # 5. Las últimas 5 ventas (para la mini-tabla en vivo)
    cursor.execute("""
        SELECT v.id, v.fecha_hora, c.nombre as cliente, v.total_venta
        FROM ventas v
        JOIN clientes c ON v.cliente_id = c.id
        ORDER BY v.id DESC
        LIMIT 5
    """)
    ultimas_ventas = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "ingresos_hoy": ingresos_hoy,
        "ventas_hoy": ventas_hoy,
        "por_cobrar": por_cobrar,
        "alertas_stock": alertas_stock,
        "ultimas_ventas": ultimas_ventas
    }