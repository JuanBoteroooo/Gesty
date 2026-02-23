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
from utils import session

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
            "🏠  Inicio",           # Índice 0
            "🛒  Ventas",           # Índice 1
            "📦  Inventario",       # Índice 2
            "👥  Clientes",         # Índice 3
            "🚚  Proveedores",      # Índice 4
            "🔄  Devoluciones",     # Índice 5
            "📊  Reportes",         # Índice 6
            "⚙️  Ajustes"           # Índice 7
        ]
        
        # ================= 🔥 MAGIA DE SEGURIDAD VISUAL 🔥 =================
        rol_usuario = session.usuario_actual['rol_id']
        
        if rol_usuario == 3: # CAJERO: Solo ve Inicio, Ventas y Clientes
            indices_permitidos = [0, 1, 3] 
        elif rol_usuario == 2: # GERENTE: Ve todo excepto Reportes y Ajustes
            indices_permitidos = [0, 1, 2, 3, 4, 5]
        else: # ADMINISTRADOR: Ve absolutamente todo
            indices_permitidos = [0, 1, 2, 3, 4, 5, 6, 7]
        
        for index, nombre in enumerate(nombres_menu):
            btn = QPushButton(nombre)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, idx=index: self.cambiar_pantalla(idx))
            self.botones_menu.append(btn)
            layout_sidebar.addWidget(btn)
            
            # Ocultamos el botón si el usuario no tiene permisos
            if index not in indices_permitidos:
                btn.hide()

        # --- ÁREA DE CONTENIDO (PANTALLAS) ---
        self.stacked_widget = QStackedWidget()
        
        # El orden aquí debe coincidir exactamente con los índices de la lista nombres_menu
        # 0. Inicio
        self.stacked_widget.addWidget(VistaInicio())
        # 1. Ventas
        self.stacked_widget.addWidget(VistaVentas())
        # 2. Inventario
        self.stacked_widget.addWidget(VistaInventario())
        # 3. Clientes
        self.stacked_widget.addWidget(VistaClientes())
        # 4. Proveedores
        self.stacked_widget.addWidget(VistaProveedores())
        # 5. Devoluciones
        self.stacked_widget.addWidget(VistaDevoluciones())
        # 6. Reportes
        self.stacked_widget.addWidget(VistaReportes())
        # 7. Ajustes
        self.stacked_widget.addWidget(VistaAjustes())
        
        layout_principal.addWidget(self.sidebar)
        layout_principal.addWidget(self.stacked_widget)

        # Iniciar en la pantalla de Inicio por defecto
        self.cambiar_pantalla(0)

    def cambiar_pantalla(self, indice):
        """Cambia la vista y actualiza automáticamente los datos (Lógica Reactiva)"""
        self.stacked_widget.setCurrentIndex(indice)
        
        # Marcar el botón correcto en el menú lateral
        for i, btn in enumerate(self.botones_menu):
            btn.setChecked(i == indice)
            
        # Refrescar los datos de la vista que se acaba de abrir
        vista_actual = self.stacked_widget.widget(indice)
        
        if hasattr(vista_actual, 'cargar_datos'):
            vista_actual.cargar_datos() 
            
        if hasattr(vista_actual, 'cargar_configuracion'):
            vista_actual.cargar_configuracion() 
            
        if hasattr(vista_actual, 'actualizar_todo'):
            vista_actual.actualizar_todo() 

# ========================================================
# PUNTO DE ARRANQUE DE LA APLICACIÓN
# ========================================================
if __name__ == "__main__":
    from utils.Gesty_BD import inicializar_db
    
    # 1. Aseguramos que la BD exista
    inicializar_db() 
    
    app = QApplication(sys.argv)
    
    # 2. Mostramos el Login PRIMERO
    login = VistaLogin()
    
    # 3. Si el login responde "accept()" (contraseña correcta), abrimos el programa
    if login.exec() == QDialog.DialogCode.Accepted:
        
        print(f"Bienvenido al sistema: {session.usuario_actual['nombre']} ({session.usuario_actual['rol_nombre']})")
        
        ventana = GestyERP() 
        ventana.show()
        sys.exit(app.exec())
    else:
        # Si cerraron la ventana de login en la "X", el programa se apaga
        print("Login cancelado. Cerrando sistema.")
        sys.exit()