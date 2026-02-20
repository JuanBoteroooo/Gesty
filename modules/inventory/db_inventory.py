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
    
    # 1. Traer datos base del producto
    cursor.execute("""
        SELECT 
            p.id, 
            p.codigo, 
            p.nombre, 
            p.cantidad_minima as stock_minimo,
            p.departamento_id,
            d.nombre as categoria,
            COALESCE(ia.cantidad, 0) as stock,
            COALESCE(pp.precio_costo, 0.0) as costo,
            pp.proveedor_id,
            COALESCE(prov.nombre, 'Sin Proveedor') as proveedor_nombre
        FROM productos p
        LEFT JOIN departamentos d ON p.departamento_id = d.id
        LEFT JOIN inventario_almacenes ia ON ia.producto_id = p.id AND ia.almacen_id = 1
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

def guardar_producto(codigo, nombre, departamento_id, proveedor_id, costo, diccionario_precios, stock, stock_minimo):
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO productos (codigo, nombre, departamento_id, cantidad_minima) 
            VALUES (?, ?, ?, ?)
        """, (codigo, nombre, departamento_id, stock_minimo))
        
        prod_id = cursor.lastrowid 
        
        cursor.execute("INSERT INTO inventario_almacenes (producto_id, almacen_id, cantidad) VALUES (?, 1, ?)", (prod_id, stock))
        
        for lista_id, precio in diccionario_precios.items():
            cursor.execute("INSERT INTO precios_producto (producto_id, lista_precio_id, precio_venta) VALUES (?, ?, ?)", (prod_id, lista_id, precio))
        
        cursor.execute("INSERT INTO productos_proveedores (producto_id, proveedor_id, precio_costo) VALUES (?, ?, ?)", (prod_id, proveedor_id, costo))
        
        conn.commit()
        return True, "Producto registrado exitosamente."
    except Exception as e:
        conn.rollback() 
        return False, f"Error (¿Código duplicado?): {str(e)}"
    finally:
        conn.close()

def editar_producto(id_prod, codigo, nombre, departamento_id, proveedor_id, costo, diccionario_precios, stock, stock_minimo):
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE productos SET codigo=?, nombre=?, departamento_id=?, cantidad_minima=? WHERE id=?
        """, (codigo, nombre, departamento_id, stock_minimo, id_prod))
        
        cursor.execute("""
            INSERT INTO inventario_almacenes (producto_id, almacen_id, cantidad) VALUES (?, 1, ?)
            ON CONFLICT(producto_id, almacen_id) DO UPDATE SET cantidad=?
        """, (id_prod, stock, stock))
        
        for lista_id, precio in diccionario_precios.items():
            cursor.execute("""
                INSERT INTO precios_producto (producto_id, lista_precio_id, precio_venta) VALUES (?, ?, ?)
                ON CONFLICT(producto_id, lista_precio_id) DO UPDATE SET precio_venta=?
            """, (id_prod, lista_id, precio, precio))
        
        cursor.execute("DELETE FROM productos_proveedores WHERE producto_id = ?", (id_prod,))
        cursor.execute("INSERT INTO productos_proveedores (producto_id, proveedor_id, precio_costo) VALUES (?, ?, ?)", (id_prod, proveedor_id, costo))
        
        conn.commit()
        return True, "Producto actualizado correctamente."
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