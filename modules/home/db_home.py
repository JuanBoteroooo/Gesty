from database.connection import connect
from datetime import date

def obtener_resumen_hoy():
    """Trae un conteo rápido para mostrar en la pantalla de bienvenida"""
    conn = connect()
    cursor = conn.cursor()
    
    # Fecha de hoy en formato YYYY-MM-DD
    hoy = date.today().strftime('%Y-%m-%d')
    
    # 1. Ventas realizadas HOY
    cursor.execute("""
        SELECT COUNT(id) as cant_facturas 
        FROM ventas 
        WHERE date(fecha_hora) = ?
    """, (hoy,))
    ventas_hoy = cursor.fetchone()['cant_facturas']
    
    # 2. Total de productos registrados
    cursor.execute("SELECT COUNT(id) as total FROM productos")
    productos = cursor.fetchone()['total']
    
    # 3. Total de clientes registrados
    cursor.execute("SELECT COUNT(id) as total FROM clientes")
    clientes = cursor.fetchone()['total']
    
    conn.close()
    
    return {
        "ventas_hoy": ventas_hoy,
        "total_productos": productos,
        "total_clientes": clientes
    }