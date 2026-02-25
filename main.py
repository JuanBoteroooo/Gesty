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
from modules.customers.ui_cxc import VistaCXC
from utils import session

class GestyERP(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # --- CONFIGURACIÓN DE LA VENTANA ---
        self.setWindowTitle("Gesty ERP - Workspace")
        self.resize(1350, 850)
        
        # Estilo Global (Fondo de la ventana principal)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F1F5F9; 
            }
            QWidget {
                font-family: 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, sans-serif;
            }
        """)

        widget_central = QWidget()
        self.setCentralWidget(widget_central)

        layout_principal = QHBoxLayout(widget_central)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        # ========================================================
        # BARRA LATERAL (SIDEBAR) - ESTILO CORPORATIVO MODERNO
        # ========================================================
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(260)
        
        # Tema Oscuro para la barra lateral
        self.sidebar.setStyleSheet("""
            QFrame#sidebar {
                background-color: #1E293B; /* Color pizarra oscuro */
            }
            QPushButton.menu-btn {
                background-color: transparent;
                border: none;
                padding: 14px 25px;
                text-align: left;
                font-size: 14px;
                font-weight: 500;
                color: #94A3B8; /* Gris claro para inactivos */
                border-left: 4px solid transparent;
            }
            QPushButton.menu-btn:hover {
                background-color: #334155;
                color: #F8FAFC;
            }
            QPushButton.menu-btn:checked {
                background-color: #0F172A; /* Fondo más oscuro al seleccionar */
                color: #38BDF8; /* Azul claro de acento */
                border-left: 4px solid #38BDF8; /* Línea indicadora */
                font-weight: bold;
            }
        """)
        layout_sidebar = QVBoxLayout(self.sidebar)
        layout_sidebar.setContentsMargins(0, 0, 0, 0)
        layout_sidebar.setSpacing(0)

        # CABECERA LOGO
        header_frame = QFrame()
        header_frame.setFixedHeight(90)
        layout_header = QVBoxLayout(header_frame)
        layout_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_logo = QLabel("GESTY")
        lbl_logo.setStyleSheet("font-size: 22px; font-weight: 900; color: #FFFFFF; letter-spacing: 2px;")
        layout_header.addWidget(lbl_logo)
        
        layout_sidebar.addWidget(header_frame)

        # ESPACIADOR PARA SEPARAR EL LOGO DEL MENÚ
        layout_sidebar.addSpacing(20)

        # MENÚ DE NAVEGACIÓN (Nombres más sobrios y sin emojis)
        self.botones_menu = []
        nombres_menu = [
            "Inicio",                 # 0
            "Punto de Venta",         # 1
            "Inventario y Stock",     # 2
            "Directorio de Clientes", # 3
            "Compras a Proveedores",  # 4
            "Devoluciones",           # 5
            "Reportes y Métricas",    # 6
            "Cuentas por Cobrar",      # 8
            "Configuración del ERP"  # 7
        ]
        
        # SEGURIDAD: LÓGICA DE PERMISOS
        rol_usuario = session.usuario_actual['rol_id'] if session.usuario_actual else 1
        
        if rol_usuario == 3: # CAJERO
            indices_permitidos = [0, 1, 3] 
        elif rol_usuario == 2: # GERENTE
            indices_permitidos = [0, 1, 2, 3, 4, 5, 8]
        else: # ADMINISTRADOR
            indices_permitidos = [0, 1, 2, 3, 4, 5, 6, 8, 7]
        
        for index, nombre in enumerate(nombres_menu):
            btn = QPushButton(nombre)
            btn.setProperty("class", "menu-btn") # Aplicamos la clase CSS definida arriba
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, idx=index: self.cambiar_pantalla(idx))
            self.botones_menu.append(btn)
            layout_sidebar.addWidget(btn)
            
            if index not in indices_permitidos:
                btn.hide()

        layout_sidebar.addStretch()

        # FOOTER CON DATOS DEL USUARIO
        user_frame = QFrame()
        user_frame.setStyleSheet("background-color: #0F172A; border-top: 1px solid #334155;")
        user_frame.setFixedHeight(80)
        layout_user = QVBoxLayout(user_frame)
        layout_user.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        nombre_str = session.usuario_actual['nombre'] if session.usuario_actual else "Administrador"
        rol_str = "Cajero" if rol_usuario == 3 else ("Gerente" if rol_usuario == 2 else "Super Admin")
        
        lbl_usuario = QLabel(nombre_str)
        lbl_usuario.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: bold;")
        lbl_rol = QLabel(rol_str)
        lbl_rol.setStyleSheet("color: #64748B; font-size: 12px;")
        
        layout_user.addWidget(lbl_usuario)
        layout_user.addWidget(lbl_rol)
        layout_sidebar.addWidget(user_frame)

        # ========================================================
        # ÁREA DE CONTENIDO (PANTALLAS)
        # ========================================================
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("background-color: transparent;")
        
        # EL ORDEN AQUÍ ES CRÍTICO (Debe coincidir con los índices de arriba)
        self.stacked_widget.addWidget(VistaInicio())       # 0
        self.stacked_widget.addWidget(VistaVentas())       # 1
        self.stacked_widget.addWidget(VistaInventario())   # 2
        self.stacked_widget.addWidget(VistaClientes())     # 3
        self.stacked_widget.addWidget(VistaProveedores())  # 4
        self.stacked_widget.addWidget(VistaDevoluciones()) # 5
        self.stacked_widget.addWidget(VistaReportes())     # 6
        self.stacked_widget.addWidget(VistaCXC())          # 8
        self.stacked_widget.addWidget(VistaAjustes())      # 7
        
        layout_principal.addWidget(self.sidebar)
        layout_principal.addWidget(self.stacked_widget)

        # Arrancar en Inicio por defecto
        self.cambiar_pantalla(0)

    def cambiar_pantalla(self, indice):
        """Cambia la vista y actualiza los botones activos"""
        self.stacked_widget.setCurrentIndex(indice)
        
        for i, btn in enumerate(self.botones_menu):
            btn.setChecked(i == indice)
            
        vista_actual = self.stacked_widget.widget(indice)
        
        # Refrescos automáticos según el módulo
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
        ventana = GestyERP() 
        ventana.show()
        sys.exit(app.exec())
    else:
        sys.exit()