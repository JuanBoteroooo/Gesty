from database.connection import connect


def obtener_proveedores():
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM proveedores ORDER BY nombre")
    resultados = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return resultados


# ============================================
# CREAR PROVEEDOR
# ============================================
def crear_proveedor(data):
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO proveedores (documento, nombre, telefono, direccion)
            VALUES (?, ?, ?, ?)
            """,
            (
                data["documento"],
                data["nombre"],
                data["telefono"],
                data["direccion"],
            ),
        )
        conn.commit()
        return True, "Proveedor registrado exitosamente."
    except Exception as e:
        return False, f"Error (¿Documento duplicado?): {str(e)}"
    finally:
        conn.close()


# ============================================
# ACTUALIZAR PROVEEDOR
# ============================================
def actualizar_proveedor(id_proveedor, data):
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE proveedores
            SET documento=?, nombre=?, telefono=?, direccion=?
            WHERE id=?
            """,
            (
                data["documento"],
                data["nombre"],
                data["telefono"],
                data["direccion"],
                id_proveedor,
            ),
        )
        conn.commit()
        return True, "Proveedor actualizado correctamente."
    except Exception as e:
        return False, f"Error al actualizar: {str(e)}"
    finally:
        conn.close()


# ============================================
# ELIMINAR PROVEEDOR
# ============================================
def eliminar_proveedor(id_proveedor):
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "DELETE FROM proveedores WHERE id = ?",
            (id_proveedor,),
        )
        conn.commit()
        return True, "Proveedor eliminado del sistema."
    except Exception:
        return False, "No se puede eliminar: El proveedor tiene productos asociados."
    finally:
        conn.close()