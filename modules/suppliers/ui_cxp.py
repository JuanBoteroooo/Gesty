import qtawesome as qta
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QMessageBox, QFrame, QAbstractItemView, QComboBox, QDoubleSpinBox, QDialog, QFormLayout, QDateEdit)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QFont
from modules.suppliers import db_cxp, db_suppliers
from modules.settings import db_settings
from utils import session

class VistaCuentasPorPagar(QWidget):
    def __init__(self):
        super().__init__()
        self.deuda_seleccionada = None
        self.setup_ui()
        self.cargar_datos()

    def setup_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(30, 30, 30, 30)
        layout_principal.setSpacing(20)
        
        # CABECERA
        header_layout = QHBoxLayout()
        box_titulos = QVBoxLayout()
        lbl_titulo = QLabel("CUENTAS POR PAGAR (CxP)")
        lbl_titulo.setStyleSheet("font-size: 24px; font-weight: 900; color: #0F172A; letter-spacing: 1px;")
        lbl_subtitulo = QLabel("Gestione las facturas a crédito otorgadas por sus proveedores y registre sus abonos.")
        lbl_subtitulo.setStyleSheet("font-size: 14px; color: #64748B;")
        box_titulos.addWidget(lbl_titulo)
        box_titulos.addWidget(lbl_subtitulo)
        
        btn_nueva_factura = QPushButton(" Registrar Factura a Crédito")
        btn_nueva_factura.setIcon(qta.icon('fa5s.file-invoice-dollar', color='white'))
        btn_nueva_factura.setStyleSheet("background-color: #0F172A; color: white; padding: 12px 20px; border-radius: 6px; font-weight: bold; font-size: 14px;")
        btn_nueva_factura.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_nueva_factura.clicked.connect(self.modal_registrar_factura)
        
        header_layout.addLayout(box_titulos)
        header_layout.addStretch()
        header_layout.addWidget(btn_nueva_factura)
        
        layout_principal.addLayout(header_layout)

        # TABLA DE DEUDAS
        tarjeta = QFrame()
        tarjeta.setStyleSheet("QFrame { background-color: #FFFFFF; border-radius: 8px; border: 1px solid #E2E8F0; }")
        layout_tarjeta = QVBoxLayout(tarjeta)
        layout_tarjeta.setContentsMargins(20, 20, 20, 20)

        lbl_lista = QLabel("Facturas Pendientes por Pagar")
        lbl_lista.setStyleSheet("font-size: 16px; font-weight: bold; color: #0F172A; border: none; margin-bottom: 10px;")
        layout_tarjeta.addWidget(lbl_lista)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(8)
        self.tabla.setHorizontalHeaderLabels(["ID", "PROVEEDOR", "N° FACTURA", "EMITIDA", "VENCIMIENTO", "TOTAL FACTURA", "SALDO DEUDOR", "ACCIONES"])
        
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        self.tabla.setColumnWidth(7, 180)
        
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.verticalHeader().setDefaultSectionSize(50)
        self.tabla.setStyleSheet("""
            QTableWidget { background-color: #FFFFFF; color: #334155; border: none; font-size: 13px; }
            QTableWidget::item { padding: 5px 10px; border-bottom: 1px solid #F1F5F9; }
            QHeaderView::section { background-color: #F8FAFC; color: #64748B; font-weight: bold; font-size: 11px; padding: 12px; border: none; border-bottom: 2px solid #E2E8F0; text-transform: uppercase; }
        """)
        layout_tarjeta.addWidget(self.tabla)
        layout_principal.addWidget(tarjeta)

    # ================= FUNCIONES DE RENDERIZADO =================
    def cargar_datos(self):
        self.tabla.setRowCount(0)
        deudas = db_cxp.obtener_deudas_activas()
        
        for i, d in enumerate(deudas):
            self.tabla.insertRow(i)
            
            item_id = QTableWidgetItem(f"#{d['id']:04d}")
            item_id.setForeground(QColor("#94A3B8"))
            self.tabla.setItem(i, 0, item_id)
            
            item_prov = QTableWidgetItem(d['proveedor'])
            item_prov.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.tabla.setItem(i, 1, item_prov)
            
            self.tabla.setItem(i, 2, QTableWidgetItem(d['numero_factura']))
            self.tabla.setItem(i, 3, QTableWidgetItem(d['fecha_emision']))
            
            # Alerta visual si está vencida
            item_ven = QTableWidgetItem(d['fecha_vencimiento'])
            if QDate.fromString(d['fecha_vencimiento'], "yyyy-MM-dd") < QDate.currentDate():
                item_ven.setForeground(QColor("#DC2626")) # Rojo
                item_ven.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.tabla.setItem(i, 4, item_ven)
            
            self.tabla.setItem(i, 5, QTableWidgetItem(f"$ {d['monto_total']:.2f}"))
            
            item_saldo = QTableWidgetItem(f"$ {d['saldo_pendiente']:.2f}")
            item_saldo.setForeground(QColor("#DC2626"))
            item_saldo.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            self.tabla.setItem(i, 6, item_saldo)
            
            # Botones de Acción
            widget_btn = QWidget()
            l_btn = QHBoxLayout(widget_btn)
            l_btn.setContentsMargins(4, 4, 4, 4)
            l_btn.setSpacing(8)
            
            btn_abonar = QPushButton(" Abonar")
            btn_abonar.setIcon(qta.icon('fa5s.money-bill-wave', color='white'))
            btn_abonar.setStyleSheet("background-color: #10B981; color: white; border-radius: 4px; padding: 6px; font-weight: bold;")
            btn_abonar.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_abonar.clicked.connect(lambda checked, cxp=d: self.modal_abonar(cxp))
            
            btn_historial = QPushButton()
            btn_historial.setIcon(qta.icon('fa5s.history', color='#0F172A'))
            btn_historial.setStyleSheet("background-color: #F1F5F9; border-radius: 4px; padding: 6px;")
            btn_historial.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_historial.clicked.connect(lambda checked, cxp_id=d['id']: self.modal_historial(cxp_id))
            
            l_btn.addWidget(btn_abonar)
            l_btn.addWidget(btn_historial)
            self.tabla.setCellWidget(i, 7, widget_btn)

    # ================= MODALES =================
    def aplicar_estilos_modal(self, dialog):
        dialog.setStyleSheet("""
            QDialog { background-color: #FFFFFF; }
            QLabel { font-weight: bold; color: #334155; }
            QLineEdit, QComboBox, QDoubleSpinBox, QDateEdit { padding: 10px; border: 1px solid #CBD5E1; border-radius: 4px; background-color: #F8FAFC; color: #0F172A; }
            QDateEdit::drop-down { border: none; }
            QCalendarWidget QWidget { color: #0F172A; background-color: #FFFFFF; }
        """)

    def mostrar_mensaje(self, titulo, texto, tipo="info"):
        msg = QMessageBox(self)
        msg.setWindowTitle(titulo)
        msg.setText(texto)
        msg.setStyleSheet("QWidget { background-color: #FFFFFF; color: #0F172A; } QLabel { font-size: 13px; font-weight: bold; border: none; } QPushButton { padding: 8px 20px; background-color: #0F172A; color: white; border-radius: 4px; font-weight: bold; }")
        if tipo == "error": msg.setIcon(QMessageBox.Icon.Warning)
        else: msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()

    def modal_registrar_factura(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Registrar Factura a Crédito")
        dialog.setFixedWidth(400)
        self.aplicar_estilos_modal(dialog)
        
        layout = QFormLayout(dialog)
        layout.setVerticalSpacing(15)

        combo_prov = QComboBox()
        for p in db_suppliers.obtener_proveedores(): combo_prov.addItem(p['nombre'], p['id'])

        txt_factura = QLineEdit()
        txt_factura.setPlaceholderText("Ej: FAC-000123")

        date_emision = QDateEdit()
        date_emision.setCalendarPopup(True)
        date_emision.setDate(QDate.currentDate())

        date_vence = QDateEdit()
        date_vence.setCalendarPopup(True)
        date_vence.setDate(QDate.currentDate().addDays(15)) # Por defecto 15 días de crédito

        spin_monto = QDoubleSpinBox()
        spin_monto.setMaximum(999999.99)
        spin_monto.setPrefix("$ ")
        spin_monto.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)

        layout.addRow("Proveedor:", combo_prov)
        layout.addRow("N° de Factura:", txt_factura)
        layout.addRow("Fecha Emisión:", date_emision)
        layout.addRow("Fecha Límite Pago:", date_vence)
        layout.addRow("Monto Total ($):", spin_monto)

        btn_guardar = QPushButton(" Guardar Factura")
        btn_guardar.setIcon(qta.icon('fa5s.save', color='white'))
        btn_guardar.setStyleSheet("background-color: #0F172A; color: white; padding: 12px; font-weight: bold; border-radius: 4px;")
        
        def procesar():
            if spin_monto.value() <= 0 or not txt_factura.text().strip():
                return self.mostrar_mensaje("Error", "El N° de Factura y el Monto son obligatorios.", "error")
            
            exito, msg = db_cxp.registrar_factura_credito(
                combo_prov.currentData(), txt_factura.text().strip(), 
                date_emision.date().toString("yyyy-MM-dd"), date_vence.date().toString("yyyy-MM-dd"), spin_monto.value()
            )
            if exito:
                self.mostrar_mensaje("Éxito", msg)
                self.cargar_datos()
                dialog.accept()
            else: self.mostrar_mensaje("Error", msg, "error")

        btn_guardar.clicked.connect(procesar)
        layout.addRow(btn_guardar)
        dialog.exec()

    def modal_abonar(self, deuda):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Abonar a Factura {deuda['numero_factura']}")
        dialog.setFixedWidth(400)
        self.aplicar_estilos_modal(dialog)
        
        layout = QFormLayout(dialog)
        layout.setVerticalSpacing(15)
        
        lbl_info = QLabel(f"Deuda Actual: ${deuda['saldo_pendiente']:.2f}")
        lbl_info.setStyleSheet("color: #DC2626; font-size: 16px; font-weight: 900; border: none;")
        layout.addRow(lbl_info)

        combo_metodo = QComboBox()
        for m in db_settings.obtener_metodos_pago(): combo_metodo.addItem(m['nombre'], m['id'])

        spin_monto = QDoubleSpinBox()
        spin_monto.setMaximum(float(deuda['saldo_pendiente']))
        spin_monto.setValue(float(deuda['saldo_pendiente'])) # Sugiere pagar todo
        spin_monto.setPrefix("$ ")
        spin_monto.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)

        layout.addRow("Método de Pago:", combo_metodo)
        layout.addRow("Monto a Abonar ($):", spin_monto)

        btn_guardar = QPushButton(" Registrar Abono")
        btn_guardar.setStyleSheet("background-color: #10B981; color: white; padding: 12px; font-weight: bold; border-radius: 4px;")
        
        def procesar():
            if spin_monto.value() <= 0: return
            
            exito, msg = db_cxp.registrar_abono(deuda['id'], spin_monto.value(), combo_metodo.currentData(), session.usuario_actual['id'])
            if exito:
                self.mostrar_mensaje("Éxito", msg)
                self.cargar_datos()
                dialog.accept()
            else: self.mostrar_mensaje("Error", msg, "error")

        btn_guardar.clicked.connect(procesar)
        layout.addRow(btn_guardar)
        dialog.exec()

    def modal_historial(self, cxp_id):
        dialog = QDialog(self)
        dialog.setWindowTitle("Historial de Pagos")
        dialog.setFixedWidth(500)
        dialog.setStyleSheet("QDialog { background-color: #FFFFFF; }")
        
        layout = QVBoxLayout(dialog)
        tabla_hist = QTableWidget()
        tabla_hist.setColumnCount(4)
        tabla_hist.setHorizontalHeaderLabels(["FECHA", "MONTO", "MÉTODO", "CAJERO"])
        tabla_hist.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tabla_hist.verticalHeader().setVisible(False)
        tabla_hist.setStyleSheet("QTableWidget { border: 1px solid #E2E8F0; } QHeaderView::section { background-color: #F8FAFC; color: #64748B; font-weight: bold; font-size: 11px; }")
        
        abonos = db_cxp.obtener_historial_abonos(cxp_id)
        tabla_hist.setRowCount(len(abonos))
        for i, a in enumerate(abonos):
            tabla_hist.setItem(i, 0, QTableWidgetItem(a['fecha'].split('.')[0]))
            tabla_hist.setItem(i, 1, QTableWidgetItem(f"${a['monto']:.2f}"))
            tabla_hist.setItem(i, 2, QTableWidgetItem(a['metodo']))
            tabla_hist.setItem(i, 3, QTableWidgetItem(a['usuario']))
            
        layout.addWidget(tabla_hist)
        dialog.exec()