from database.connection import connect

# ==========================================
# 1. DIRECTORIO DE PROVEEDORES (CRUD)
# ==========================================
def obtener_proveedores():
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT id, documento, nombre, telefono, direccion FROM proveedores ORDER BY nombre")
    res = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return res

def guardar_proveedor(documento, nombre, telefono, direccion):
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO proveedores (documento, nombre, telefono, direccion) VALUES (?, ?, ?, ?)", 
                       (documento, nombre, telefono, direccion))
        conn.commit()
        return True, "Proveedor registrado exitosamente."
    except Exception as e:
        return False, f"Error al registrar (¿Documento duplicado?): {str(e)}"
    finally:
        conn.close()

def eliminar_proveedor(proveedor_id):
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM proveedores WHERE id = ?", (proveedor_id,))
        conn.commit()
        return True, "Proveedor eliminado."
    except Exception as e:
        return False, f"Error al eliminar: {str(e)}"
    finally:
        conn.close()

# ==========================================
# 2. LÓGICA DE COMPRAS (INGRESO DE MERCANCÍA)
# ==========================================
def obtener_datos_configuracion_compras():
    """Trae los proveedores y almacenes para los selectores de la compra"""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre FROM proveedores ORDER BY nombre")
    proveedores = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT id, nombre FROM almacenes ORDER BY id")
    almacenes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return proveedores, almacenes

def buscar_productos_compra(termino):
    """Busca productos y muestra su último costo registrado"""
    conn = connect()
    cursor = conn.cursor()
    termino = f"%{termino.lower()}%"
    cursor.execute("""
        SELECT 
            p.id, p.codigo, p.nombre,
            COALESCE((SELECT precio_costo FROM productos_proveedores WHERE producto_id = p.id ORDER BY fecha_actualizacion DESC LIMIT 1), 0) as costo_actual
        FROM productos p
        WHERE LOWER(p.nombre) LIKE ? OR LOWER(p.codigo) LIKE ?
        LIMIT 20
    """, (termino, termino))
    res = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return res

def procesar_compra(proveedor_id, nro_factura, almacen_id, total_compra, carrito, usuario_id):
    """Guarda la compra, suma el stock, actualiza costos y registra en Kardex"""
    conn = connect()
    cursor = conn.cursor()
    try:
        # 1. Registrar la Factura de Compra
        cursor.execute("""
            INSERT INTO compras (proveedor_id, nro_factura_prov, total_compra) 
            VALUES (?, ?, ?)
        """, (proveedor_id, nro_factura, total_compra))
        compra_id = cursor.lastrowid
        
        for item in carrito:
            # 2. Registrar el detalle de los productos que entraron
            cursor.execute("""
                INSERT INTO detalles_compra (compra_id, producto_id, almacen_destino_id, cantidad, costo_unitario) 
                VALUES (?, ?, ?, ?, ?)
            """, (compra_id, item['id'], almacen_id, item['cantidad'], item['costo']))
            
            # 3. Sumar el Stock Físico en el Almacén Destino
            # Verificamos si ya existe el producto en ese almacén
            cursor.execute("SELECT id FROM inventario_almacenes WHERE producto_id = ? AND almacen_id = ?", (item['id'], almacen_id))
            if cursor.fetchone():
                cursor.execute("UPDATE inventario_almacenes SET cantidad = cantidad + ? WHERE producto_id = ? AND almacen_id = ?", (item['cantidad'], item['id'], almacen_id))
            else:
                cursor.execute("INSERT INTO inventario_almacenes (producto_id, almacen_id, cantidad) VALUES (?, ?, ?)", (item['id'], almacen_id, item['cantidad']))
            
            # 4. Actualizar el Costo de Compra del Producto (UPSERT)
            cursor.execute("""
                INSERT INTO productos_proveedores (producto_id, proveedor_id, precio_costo, fecha_actualizacion)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(producto_id, proveedor_id) 
                DO UPDATE SET precio_costo=excluded.precio_costo, fecha_actualizacion=CURRENT_TIMESTAMP;
            """, (item['id'], proveedor_id, item['costo']))

            # 5. Registrar el movimiento en el KARDEX
            motivo = f"Compra. Fac. Prov: {nro_factura}" if nro_factura else f"Ingreso de Compra #{compra_id}"
            cursor.execute("""
                INSERT INTO movimientos_inventario (producto_id, almacen_destino_id, tipo_movimiento, cantidad, motivo, usuario_id)
                VALUES (?, ?, 'ENTRADA', ?, ?, ?)
            """, (item['id'], almacen_id, item['cantidad'], motivo, usuario_id))
            
        conn.commit()
        return True, "Compra registrada. Stock, costos y Kardex actualizados."
    except Exception as e:
        conn.rollback() 
        return False, f"Error al procesar compra: {str(e)}"
    finally:
        conn.close()