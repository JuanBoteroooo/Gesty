# logica.py
import sqlite3
from database_setup import DB_NAME

def conectar():
    return sqlite3.connect(DB_NAME)

# --- GESTIÓN DE PRODUCTOS ---

def crear_producto(codigo, nombre, cantidad, stock_minimo):
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO productos (codigo, nombre, cantidad_actual, cantidad_minima)
            VALUES (?, ?, ?, ?)
        """, (codigo.upper(), nombre, cantidad, stock_minimo))
        conn.commit()
        return True, "Producto creado exitosamente."
    except sqlite3.IntegrityError:
        return False, "Error: El código del producto ya existe."
    except Exception as e:
        return False, f"Error desconocido: {e}"
    finally:
        conn.close()

def obtener_productos(filtro=None):
    """Devuelve todos los productos o busca por nombre/código."""
    conn = conectar()
    conn.row_factory = sqlite3.Row # Para acceder a columnas por nombre
    cursor = conn.cursor()
    
    if filtro:
        filtro = f"%{filtro}%"
        cursor.execute("""
            SELECT * FROM productos 
            WHERE nombre LIKE ? OR codigo LIKE ?
            ORDER BY nombre
        """, (filtro, filtro))
    else:
        cursor.execute("SELECT * FROM productos ORDER BY nombre")
        
    resultado = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return resultado

def editar_producto_completo(id_prod, codigo, nombre, stock, minimo):
    """Permite editar todos los datos de un producto existente"""
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE productos 
            SET codigo = ?, nombre = ?, cantidad_actual = ?, cantidad_minima = ?
            WHERE id = ?
        """, (codigo, nombre, stock, minimo, id_prod))
        conn.commit()
        return True, "Producto actualizado correctamente."
    except sqlite3.IntegrityError:
        return False, "Error: El código ya está en uso por otro producto."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def agregar_stock(id_prod, cantidad_extra):
    """Suma stock a un producto existente (entrada de mercancía)."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE productos SET cantidad_actual = cantidad_actual + ? WHERE id = ?", (cantidad_extra, id_prod))
    conn.commit()
    conn.close()

def eliminar_producto(id_prod):
    conn = conectar()
    cursor = conn.cursor()
    # Nota: Si el producto ya tiene despachos asociados, SQLite podría bloquear esto 
    # si no configuramos ON DELETE CASCADE, pero por seguridad es mejor no borrar historial.
    try:
        cursor.execute("DELETE FROM productos WHERE id = ?", (id_prod,))
        conn.commit()
        return True, "Eliminado"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def obtener_alertas_stock():
    """Retorna productos donde el stock actual <= stock minimo."""
    conn = conectar()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM productos WHERE cantidad_actual <= cantidad_minima")
    alertas = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return alertas

# --- GESTIÓN DE DESPACHOS (TICKETS) ---

def registrar_despacho(cliente_data, items_despacho):
    """
    cliente_data: dict {'nombre': 'Juan', 'telefono': '555', 'direccion': 'Calle 1'}
    items_despacho: lista de dicts [{'id': 1, 'cantidad': 2}, ...]
    """
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        # Iniciamos transacción (todo o nada)
        cursor.execute("BEGIN")
        
        # 1. Crear el despacho (Cabecera)
        cursor.execute("""
            INSERT INTO despachos (cliente_nombre, cliente_telefono, cliente_direccion)
            VALUES (?, ?, ?)
        """, (cliente_data['nombre'], cliente_data['telefono'], cliente_data['direccion']))
        
        despacho_id = cursor.lastrowid
        
        # 2. Procesar cada item
        for item in items_despacho:
            prod_id = item['id']
            cantidad_solicitada = int(item['cantidad'])
            
            # Verificar stock actual
            cursor.execute("SELECT cantidad_actual FROM productos WHERE id = ?", (prod_id,))
            stock_actual = cursor.fetchone()[0]
            
            if stock_actual < cantidad_solicitada:
                raise ValueError(f"Stock insuficiente para producto ID {prod_id}. Disponible: {stock_actual}")
            
            # Restar inventario
            cursor.execute("UPDATE productos SET cantidad_actual = cantidad_actual - ? WHERE id = ?", (cantidad_solicitada, prod_id))
            
            # Guardar detalle
            cursor.execute("""
                INSERT INTO detalles_despacho (despacho_id, producto_id, cantidad)
                VALUES (?, ?, ?)
            """, (despacho_id, prod_id, cantidad_solicitada))
            
        conn.commit() # Confirmar cambios
        return True, despacho_id
        
    except ValueError as ve:
        conn.rollback() # Deshacer todo si falta stock
        return False, str(ve)
    except Exception as e:
        conn.rollback()
        return False, f"Error en base de datos: {e}"
    finally:
        conn.close()