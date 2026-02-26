import qtawesome as qta
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QMessageBox, QFrame, QAbstractItemView, QComboBox, QDoubleSpinBox, QDialog, QFormLayout, QTabWidget, QGridLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from modules.finance import db_finance
from modules.sales import db_sales  # 🔥 IMPORTAMOS DB_SALES PARA TRAER LAS TASAS CORRECTAMENTE
from utils import session

class VistaFinanzas(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.cargar_datos()

    def setup_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(30, 30, 30, 30)
        layout_principal.setSpacing(20)
        
        # CABECERA
        header_layout = QVBoxLayout()
        lbl_titulo = QLabel("FINANZAS Y CONTROL DE GASTOS")
        lbl_titulo.setStyleSheet("font-size: 24px; font-weight: 900; color: #0F172A; letter-spacing: 1px;")
        lbl_subtitulo = QLabel("Registro de gastos operativos del local y estado real de los bancos/cajas.")
        lbl_subtitulo.setStyleSheet("font-size: 14px; color: #64748B;")
        header_layout.addWidget(lbl_titulo)
        header_layout.addWidget(lbl_subtitulo)
        layout_principal.addLayout(header_layout)

        # TABS DE NAVEGACIÓN
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #E2E8F0; background: #FFFFFF; border-radius: 8px; top: -1px; }
            QTabBar::tab { background: #F1F5F9; color: #64748B; padding: 12px 25px; border-top-left-radius: 8px; border-top-right-radius: 8px; font-weight: bold; font-size: 13px; margin-right: 4px; }
            QTabBar::tab:selected { background: #FFFFFF; color: #0F172A; border-top: 3px solid #38BDF8; border-bottom: 1px solid #FFFFFF; }
        """)
        
        self.tab_gastos = QWidget()
        self.tab_bancos = QWidget()
        
        self.setup_tab_gastos()
        self.setup_tab_bancos()
        
        self.tabs.addTab(self.tab_gastos, qta.icon('fa5s.receipt', color='#64748B'), "Gastos Operativos")
        self.tabs.addTab(self.tab_bancos, qta.icon('fa5s.building', color='#64748B'), "Saldos en Cuentas y Bancos")
        
        layout_principal.addWidget(self.tabs)

    # ==========================================
    # PESTAÑA 1: GASTOS OPERATIVOS
    # ==========================================
    def setup_tab_gastos(self):
        layout = QVBoxLayout(self.tab_gastos)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        barra_superior = QHBoxLayout()
        lbl_historial = QLabel("Historial de Salidas de Dinero")
        lbl_historial.setStyleSheet("font-size: 16px; font-weight: bold; color: #0F172A;")
        
        btn_nuevo_gasto = QPushButton(" Registrar Nuevo Gasto")
        btn_nuevo_gasto.setIcon(qta.icon('fa5s.minus-circle', color='white'))
        btn_nuevo_gasto.setStyleSheet("background-color: #DC2626; color: white; font-weight: bold; border-radius: 6px; padding: 10px 20px;")
        btn_nuevo_gasto.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_nuevo_gasto.clicked.connect(self.modal_registrar_gasto)
        
        barra_superior.addWidget(lbl_historial)
        barra_superior.addStretch()
        barra_superior.addWidget(btn_nuevo_gasto)
        layout.addLayout(barra_superior)

        self.tabla_gastos = QTableWidget()
        self.tabla_gastos.setColumnCount(5)
        self.tabla_gastos.setHorizontalHeaderLabels(["FECHA", "CATEGORÍA", "DESCRIPCIÓN", "MÉTODO DE PAGO", "MONTO"])
        header = self.tabla_gastos.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        self.tabla_gastos.verticalHeader().setVisible(False)
        self.tabla_gastos.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_gastos.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_gastos.verticalHeader().setDefaultSectionSize(45)
        self.tabla_gastos.setStyleSheet("""
            QTableWidget { background-color: #FFFFFF; color: #334155; border: 1px solid #E2E8F0; border-radius: 6px; font-size: 13px; }
            QTableWidget::item { padding: 5px 15px; border-bottom: 1px solid #F1F5F9; }
            QHeaderView::section { background-color: #F8FAFC; color: #64748B; font-weight: bold; font-size: 11px; padding: 12px; border: none; border-bottom: 2px solid #E2E8F0; text-transform: uppercase; }
        """)
        layout.addWidget(self.tabla_gastos)

    def modal_registrar_gasto(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Registrar Gasto del Local")
        dialog.setFixedWidth(400)
        dialog.setStyleSheet("QDialog { background-color: #FFFFFF; } QLabel { font-weight: bold; color: #334155; } QComboBox, QLineEdit, QDoubleSpinBox { padding: 10px; border: 1px solid #CBD5E1; border-radius: 4px; background-color: #F8FAFC; }")
        
        layout = QFormLayout(dialog)
        layout.setVerticalSpacing(15)

        combo_categoria = QComboBox()
        categorias = ["Nómina y Salarios", "Alquiler de Local", "Servicios (Luz, Agua, Internet)", "Mantenimiento y Limpieza", "Impuestos", "Caja Chica / Otros"]
        combo_categoria.addItems(categorias)

        txt_desc = QLineEdit()
        txt_desc.setPlaceholderText("Ej: Pago de quincena Juan, Internet NetUno...")

        combo_metodo = QComboBox()
        
        # 🔥 AQUÍ ESTÁ LA CORRECCIÓN: Traemos los métodos con todas sus tasas y símbolos
        _, _, _, metodos, _ = db_sales.obtener_datos_configuracion()
        for m in metodos: combo_metodo.addItem(m['nombre'], m)

        spin_monto = QDoubleSpinBox()
        spin_monto.setMaximum(999999.99)
        spin_monto.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        
        lbl_equiv = QLabel("Equivale a: $ 0.00")
        lbl_equiv.setStyleSheet("color: #64748B; font-weight: bold;")

        def actualizar_moneda():
            metodo = combo_metodo.currentData()
            if not metodo: return
            
            spin_monto.setPrefix(f"{metodo['simbolo']} ")
            
            equiv = spin_monto.value() / float(metodo['tasa_cambio'])
            lbl_equiv.setText(f"Equivale a: $ {equiv:.2f}")

        combo_metodo.currentIndexChanged.connect(actualizar_moneda)
        spin_monto.valueChanged.connect(actualizar_moneda)
        actualizar_moneda()

        layout.addRow("Categoría:", combo_categoria)
        layout.addRow("Descripción:", txt_desc)
        layout.addRow("Método (De dónde sale la plata):", combo_metodo)
        layout.addRow("Monto a Pagar:", spin_monto)
        layout.addRow("", lbl_equiv)

        btn_guardar = QPushButton(" Registrar Gasto")
        btn_guardar.setIcon(qta.icon('fa5s.check', color='white'))
        btn_guardar.setStyleSheet("background-color: #DC2626; color: white; padding: 12px; font-weight: bold; border-radius: 4px; font-size: 14px;")
        
        def procesar():
            if spin_monto.value() <= 0 or not txt_desc.text().strip():
                return self.mostrar_mensaje("Error", "Descripción y Monto son obligatorios.", "error")
            
            metodo = combo_metodo.currentData()
            monto_usd = spin_monto.value() / float(metodo['tasa_cambio'])
            
            exito, msg = db_finance.registrar_gasto(combo_categoria.currentText(), txt_desc.text().strip(), monto_usd, metodo['id'], session.usuario_actual['id'])
            if exito:
                self.mostrar_mensaje("Éxito", msg)
                self.cargar_datos()
                dialog.accept()
            else: self.mostrar_mensaje("Error", msg, "error")

        btn_guardar.clicked.connect(procesar)
        layout.addRow(btn_guardar)
        dialog.exec()

    # ==========================================
    # PESTAÑA 2: SALDOS Y BANCOS
    # ==========================================
    def setup_tab_bancos(self):
        layout = QVBoxLayout(self.tab_bancos)
        layout.setContentsMargins(20, 20, 20, 20)
        
        lbl_info = QLabel("DINERO DISPONIBLE POR MÉTODO DE PAGO (Ventas - Gastos)")
        lbl_info.setStyleSheet("font-size: 16px; font-weight: bold; color: #0F172A; margin-bottom: 15px;")
        layout.addWidget(lbl_info)

        self.grid_bancos = QGridLayout()
        self.grid_bancos.setSpacing(20)
        layout.addLayout(self.grid_bancos)
        layout.addStretch()

    def cargar_datos(self):
        # 1. Cargar Historial de Gastos
        gastos = db_finance.obtener_historial_gastos()
        self.tabla_gastos.setRowCount(0)
        for i, g in enumerate(gastos):
            self.tabla_gastos.insertRow(i)
            self.tabla_gastos.setItem(i, 0, QTableWidgetItem(g['fecha'].split('.')[0]))
            self.tabla_gastos.setItem(i, 1, QTableWidgetItem(g['categoria']))
            
            item_desc = QTableWidgetItem(g['descripcion'])
            item_desc.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.tabla_gastos.setItem(i, 2, item_desc)
            
            self.tabla_gastos.setItem(i, 3, QTableWidgetItem(g['metodo_pago']))
            
            item_monto = QTableWidgetItem(f"- $ {g['monto']:.2f}")
            item_monto.setForeground(QColor("#DC2626"))
            item_monto.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            self.tabla_gastos.setItem(i, 4, item_monto)

        # 2. Cargar Saldos de Bancos
        # Limpiar el grid actual
        for i in reversed(range(self.grid_bancos.count())): 
            self.grid_bancos.itemAt(i).widget().setParent(None)
            
        saldos = db_finance.obtener_saldos_cuentas()
        row, col = 0, 0
        for s in saldos:
            frame = QFrame()
            frame.setStyleSheet("""
                QFrame { background-color: #FFFFFF; border-radius: 8px; border: 1px solid #E2E8F0; border-top: 4px solid #38BDF8; }
            """)
            frame.setFixedHeight(110)
            l_frame = QVBoxLayout(frame)
            
            lbl_metodo = QLabel(s['metodo'].upper())
            lbl_metodo.setStyleSheet("font-size: 12px; color: #64748B; font-weight: bold; border: none;")
            
            saldo_usd = float(s['saldo_usd'])
            saldo_local = saldo_usd * float(s['tasa_cambio'])
            
            lbl_usd = QLabel(f"$ {saldo_usd:.2f}")
            lbl_usd.setStyleSheet("font-size: 26px; font-weight: 900; color: #0F172A; border: none;")
            
            lbl_local = QLabel(f"Equiv: {s['simbolo']} {saldo_local:.2f}")
            lbl_local.setStyleSheet("font-size: 12px; color: #10B981; font-weight: bold; border: none;")
            
            l_frame.addWidget(lbl_metodo)
            l_frame.addWidget(lbl_usd)
            l_frame.addWidget(lbl_local)
            
            self.grid_bancos.addWidget(frame, row, col)
            col += 1
            if col > 3: # 4 tarjetas por fila
                col = 0
                row += 1

    def mostrar_mensaje(self, titulo, texto, tipo="info"):
        msg = QMessageBox(self)
        msg.setWindowTitle(titulo)
        msg.setText(texto)
        msg.setStyleSheet("QWidget { background-color: #FFFFFF; color: #0F172A; } QLabel { font-size: 13px; font-weight: bold; border: none; } QPushButton { padding: 8px 20px; background-color: #0F172A; color: white; border-radius: 4px; font-weight: bold; }")
        if tipo == "error": msg.setIcon(QMessageBox.Icon.Warning)
        else: msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()