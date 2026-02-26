from database.connection import connect

def obtener_productos_basico():
    """Trae una lista ligera de productos para llenar los buscadores rápidamente"""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT id, codigo, nombre FROM productos ORDER BY nombre ASC")
    res = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return res

def procesar_produccion(almacen_origen_id, almacen_destino_id, insumos, generados, usuario_id, motivo):
    """
    Resta los 'insumos' del almacén de origen y suma los 'generados' al almacén de destino.
    """
    conn = connect()
    cursor = conn.cursor()
    try:
        # 1. VERIFICAR STOCK DE INSUMOS (Materia Prima)
        for item in insumos:
            cursor.execute("SELECT cantidad FROM inventario_almacenes WHERE producto_id = ? AND almacen_id = ?", (item['id'], almacen_origen_id))
            row = cursor.fetchone()
            stock = row['cantidad'] if row else 0
            if stock < item['cantidad']:
                return False, f"Stock insuficiente de la materia prima ID {item['id']}. Disponible: {stock}"

        # 2. DESCONTAR INSUMOS
        for item in insumos:
            cursor.execute("UPDATE inventario_almacenes SET cantidad = cantidad - ? WHERE producto_id = ? AND almacen_id = ?", (item['cantidad'], item['id'], almacen_origen_id))
            
            # Registrar en Kardex la salida
            cursor.execute("""
                INSERT INTO movimientos_inventario (producto_id, almacen_origen_id, tipo_movimiento, cantidad, motivo, usuario_id)
                VALUES (?, ?, 'SALIDA', ?, ?, ?)
            """, (item['id'], almacen_origen_id, item['cantidad'], f"Consumo por Producción: {motivo}", usuario_id))

        # 3. SUMAR PRODUCTOS GENERADOS (Nuevos)
        for item in generados:
            cursor.execute("SELECT id FROM inventario_almacenes WHERE producto_id = ? AND almacen_id = ?", (item['id'], almacen_destino_id))
            if cursor.fetchone():
                cursor.execute("UPDATE inventario_almacenes SET cantidad = cantidad + ? WHERE producto_id = ? AND almacen_id = ?", (item['cantidad'], item['id'], almacen_destino_id))
            else:
                cursor.execute("INSERT INTO inventario_almacenes (producto_id, almacen_id, cantidad) VALUES (?, ?, ?)", (item['id'], almacen_destino_id, item['cantidad']))
            
            # Registrar en Kardex la entrada
            cursor.execute("""
                INSERT INTO movimientos_inventario (producto_id, almacen_destino_id, tipo_movimiento, cantidad, motivo, usuario_id)
                VALUES (?, ?, 'ENTRADA', ?, ?, ?)
            """, (item['id'], almacen_destino_id, item['cantidad'], f"Ingreso por Producción: {motivo}", usuario_id))

        conn.commit()
        return True, "El proceso de producción/preparación se registró exitosamente."
    except Exception as e:
        conn.rollback()
        return False, f"Error en base de datos: {str(e)}"
    finally:
        conn.close()