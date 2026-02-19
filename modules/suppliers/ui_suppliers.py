import flet as ft
from modules.suppliers import db_suppliers

def vista_proveedores(page: ft.Page):
    COLOR_PRIMARIO = ft.colors.BLUE_800
    COLOR_FONDO_INPUT = ft.colors.BLUE_GREY_50
    
    estado = {"id_editar": None, "id_borrar": None}

    def mostrar_mensaje(texto, color="green"):
        snack = ft.SnackBar(content=ft.Text(texto, weight="bold", color="white"), bgcolor=color, duration=3000)
        page.overlay.clear()
        page.overlay.append(snack)
        snack.open = True
        page.update()

    estilo_input = {
        "filled": True, "bgcolor": COLOR_FONDO_INPUT, "border_color": "transparent",
        "border_radius": 8, "height": 50, "content_padding": 15, "cursor_color": COLOR_PRIMARIO
    }

    # ==========================
    # CAMPOS DEL FORMULARIO
    # ==========================
    txt_documento = ft.TextField(label="Documento (RIF/NIT/DNI)", width=350, **estilo_input)
    txt_nombre = ft.TextField(label="Nombre o Razón Social", width=350, **estilo_input)
    txt_telefono = ft.TextField(label="Teléfono", width=350, **estilo_input)
    txt_direccion = ft.TextField(label="Dirección Física", width=350, **estilo_input)

    # ==========================
    # TABLA VISUAL
    # ==========================
    tabla_proveedores = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("DOCUMENTO", weight="bold", color=ft.colors.BLUE_GREY_600)),
            ft.DataColumn(ft.Text("NOMBRE COMERCIAL", weight="bold", color=ft.colors.BLUE_GREY_600)),
            ft.DataColumn(ft.Text("TELÉFONO", weight="bold", color=ft.colors.BLUE_GREY_600)),
            ft.DataColumn(ft.Text("ACCIONES", weight="bold", color=ft.colors.BLUE_GREY_600)),
        ],
        rows=[], border=ft.border.all(1, ft.colors.GREY_200), border_radius=8, heading_row_color=ft.colors.GREY_50, expand=True
    )

    # ==========================
    # LÓGICA DE BASE DE DATOS
    # ==========================
    def guardar_proveedor(e):
        if not txt_documento.value or not txt_nombre.value:
            mostrar_mensaje("Documento y Nombre son obligatorios", "red")
            return

        if estado["id_editar"] is None:
            exito, msg = db_suppliers.guardar_proveedor(txt_documento.value, txt_nombre.value, txt_telefono.value, txt_direccion.value)
        else:
            exito, msg = db_suppliers.editar_proveedor(estado["id_editar"], txt_documento.value, txt_nombre.value, txt_telefono.value, txt_direccion.value)
            
        if exito:
            mostrar_mensaje(msg, "green")
            dialogo_proveedor.open = False
            cargar_datos()
        else:
            mostrar_mensaje(msg, "red")

    def confirmar_borrado(e):
        exito, msg = db_suppliers.eliminar_proveedor(estado["id_borrar"])
        dialogo_borrar.open = False
        mostrar_mensaje(msg, "green" if exito else "red")
        if exito: cargar_datos()
        else: page.update()

    # ==========================
    # MODALES (DISEÑO)
    # ==========================
    lbl_titulo_modal = ft.Text("Proveedor")
    btn_guardar_modal = ft.ElevatedButton("Guardar", bgcolor=COLOR_PRIMARIO, color="white", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)), on_click=guardar_proveedor)

    dialogo_proveedor = ft.AlertDialog(
        title=ft.Row([ft.Icon(ft.icons.BUSINESS, color=COLOR_PRIMARIO), lbl_titulo_modal]),
        content=ft.Container(width=400, content=ft.Column([txt_documento, txt_nombre, txt_telefono, txt_direccion], tight=True)),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: (setattr(dialogo_proveedor, 'open', False), page.update())),
            btn_guardar_modal
        ],
        actions_padding=15
    )

    dialogo_borrar = ft.AlertDialog(
        title=ft.Row([ft.Icon(ft.icons.WARNING, color="red"), ft.Text("Confirmar Eliminación")]),
        content=ft.Text("¿Seguro que deseas eliminar este proveedor?"),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: (setattr(dialogo_borrar, 'open', False), page.update())),
            ft.ElevatedButton("Sí, Eliminar", bgcolor="red", color="white", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)), on_click=confirmar_borrado)
        ],
        actions_padding=15
    )

    # ==========================
    # FUNCIONES DE APERTURA 
    # ==========================
    def abrir_dialogo_proveedor(proveedor=None):
        if proveedor:
            estado["id_editar"] = proveedor['id']
            txt_documento.value = proveedor['documento']
            txt_nombre.value = proveedor['nombre']
            txt_telefono.value = proveedor['telefono'] if proveedor['telefono'] else ""
            txt_direccion.value = proveedor['direccion'] if proveedor['direccion'] else ""
            lbl_titulo_modal.value = "Editar Proveedor"
            btn_guardar_modal.text = "Actualizar"
        else:
            estado["id_editar"] = None
            txt_documento.value = ""
            txt_nombre.value = ""
            txt_telefono.value = ""
            txt_direccion.value = ""
            lbl_titulo_modal.value = "Nuevo Proveedor"
            btn_guardar_modal.text = "Guardar"
            
        page.dialog = dialogo_proveedor
        dialogo_proveedor.open = True
        page.update()

    def abrir_dialogo_borrar(id_prov):
        estado["id_borrar"] = id_prov
        page.dialog = dialogo_borrar
        dialogo_borrar.open = True
        page.update()

    # ==========================
    # GENERADORES DE EVENTOS
    # ==========================
    def evento_editar(prov):
        return lambda e: abrir_dialogo_proveedor(prov)

    def evento_borrar(id_prov):
        return lambda e: abrir_dialogo_borrar(id_prov)

    # ==========================
    # CARGAR DATOS Y CREAR MENÚ
    # ==========================
    def cargar_datos():
        tabla_proveedores.rows.clear()
        for p in db_suppliers.obtener_proveedores():
            
            # EL NUEVO ENFOQUE: Un menú desplegable en lugar de botones sueltos
            menu_opciones = ft.PopupMenuButton(
                icon=ft.icons.MORE_VERT,
                tooltip="Opciones",
                items=[
                    ft.PopupMenuItem(icon=ft.icons.EDIT, text="Editar", on_click=evento_editar(p)),
                    ft.PopupMenuItem(icon=ft.icons.DELETE, text="Eliminar", on_click=evento_borrar(p['id'])),
                ]
            )

            tabla_proveedores.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(p['documento'], size=13)),
                ft.DataCell(ft.Text(p['nombre'], weight="bold", size=14)),
                ft.DataCell(ft.Text(p['telefono'] or "N/A", size=13)),
                ft.DataCell(menu_opciones) # Un solo elemento en la celda
            ]))
        page.update()

    cargar_datos()

    # ==========================
    # DISEÑO PRINCIPAL (LAYOUT)
    # ==========================
    boton_nuevo = ft.ElevatedButton("Añadir Proveedor", icon=ft.icons.ADD, bgcolor=COLOR_PRIMARIO, color="white", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)), on_click=lambda e: abrir_dialogo_proveedor(None))

    encabezado = ft.Row([
        ft.Row([
            ft.Container(content=ft.Icon(ft.icons.LOCAL_SHIPPING, size=30, color=COLOR_PRIMARIO), padding=10, bgcolor=ft.colors.BLUE_50, border_radius=10),
            ft.Column([
                ft.Text("Directorio de Proveedores", size=24, weight="bold", color=ft.colors.BLUE_GREY_900),
                ft.Text("Gestiona las empresas que te surten mercancía", size=13, color=ft.colors.GREY_500)
            ], spacing=2)
        ]),
        ft.Container(expand=True), boton_nuevo
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    contenedor_tabla = ft.Container(
        content=ft.Column([tabla_proveedores], scroll=ft.ScrollMode.AUTO, expand=True),
        bgcolor="white", border_radius=12, border=ft.border.all(1, ft.colors.GREY_200), expand=True, padding=0, 
        shadow=ft.BoxShadow(blur_radius=15, color=ft.colors.with_opacity(0.05, ft.colors.BLACK), offset=ft.Offset(0, 4))
    )

    return ft.Container(
        content=ft.Column([
            encabezado,
            ft.Divider(height=20, color="transparent"),
            contenedor_tabla
        ], expand=True),
        padding=30, expand=True
    )