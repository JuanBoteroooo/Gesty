from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QAbstractItemView, QDialog, 
                             QFormLayout, QDoubleSpinBox, QComboBox, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from modules.customers import db_cxc
from modules.sales import db_sales
from utils import session

class VistaCXC(QWidget):
    def __init__(self):
        super().__init__()
        self.deuda_seleccionada = None
        self.setup_ui()
        self.cargar_datos()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        
        lbl_titulo = QLabel("📊 Cuentas por Cobrar (Créditos)")
        lbl_titulo.setStyleSheet("font-size: 26px; font-weight: 900; color: #0F172A;")
        layout.addWidget(lbl_titulo)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels(["NRO. VENTA", "CLIENTE", "TOTAL VENTA", "SALDO PENDIENTE", "FECHA VENTA", "VENCIMIENTO"])
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setStyleSheet("QTableWidget { background-color: white; border-radius: 8px; font-weight: bold; }")
        layout.addWidget(self.tabla)

        btn_abono = QPushButton("💵 REGISTRAR ABONO / PAGO")
        btn_abono.setFixedHeight(50)
        btn_abono.setStyleSheet("background-color: #16A34A; color: white; font-weight: bold; font-size: 16px; border-radius: 8px;")
        btn_abono.clicked.connect(self.abrir_modal_abono)
        layout.addWidget(btn_abono)

    def cargar_datos(self):
        self.tabla.setRowCount(0)
        deudas = db_cxc.obtener_cuentas_por_cobrar()
        for i, d in enumerate(deudas):
            self.tabla.insertRow(i)
            item_id = QTableWidgetItem(f"#{d['venta_id']:06d}")
            item_id.setData(Qt.ItemDataRole.UserRole, d)
            self.tabla.setItem(i, 0, item_id)
            self.tabla.setItem(i, 1, QTableWidgetItem(d['cliente_nombre']))
            self.tabla.setItem(i, 2, QTableWidgetItem(f"$ {d['monto_total']:.2f}"))
            
            item_saldo = QTableWidgetItem(f"$ {d['saldo_pendiente']:.2f}")
            item_saldo.setForeground(QColor("#DC2626"))
            self.tabla.setItem(i, 3, item_saldo)
            
            self.tabla.setItem(i, 4, QTableWidgetItem(d['fecha_venta']))
            self.tabla.setItem(i, 5, QTableWidgetItem(d['fecha_vencimiento']))

    def abrir_modal_abono(self):
        filas = self.tabla.selectedItems()
        if not filas: return QMessageBox.warning(self, "Aviso", "Selecciona una deuda de la lista.")
        deuda = self.tabla.item(filas[0].row(), 0).data(Qt.ItemDataRole.UserRole)

        # Verificar si hay caja abierta
        sesion = db_sales.verificar_caja_abierta()
        if not sesion: return QMessageBox.warning(self, "Caja Cerrada", "Debes abrir turno de caja para recibir dinero.")

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Abono - {deuda['cliente_nombre']}")
        dialog.setFixedWidth(350)
        layout = QFormLayout(dialog)

        lbl_info = QLabel(f"Deuda pendiente: $ {deuda['saldo_pendiente']:.2f}")
        lbl_info.setStyleSheet("color: #DC2626; font-weight: bold; font-size: 14px;")
        layout.addRow(lbl_info)

        spin_monto = QDoubleSpinBox()
        spin_monto.setRange(0.01, deuda['saldo_pendiente'])
        spin_monto.setValue(deuda['saldo_pendiente'])
        spin_monto.setPrefix("$ ")
        layout.addRow("Monto a pagar:", spin_monto)

        combo_metodo = QComboBox()
        # Traer métodos de pago (Usamos la moneda principal para abonos por ahora)
        _, _, _, metodos, _ = db_sales.obtener_datos_configuracion()
        for m in metodos: combo_metodo.addItem(m['nombre'], m['id'])
        layout.addRow("Método de pago:", combo_metodo)

        btn_confirmar = QPushButton("Confirmar Abono")
        btn_confirmar.setStyleSheet("background-color: #2563EB; color: white; padding: 10px; font-weight: bold;")
        
        def confirmar():
            exito, msg = db_cxc.registrar_abono(deuda['id'], spin_monto.value(), combo_metodo.currentData(), sesion['id'])
            if exito:
                QMessageBox.information(dialog, "Éxito", msg)
                self.cargar_datos()
                dialog.accept()
            else: QMessageBox.critical(dialog, "Error", msg)

        btn_confirmar.clicked.connect(confirmar)
        layout.addRow(btn_confirmar)
        dialog.exec()