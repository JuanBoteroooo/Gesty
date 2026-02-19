import flet as ft
from modules.customers import db_customers
from modules.settings import db_settings  # Importamos para leer las Listas de Precios

def vista_clientes(page: ft.Page):
    COLOR_PRIMARIO = ft.colors.BLUE_800
    COLOR_FONDO_INPUT = ft.colors.BLUE_GREY_50

    def mostrar_mensaje(texto, color="green"):
        snack = ft.SnackBar(content=ft.Text(texto, weight="bold", color="white"), bgcolor=color, duration=3000)
        page.overlay.clear()
        page.overlay.append(snack)
        snack.open = True
        page.update()

    estilo_input = {
        "filled": True,
        "bgcolor": COLOR_FONDO_INPUT,
        "border_color": "transparent",
        "border_radius": 8,
        "height": 50,
        "content_padding": 15,
        "cursor_color": COLOR_PRIMARIO
    }
    
    # NUEVO: Un estilo especial para el Dropdown (sin el cursor_color)
    estilo_dropdown = {
        "filled": True,
        "bgcolor": COLOR_FONDO_INPUT,
        "border_color": "transparent",
        "border_radius": 8,
        "height": 50,
        "content_padding": 15
    }

    # --- CAMPOS DEL FORMULARIO (MODAL) ---
    txt_documento = ft.TextField(label="Documento (Cédula/RIF/DNI)", width=350, **estilo_input)
    txt_nombre = ft.TextField(label="Nombre Completo o Razón Social", width=350, **estilo_input)
    txt_telefono = ft.TextField(label="Teléfono", width=350, **estilo_input)
    txt_direccion = ft.TextField(label="Dirección Físico", width=350, **estilo_input)
    
    # Aplicamos el estilo correcto al Dropdown
    dd_lista_precio = ft.Dropdown(label="Tarifa de Precios", width=350, **estilo_dropdown)

    def cargar_opciones_listas():
        dd_lista_precio.options.clear()
        listas = db_settings.obtener_listas_precios()
        for l in listas:
            dd_lista_precio.options.append(ft.dropdown.Option(key=str(l['id']), text=l['nombre']))
        
        # Seleccionar por defecto la primera lista (Suele ser Detal)
        if listas:
            dd_lista_precio.value = str(listas[0]['id'])

    # --- TABLA DE CLIENTES ---
    tabla_clientes = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("DOCUMENTO", weight="bold", color=ft.colors.BLUE_GREY_600)),
            ft.DataColumn(ft.Text("NOMBRE", weight="bold", color=ft.colors.BLUE_GREY_600)),
            ft.DataColumn(ft.Text("TELÉFONO", weight="bold", color=ft.colors.BLUE_GREY_600)),
            ft.DataColumn(ft.Text("TARIFA ASIGNADA", weight="bold", color=ft.colors.BLUE_GREY_600)),
            ft.DataColumn(ft.Text("ACCIONES", weight="bold", color=ft.colors.BLUE_GREY_600)),
        ],
        rows=[],
        border=ft.border.all(1, ft.colors.GREY_200), border_radius=10,
        heading_row_color=ft.colors.GREY_50, heading_row_height=50, data_row_max_height=55, expand=True
    )

    def cargar_datos():
        tabla_clientes.rows.clear()
        for c in db_customers.obtener_clientes():
            # Chip visual para destacar qué tipo de cliente es (Detal, Mayorista)
            tarifa_chip = ft.Container(
                content=ft.Text(c['lista_precio'] or "Sin asignar", color=COLOR_PRIMARIO, weight="bold", size=11),
                bgcolor=ft.colors.BLUE_50, padding=5, border_radius=4
            )

            # Para el "Cliente Mostrador" (ID 1) desactivamos el botón de borrar
            es_mostrador = (c['id'] == 1)
            boton_borrar = ft.Container(
                content=ft.IconButton(
                    icon=ft.icons.DELETE_OUTLINE, 
                    icon_color="grey" if es_mostrador else "red", 
                    tooltip="No se puede borrar el default" if es_mostrador else "Eliminar",
                    disabled=es_mostrador,
                    on_click=lambda e, x=c['id']: borrar_registro(x)
                ),
                bgcolor=ft.colors.GREY_100 if es_mostrador else ft.colors.RED_50, 
                border_radius=8
            )

            tabla_clientes.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(c['documento'], size=13)),
                    ft.DataCell(ft.Text(c['nombre'], weight="bold", size=14)),
                    ft.DataCell(ft.Text(c['telefono'] or "N/A", size=13, color=ft.colors.GREY_700)),
                    ft.DataCell(tarifa_chip),
                    ft.DataCell(boton_borrar)
                ])
            )
        page.update()

    # --- LÓGICA DEL MODAL ---
    def abrir_dialogo(e):
        cargar_opciones_listas() 
        txt_documento.value = ""
        txt_nombre.value = ""
        txt_telefono.value = ""
        txt_direccion.value = ""
        page.dialog = dialogo_cliente
        dialogo_cliente.open = True
        page.update()

    def guardar_registro(e):
        if not txt_documento.value or not txt_nombre.value or not dd_lista_precio.value:
            mostrar_mensaje("Documento, Nombre y Tarifa son obligatorios.", "red")
            return
            
        exito, msg = db_customers.guardar_cliente(
            txt_documento.value, txt_nombre.value, txt_telefono.value, txt_direccion.value, int(dd_lista_precio.value)
        )
        
        if exito:
            mostrar_mensaje(msg, "green")
            dialogo_cliente.open = False
            cargar_datos()
        else:
            mostrar_mensaje(msg, "red")

    dialogo_cliente = ft.AlertDialog(
        title=ft.Row([ft.Icon(ft.icons.PERSON_ADD, color=COLOR_PRIMARIO), ft.Text("Nuevo Cliente")]),
        content=ft.Container(
            width=400,
            content=ft.Column([
                ft.Text("Datos de contacto", color=ft.colors.GREY_500, size=12),
                txt_documento, txt_nombre, txt_telefono, txt_direccion,
                ft.Divider(color="transparent", height=5),
                ft.Text("Preferencias de venta", color=ft.colors.GREY_500, size=12),
                dd_lista_precio
            ], tight=True)
        ),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: (setattr(dialogo_cliente, 'open', False), page.update())),
            ft.ElevatedButton(
                "Guardar Cliente", bgcolor=COLOR_PRIMARIO, color="white", 
                on_click=guardar_registro, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
            )
        ],
        actions_padding=15
    )

    def borrar_registro(id_cli):
        exito, msg = db_customers.eliminar_cliente(id_cli)
        mostrar_mensaje(msg, "green" if exito else "red")
        if exito: cargar_datos()

    cargar_datos()

    # --- DISEÑO PRINCIPAL (LAYOUT) ---
    boton_nuevo = ft.ElevatedButton(
        "Añadir Cliente",
        icon=ft.icons.ADD,
        bgcolor=COLOR_PRIMARIO,
        color="white",
        height=45,
        on_click=abrir_dialogo,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
    )

    encabezado = ft.Row([
        ft.Row([
            ft.Container(content=ft.Icon(ft.icons.PEOPLE, size=30, color=COLOR_PRIMARIO), padding=10, bgcolor=ft.colors.BLUE_50, border_radius=10),
            ft.Column([
                ft.Text("Directorio de Clientes", size=24, weight="bold", color=ft.colors.BLUE_GREY_900),
                ft.Text("Administra los datos y tarifas asignadas a tus compradores", size=13, color=ft.colors.GREY_500)
            ], spacing=2)
        ]),
        ft.Container(expand=True),
        boton_nuevo
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    contenedor_tabla = ft.Container(
        content=ft.Column([tabla_clientes], scroll=ft.ScrollMode.AUTO),
        bgcolor="white", padding=0, border_radius=12, border=ft.border.all(1, ft.colors.GREY_200),
        shadow=ft.BoxShadow(blur_radius=15, color=ft.colors.with_opacity(0.05, ft.colors.BLACK), offset=ft.Offset(0, 4)),
        expand=True
    )

    return ft.Container(
        content=ft.Column([
            encabezado,
            ft.Divider(height=20, color="transparent"),
            contenedor_tabla
        ], expand=True),
        padding=30, expand=True
    )