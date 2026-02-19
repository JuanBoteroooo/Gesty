from database.connection import connect

def obtener_proveedores():
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM proveedores ORDER BY nombre")
    resultados = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return resultados

def guardar_proveedor(documento, nombre, telefono, direccion):
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO proveedores (documento, nombre, telefono, direccion) VALUES (?, ?, ?, ?)", (documento, nombre, telefono, direccion))
        conn.commit()
        return True, "Proveedor registrado exitosamente."
    except Exception as e:
        return False, f"Error (¿Documento duplicado?): {str(e)}"
    finally:
        conn.close()

def editar_proveedor(id_prov, documento, nombre, telefono, direccion):
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE proveedores SET documento=?, nombre=?, telefono=?, direccion=? WHERE id=?", (documento, nombre, telefono, direccion, id_prov))
        conn.commit()
        return True, "Proveedor actualizado correctamente."
    except Exception as e:
        return False, f"Error al actualizar: {str(e)}"
    finally:
        conn.close()

def eliminar_proveedor(id_proveedor):
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM proveedores WHERE id = ?", (id_proveedor,))
        conn.commit()
        return True, "Proveedor eliminado del sistema."
    except Exception as e:
        return False, "No se puede eliminar: El proveedor tiene productos asociados."
    finally:
        conn.close()