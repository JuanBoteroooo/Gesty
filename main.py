import flet as ft
import logica
import ticket

def main(page: ft.Page):
    # --- CONFIGURACIÓN VISUAL GENERAL ---
    page.title = "Gesty"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 1300
    page.window_height = 850
    page.padding = 0
    page.bgcolor = "#f5f5f5" 

    # Estilos de color
    COLOR_PRIMARIO = ft.colors.BLUE_800
    COLOR_SECUNDARIO = ft.colors.BLUE_600
    COLOR_FONDO = "#f5f5f5"
    COLOR_BLANCO = "#ffffff"
    
    # ==========================
    # VARIABLES GLOBALES
    # ==========================
    id_producto_editar = ft.Ref[int]() 
    producto_seleccionado_para_venta = ft.Ref[dict]() 

    # --- CAMPOS INVENTARIO ---
    txt_codigo = ft.TextField(label="Código", border_color=COLOR_PRIMARIO, height=45, text_size=14)
    txt_nombre = ft.TextField(label="Nombre del Producto", border_color=COLOR_PRIMARIO, height=45, text_size=14)
    txt_stock = ft.TextField(label="Stock", value="0", keyboard_type="number", border_color=COLOR_PRIMARIO, height=45, text_size=14)
    txt_minimo = ft.TextField(label="Mínimo", value="5", keyboard_type="number", border_color=COLOR_PRIMARIO, height=45, text_size=14)

    # --- CAMPOS MODAL AGREGAR (CANTIDAD) ---
    txt_cantidad_modal = ft.TextField(
        value="1", 
        text_align="center", 
        width=80,
        read_only=True, 
        border_color=COLOR_PRIMARIO
    )

    # ==========================
    # 1. FUNCIONES UTILITARIAS
    # ==========================
    
    def mostrar_mensaje(texto, color):
        snack = ft.SnackBar(
            content=ft.Text(texto, weight="bold", color="white"), 
            bgcolor=color,
            duration=3000,
            action="OK"
        )
        page.overlay.clear()
        page.overlay.append(snack)
        snack.open = True
        page.update()

    # ==========================
    # 2. INVENTARIO (Lógica Visual)
    # ==========================
    
    tabla_inventario = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("CÓDIGO", weight="bold")),
            ft.DataColumn(ft.Text("PRODUCTO", weight="bold")),
            ft.DataColumn(ft.Text("STOCK", weight="bold"), numeric=True),
            ft.DataColumn(ft.Text("ESTADO")), 
            ft.DataColumn(ft.Text("ACCIONES")),
        ],
        rows=[],
        border=ft.border.all(0, "white"),
        vertical_lines=ft.border.BorderSide(0, "white"),
        heading_row_color=ft.colors.BLUE_50,
        heading_row_height=60,
        data_row_max_height=60,
        width=2000, 
    )

    contenedor_tabla = ft.Container(
        content=ft.Column([tabla_inventario], scroll=ft.ScrollMode.AUTO),
        bgcolor=COLOR_BLANCO,
        border_radius=10,
        padding=20,
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color=ft.colors.BLUE_GREY_100),
        expand=True 
    )

    def cargar_inventario(filtro=None):
        tabla_inventario.rows.clear()
        productos = logica.obtener_productos(filtro)
        
        for p in productos:
            stock = p['cantidad_actual']
            minimo = p['cantidad_minima']
            
            if stock == 0:
                estado_widget = ft.Container(content=ft.Text("AGOTADO", color="white", size=10, weight="bold"), bgcolor="grey_800", padding=5, border_radius=5)
            elif stock <= minimo:
                estado_widget = ft.Container(content=ft.Text("BAJO STOCK", color="white", size=10, weight="bold"), bgcolor="red", padding=5, border_radius=5)
            else:
                estado_widget = ft.Container(content=ft.Text("OK", color="green", size=10, weight="bold"), bgcolor="green_100", padding=5, border_radius=5)

            tabla_inventario.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(p['codigo'], size=12)),
                        ft.DataCell(ft.Text(p['nombre'], weight="bold", size=13)),
                        ft.DataCell(ft.Text(str(stock), size=13)),
                        ft.DataCell(estado_widget),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(icon=ft.icons.EDIT, icon_color="blue", tooltip="Editar",
                                    on_click=lambda e, x=p: abrir_dialogo_producto(e, producto=x)),
                                ft.IconButton(icon=ft.icons.DELETE, icon_color="red", tooltip="Eliminar",
                                    on_click=lambda e, x=p['id']: borrar_producto(x))
                            ], spacing=0)
                        )
                    ]
                )
            )
        page.update()

    def guardar_cambios_producto(e):
        try:
            s = int(txt_stock.value)
            m = int(txt_minimo.value)
        except:
            txt_stock.error_text = "Número inválido"
            page.update()
            return

        if id_producto_editar.current is None:
            exito, msg = logica.crear_producto(txt_codigo.value, txt_nombre.value, s, m)
        else:
            exito, msg = logica.editar_producto_completo(id_producto_editar.current, txt_codigo.value, txt_nombre.value, s, m)

        if exito:
            dialogo_producto.open = False
            mostrar_mensaje("Producto guardado", "green")
            cargar_inventario()
        else:
            mostrar_mensaje(f"Error: {msg}", "red")
        page.update()

    def borrar_producto(id_prod):
        logica.eliminar_producto(id_prod)
        cargar_inventario()

    def abrir_dialogo_producto(e, producto=None):
        if producto:
            id_producto_editar.current = producto['id']
            txt_codigo.value = producto['codigo']
            txt_nombre.value = producto['nombre']
            txt_stock.value = str(producto['cantidad_actual'])
            txt_minimo.value = str(producto['cantidad_minima'])
            titulo = "Editar Producto"
        else:
            id_producto_editar.current = None
            txt_codigo.value = ""
            txt_nombre.value = ""
            txt_stock.value = "0"
            txt_minimo.value = "5"
            titulo = "Nuevo Producto"
        
        dialogo_producto.title = ft.Text(titulo)
        page.dialog = dialogo_producto
        dialogo_producto.open = True
        page.update()

    def cerrar_dialogo(e):
        dialogo_producto.open = False
        dialogo_cantidad.open = False
        page.update()

    dialogo_producto = ft.AlertDialog(
        title=ft.Text("Producto"),
        content=ft.Container(
            width=400, height=220,
            content=ft.Column([
                txt_codigo,
                ft.Divider(height=10, color="transparent"),
                txt_nombre,
                ft.Divider(height=10, color="transparent"),
                ft.Row([
                    ft.Container(content=txt_stock, expand=True),
                    ft.VerticalDivider(width=10),
                    ft.Container(content=txt_minimo, expand=True)
                ])
            ])
        ),
        actions=[
            ft.TextButton("Cancelar", on_click=cerrar_dialogo), 
            ft.ElevatedButton("Guardar", bgcolor=COLOR_PRIMARIO, color="white", on_click=guardar_cambios_producto)
        ]
    )

    # ==========================
    # 3. LÓGICA DE DESPACHO (CARRITO)
    # ==========================
    
    carrito = [] 
    cl_nombre = ft.TextField(label="Nombre Cliente", bgcolor="white", text_size=12, height=40)
    cl_tel = ft.TextField(label="Teléfono", bgcolor="white", text_size=12, height=40)
    cl_dir = ft.TextField(label="Dirección", bgcolor="white", text_size=12, height=40)
    
    columna_carrito = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
    lista_busqueda = ft.ListView(expand=True, spacing=10)

    # --- A. BUSCADOR ---
    def buscar_para_venta(e):
        texto = e.control.value
        lista_busqueda.controls.clear()
        if not texto:
            page.update()
            return
        prods = logica.obtener_productos(texto)
        
        for p in prods:
            stock = p['cantidad_actual']
            btn_color = COLOR_PRIMARIO if stock > 0 else "grey"
            btn_icon = ft.icons.ADD_CIRCLE if stock > 0 else ft.icons.BLOCK
            
            item = ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text(p['nombre'], weight="bold", size=14),
                        ft.Text(f"Cód: {p['codigo']} | Stock: {stock}", size=12, color="grey")
                    ], expand=True),
                    
                    ft.IconButton(
                        icon=btn_icon, 
                        icon_color=btn_color, 
                        tooltip="Agregar",
                        on_click=lambda e, x=p: abrir_modal_agregar(x) 
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), 
                bgcolor="white", padding=10, border_radius=8, 
                border=ft.border.all(1, "#e0e0e0")
            )
            lista_busqueda.controls.append(item)
        page.update()

    # --- B. MODAL AGREGAR ---
    def modal_cambiar_cantidad(delta):
        try:
            actual = int(txt_cantidad_modal.value)
            nuevo = actual + delta
            max_stock = producto_seleccionado_para_venta.current['cantidad_actual']
            
            if nuevo < 1: nuevo = 1
            if nuevo > max_stock: 
                nuevo = max_stock
                mostrar_mensaje(f"Máximo stock disponible: {max_stock}", "orange")

            txt_cantidad_modal.value = str(nuevo)
            txt_cantidad_modal.update()
        except:
            pass

    def abrir_modal_agregar(producto):
        if producto['cantidad_actual'] <= 0:
            mostrar_mensaje("Producto agotado", "red")
            return

        producto_seleccionado_para_venta.current = producto
        txt_cantidad_modal.value = "1"
        
        lbl_info_stock.value = f"Stock disponible: {producto['cantidad_actual']}"
        lbl_info_producto.value = producto['nombre']
        
        page.dialog = dialogo_cantidad
        dialogo_cantidad.open = True
        page.update()

    def confirmar_agregar_carrito(e):
        p = producto_seleccionado_para_venta.current
        cantidad_solicitada = int(txt_cantidad_modal.value)

        encontrado = False
        for item in carrito:
            if item['id'] == p['id']:
                if (item['cantidad'] + cantidad_solicitada) > p['cantidad_actual']:
                     mostrar_mensaje(f"No puedes superar el stock ({p['cantidad_actual']})", "red")
                     return
                item['cantidad'] += cantidad_solicitada
                encontrado = True
                break
        
        if not encontrado:
            carrito.append({
                'id': p['id'], 
                'nombre': p['nombre'], 
                'cantidad': cantidad_solicitada,
                'max_stock': p['cantidad_actual']
            })
        
        dialogo_cantidad.open = False
        mostrar_mensaje("Producto agregado", "green")
        renderizar_carrito()
        page.update()

    lbl_info_producto = ft.Text("", weight="bold", size=16, text_align="center")
    lbl_info_stock = ft.Text("", color="grey", size=12, text_align="center")

    dialogo_cantidad = ft.AlertDialog(
        title=ft.Text("Agregar Producto", text_align="center"),
        content=ft.Container(
            height=180, width=300,
            content=ft.Column([
                lbl_info_producto,
                lbl_info_stock,
                ft.Divider(),
                ft.Row([
                    ft.IconButton(icon=ft.icons.REMOVE_CIRCLE_OUTLINE, icon_size=30, on_click=lambda e: modal_cambiar_cantidad(-1)),
                    txt_cantidad_modal,
                    ft.IconButton(icon=ft.icons.ADD_CIRCLE_OUTLINE, icon_size=30, on_click=lambda e: modal_cambiar_cantidad(1)),
                ], alignment=ft.MainAxisAlignment.CENTER),
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        ),
        actions=[
            ft.TextButton("Cancelar", on_click=cerrar_dialogo),
            ft.ElevatedButton("AGREGAR AL CARRITO", bgcolor=COLOR_PRIMARIO, color="white", on_click=confirmar_agregar_carrito)
        ],
        actions_alignment=ft.MainAxisAlignment.CENTER
    )

    # --- C. CARRITO VISUAL ---
    def cambiar_cantidad_item(item, delta):
        nuevo = item['cantidad'] + delta
        maximo = item['max_stock']

        if nuevo < 1: 
            return 
        if nuevo > maximo:
            mostrar_mensaje(f"No hay más stock (Máx: {maximo})", "red")
            return
        
        item['cantidad'] = nuevo
        renderizar_carrito()

    def borrar_del_carrito(item):
        carrito.remove(item)
        renderizar_carrito()

    def renderizar_carrito():
        columna_carrito.controls.clear()
        
        if not carrito:
            # ICONO SEGURO
            columna_carrito.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.icons.SHOPPING_CART, size=40, color="grey"), 
                        ft.Text("Carrito vacío", color="grey")
                    ], horizontal_alignment="center"),
                    padding=20, alignment=ft.alignment.center
                )
            )
        else:
            for item in carrito:
                tarjeta = ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text(item['nombre'], weight="bold", size=14),
                            ft.Text(f"Máx: {item['max_stock']}", size=11, color="grey")
                        ], expand=True),
                        
                        ft.Container(
                            content=ft.Row([
                                ft.IconButton(icon=ft.icons.REMOVE, icon_size=16, on_click=lambda e, x=item: cambiar_cantidad_item(x, -1)),
                                ft.Container(
                                    content=ft.Text(str(item['cantidad']), weight="bold"),
                                    padding=5, bgcolor=ft.colors.BLUE_50, border_radius=4, width=30, alignment=ft.alignment.center
                                ),
                                ft.IconButton(icon=ft.icons.ADD, icon_size=16, on_click=lambda e, x=item: cambiar_cantidad_item(x, 1)),
                            ], spacing=0),
                            border=ft.border.all(1, "grey"),
                            border_radius=5,
                            padding=0
                        ),
                        
                        # AQUÍ ESTABA EL ERROR: Reemplazamos SizedBox por Container
                        ft.Container(width=10),
                        
                        ft.IconButton(
                            icon=ft.icons.DELETE_OUTLINE, 
                            icon_color="red", 
                            tooltip="Quitar",
                            on_click=lambda e, x=item: borrar_del_carrito(x)
                        )
                    ]),
                    padding=10,
                    bgcolor="white",
                    border_radius=8,
                    shadow=ft.BoxShadow(blur_radius=2, color=ft.colors.GREY_300)
                )
                columna_carrito.controls.append(tarjeta)
        
        page.update()

    def procesar_venta(e):
        if not carrito:
            mostrar_mensaje("El carrito está vacío", "red")
            return
        
        if not cl_nombre.value:
            mostrar_mensaje("Error: Debes ingresar el Nombre del Cliente", "red")
            cl_nombre.focus()
            page.update()
            return
            
        cliente = {'nombre': cl_nombre.value, 'telefono': cl_tel.value, 'direccion': cl_dir.value}
        ok, res = logica.registrar_despacho(cliente, carrito)
        
        if ok:
            mostrar_mensaje("¡Ticket generado con éxito!", "green")
            try:
                ticket.generar_pdf(res, cliente, carrito)
            except:
                pass
            carrito.clear()
            cl_nombre.value = ""
            cl_tel.value = ""
            cl_dir.value = ""
            renderizar_carrito()
            cargar_inventario()
            lista_busqueda.controls.clear()
        else:
            mostrar_mensaje(res, "red")
        
        page.update()

    # ==========================
    # LAYOUT
    # ==========================
    
    campo_busqueda = ft.TextField(
        label="Buscar...", prefix_icon=ft.icons.SEARCH, bgcolor="white", border_radius=10,
        on_change=lambda e: cargar_inventario(e.control.value), expand=True
    )

    boton_nuevo = ft.FloatingActionButton(
        icon=ft.icons.ADD, bgcolor=COLOR_PRIMARIO, on_click=lambda e: abrir_dialogo_producto(e, None)
    )

    vista_inventario = ft.Container(
        padding=30,
        content=ft.Column([
            ft.Text("Inventario", size=28, weight="bold", color=ft.colors.BLUE_GREY_800),
            ft.Divider(height=10, color="transparent"),
            ft.Row([campo_busqueda, boton_nuevo]),
            ft.Divider(height=20, color="transparent"),
            contenedor_tabla
        ], expand=True)
    )

    vista_ventas = ft.Container(
        padding=20,
        content=ft.Row([
            ft.Container(
                content=ft.Column([
                    ft.Text("Catálogo", size=20, weight="bold", color=COLOR_PRIMARIO),
                    ft.TextField(hint_text="Buscar producto...", prefix_icon=ft.icons.SEARCH, on_change=buscar_para_venta, bgcolor="white", border_radius=10),
                    ft.Container(content=lista_busqueda, expand=True, bgcolor="#fafafa", border_radius=10, padding=10)
                ], expand=True), 
                expand=True, 
                bgcolor="white", 
                padding=20, 
                border_radius=10, 
                shadow=ft.BoxShadow(blur_radius=5, color=ft.colors.GREY_300)
            ),
            
            ft.VerticalDivider(width=20, color="transparent"),
            
            ft.Container(
                content=ft.Column([
                    ft.Text("Datos del Cliente", size=18, weight="bold"),
                    cl_nombre, cl_tel, cl_dir,
                    ft.Divider(),
                    ft.Row([
                        ft.Text("Carrito de Despacho", size=18, weight="bold"),
                        ft.Icon(ft.icons.SHOPPING_CART, color=COLOR_SECUNDARIO)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    
                    ft.Container(
                        content=columna_carrito, 
                        expand=True, 
                        bgcolor="#fafafa", 
                        border=ft.border.all(1, "#eeeeee"), 
                        border_radius=5,
                        padding=5
                    ),
                    
                    ft.Divider(),
                    ft.ElevatedButton("GENERAR TICKET", bgcolor=COLOR_PRIMARIO, color="white", height=50, width=400, on_click=procesar_venta)
                ], expand=True),
                width=450, 
                bgcolor="white", 
                padding=20, 
                border_radius=10, 
                shadow=ft.BoxShadow(blur_radius=5, color=ft.colors.GREY_300)
            )
        ], expand=True)
    )

    rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=400,
        bgcolor="white",
        destinations=[
            ft.NavigationRailDestination(icon=ft.icons.INVENTORY_2_OUTLINED, selected_icon=ft.icons.INVENTORY_2, label="Inventario"),
            ft.NavigationRailDestination(icon=ft.icons.SHOPPING_CART_OUTLINED, selected_icon=ft.icons.SHOPPING_CART, label="Despacho"),
        ],
        on_change=lambda e: nav_cambiar(e.control.selected_index),
    )

    contenedor_principal = ft.Container(content=vista_inventario, expand=True, bgcolor="#f5f5f5")

    def nav_cambiar(indice):
        if indice == 0:
            contenedor_principal.content = vista_inventario
            cargar_inventario()
        else:
            contenedor_principal.content = vista_ventas
        page.update()

    page.add(ft.Row([rail, contenedor_principal], expand=True, spacing=0))
    cargar_inventario()
    renderizar_carrito() 

ft.app(target=main)