from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFrame)
from PyQt6.QtCore import Qt
from modules.users import db_users
from utils import session

class VistaLogin(QDialog):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        # Configuración de la ventana
        self.setWindowTitle("Gesty ERP - Acceso Seguro")
        self.setFixedSize(450, 550)
        self.setStyleSheet("background-color: #F1F5F9;") # Fondo general gris muy claro
        
        # Layout principal centrador
        layout_principal = QVBoxLayout(self)
        layout_principal.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # ==========================================
        # TARJETA CENTRAL (CARD)
        # ==========================================
        tarjeta = QFrame()
        tarjeta.setFixedSize(380, 420)
        tarjeta.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 12px;
                border: 1px solid #E2E8F0;
            }
        """)
        
        layout_tarjeta = QVBoxLayout(tarjeta)
        layout_tarjeta.setContentsMargins(40, 40, 40, 40)
        layout_tarjeta.setSpacing(20)
        
        # --- HEADER DE LA TARJETA ---
        lbl_logo = QLabel("GESTY ERP")
        lbl_logo.setStyleSheet("font-size: 28px; font-weight: 900; color: #1E293B; letter-spacing: 2px; border: none;")
        lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_sub = QLabel("Ingresa tus credenciales para continuar")
        lbl_sub.setStyleSheet("font-size: 13px; color: #64748B; border: none;")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout_tarjeta.addWidget(lbl_logo)
        layout_tarjeta.addWidget(lbl_sub)
        layout_tarjeta.addSpacing(15)
        
        # --- CAMPOS DE TEXTO ---
        estilo_inputs = """
            QLineEdit {
                padding: 12px 15px;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                background-color: #F8FAFC;
                font-size: 14px;
                color: #0F172A;
            }
            QLineEdit:focus {
                border: 2px solid #2563EB;
                background-color: #FFFFFF;
            }
        """
        
        self.txt_usuario = QLineEdit()
        self.txt_usuario.setPlaceholderText("Usuario")
        self.txt_usuario.setStyleSheet(estilo_inputs)
        
        self.txt_password = QLineEdit()
        self.txt_password.setPlaceholderText("Contraseña")
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_password.setStyleSheet(estilo_inputs)
        
        # Etiqueta para mostrar errores (Oculta por defecto)
        self.lbl_error = QLabel("")
        self.lbl_error.setStyleSheet("color: #DC2626; font-size: 12px; font-weight: bold; border: none;")
        self.lbl_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_error.hide()
        
        layout_tarjeta.addWidget(self.txt_usuario)
        layout_tarjeta.addWidget(self.txt_password)
        layout_tarjeta.addWidget(self.lbl_error)
        
        layout_tarjeta.addSpacing(10)
        
        # --- BOTÓN DE INGRESO ---
        btn_ingresar = QPushButton("Iniciar Sesión")
        btn_ingresar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ingresar.setFixedHeight(50)
        btn_ingresar.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: white;
                border-radius: 6px;
                font-size: 15px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #1D4ED8;
            }
            QPushButton:pressed {
                background-color: #1E40AF;
            }
        """)
        btn_ingresar.clicked.connect(self.procesar_login)
        
        layout_tarjeta.addWidget(btn_ingresar)
        layout_tarjeta.addStretch()
        
        # Atajos de teclado (Presionar Enter para entrar)
        self.txt_usuario.returnPressed.connect(self.txt_password.setFocus)
        self.txt_password.returnPressed.connect(self.procesar_login)
        
        layout_principal.addWidget(tarjeta)

    def procesar_login(self):
        usuario = self.txt_usuario.text().strip()
        password = self.txt_password.text().strip()
        
        if not usuario or not password:
            self.lbl_error.setText("⚠️ Completa todos los campos.")
            self.lbl_error.show()
            return
            
        # 🔥 AQUÍ ESTÁ LA CORRECCIÓN: Llamamos a verificar_credenciales
        exito, resp = db_users.verificar_credenciales(usuario, password)
        
        if exito:
            session.usuario_actual = resp # Guardamos los datos del usuario
            self.accept() # Cierra el modal y da luz verde a main.py
        else:
            self.lbl_error.setText(f"⚠️ {resp}")
            self.lbl_error.show()
            self.txt_password.clear()
            self.txt_password.setFocus()