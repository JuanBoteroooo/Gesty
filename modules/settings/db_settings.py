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
        # Si esta nueva moneda es la principal, quitamos el status a las demás
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

def eliminar_moneda(id_moneda):
    conn = connect()
    cursor = conn.cursor()
    try:
        # Validar que no se elimine la moneda principal
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