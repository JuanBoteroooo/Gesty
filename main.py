import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QStackedWidget, QLabel, QFrame, QDialog)
from PyQt6.QtCore import Qt

# ========================================================
# IMPORTACIÓN DE LOS MÓDULOS (VISTAS) Y SESIÓN
# ========================================================
from modules.inventory.ui_inventory import VistaInventario
from modules.sales.ui_sales import VistaVentas
from modules.customers.ui_customers import VistaClientes
from modules.suppliers.ui_suppliers import VistaProveedores
from modules.settings.ui_settings import VistaAjustes
from modules.returns.ui_returns import VistaDevoluciones
from modules.reports.ui_reports import VistaReportes
from modules.home.ui_home import VistaInicio
from modules.users.ui_login import VistaLogin
from modules.customers.ui_cxc import VistaCXC # 🔥 Nuevo módulo
from utils import session

class GestyERP(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # --- CONFIGURACIÓN DE LA VENTANA ---
        self.setWindowTitle("Gesty ERP - Sistema de Gestión")
        self.resize(1350, 850)
        
        # Estilo Global
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

        lbl_logo = QLabel("Gesty ERP")
        lbl_logo.setStyleSheet("font-size: 24px; font-weight: 900; color: #0F172A; padding-left: 20px; margin-bottom: 30px; border: none;")
        layout_sidebar.addWidget(lbl_logo)

        # Botones de navegación
        self.botones_menu = []
        nombres_menu = [
            "🏠  Inicio",           # 0
            "🛒  Ventas",           # 1
            "📦  Inventario",       # 2
            "👥  Clientes",         # 3
            "🚚  Proveedores",      # 4
            "🔄  Devoluciones",     # 5
            "📊  Reportes",         # 6
            "⚙️  Ajustes",          # 7
            "💸  Cuentas por Cobrar"  # 8 <- NUEVO
        ]
        
        # ================= 🔥 SEGURIDAD VISUAL 🔥 =================
        rol_usuario = session.usuario_actual['rol_id']
        
        if rol_usuario == 3: # CAJERO
            indices_permitidos = [0, 1, 3] 
        elif rol_usuario == 2: # GERENTE
            indices_permitidos = [0, 1, 2, 3, 4, 5, 8]
        else: # ADMINISTRADOR
            indices_permitidos = [0, 1, 2, 3, 4, 5, 6, 7, 8]
        
        for index, nombre in enumerate(nombres_menu):
            btn = QPushButton(nombre)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, idx=index: self.cambiar_pantalla(idx))
            self.botones_menu.append(btn)
            layout_sidebar.addWidget(btn)
            
            if index not in indices_permitidos:
                btn.hide()

        # --- ÁREA DE CONTENIDO (PANTALLAS) ---
        self.stacked_widget = QStackedWidget()
        
        # EL ORDEN AQUÍ ES CRÍTICO (Debe coincidir con los índices de arriba)
        self.stacked_widget.addWidget(VistaInicio())       # 0
        self.stacked_widget.addWidget(VistaVentas())       # 1
        self.stacked_widget.addWidget(VistaInventario())   # 2
        self.stacked_widget.addWidget(VistaClientes())     # 3
        self.stacked_widget.addWidget(VistaProveedores())  # 4
        self.stacked_widget.addWidget(VistaDevoluciones()) # 5
        self.stacked_widget.addWidget(VistaReportes())     # 6
        self.stacked_widget.addWidget(VistaAjustes())      # 7
        self.stacked_widget.addWidget(VistaCXC())          # 8 <- NUEVO
        
        layout_principal.addWidget(self.sidebar)
        layout_principal.addWidget(self.stacked_widget)

        self.cambiar_pantalla(0)

    def cambiar_pantalla(self, indice):
        """Cambia la vista y actualiza automáticamente los datos"""
        self.stacked_widget.setCurrentIndex(indice)
        
        for i, btn in enumerate(self.botones_menu):
            btn.setChecked(i == indice)
            
        vista_actual = self.stacked_widget.widget(indice)
        
        # Funciones de recarga automática según el módulo
        if hasattr(vista_actual, 'cargar_datos'):
            vista_actual.cargar_datos() 
            
        if hasattr(vista_actual, 'cargar_configuracion'):
            vista_actual.cargar_configuracion() 
            
        if hasattr(vista_actual, 'actualizar_todo'):
            vista_actual.actualizar_todo() 

# ========================================================
# PUNTO DE ARRANQUE
# ========================================================
if __name__ == "__main__":
    from utils.Gesty_BD import inicializar_db
    
    inicializar_db() 
    
    app = QApplication(sys.argv)
    
    login = VistaLogin()
    
    if login.exec() == QDialog.DialogCode.Accepted:
        print(f"Sesión iniciada: {session.usuario_actual['nombre']}")
        ventana = GestyERP() 
        ventana.show()
        sys.exit(app.exec())
    else:
        sys.exit()