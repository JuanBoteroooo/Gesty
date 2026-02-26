import qtawesome as qta
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
                             QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QPushButton, QScrollArea)
from PyQt6.QtCore import Qt, QTimer, QDateTime, QSize
from PyQt6.QtGui import QColor, QFont, QCursor
from modules.home import db_home
from utils import session

class VistaInicio(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.cargar_datos()
        
        # Reloj en tiempo real ultra preciso
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.actualizar_reloj)
        self.timer.start(1000) 
        self.actualizar_reloj()

    def setup_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(35, 35, 35, 35)
        layout_principal.setSpacing(25)
        
        # ==========================================
        # 1. HEADER: SALUDO Y RELOJ DIGITAL
        # ==========================================
        header = QHBoxLayout()
        
        box_textos = QVBoxLayout()
        nombre_usuario = session.usuario_actual['nombre'] if session.usuario_actual else "Administrador"
        lbl_hola = QLabel(f"¡Hola, {nombre_usuario}!")
        lbl_hola.setStyleSheet("font-size: 32px; font-weight: 900; color: #0F172A; letter-spacing: -1px;")
        lbl_sub = QLabel("Aquí tienes el resumen operativo de hoy.")
        lbl_sub.setStyleSheet("font-size: 16px; color: #64748B;")
        
        box_textos.addWidget(lbl_hola)
        box_textos.addWidget(lbl_sub)
        header.addLayout(box_textos)
        
        header.addStretch()
        
        box_reloj = QVBoxLayout()
        self.lbl_reloj = QLabel("00:00:00")
        self.lbl_reloj.setStyleSheet("font-size: 36px; font-weight: 900; color: #0F172A; letter-spacing: 2px;")
        self.lbl_reloj.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.lbl_fecha = QLabel("Cargando fecha...")
        self.lbl_fecha.setStyleSheet("font-size: 14px; font-weight: bold; color: #38BDF8; text-transform: uppercase;")
        self.lbl_fecha.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        box_reloj.addWidget(self.lbl_reloj)
        box_reloj.addWidget(self.lbl_fecha)
        header.addLayout(box_reloj)
        
        layout_principal.addLayout(header)

        # ==========================================
        # 2. SECCIÓN CENTRAL DIVIDIDA (ACCESOS VS MÉTRICAS)
        # ==========================================
        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(25)
        
        # --- COLUMNA IZQUIERDA: TARJETAS FINANCIERAS Y TABLA ---
        col_izq = QVBoxLayout()
        col_izq.setSpacing(20)
        
        # Tarjetas Superiores
        fila_tarjetas = QHBoxLayout()
        fila_tarjetas.setSpacing(20)
        
        self.tarjeta_ventas = self.crear_tarjeta_kpi("Ingresos de Hoy", "$ 0.00", "fa5s.chart-line", "#10B981") 
        self.tarjeta_cxc = self.crear_tarjeta_kpi("Cuentas x Cobrar", "$ 0.00", "fa5s.hand-holding-usd", "#F59E0B") 
        self.tarjeta_alertas = self.crear_tarjeta_kpi("Alertas de Stock", "0 Prods", "fa5s.exclamation-triangle", "#DC2626") 
        
        fila_tarjetas.addWidget(self.tarjeta_ventas['widget'])
        fila_tarjetas.addWidget(self.tarjeta_cxc['widget'])
        fila_tarjetas.addWidget(self.tarjeta_alertas['widget'])
        col_izq.addLayout(fila_tarjetas)
        
        # Tabla de Movimientos
        panel_tabla = QFrame()
        panel_tabla.setStyleSheet("background-color: #FFFFFF; border-radius: 12px; border: 1px solid #E2E8F0;")
        layout_tabla = QVBoxLayout(panel_tabla)
        layout_tabla.setContentsMargins(25, 25, 25, 25)
        
        lbl_tabla = QLabel("Últimas 15 Transacciones Realizadas")
        lbl_tabla.setStyleSheet("font-size: 16px; font-weight: bold; color: #0F172A; border: none;")
        layout_tabla.addWidget(lbl_tabla)
        
        self.tabla_recientes = QTableWidget()
        self.tabla_recientes.setColumnCount(4)
        self.tabla_recientes.setHorizontalHeaderLabels(["FACTURA", "FECHA", "CLIENTE", "MONTO TOTAL"])
        self.tabla_recientes.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla_recientes.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla_recientes.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tabla_recientes.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla_recientes.verticalHeader().setVisible(False)
        self.tabla_recientes.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_recientes.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_recientes.setShowGrid(False)
        self.tabla_recientes.verticalHeader().setDefaultSectionSize(50)
        
        self.tabla_recientes.setStyleSheet("""
            QTableWidget { background-color: #FFFFFF; font-size: 14px; color: #334155; border: none;}
            QTableWidget::item { padding: 10px 15px; border-bottom: 1px solid #F1F5F9; }
            QTableWidget::item:selected { background-color: #F8FAFC; color: #0F172A; }
            QHeaderView::section { background-color: #F8FAFC; color: #64748B; font-weight: bold; font-size: 11px; padding: 15px; border: none; text-transform: uppercase; }
        """)
        layout_tabla.addWidget(self.tabla_recientes)
        col_izq.addWidget(panel_tabla)
        
        # --- COLUMNA DERECHA: ACCESOS RÁPIDOS Y ESTADO ---
        col_der = QVBoxLayout()
        col_der.setSpacing(20)
        
        # Panel Estado de Caja
        self.panel_caja = QFrame()
        self.layout_caja = QVBoxLayout(self.panel_caja)
        self.layout_caja.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.panel_caja.setFixedHeight(120)
        col_der.addWidget(self.panel_caja)
        
        # Panel Botones Gigantes
        panel_botones = QFrame()
        panel_botones.setStyleSheet("background-color: #FFFFFF; border-radius: 12px; border: 1px solid #E2E8F0;")
        layout_botones = QVBoxLayout(panel_botones)
        layout_botones.setContentsMargins(25, 25, 25, 25)
        layout_botones.setSpacing(15)
        
        lbl_acc = QLabel("⚡ Accesos Rápidos")
        lbl_acc.setStyleSheet("font-size: 16px; font-weight: bold; color: #0F172A; border: none; margin-bottom: 10px;")
        layout_botones.addWidget(lbl_acc)
        
        # Función para simular clics en la barra lateral
        def ir_a(indice):
            # Accedemos a la ventana principal para cambiar la pestaña
            ventana_principal = self.window()
            if hasattr(ventana_principal, 'cambiar_pantalla'):
                ventana_principal.cambiar_pantalla(indice)

        btn_pos = self.crear_boton_gigante("Punto de Venta (POS)", "fa5s.desktop", "#0F172A", lambda: ir_a(1))
        btn_inv = self.crear_boton_gigante("Revisar Inventario", "fa5s.box-open", "#38BDF8", lambda: ir_a(2))
        btn_prod = self.crear_boton_gigante("Módulo Producción", "fa5s.industry", "#10B981", lambda: ir_a(8))
        btn_cxc = self.crear_boton_gigante("Cobrar Cuaderno", "fa5s.book", "#F59E0B", lambda: ir_a(7))
        
        layout_botones.addWidget(btn_pos)
        layout_botones.addWidget(btn_inv)
        layout_botones.addWidget(btn_prod)
        layout_botones.addWidget(btn_cxc)
        layout_botones.addStretch()
        
        col_der.addWidget(panel_botones)
        
        cuerpo.addLayout(col_izq, stretch=7) # 70% del ancho
        cuerpo.addLayout(col_der, stretch=3) # 30% del ancho
        
        layout_principal.addLayout(cuerpo)

    def crear_tarjeta_kpi(self, titulo, valor_inicial, icono, color_acento):
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{ 
                background-color: #FFFFFF; 
                border-radius: 12px; 
                border: 1px solid #E2E8F0; 
                border-bottom: 4px solid {color_acento}; 
            }}
        """)
        frame.setFixedHeight(120)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(25, 20, 25, 20)
        
        box_textos = QVBoxLayout()
        lbl_titulo = QLabel(titulo.upper())
        lbl_titulo.setStyleSheet("font-size: 13px; color: #64748B; font-weight: bold; border: none; letter-spacing: 1px;")
        lbl_valor = QLabel(valor_inicial)
        lbl_valor.setStyleSheet("font-size: 32px; font-weight: 900; color: #0F172A; border: none;")
        
        box_textos.addWidget(lbl_titulo)
        box_textos.addWidget(lbl_valor)
        box_textos.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        lbl_icono = QLabel()
        lbl_icono.setPixmap(qta.icon(icono, color=color_acento).pixmap(QSize(45, 45)))
        lbl_icono.setStyleSheet("border: none; background: transparent;")
        
        layout.addLayout(box_textos)
        layout.addStretch()
        layout.addWidget(lbl_icono)
        
        return {'widget': frame, 'lbl_valor': lbl_valor}

    def crear_boton_gigante(self, texto, icono, color, funcion_callback):
        btn = QPushButton(f"  {texto}")
        btn.setIcon(qta.icon(icono, color='white'))
        btn.setIconSize(QSize(24, 24))
        btn.setFixedHeight(60)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                font-size: 15px;
                font-weight: bold;
                border-radius: 8px;
                text-align: left;
                padding-left: 20px;
            }}
            QPushButton:hover {{
                background-color: #1E293B; /* Oscurece al pasar el mouse */
            }}
        """)
        btn.clicked.connect(funcion_callback)
        return btn

    def actualizar_reloj(self):
        ahora = QDateTime.currentDateTime()
        self.lbl_reloj.setText(ahora.toString("hh:mm:ss AP"))
        self.lbl_fecha.setText(ahora.toString("dddd, dd 'de' MMMM 'de' yyyy"))

    def actualizar_estado_caja(self, estado_abierta):
        # Limpiamos el panel actual
        for i in reversed(range(self.layout_caja.count())): 
            self.layout_caja.itemAt(i).widget().setParent(None)
            
        if estado_abierta:
            self.panel_caja.setStyleSheet("background-color: #D1FAE5; border-radius: 12px; border: 2px solid #10B981;")
            lbl = QLabel("✅ CAJA ABIERTA Y OPERATIVA")
            lbl.setStyleSheet("color: #065F46; font-size: 16px; font-weight: 900; border: none;")
        else:
            self.panel_caja.setStyleSheet("background-color: #FEE2E2; border-radius: 12px; border: 2px dashed #DC2626;")
            lbl = QLabel("❌ CAJA CERRADA")
            lbl.setStyleSheet("color: #991B1B; font-size: 16px; font-weight: 900; border: none;")
            
        self.layout_caja.addWidget(lbl)

    def cargar_datos(self):
        try:
            datos = db_home.obtener_resumen_dashboard()
            
            # KPI Superiores
            self.tarjeta_ventas['lbl_valor'].setText(f"$ {datos['ingresos_hoy']:.2f}")
            self.tarjeta_cxc['lbl_valor'].setText(f"$ {datos['por_cobrar']:.2f}")
            self.tarjeta_alertas['lbl_valor'].setText(f"{datos['alertas_stock']} Prods")
            
            if datos['alertas_stock'] > 0:
                self.tarjeta_alertas['lbl_valor'].setStyleSheet("font-size: 32px; font-weight: 900; color: #DC2626; border: none;")
            else:
                self.tarjeta_alertas['lbl_valor'].setStyleSheet("font-size: 32px; font-weight: 900; color: #0F172A; border: none;")

            # Estado de Caja Dinámico
            from modules.sales import db_sales
            caja = db_sales.verificar_caja_abierta()
            self.actualizar_estado_caja(caja is not None)

            # Llenado de Tabla
            ventas = datos['ultimas_ventas'][:15] # Top 15
            self.tabla_recientes.setRowCount(len(ventas))
            
            for i, v in enumerate(ventas):
                item_id = QTableWidgetItem(f"#{v['id']:06d}")
                item_id.setForeground(QColor("#94A3B8"))
                item_id.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
                self.tabla_recientes.setItem(i, 0, item_id)
                
                self.tabla_recientes.setItem(i, 1, QTableWidgetItem(v['fecha_hora'].split(' ')[1])) # Solo muestra la hora
                self.tabla_recientes.setItem(i, 2, QTableWidgetItem(v['cliente']))
                
                item_total = QTableWidgetItem(f"$ {v['total_venta']:.2f}")
                item_total.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
                item_total.setForeground(QColor("#10B981")) 
                self.tabla_recientes.setItem(i, 3, item_total)
                
        except Exception as e:
            print(f"Error cargando el nuevo Dashboard: {e}")