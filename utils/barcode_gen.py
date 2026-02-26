import os
import barcode
from barcode.writer import ImageWriter

def generar_e_imprimir_codigo(codigo_texto, nombre_producto):
    """
    Genera una imagen PNG con el código de barras y la guarda en una carpeta.
    codigo_texto: El número o texto del código (Ej: "PROD-001")
    """
    # 1. Crear carpeta si no existe
    carpeta = "codigos_generados"
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)
        
    # 2. Configurar el formato Code128
    ClaseCodigo = barcode.get_barcode_class('code128')
    
    # 3. Generar el código con el texto abajo
    codigo_generado = ClaseCodigo(codigo_texto, writer=ImageWriter())
    
    # 4. Guardar la imagen (le pone el nombre del producto para que lo encuentres fácil)
    nombre_archivo = f"{carpeta}/{codigo_texto}_{nombre_producto.replace(' ', '_')}"
    ruta_final = codigo_generado.save(nombre_archivo)
    
    return ruta_final # Devuelve la ruta, ej: "codigos_generados/PROD-001_Martillo.png"