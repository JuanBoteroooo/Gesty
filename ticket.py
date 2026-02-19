from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
import os

def generar_pdf(id_despacho, cliente, items):
    """
    Genera un archivo PDF con la nota de entrega.
    cliente: dict {nombre, telefono, direccion}
    items: list of dicts {nombre, cantidad}
    """
    nombre_archivo = f"ticket_despacho_{id_despacho}.pdf"
    c = canvas.Canvas(nombre_archivo, pagesize=A4)
    width, height = A4

    # --- ENCABEZADO ---
    c.setFont("Helvetica-Bold", 20)
    c.drawString(2*cm, height - 2*cm, "FERRETERÍA - NOTA DE ENTREGA")
    
    c.setFont("Helvetica", 10)
    c.drawString(2*cm, height - 3*cm, f"Despacho N°: {id_despacho}")
    c.drawString(2*cm, height - 3.5*cm, f"Fecha: {cliente.get('fecha', 'Hoy')}")

    # --- DATOS DEL CLIENTE ---
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, height - 5*cm, "Datos del Cliente:")
    
    c.setFont("Helvetica", 12)
    c.drawString(2*cm, height - 5.8*cm, f"Nombre: {cliente['nombre']}")
    c.drawString(2*cm, height - 6.4*cm, f"Teléfono: {cliente['telefono']}")
    c.drawString(2*cm, height - 7.0*cm, f"Dirección: {cliente['direccion']}")

    # --- TABLA DE PRODUCTOS ---
    y_position = height - 9*cm
    
    # Encabezados de tabla
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, y_position, "CANT.")
    c.drawString(5*cm, y_position, "DESCRIPCIÓN DEL PRODUCTO")
    c.line(2*cm, y_position - 0.2*cm, 19*cm, y_position - 0.2*cm)
    
    y_position -= 1*cm
    c.setFont("Helvetica", 12)

    total_items = 0

    for item in items:
        # Escribir cantidad y nombre
        c.drawString(2.5*cm, y_position, str(item['cantidad']))
        c.drawString(5*cm, y_position, item['nombre'])
        
        total_items += int(item['cantidad'])
        y_position -= 0.8*cm

        # Si se acaba la hoja (caso borde), creamos nueva página (simplificado)
        if y_position < 2*cm:
            c.showPage()
            y_position = height - 2*cm

    # --- PIE DE PÁGINA ---
    c.line(2*cm, y_position + 0.5*cm, 19*cm, y_position + 0.5*cm)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, y_position - 1*cm, f"Total Artículos Entregados: {total_items}")
    
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(2*cm, 2*cm, "Gracias por su preferencia. Documento de control interno.")

    c.save()
    
    # Intentar abrir el PDF automáticamente (solo funciona en Windows)
    try:
        os.startfile(nombre_archivo)
    except:
        pass # Si no es Windows o falla, no pasa nada