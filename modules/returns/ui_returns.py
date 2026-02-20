from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QMessageBox, QFrame, QAbstractItemView)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from modules.returns import db_returns

class VistaDevoluciones(QWidget):
    def __init__(self):
        super().__init__()
        self.factura_seleccionada = None
        self.setup_ui()
        self.cargar_facturas() # Carga las últimas facturas al abrir

    def setup_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(40, 40, 40, 40)
        layout_principal.setSpacing(20)
        
        # --- Encabezado ---
        lbl_titulo = QLabel("🔄 Devoluciones y Anulaciones")
        lbl_titulo.setStyleSheet("font-size: 28px; font-weight: 900; color: #0F172A; margin-bottom: 5px;")
        lbl_subtitulo = QLabel("Busca una factura para anularla y retornar automáticamente los productos al stock.")
        lbl_subtitulo.setStyleSheet("font-size: 14px; color: #64748B; margin-bottom: 15px;")
        layout_principal.addWidget(lbl_titulo)
        layout_principal.addWidget(lbl_subtitulo)
        
        tarjeta = QFrame()
        tarjeta.setStyleSheet("QFrame { background-color: #FFFFFF; border-radius: 12px; border: 1px solid #E2E8F0; }")
        layout_tarjeta = QVBoxLayout(tarjeta)
        layout_tarjeta.setContentsMargins(20, 20, 20, 20)
        layout_tarjeta.setSpacing(15)
        
        # --- Buscador ---
        box_buscador = QHBoxLayout()
        self.txt_buscador = QLineEdit()
        self.txt_buscador.setPlaceholderText("🔍 Buscar por N° de Factura, Nombre de Cliente o Cédula/RIF...")
        self.txt_buscador.setFixedHeight(45)
        self.txt_buscador.setStyleSheet("padding: 5px 15px; border: 2px solid #CBD5E1; border-radius: 6px; font-size: 15px; color: #000000; background-color: #F8FAFC;")
        self.txt_buscador.textChanged.connect(self.cargar_facturas)
        box_buscador.addWidget(self.txt_buscador)
        layout_tarjeta.addLayout(box_buscador)
        
        # --- Tabla Principal: Facturas ---
        layout_tarjeta.addWidget(QLabel("<b>Historial de Facturas (Últimas 50)</b>", styleSheet="font-size: 14px; color: #0F172A;"))
        self.tabla_facturas = QTableWidget()
        self.tabla_facturas.setColumnCount(5)
        self.tabla_facturas.setHorizontalHeaderLabels(["N° FACTURA", "FECHA", "CLIENTE", "DOCUMENTO", "TOTAL PAGADO"])
        self.tabla_facturas.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_facturas.verticalHeader().setVisible(False)
        self.tabla_facturas.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_facturas.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla_facturas.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_facturas.setStyleSheet("""
            QTableWidget { background-color: #FFFFFF; color: #000000; border: 1px solid #E2E8F0; border-radius: 6px; font-size: 13px; font-weight: bold; }
            QTableWidget::item { padding: 10px; border-bottom: 1px solid #F1F5F9; }
            QTableWidget::item:selected { background-color: #EFF6FF; color: #1E3A8A; }
            QHeaderView::section { background-color: #F8FAFC; color: #64748B; font-weight: bold; font-size: 12px; padding: 12px; border: none; border-bottom: 2px solid #E2E8F0; }
        """)
        self.tabla_facturas.itemSelectionChanged.connect(self.seleccionar_factura)
        layout_tarjeta.addWidget(self.tabla_facturas)
        
        # --- Tabla Secundaria: Detalles de la Factura ---
        layout_tarjeta.addWidget(QLabel("<b>Productos contenidos en la factura seleccionada:</b>", styleSheet="font-size: 14px; color: #0F172A; margin-top: 10px;"))
        self.tabla_detalles = QTableWidget()
        self.tabla_detalles.setColumnCount(5)
        self.tabla_detalles.setHorizontalHeaderLabels(["CÓDIGO", "DESCRIPCIÓN", "CANTIDAD", "PRECIO UNIT.", "SUBTOTAL"])
        self.tabla_detalles.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_detalles.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla_detalles.verticalHeader().setVisible(False)
        self.tabla_detalles.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_detalles.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_detalles.setFixedHeight(180)
        self.tabla_detalles.setStyleSheet("""
            QTableWidget { background-color: #F8FAFC; color: #475569; border: 1px solid #CBD5E1; border-radius: 6px; font-size: 13px; }
            QHeaderView::section { background-color: #E2E8F0; color: #475569; font-weight: bold; font-size: 12px; padding: 8px; border: none; }
        """)
        layout_tarjeta.addWidget(self.tabla_detalles)
        
        # --- Botón de Acción ---
        box_btn = QHBoxLayout()
        box_btn.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.btn_devolver = QPushButton("⚠️ ANULAR FACTURA Y DEVOLVER STOCK")
        self.btn_devolver.setEnabled(False) # Se activa solo si hay una factura seleccionada
        self.btn_devolver.setFixedHeight(50)
        self.btn_devolver.setStyleSheet("""
            QPushButton { background-color: #DC2626; color: white; border-radius: 6px; font-weight: bold; font-size: 15px; padding: 0 25px; } 
            QPushButton:hover { background-color: #B91C1C; }
            QPushButton:disabled { background-color: #FCA5A5; color: #FEF2F2; }
        """)
        self.btn_devolver.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_devolver.clicked.connect(self.procesar_devolucion)
        box_btn.addWidget(self.btn_devolver)
        
        layout_tarjeta.addLayout(box_btn)
        layout_principal.addWidget(tarjeta)

    def cargar_datos(self):
        """Función reactiva requerida por main.py al cambiar de pestaña"""
        self.txt_buscador.clear()
        self.cargar_facturas()

    def cargar_facturas(self):
        self.tabla_facturas.setRowCount(0)
        self.tabla_detalles.setRowCount(0)
        self.factura_seleccionada = None
        self.btn_devolver.setEnabled(False)
        
        termino = self.txt_buscador.text().strip()
        facturas = db_returns.buscar_facturas(termino)
        
        for i, f in enumerate(facturas):
            self.tabla_facturas.insertRow(i)
            
            item_id = QTableWidgetItem(f"{f['id']:06d}")
            item_id.setData(Qt.ItemDataRole.UserRole, f['id'])
            
            self.tabla_facturas.setItem(i, 0, item_id)
            self.tabla_facturas.setItem(i, 1, QTableWidgetItem(f['fecha_hora']))
            self.tabla_facturas.setItem(i, 2, QTableWidgetItem(f['cliente_nombre']))
            self.tabla_facturas.setItem(i, 3, QTableWidgetItem(f['cliente_doc']))
            
            total_str = f"{f['moneda_simbolo']} {f['total_venta']:.2f}"
            item_total = QTableWidgetItem(total_str)
            item_total.setForeground(QColor("#16A34A"))
            self.tabla_facturas.setItem(i, 4, item_total)

    def seleccionar_factura(self):
        filas = self.tabla_facturas.selectedItems()
        if filas:
            self.factura_seleccionada = self.tabla_facturas.item(filas[0].row(), 0).data(Qt.ItemDataRole.UserRole)
            self.btn_devolver.setEnabled(True)
            self.cargar_detalles()
        else:
            self.factura_seleccionada = None
            self.btn_devolver.setEnabled(False)
            self.tabla_detalles.setRowCount(0)

    def cargar_detalles(self):
        if not self.factura_seleccionada: return
        
        self.tabla_detalles.setRowCount(0)
        detalles = db_returns.obtener_detalles_factura(self.factura_seleccionada)
        
        for i, d in enumerate(detalles):
            self.tabla_detalles.insertRow(i)
            self.tabla_detalles.setItem(i, 0, QTableWidgetItem(d['codigo']))
            self.tabla_detalles.setItem(i, 1, QTableWidgetItem(d['nombre']))
            self.tabla_detalles.setItem(i, 2, QTableWidgetItem(str(d['cantidad'])))
            self.tabla_detalles.setItem(i, 3, QTableWidgetItem(f"${d['precio_unitario']:.2f}"))
            self.tabla_detalles.setItem(i, 4, QTableWidgetItem(f"${d['subtotal']:.2f}"))

    def procesar_devolucion(self):
        if not self.factura_seleccionada: return
        
        respuesta = QMessageBox.question(
            self, "Confirmar Anulación", 
            f"¿Estás seguro que deseas ANULAR COMPLETAMENTE la factura #{self.factura_seleccionada:06d}?\n\nEsto devolverá todos los productos al inventario y borrará los registros de pago.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if respuesta == QMessageBox.StandardButton.Yes:
            exito, msg = db_returns.procesar_devolucion(self.factura_seleccionada)
            if exito:
                QMessageBox.information(self, "Éxito", msg)
                self.cargar_facturas() # Recarga todo para que la factura desaparezca
            else:
                QMessageBox.critical(self, "Error", msg)