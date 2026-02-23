from database.connection import connect

# ==========================================
# GESTIÓN DE MONEDAS
# ==========================================
def obtener_monedas():
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM monedas ORDER BY id")
    resultados = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return resultados

def guardar_moneda(nombre, simbolo, tasa_cambio, es_principal=0):
    conn = connect()
    cursor = conn.cursor()
    try:
        if es_principal == 1:
            cursor.execute("UPDATE monedas SET es_principal = 0")
            
        cursor.execute("""
            INSERT INTO monedas (nombre, simbolo, tasa_cambio, es_principal)
            VALUES (?, ?, ?, ?)
        """, (nombre, simbolo, tasa_cambio, es_principal))
        conn.commit()
        return True, "Moneda registrada con éxito."
    except Exception as e:
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def actualizar_moneda(id_moneda, nombre, simbolo, tasa_cambio, es_principal=0):
    conn = connect()
    cursor = conn.cursor()
    try:
        if es_principal == 1:
            cursor.execute("UPDATE monedas SET es_principal = 0")
            
        cursor.execute("""
            UPDATE monedas 
            SET nombre = ?, simbolo = ?, tasa_cambio = ?, es_principal = ?
            WHERE id = ?
        """, (nombre, simbolo, tasa_cambio, es_principal, id_moneda))
        conn.commit()
        return True, "Tasa de cambio y datos actualizados."
    except Exception as e:
        return False, f"Error al actualizar: {str(e)}"
    finally:
        conn.close()

def eliminar_moneda(id_moneda):
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT es_principal FROM monedas WHERE id = ?", (id_moneda,))
        if cursor.fetchone()['es_principal'] == 1:
            return False, "No puedes eliminar la moneda principal del sistema."
            
        cursor.execute("DELETE FROM monedas WHERE id = ?", (id_moneda,))
        conn.commit()
        return True, "Moneda eliminada."
    except Exception as e:
        return False, f"Error: No se puede borrar si hay ventas con esta moneda. ({e})"
    finally:
        conn.close()

# ==========================================
# GESTIÓN DE LISTAS DE PRECIOS
# ==========================================
def obtener_listas_precios():
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM listas_precios ORDER BY id")
    resultados = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return resultados

def guardar_lista_precio(nombre):
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO listas_precios (nombre) VALUES (?)", (nombre,))
        conn.commit()
        return True, "Lista de precio registrada."
    except Exception as e:
        return False, f"Error (¿Nombre duplicado?): {str(e)}"
    finally:
        conn.close()

def eliminar_lista_precio(id_lista):
    conn = connect()
    cursor = conn.cursor()
    try:
        if id_lista == 1:
            return False, "No puedes eliminar la lista base (Detal)."
        cursor.execute("DELETE FROM listas_precios WHERE id = ?", (id_lista,))
        conn.commit()
        return True, "Lista eliminada."
    except Exception as e:
        return False, f"Error: No se puede borrar si hay clientes usándola. ({e})"
    finally:
        conn.close()

# ==========================================
# GESTIÓN DE DEPARTAMENTOS
# ==========================================
def obtener_departamentos():
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM departamentos ORDER BY id")
    resultados = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return resultados

def guardar_departamento(nombre, descripcion):
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO departamentos (nombre, descripcion) VALUES (?, ?)", (nombre, descripcion))
        conn.commit()
        return True, "Departamento registrado."
    except Exception as e:
        return False, f"Error (¿Nombre duplicado?): {str(e)}"
    finally:
        conn.close()

def eliminar_departamento(id_dep):
    conn = connect()
    cursor = conn.cursor()
    try:
        if id_dep == 1:
            return False, "No puedes eliminar el departamento 'General'."
        cursor.execute("DELETE FROM departamentos WHERE id = ?", (id_dep,))
        conn.commit()
        return True, "Departamento eliminado."
    except Exception as e:
        return False, f"Error: No se puede borrar si hay productos usándolo. ({e})"
    finally:
        conn.close()

# ==========================================
# GESTIÓN DE MÉTODOS DE PAGO
# ==========================================
def obtener_metodos_pago():
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT mp.id, mp.nombre, mp.moneda_id, m.nombre as moneda_nombre, m.simbolo 
        FROM metodos_pago mp
        JOIN monedas m ON mp.moneda_id = m.id
        ORDER BY m.id, mp.nombre
    """)
    res = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return res

def guardar_metodo_pago(nombre, moneda_id):
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO metodos_pago (nombre, moneda_id) VALUES (?, ?)", (nombre, moneda_id))
        conn.commit()
        return True, "Método de pago registrado."
    except Exception as e:
        return False, f"Error: {e}"
    finally:
        conn.close()

def eliminar_metodo_pago(id_metodo):
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM metodos_pago WHERE id = ?", (id_metodo,))
        conn.commit()
        return True, "Método eliminado."
    except Exception as e:
        return False, f"Error: {e}"
    finally:
        conn.close()

# ==========================================
# GESTIÓN DE ALMACENES
# ==========================================
def obtener_almacenes():
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM almacenes ORDER BY id")
    resultados = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return resultados

def guardar_almacen(nombre, ubicacion):
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO almacenes (nombre, ubicacion) VALUES (?, ?)", (nombre, ubicacion))
        conn.commit()
        return True, "Almacén registrado."
    except Exception as e:
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def eliminar_almacen(id_almacen):
    conn = connect()
    cursor = conn.cursor()
    try:
        if id_almacen == 1:
            return False, "No puedes eliminar el Almacén 'Principal'."
        cursor.execute("DELETE FROM almacenes WHERE id = ?", (id_almacen,))
        conn.commit()
        return True, "Almacén eliminado."
    except Exception as e:
        return False, f"Error: No se puede borrar si hay productos usándolo. ({e})"
    finally:
        conn.close()

# ==========================================
# 🔥 NUEVO: GESTIÓN DE USUARIOS Y ROLES
# ==========================================
def obtener_roles():
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre FROM roles ORDER BY id")
    res = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return res

def obtener_usuarios():
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.nombre, u.usuario, u.rol_id, r.nombre as rol_nombre 
        FROM usuarios u 
        JOIN roles r ON u.rol_id = r.id 
        ORDER BY u.id
    """)
    res = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return res

def guardar_usuario(nombre, usuario, password, rol_id):
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO usuarios (nombre, usuario, password, rol_id) VALUES (?, ?, ?, ?)", 
                       (nombre, usuario, password, rol_id))
        conn.commit()
        return True, "Usuario registrado exitosamente."
    except Exception as e:
        return False, f"Error (¿Usuario duplicado?): {str(e)}"
    finally:
        conn.close()

def eliminar_usuario(usuario_id):
    if usuario_id == 1: # Protección de oro
        return False, "Por seguridad, el Administrador Principal (ID 1) no puede ser eliminado."
        
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
        conn.commit()
        return True, "Usuario eliminado."
    except Exception as e:
        return False, f"Error al eliminar usuario: {str(e)}"
    finally:
        conn.close()