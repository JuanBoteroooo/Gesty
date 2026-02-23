from database.connection import connect

def verificar_credenciales(usuario, password):
    """Verifica si el usuario y la contraseña existen en la base de datos"""
    conn = connect()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT u.id, u.nombre, u.usuario, u.rol_id, r.nombre as rol_nombre
        FROM usuarios u
        JOIN roles r ON u.rol_id = r.id
        WHERE u.usuario = ? AND u.password = ? AND u.estado = 1
    """, (usuario, password))
    
    user = cursor.fetchone()
    conn.close()

    if user:
        return True, dict(user)
    else:
        return False, "Usuario o contraseña incorrectos. (O el usuario está inactivo)"