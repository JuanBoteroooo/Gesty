from database.connection import connect

# ==========================================
# LECTURA DE DATOS (TABLA PRINCIPAL)
# ==========================================
def obtener_productos():
    """Trae todos los productos calculando su stock total y agrupando sus precios"""
    conn = connect()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT p.id, p.codigo, p.nombre, p.stock_minimo,
               d.id as departamento_id, d.nombre as categoria,
               prov.id as proveedor_id, prov.nombre as proveedor_nombre,
               COALESCE((SELECT precio_costo FROM productos_proveedores WHERE producto_id = p.id ORDER BY fecha_actualizacion DESC LIMIT 1), 0) as costo,
               COALESCE((SELECT SUM(cantidad) FROM inventario_almacenes WHERE producto_id = p.id), 0) as stock_total
        FROM productos p
        LEFT JOIN departamentos d ON p.departamento_id = d.id
        LEFT JOIN proveedores prov ON p.proveedor_id = prov.id
        ORDER BY p.id DESC
    """)
    productos_base = [dict(row) for row in cursor.fetchall()]

    cursor.execute("SELECT producto_id, lista_precio_id, precio_venta FROM precios_producto")
    precios_rows = cursor.fetchall()
    
    mapa_precios = {}
    for r in precios_rows:
        pid = r['producto_id']
        if pid not in mapa_precios:
            mapa_precios[pid] = {}
        mapa_precios[pid][r['lista_precio_id']] = r['precio_venta']

    for prod in productos_base:
        prod['precios'] = mapa_precios.get(prod['id'], {})
        
    conn.close()
    return productos_base

def obtener_precios_producto(producto_id):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT lista_precio_id, precio_venta FROM precios_producto WHERE producto_id = ?", (producto_id,))
    res = {row['lista_precio_id']: row['precio_venta'] for row in cursor.fetchall()}
    conn.close()
    return res

def obtener_stock_por_almacen(producto_id):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT almacen_id, cantidad FROM inventario_almacenes WHERE producto_id = ?", (producto_id,))
    res = {row['almacen_id']: row['cantidad'] for row in cursor.fetchall()}
    conn.close()
    return res

# ==========================================
# CRUD DE PRODUCTOS (CREAR, EDITAR, ELIMINAR)
# ==========================================
def guardar_producto(codigo, nombre, departamento_id, proveedor_id, costo, precios_dict, stock_dict, stock_min):
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO productos (codigo, nombre, departamento_id, proveedor_id, stock_minimo) 
            VALUES (?, ?, ?, ?, ?)
        """, (codigo, nombre, departamento_id, proveedor_id, stock_min))
        producto_id = cursor.lastrowid
        
        # 🔥 LÓGICA DE CÓDIGOS DE BARRA 🔥
        codigo_final = codigo
        if not codigo or str(codigo).strip() == "":
            codigo_final = f"PRD-{producto_id:05d}"
            cursor.execute("UPDATE productos SET codigo = ? WHERE id = ?", (codigo_final, producto_id))
            
        # Intentamos generar la imagen del código para imprimir
        try:
            from utils.barcode_gen import generar_e_imprimir_codigo
            generar_e_imprimir_codigo(codigo_final, nombre)
        except Exception as e:
            print(f"Aviso: No se pudo generar la imagen del código de barras ({e})")
        
        cursor.execute("INSERT INTO productos_proveedores (producto_id, proveedor_id, precio_costo) VALUES (?, ?, ?)", 
                       (producto_id, proveedor_id, costo))
        
        for lista_id, precio in precios_dict.items():
            cursor.execute("INSERT INTO precios_producto (producto_id, lista_precio_id, precio_venta) VALUES (?, ?, ?)", 
                           (producto_id, lista_id, precio))
            
        for almacen_id, cantidad in stock_dict.items():
            if cantidad > 0:
                cursor.execute("INSERT INTO inventario_almacenes (producto_id, almacen_id, cantidad) VALUES (?, ?, ?)", 
                               (producto_id, almacen_id, cantidad))
                
                cursor.execute("""
                    INSERT INTO movimientos_inventario (producto_id, almacen_destino_id, tipo_movimiento, cantidad, motivo, usuario_id)
                    VALUES (?, ?, 'ENTRADA', ?, 'Stock Inicial del Sistema', 1)
                """, (producto_id, almacen_id, cantidad))

        conn.commit()
        return True, "Producto guardado y stock inicializado correctamente."
    except Exception as e:
        conn.rollback()
        return False, f"Error (¿Código duplicado?): {str(e)}"
    finally:
        conn.close()

def editar_producto(producto_id, codigo, nombre, departamento_id, proveedor_id, costo, precios_dict, stock_dict, stock_min):
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE productos SET codigo = ?, nombre = ?, departamento_id = ?, proveedor_id = ?, stock_minimo = ?
            WHERE id = ?
        """, (codigo, nombre, departamento_id, proveedor_id, stock_min, producto_id))
        
        cursor.execute("""
            INSERT INTO productos_proveedores (producto_id, proveedor_id, precio_costo, fecha_actualizacion)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(producto_id, proveedor_id) 
            DO UPDATE SET precio_costo=excluded.precio_costo, fecha_actualizacion=CURRENT_TIMESTAMP;
        """, (producto_id, proveedor_id, costo))

        cursor.execute("DELETE FROM precios_producto WHERE producto_id = ?", (producto_id,))
        for lista_id, precio in precios_dict.items():
            cursor.execute("INSERT INTO precios_producto (producto_id, lista_precio_id, precio_venta) VALUES (?, ?, ?)", 
                           (producto_id, lista_id, precio))
            
        for almacen_id, nueva_cantidad in stock_dict.items():
            cursor.execute("SELECT cantidad FROM inventario_almacenes WHERE producto_id = ? AND almacen_id = ?", (producto_id, almacen_id))
            row = cursor.fetchone()
            
            if row:
                stock_actual = row['cantidad']
                diferencia = nueva_cantidad - stock_actual
                
                if diferencia != 0: 
                    cursor.execute("UPDATE inventario_almacenes SET cantidad = ? WHERE producto_id = ? AND almacen_id = ?", (nueva_cantidad, producto_id, almacen_id))
                    
                    tipo_mov = 'AJUSTE_POSITIVO' if diferencia > 0 else 'AJUSTE_NEGATIVO'
                    cursor.execute("""
                        INSERT INTO movimientos_inventario (producto_id, almacen_destino_id, tipo_movimiento, cantidad, motivo, usuario_id)
                        VALUES (?, ?, ?, ?, 'Ajuste manual desde ficha técnica', 1)
                    """, (producto_id, almacen_id, tipo_mov, abs(diferencia)))
            else:
                if nueva_cantidad > 0:
                    cursor.execute("INSERT INTO inventario_almacenes (producto_id, almacen_id, cantidad) VALUES (?, ?, ?)", (producto_id, almacen_id, nueva_cantidad))
                    cursor.execute("""
                        INSERT INTO movimientos_inventario (producto_id, almacen_destino_id, tipo_movimiento, cantidad, motivo, usuario_id)
                        VALUES (?, ?, 'ENTRADA', ?, 'Ingreso manual desde ficha', 1)
                    """, (producto_id, almacen_id, nueva_cantidad))

        conn.commit()
        return True, "Ficha del producto actualizada correctamente."
    except Exception as e:
        conn.rollback()
        return False, f"Error al editar: {str(e)}"
    finally:
        conn.close()

def eliminar_producto(producto_id):
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM productos WHERE id = ?", (producto_id,))
        conn.commit()
        return True, "Producto eliminado definitivamente."
    except Exception as e:
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

# ==========================================
# KARDEX, AJUSTES Y TRASPASOS
# ==========================================
def registrar_movimiento(producto_id, almacen_origen_id, almacen_destino_id, tipo_movimiento, cantidad, motivo, usuario_id):
    conn = connect()
    cursor = conn.cursor()
    try:
        if tipo_movimiento in ['AJUSTE_NEGATIVO', 'TRASPASO']:
            cursor.execute("SELECT cantidad FROM inventario_almacenes WHERE producto_id = ? AND almacen_id = ?", (producto_id, almacen_origen_id))
            row = cursor.fetchone()
            stock_actual = row['cantidad'] if row else 0
            if stock_actual < cantidad:
                return False, f"Stock insuficiente en el almacén de origen. Disponible: {stock_actual}"

        cursor.execute("""
            INSERT INTO movimientos_inventario (producto_id, almacen_origen_id, almacen_destino_id, tipo_movimiento, cantidad, motivo, usuario_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (producto_id, almacen_origen_id, almacen_destino_id, tipo_movimiento, cantidad, motivo, usuario_id))

        if tipo_movimiento == 'AJUSTE_POSITIVO':
            cursor.execute("SELECT id FROM inventario_almacenes WHERE producto_id = ? AND almacen_id = ?", (producto_id, almacen_origen_id))
            if cursor.fetchone():
                cursor.execute("UPDATE inventario_almacenes SET cantidad = cantidad + ? WHERE producto_id = ? AND almacen_id = ?", (cantidad, producto_id, almacen_origen_id))
            else:
                cursor.execute("INSERT INTO inventario_almacenes (producto_id, almacen_id, cantidad) VALUES (?, ?, ?)", (producto_id, almacen_origen_id, cantidad))
            
        elif tipo_movimiento == 'AJUSTE_NEGATIVO':
            cursor.execute("UPDATE inventario_almacenes SET cantidad = cantidad - ? WHERE producto_id = ? AND almacen_id = ?", (cantidad, producto_id, almacen_origen_id))
            
        elif tipo_movimiento == 'TRASPASO':
            cursor.execute("UPDATE inventario_almacenes SET cantidad = cantidad - ? WHERE producto_id = ? AND almacen_id = ?", (cantidad, producto_id, almacen_origen_id))
            
            cursor.execute("SELECT id FROM inventario_almacenes WHERE producto_id = ? AND almacen_id = ?", (producto_id, almacen_destino_id))
            if cursor.fetchone():
                cursor.execute("UPDATE inventario_almacenes SET cantidad = cantidad + ? WHERE producto_id = ? AND almacen_id = ?", (cantidad, producto_id, almacen_destino_id))
            else:
                cursor.execute("INSERT INTO inventario_almacenes (producto_id, almacen_id, cantidad) VALUES (?, ?, ?)", (producto_id, almacen_destino_id, cantidad))
                
        conn.commit()
        return True, "Movimiento registrado correctamente."
    except Exception as e:
        conn.rollback()
        return False, f"Error de base de datos: {str(e)}"
    finally:
        conn.close()

def obtener_historial_kardex(producto_id):
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