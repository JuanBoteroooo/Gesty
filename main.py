import flet as ft
from modules.settings.ui_settings import vista_ajustes
from modules.suppliers.ui_suppliers import vista_proveedores
from modules.customers.ui_customers import vista_clientes

# Más adelante importaremos las vistas reales así:
# from modules.inventory.ui_inventory import view_inventory
# from modules.sales.ui_sales import view_sales

def main(page: ft.Page):
    # --- CONFIGURACIÓN PRINCIPAL ---
    page.title = "Gesty ERP"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 1300
    page.window_height = 850
    page.padding = 0
    page.bgcolor = "#f5f5f5"

# --- VISTAS DE PRUEBA (Placeholders) ---
    view_inventory = ft.Container(content=ft.Text("Módulo de Inventario", size=30, weight="bold"), alignment=ft.alignment.center, expand=True)
    view_sales = ft.Container(content=ft.Text("Módulo de Ventas (Despacho)", size=30, weight="bold"), alignment=ft.alignment.center, expand=True)
    view_reports = ft.Container(content=ft.Text("Módulo de Reportes", size=30, weight="bold"), alignment=ft.alignment.center, expand=True)
    view_suppliers = vista_proveedores(page)
    view_settings = vista_ajustes(page)
    view_customers = vista_clientes(page)

    views = [
        view_inventory,
        view_sales,
        view_customers,
        view_suppliers,
        view_reports,
        view_settings
    ]

    # Contenedor dinámico donde se inyecta la vista actual
    content_area = ft.Container(content=views[0], expand=True, bgcolor="#f5f5f5")

    def change_route(e):
        """Cambia el contenido de la pantalla al hacer clic en el menú"""
        index = e.control.selected_index
        content_area.content = views[index]
        page.update()

    # --- MENÚ LATERAL ---
    rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=200,
        bgcolor=ft.colors.WHITE,
        destinations=[
            ft.NavigationRailDestination(icon=ft.icons.INVENTORY_2_OUTLINED, selected_icon=ft.icons.INVENTORY_2, label="Inventario"),
            ft.NavigationRailDestination(icon=ft.icons.SHOPPING_CART_OUTLINED, selected_icon=ft.icons.SHOPPING_CART, label="Ventas"),
            ft.NavigationRailDestination(icon=ft.icons.PEOPLE_OUTLINE, selected_icon=ft.icons.PEOPLE, label="Clientes"),
            ft.NavigationRailDestination(icon=ft.icons.LOCAL_SHIPPING_OUTLINED, selected_icon=ft.icons.LOCAL_SHIPPING, label="Proveedores"),
            ft.NavigationRailDestination(icon=ft.icons.BAR_CHART_OUTLINED, selected_icon=ft.icons.INSERT_CHART, label="Reportes"),
            ft.NavigationRailDestination(icon=ft.icons.SETTINGS_OUTLINED, selected_icon=ft.icons.SETTINGS, label="Ajustes"),
        ],
        on_change=change_route,
    )

    # Añadir todo a la ventana
    page.add(
        ft.Row(
            [
                rail, 
                ft.VerticalDivider(width=1, color="#eeeeee"), 
                content_area
            ], 
            expand=True, 
            spacing=0
        )
    )

ft.app(target=main)