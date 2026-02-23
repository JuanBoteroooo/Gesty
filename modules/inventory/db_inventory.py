from database.connection import connect

def obtener_departamentos():
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre FROM departamentos ORDER BY nombre")
    res = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return res

def obtener_proveedores():
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre FROM proveedores ORDER BY nombre")
    res = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return res

def obtener_almacenes():
    """Trae la lista de almacenes disponibles (Ej: Tienda, Depósito)"""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre FROM almacenes ORDER BY id")
    res = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return res

def obtener_stock_por_almacen(producto_id):
    """Devuelve un diccionario {almacen_id: cantidad} para un producto específico"""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT almacen_id, cantidad FROM inventario_almacenes WHERE producto_id = ?", (producto_id,))
    res = {row['almacen_id']: row['cantidad'] for row in cursor.fetchall()}
    conn.close()
    return res

def obtener_precios_producto(producto_id):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT lista_precio_id, precio_venta FROM precios_producto WHERE producto_id = ?", (producto_id,))
    res = {row['lista_precio_id']: row['precio_venta'] for row in cursor.fetchall()}
    conn.close()
    return res

def obtener_productos():
    conn = connect()
    cursor = conn.cursor()
    
    # 1. Traer datos base y calcular el STOCK TOTAL (suma de todos los almacenes)
    cursor.execute("""
        SELECT 
            p.id, 
            p.codigo, 
            p.nombre, 
            p.cantidad_minima as stock_minimo,
            p.departamento_id,
            d.nombre as categoria,
            COALESCE((SELECT SUM(cantidad) FROM inventario_almacenes WHERE producto_id = p.id), 0) as stock_total,
            COALESCE(pp.precio_costo, 0.0) as costo,
            pp.proveedor_id,
            COALESCE(prov.nombre, 'Sin Proveedor') as proveedor_nombre
        FROM productos p
        LEFT JOIN departamentos d ON p.departamento_id = d.id
        LEFT JOIN productos_proveedores pp ON pp.producto_id = p.id
        LEFT JOIN proveedores prov ON prov.id = pp.proveedor_id
        ORDER BY p.nombre
    """)
    productos = [dict(row) for row in cursor.fetchall()]

    # 2. Buscar TODOS los precios en la BD para insertarlos en el diccionario
    cursor.execute("SELECT producto_id, lista_precio_id, precio_venta FROM precios_producto")
    precios_bd = cursor.fetchall()
    
    mapa_precios = {}
    for row in precios_bd:
        p_id = row['producto_id']
        l_id = row['lista_precio_id']
        precio = row['precio_venta']
        if p_id not in mapa_precios:
            mapa_precios[p_id] = {}
        mapa_precios[p_id][l_id] = precio

    # 3. Empaquetar los precios dentro de cada producto
    for prod in productos:
        prod['precios'] = mapa_precios.get(prod['id'], {})
        
    conn.close()
    return productos

def guardar_producto(codigo, nombre, departamento_id, proveedor_id, costo, diccionario_precios, diccionario_stock, stock_minimo):
    """Guarda un producto distribuyendo su stock en varios almacenes"""
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO productos (codigo, nombre, departamento_id, cantidad_minima) 
            VALUES (?, ?, ?, ?)
        """, (codigo, nombre, departamento_id, stock_minimo))
        
        prod_id = cursor.lastrowid 
        
        # Guardar stock por almacén dinámicamente
        for almacen_id, cantidad in diccionario_stock.items():
            cursor.execute("INSERT INTO inventario_almacenes (producto_id, almacen_id, cantidad) VALUES (?, ?, ?)", (prod_id, almacen_id, cantidad))
        
        for lista_id, precio in diccionario_precios.items():
            cursor.execute("INSERT INTO precios_producto (producto_id, lista_precio_id, precio_venta) VALUES (?, ?, ?)", (prod_id, lista_id, precio))
        
        cursor.execute("INSERT INTO productos_proveedores (producto_id, proveedor_id, precio_costo) VALUES (?, ?, ?)", (prod_id, proveedor_id, costo))
        
        conn.commit()
        return True, "Producto registrado exitosamente en todos los almacenes."
    except Exception as e:
        conn.rollback() 
        return False, f"Error (¿Código duplicado?): {str(e)}"
    finally:
        conn.close()

def editar_producto(id_prod, codigo, nombre, departamento_id, proveedor_id, costo, diccionario_precios, diccionario_stock, stock_minimo):
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE productos SET codigo=?, nombre=?, departamento_id=?, cantidad_minima=? WHERE id=?
        """, (codigo, nombre, departamento_id, stock_minimo, id_prod))
        
        # Actualizar stock por almacén (Insertar si no existía, actualizar si ya estaba)
        for almacen_id, cantidad in diccionario_stock.items():
            cursor.execute("""
                INSERT INTO inventario_almacenes (producto_id, almacen_id, cantidad) VALUES (?, ?, ?)
                ON CONFLICT(producto_id, almacen_id) DO UPDATE SET cantidad=?
            """, (id_prod, almacen_id, cantidad, cantidad))
        
        for lista_id, precio in diccionario_precios.items():
            cursor.execute("""
                INSERT INTO precios_producto (producto_id, lista_precio_id, precio_venta) VALUES (?, ?, ?)
                ON CONFLICT(producto_id, lista_precio_id) DO UPDATE SET precio_venta=?
            """, (id_prod, lista_id, precio, precio))
        
        cursor.execute("DELETE FROM productos_proveedores WHERE producto_id = ?", (id_prod,))
        cursor.execute("INSERT INTO productos_proveedores (producto_id, proveedor_id, precio_costo) VALUES (?, ?, ?)", (id_prod, proveedor_id, costo))
        
        conn.commit()
        return True, "Ficha del producto actualizada correctamente."
    except Exception as e:
        conn.rollback()
        return False, f"Error al actualizar: {str(e)}"
    finally:
        conn.close()

def eliminar_producto(id_prod):
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM productos WHERE id = ?", (id_prod,))
        conn.commit()
        return True, "Producto eliminado."
    except Exception as e:
        return False, f"No se puede eliminar: {e}"
    finally:
        conn.close()

# ==========================================
# 🔥 NUEVO: KARDEX, AJUSTES Y TRASPASOS
# ==========================================

def registrar_movimiento(producto_id, almacen_origen_id, almacen_destino_id, tipo_movimiento, cantidad, motivo, usuario_id):
    """Procesa un Ajuste o Traspaso y deja el registro en el Kardex"""
    conn = connect()
    cursor = conn.cursor()
    try:
        # 1. Validar que haya stock suficiente si es una salida o un traspaso
        if tipo_movimiento in ['AJUSTE_NEGATIVO', 'TRASPASO']:
            cursor.execute("SELECT cantidad FROM inventario_almacenes WHERE producto_id = ? AND almacen_id = ?", (producto_id, almacen_origen_id))
            row = cursor.fetchone()
            stock_actual = row['cantidad'] if row else 0
            if stock_actual < cantidad:
                return False, f"Stock insuficiente en el almacén de origen. Disponible: {stock_actual}"

        # 2. Registrar el movimiento en el Kardex (Historial intocable)
        cursor.execute("""
            INSERT INTO movimientos_inventario (producto_id, almacen_origen_id, almacen_destino_id, tipo_movimiento, cantidad, motivo, usuario_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (producto_id, almacen_origen_id, almacen_destino_id, tipo_movimiento, cantidad, motivo, usuario_id))

        # 3. Mover la mercancía físicamente en las tablas
        if tipo_movimiento == 'AJUSTE_POSITIVO':
            # Sumar al almacén elegido
            cursor.execute("UPDATE inventario_almacenes SET cantidad = cantidad + ? WHERE producto_id = ? AND almacen_id = ?", (cantidad, producto_id, almacen_origen_id))
            
        elif tipo_movimiento == 'AJUSTE_NEGATIVO':
            # Restar del almacén elegido
            cursor.execute("UPDATE inventario_almacenes SET cantidad = cantidad - ? WHERE producto_id = ? AND almacen_id = ?", (cantidad, producto_id, almacen_origen_id))
            
        elif tipo_movimiento == 'TRASPASO':
            # Restar del origen
            cursor.execute("UPDATE inventario_almacenes SET cantidad = cantidad - ? WHERE producto_id = ? AND almacen_id = ?", (cantidad, producto_id, almacen_origen_id))
            
            # Verificar si el producto ya existe en el destino (si no, crearlo con ese stock)
            cursor.execute("SELECT id FROM inventario_almacenes WHERE producto_id = ? AND almacen_id = ?", (producto_id, almacen_destino_id))
            if cursor.fetchone():
                cursor.execute("UPDATE inventario_almacenes SET cantidad = cantidad + ? WHERE producto_id = ? AND almacen_id = ?", (cantidad, producto_id, almacen_destino_id))
            else:
                cursor.execute("INSERT INTO inventario_almacenes (producto_id, almacen_id, cantidad) VALUES (?, ?, ?)", (producto_id, almacen_destino_id, cantidad))
                
        conn.commit()
        return True, "Movimiento de inventario procesado y registrado correctamente."
    except Exception as e:
        conn.rollback()
        return False, f"Error de base de datos: {str(e)}"
    finally:
        conn.close()

def obtener_historial_kardex(producto_id):
    """Obtiene toda la vida e historia de un producto"""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.fecha, m.tipo_movimiento, m.cantidad, m.motivo, 
               ao.nombre as almacen_origen, ad.nombre as almacen_destino, u.usuario
        FROM movimientos_inventario m
        LEFT JOIN almacenes ao ON m.almacen_origen_id = ao.id
        LEFT JOIN almacenes ad ON m.almacen_destino_id = ad.id
        LEFT JOIN usuarios u ON m.usuario_id = u.id
        WHERE m.producto_id = ?
        ORDER BY m.id DESC
    """, (producto_id,))
    res = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return res