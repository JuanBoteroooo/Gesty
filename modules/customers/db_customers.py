from database.connection import connect

def obtener_clientes():
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id, c.documento, c.nombre, c.telefono, c.direccion, c.lista_precio_id, lp.nombre as lista_precio
        FROM clientes c LEFT JOIN listas_precios lp ON c.lista_precio_id = lp.id ORDER BY c.nombre
    """)
    res = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return res

def guardar_cliente(documento, nombre, telefono, direccion, lista_precio_id):
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO clientes (documento, nombre, telefono, direccion, lista_precio_id) VALUES (?, ?, ?, ?, ?)", (documento, nombre, telefono, direccion, lista_precio_id))
        conn.commit()
        return True, "Cliente registrado exitosamente."
    except Exception as e:
        return False, f"Error (¿Documento duplicado?): {str(e)}"
    finally: conn.close()

def editar_cliente(id_cli, documento, nombre, telefono, direccion, lista_precio_id):
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE clientes SET documento=?, nombre=?, telefono=?, direccion=?, lista_precio_id=? WHERE id=?", (documento, nombre, telefono, direccion, lista_precio_id, id_cli))
        conn.commit()
        return True, "Cliente actualizado correctamente."
    except Exception as e:
        return False, f"Error al actualizar: {str(e)}"
    finally: conn.close()

def eliminar_cliente(id_cliente):
    conn = connect()
    cursor = conn.cursor()
    try:
        if id_cliente == 1: return False, "No puedes eliminar al 'Cliente Mostrador'."
        cursor.execute("DELETE FROM clientes WHERE id = ?", (id_cliente,))
        conn.commit()
        return True, "Cliente eliminado."
    except Exception as e:
        return False, "No se puede eliminar: El cliente tiene facturas asociadas."
    finally: conn.close()