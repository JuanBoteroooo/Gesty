from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QMessageBox, QFrame, QHBoxLayout)
from PyQt6.QtCore import Qt
from modules.users import db_users
from utils import session # Importamos la memoria del sistema

class VistaLogin(QDialog):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Gesty ERP - Seguridad")
        self.setFixedSize(450, 500)
        self.setStyleSheet("QDialog { background-color: #E2E8F0; }")

        layout_principal = QVBoxLayout(self)
        layout_principal.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Tarjeta blanca central
        tarjeta = QFrame()
        tarjeta.setStyleSheet("QFrame { background-color: #FFFFFF; border-radius: 15px; border: 1px solid #CBD5E1; }")
        tarjeta.setFixedSize(380, 420)
        layout_tarjeta = QVBoxLayout(tarjeta)
        layout_tarjeta.setContentsMargins(40, 40, 40, 40)
        layout_tarjeta.setSpacing(20)
        
        # Textos
        lbl_titulo = QLabel("Gesty ERP")
        lbl_titulo.setStyleSheet("font-size: 32px; font-weight: 900; color: #2563EB; border: none;")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_sub = QLabel("Inicia sesión para continuar")
        lbl_sub.setStyleSheet("font-size: 14px; color: #64748B; border: none;")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout_tarjeta.addWidget(lbl_titulo)
        layout_tarjeta.addWidget(lbl_sub)
        layout_tarjeta.addSpacing(10)
        
        # Campos de texto
        estilo_input = "QLineEdit { padding: 12px; border: 2px solid #E2E8F0; border-radius: 6px; color: #0F172A; font-size: 15px; background-color: #F8FAFC; } QLineEdit:focus { border: 2px solid #2563EB; background-color: #FFFFFF; }"
        
        self.txt_usuario = QLineEdit()
        self.txt_usuario.setPlaceholderText("👤 Nombre de Usuario")
        self.txt_usuario.setStyleSheet(estilo_input)
        
        self.txt_password = QLineEdit()
        self.txt_password.setPlaceholderText("🔒 Contraseña")
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password) # Oculta los caracteres
        self.txt_password.setStyleSheet(estilo_input)
        
        layout_tarjeta.addWidget(self.txt_usuario)
        layout_tarjeta.addWidget(self.txt_password)
        layout_tarjeta.addSpacing(20)
        
        # Botón
        self.btn_entrar = QPushButton("INGRESAR")
        self.btn_entrar.setFixedHeight(50)
        self.btn_entrar.setStyleSheet("QPushButton { background-color: #2563EB; color: white; border-radius: 8px; font-weight: 900; font-size: 16px; } QPushButton:hover { background-color: #1D4ED8; }")
        self.btn_entrar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_entrar.clicked.connect(self.procesar_login)
        
        layout_tarjeta.addWidget(self.btn_entrar)
        
        # Permitir entrar con la tecla Enter
        self.txt_password.returnPressed.connect(self.procesar_login)
        self.txt_usuario.returnPressed.connect(lambda: self.txt_password.setFocus())
        
        layout_principal.addWidget(tarjeta)

    def procesar_login(self):
        usuario = self.txt_usuario.text().strip()
        password = self.txt_password.text().strip()
        
        if not usuario or not password:
            return QMessageBox.warning(self, "Error", "Por favor ingresa usuario y contraseña.")
            
        exito, resultado = db_users.verificar_credenciales(usuario, password)
        
        if exito:
            # 🔥 Guardamos los datos del usuario en la memoria global
            session.usuario_actual = resultado 
            # Le decimos al programa principal que todo salió bien
            self.accept() 
        else:
            QMessageBox.critical(self, "Acceso Denegado", resultado)
            self.txt_password.clear()
            self.txt_password.setFocus()