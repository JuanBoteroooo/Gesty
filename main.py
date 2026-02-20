import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QStackedWidget, QLabel, QFrame)
from PyQt6.QtCore import Qt

# ========================================================
# IMPORTACIÓN DE LOS MÓDULOS (VISTAS)
# ========================================================
from modules.inventory.ui_inventory import VistaInventario
from modules.sales.ui_sales import VistaVentas
from modules.customers.ui_customers import VistaClientes
from modules.suppliers.ui_suppliers import VistaProveedores
from modules.settings.ui_settings import VistaAjustes
from modules.returns.ui_returns import VistaDevoluciones
from modules.reports.ui_reports import VistaReportes
from modules.home.ui_home import VistaInicio

class GestyERP(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # --- CONFIGURACIÓN DE LA VENTANA ---
        self.setWindowTitle("Gesty ERP - Sistema de Gestión")
        self.resize(1300, 850)
        
        # Estilo Global (Tipografía moderna y fondo neutro)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F8FAFC; 
            }
            QWidget {
                font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
            }
        """)

        widget_central = QWidget()
        self.setCentralWidget(widget_central)

        layout_principal = QHBoxLayout(widget_central)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        # --- MENÚ LATERAL (SIDEBAR) ---
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(240)
        self.sidebar.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-right: 1px solid #E2E8F0;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 12px 20px;
                text-align: left;
                font-size: 14px;
                font-weight: 600;
                color: #64748B; 
                border-radius: 6px;
                margin: 4px 15px;
            }
            QPushButton:hover {
                background-color: #F1F5F9;
                color: #0F172A;
            }
            QPushButton:checked {
                background-color: #EFF6FF;
                color: #2563EB; 
                font-weight: bold;
            }
        """)
        layout_sidebar = QVBoxLayout(self.sidebar)
        layout_sidebar.setContentsMargins(0, 30, 0, 30)
        layout_sidebar.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Logo / Título
        lbl_logo = QLabel("Gesty ERP")
        lbl_logo.setStyleSheet("""
            font-size: 24px; 
            font-weight: 900; 
            color: #0F172A; 
            padding-left: 20px; 
            margin-bottom: 30px;
            border: none;
        """)
        layout_sidebar.addWidget(lbl_logo)

        # Botones de navegación
        self.botones_menu = []
        nombres_menu = [
            "🏠  Inicio",
            "🛒  Ventas", 
            "📦  Inventario", 
            "👥  Clientes", 
            "🚚  Proveedores", 
            "🔄  Devoluciones",
            "📊  Reportes", 
            "⚙️  Ajustes"
        ]
        
        for index, nombre in enumerate(nombres_menu):
            btn = QPushButton(nombre)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, idx=index: self.cambiar_pantalla(idx))
            self.botones_menu.append(btn)
            layout_sidebar.addWidget(btn)

        # --- ÁREA DE CONTENIDO (PANTALLAS) ---
        self.stacked_widget = QStackedWidget()
        
        # 0. Inicio
        self.stacked_widget.addWidget(VistaInicio())

        # 2. Ventas
        self.stacked_widget.addWidget(VistaVentas())
        
        # 1. Inventario
        self.stacked_widget.addWidget(VistaInventario())
        
        
        # 3. Clientes
        self.stacked_widget.addWidget(VistaClientes())
        
        # 4. Proveedores
        self.stacked_widget.addWidget(VistaProveedores())
        # 7. Devoluciones
        self.stacked_widget.addWidget(VistaDevoluciones())
        
        # 5. Reportes (Este aún no lo hemos creado, dejamos el placeholder)
        self.stacked_widget.addWidget(VistaReportes())
        
        # 6. Ajustes
        self.stacked_widget.addWidget(VistaAjustes())
        
        layout_principal.addWidget(self.sidebar)
        layout_principal.addWidget(self.stacked_widget)

        # Iniciar en la pantalla de Inicio (Índice 0) por defecto
        self.cambiar_pantalla(0)

    def crear_placeholder(self, texto):
        """Crea una pantalla temporal para los módulos que aún no existen"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        lbl = QLabel(texto)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("font-size: 28px; font-weight: bold; color: #94A3B8; border: none;")
        layout.addWidget(lbl)
        return widget

    def cambiar_pantalla(self, indice):
        """Cambia la vista y actualiza automáticamente los datos (Lógica Reactiva)"""
        self.stacked_widget.setCurrentIndex(indice)
        
        # Marcar el botón correcto en el menú lateral
        for i, btn in enumerate(self.botones_menu):
            btn.setChecked(i == indice)
            
        # 🔥 MAGIA REACTIVA: Le preguntamos a la vista actual si tiene funciones de recarga y las ejecutamos
        vista_actual = self.stacked_widget.widget(indice)
        
        if hasattr(vista_actual, 'cargar_datos'):
            vista_actual.cargar_datos() # Recarga tablas de clientes, proveedores, inventario
            
        if hasattr(vista_actual, 'cargar_configuracion'):
            vista_actual.cargar_configuracion() # Recarga combos en Ventas
            
        if hasattr(vista_actual, 'actualizar_todo'):
            vista_actual.actualizar_todo() # Recarga todas las pestañas en Ajustes


# ========================================================
# PUNTO DE ARRANQUE DE LA APLICACIÓN
# ========================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion") 
    ventana = GestyERP()
    ventana.show()
    sys.exit(app.exec())