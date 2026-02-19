import flet as ft
from modules.settings import db_settings

def vista_ajustes(page: ft.Page):
    COLOR_PRIMARIO = ft.colors.BLUE_800
    COLOR_FONDO_INPUT = ft.colors.BLUE_GREY_50

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
    # LÓGICA: MONEDAS
    # ==========================
    txt_nombre_moneda = ft.TextField(label="Nombre (Ej: Peso)", width=350, **estilo_input)
    txt_simbolo_moneda = ft.TextField(label="Símbolo (Ej: $)", width=350, **estilo_input)
    txt_tasa_moneda = ft.TextField(label="Tasa (Ej: 4000)", width=350, **estilo_input)
    chk_principal = ft.Checkbox(label="Convertir en Moneda Principal (Referencia)", value=False)

    tabla_monedas = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID", color=ft.colors.BLUE_GREY_600)),
            ft.DataColumn(ft.Text("DIVISA", weight="bold", color=ft.colors.BLUE_GREY_600)),
            ft.DataColumn(ft.Text("SÍMBOLO", weight="bold", color=ft.colors.BLUE_GREY_600)),
            ft.DataColumn(ft.Text("TASA CAMBIO", weight="bold", color=ft.colors.BLUE_GREY_600), numeric=True),
            ft.DataColumn(ft.Text("ESTADO", weight="bold", color=ft.colors.BLUE_GREY_600)),
            ft.DataColumn(ft.Text("ACCIONES", weight="bold", color=ft.colors.BLUE_GREY_600)),
        ],
        rows=[], border=ft.border.all(1, ft.colors.GREY_200), border_radius=8, heading_row_color=ft.colors.GREY_50
    )

    def cargar_monedas():
        tabla_monedas.rows.clear()
        for m in db_settings.obtener_monedas():
            estado = ft.Container(content=ft.Text("PRINCIPAL", color="green", weight="bold", size=10), bgcolor=ft.colors.GREEN_50, padding=5, border_radius=4) if m['es_principal'] else ft.Text("Secundaria", color="grey", size=11)
            tabla_monedas.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(m['id']), size=13)),
                ft.DataCell(ft.Text(m['nombre'], weight="bold", size=14)),
                ft.DataCell(ft.Text(m['simbolo'], size=13)),
                ft.DataCell(ft.Text(str(m['tasa_cambio']), size=13)),
                ft.DataCell(estado),
                ft.DataCell(ft.IconButton(icon=ft.icons.DELETE_OUTLINE, icon_color="red", on_click=lambda e, x=m['id']: borrar_moneda(x)))
            ]))
        page.update()

    def guardar_moneda(e):
        if not txt_nombre_moneda.value or not txt_tasa_moneda.value:
            mostrar_mensaje("Completa los datos", "red")
            return
        try: tasa = float(txt_tasa_moneda.value)
        except: return mostrar_mensaje("Tasa inválida", "red")

        exito, msg = db_settings.guardar_moneda(txt_nombre_moneda.value, txt_simbolo_moneda.value, tasa, 1 if chk_principal.value else 0)
        if exito:
            mostrar_mensaje(msg, "green")
            dialogo_moneda.open = False
            cargar_monedas()
        else: mostrar_mensaje(msg, "red")

    def borrar_moneda(id_m):
        exito, msg = db_settings.eliminar_moneda(id_m)
        mostrar_mensaje(msg, "green" if exito else "red")
        if exito: cargar_monedas()

    dialogo_moneda = ft.AlertDialog(
        title=ft.Row([ft.Icon(ft.icons.MONETIZATION_ON, color=COLOR_PRIMARIO), ft.Text("Nueva Divisa")]),
        content=ft.Container(width=400, content=ft.Column([txt_nombre_moneda, txt_simbolo_moneda, txt_tasa_moneda, ft.Divider(color="transparent", height=5), chk_principal], tight=True)),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: (setattr(dialogo_moneda, 'open', False), page.update())),
            ft.ElevatedButton("Guardar", bgcolor=COLOR_PRIMARIO, color="white", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)), on_click=guardar_moneda)
        ]
    )

    def abrir_dialogo_moneda(e):
        txt_nombre_moneda.value = ""
        txt_simbolo_moneda.value = ""
        txt_tasa_moneda.value = ""
        chk_principal.value = False
        page.dialog = dialogo_moneda
        dialogo_moneda.open = True
        page.update()

    # ==========================
    # LÓGICA: LISTAS DE PRECIOS
    # ==========================
    txt_nombre_lista = ft.TextField(label="Nombre de la Lista (Ej: VIP)", width=350, **estilo_input)

    tabla_listas = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID", color=ft.colors.BLUE_GREY_600)),
            ft.DataColumn(ft.Text("NOMBRE DE LA LISTA", weight="bold", color=ft.colors.BLUE_GREY_600)),
            ft.DataColumn(ft.Text("ACCIONES", weight="bold", color=ft.colors.BLUE_GREY_600)),
        ],
        rows=[], border=ft.border.all(1, ft.colors.GREY_200), border_radius=8, heading_row_color=ft.colors.GREY_50
    )

    def cargar_listas():
        tabla_listas.rows.clear()
        for m in db_settings.obtener_listas_precios():
            tabla_listas.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(m['id']), size=13)),
                ft.DataCell(ft.Text(m['nombre'], weight="bold", size=14)),
                ft.DataCell(ft.IconButton(icon=ft.icons.DELETE_OUTLINE, icon_color="red", on_click=lambda e, x=m['id']: borrar_lista(x)))
            ]))
        page.update()

    def guardar_lista(e):
        if not txt_nombre_lista.value: return
        exito, msg = db_settings.guardar_lista_precio(txt_nombre_lista.value)
        if exito:
            mostrar_mensaje(msg, "green")
            dialogo_lista.open = False
            cargar_listas()
        else: mostrar_mensaje(msg, "red")

    def borrar_lista(id_l):
        exito, msg = db_settings.eliminar_lista_precio(id_l)
        mostrar_mensaje(msg, "green" if exito else "red")
        if exito: cargar_listas()

    dialogo_lista = ft.AlertDialog(
        title=ft.Row([ft.Icon(ft.icons.FORMAT_LIST_BULLETED, color=COLOR_PRIMARIO), ft.Text("Nueva Lista")]),
        content=ft.Container(width=400, content=ft.Column([ft.Text("Clasifica tus precios de venta", size=12, color="grey"), txt_nombre_lista], tight=True)),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: (setattr(dialogo_lista, 'open', False), page.update())),
            ft.ElevatedButton("Guardar", bgcolor=COLOR_PRIMARIO, color="white", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)), on_click=guardar_lista)
        ]
    )

    def abrir_dialogo_lista(e):
        txt_nombre_lista.value = ""
        page.dialog = dialogo_lista
        dialogo_lista.open = True
        page.update()

    # ==========================
    # TABS Y ESTRUCTURA FINAL
    # ==========================
    cargar_monedas()
    cargar_listas()

    seccion_monedas = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text("Monedas Registradas", weight="bold", size=16), 
                ft.Container(expand=True), 
                ft.ElevatedButton("Añadir Moneda", icon=ft.icons.ADD, bgcolor=COLOR_PRIMARIO, color="white", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)), on_click=abrir_dialogo_moneda)
            ]),
            ft.Divider(color="transparent", height=10),
            ft.Column([tabla_monedas], scroll=ft.ScrollMode.AUTO, expand=True)
        ]), padding=20
    )

    seccion_listas = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text("Listas Registradas", weight="bold", size=16), 
                ft.Container(expand=True), 
                ft.ElevatedButton("Añadir Lista", icon=ft.icons.ADD, bgcolor=COLOR_PRIMARIO, color="white", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)), on_click=abrir_dialogo_lista)
            ]),
            ft.Divider(color="transparent", height=10),
            ft.Column([tabla_listas], scroll=ft.ScrollMode.AUTO, expand=True)
        ]), padding=20
    )

    tabs = ft.Tabs(
        selected_index=0,
        tabs=[
            ft.Tab(text="Divisas y Tasas", icon=ft.icons.MONETIZATION_ON, content=seccion_monedas),
            ft.Tab(text="Estructura de Precios", icon=ft.icons.FORMAT_LIST_BULLETED, content=seccion_listas),
        ],
        expand=True,
    )

    encabezado = ft.Row([
        ft.Container(content=ft.Icon(ft.icons.SETTINGS, size=30, color=COLOR_PRIMARIO), padding=10, bgcolor=ft.colors.BLUE_50, border_radius=10),
        ft.Column([
            ft.Text("Ajustes y Parámetros", size=24, weight="bold", color=ft.colors.BLUE_GREY_900),
            ft.Text("Configura las reglas de negocio de tu ferretería", size=13, color=ft.colors.GREY_500)
        ], spacing=2)
    ])

    return ft.Container(
        content=ft.Column([
            encabezado,
            ft.Divider(height=20, color="transparent"),
            ft.Container(content=tabs, bgcolor="white", border_radius=12, border=ft.border.all(1, ft.colors.GREY_200), expand=True, padding=0, shadow=ft.BoxShadow(blur_radius=15, color=ft.colors.with_opacity(0.05, ft.colors.BLACK), offset=ft.Offset(0, 4)))
        ], expand=True),
        padding=30, expand=True
    )