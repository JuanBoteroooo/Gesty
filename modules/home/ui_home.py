from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout)
from PyQt6.QtCore import Qt, QTimer, QDateTime
from modules.home import db_home

class VistaInicio(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.cargar_datos()
        
        # Iniciar el reloj en tiempo real
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.actualizar_reloj)
        self.timer.start(1000) # Se actualiza cada 1000 ms (1 segundo)
        self.actualizar_reloj()

    def setup_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(40, 40, 40, 40)
        layout_principal.setSpacing(30)
        
        # ==========================================
        # BANNER DE BIENVENIDA Y RELOJ
        # ==========================================
        panel_bienvenida = QFrame()
        panel_bienvenida.setStyleSheet("""
            QFrame {
                background-color: #2563EB; 
                border-radius: 15px;
            }
        """)
        panel_bienvenida.setFixedHeight(160)
        layout_bienvenida = QHBoxLayout(panel_bienvenida)
        layout_bienvenida.setContentsMargins(40, 20, 40, 20)
        
        # Textos de Bienvenida (Izquierda)
        box_textos = QVBoxLayout()
        lbl_hola = QLabel("¡Hola, Bienvenido a Gesty ERP! 👋")
        lbl_hola.setStyleSheet("font-size: 32px; font-weight: 900; color: #FFFFFF; border: none;")
        lbl_sub = QLabel("Tu sistema de gestión comercial y punto de venta.")
        lbl_sub.setStyleSheet("font-size: 16px; color: #BFDBFE; border: none;")
        box_textos.addWidget(lbl_hola)
        box_textos.addWidget(lbl_sub)
        box_textos.addStretch()
        
        # Reloj (Derecha)
        self.lbl_reloj = QLabel("00:00:00")
        self.lbl_reloj.setStyleSheet("font-size: 45px; font-weight: bold; color: #FFFFFF; border: none;")
        self.lbl_reloj.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        self.lbl_fecha = QLabel("Fecha")
        self.lbl_fecha.setStyleSheet("font-size: 16px; font-weight: bold; color: #BFDBFE; border: none;")
        self.lbl_fecha.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        box_reloj = QVBoxLayout()
        box_reloj.addWidget(self.lbl_reloj)
        box_reloj.addWidget(self.lbl_fecha)
        box_reloj.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        layout_bienvenida.addLayout(box_textos)
        layout_bienvenida.addLayout(box_reloj)
        
        layout_principal.addWidget(panel_bienvenida)

        # ==========================================
        # TARJETAS DE RESUMEN RÁPIDO
        # ==========================================
        lbl_resumen = QLabel("Resumen Rápido")
        lbl_resumen.setStyleSheet("font-size: 20px; font-weight: bold; color: #0F172A;")
        layout_principal.addWidget(lbl_resumen)
        
        layout_tarjetas = QHBoxLayout()
        layout_tarjetas.setSpacing(20)
        
        self.tarjeta_ventas = self.crear_tarjeta("🛒", "Facturas Hoy", "0", "#16A34A")
        self.tarjeta_productos = self.crear_tarjeta("📦", "Productos Totales", "0", "#D97706")
        self.tarjeta_clientes = self.crear_tarjeta("👥", "Clientes Registrados", "0", "#7C3AED")
        
        layout_tarjetas.addWidget(self.tarjeta_ventas['widget'])
        layout_tarjetas.addWidget(self.tarjeta_productos['widget'])
        layout_tarjetas.addWidget(self.tarjeta_clientes['widget'])
        
        layout_principal.addLayout(layout_tarjetas)
        layout_principal.addStretch()

    def crear_tarjeta(self, icono, titulo, valor_inicial, color_icono):
        frame = QFrame()
        frame.setStyleSheet("QFrame { background-color: #FFFFFF; border-radius: 12px; border: 1px solid #E2E8F0; }")
        frame.setFixedHeight(120)
        
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(25, 20, 25, 20)
        
        lbl_icono = QLabel(icono)
        lbl_icono.setStyleSheet(f"font-size: 40px; color: {color_icono}; background: transparent; border: none;")
        
        box_textos = QVBoxLayout()
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setStyleSheet("font-size: 15px; color: #64748B; font-weight: bold; background: transparent; border: none;")
        
        lbl_valor = QLabel(valor_inicial)
        lbl_valor.setStyleSheet("font-size: 30px; font-weight: 900; color: #0F172A; background: transparent; border: none;")
        
        box_textos.addWidget(lbl_titulo)
        box_textos.addWidget(lbl_valor)
        box_textos.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        layout.addWidget(lbl_icono)
        layout.addLayout(box_textos)
        layout.addStretch()
        
        return {'widget': frame, 'lbl_valor': lbl_valor}

    def actualizar_reloj(self):
        ahora = QDateTime.currentDateTime()
        hora_formateada = ahora.toString("hh:mm:ss AP")
        fecha_formateada = ahora.toString("dddd, dd 'de' MMMM 'de' yyyy").capitalize()
        
        self.lbl_reloj.setText(hora_formateada)
        self.lbl_fecha.setText(fecha_formateada)

    def cargar_datos(self):
        """Se ejecuta al abrir la app o al cambiar a esta pestaña"""
        datos = db_home.obtener_resumen_hoy()
        self.tarjeta_ventas['lbl_valor'].setText(str(datos['ventas_hoy']))
        self.tarjeta_productos['lbl_valor'].setText(str(datos['total_productos']))
        self.tarjeta_clientes['lbl_valor'].setText(str(datos['total_clientes']))