import qtawesome as qta
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QMessageBox, QFrame, QAbstractItemView, QInputDialog)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QFont
from modules.returns import db_returns
from utils import session

class VistaDevoluciones(QWidget):
    def __init__(self):
        super().__init__()
        self.factura_seleccionada = None
        self.setup_ui()
        self.cargar_facturas()

    def setup_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(30, 30, 30, 30)
        layout_principal.setSpacing(25)
        
        # ==========================================
        # CABECERA DEL MÓDULO
        # ==========================================
        header_layout = QVBoxLayout()
        header_layout.setSpacing(5)
        
        lbl_titulo = QLabel("DEVOLUCIONES Y ANULACIONES")
        lbl_titulo.setStyleSheet("font-size: 24px; font-weight: 900; color: #0F172A; letter-spacing: 1px;")
        
        lbl_subtitulo = QLabel("Busque una factura para anularla por completo o devolver productos específicos al inventario.")
        lbl_subtitulo.setStyleSheet("font-size: 14px; color: #64748B;")
        
        header_layout.addWidget(lbl_titulo)
        header_layout.addWidget(lbl_subtitulo)
        layout_principal.addLayout(header_layout)
        
        # ==========================================
        # TARJETA PRINCIPAL (CONTENEDOR)
        # ==========================================
        tarjeta = QFrame()
        tarjeta.setStyleSheet("QFrame { background-color: #FFFFFF; border-radius: 8px; border: 1px solid #E2E8F0; }")
        layout_tarjeta = QVBoxLayout(tarjeta)
        layout_tarjeta.setContentsMargins(25, 25, 25, 25)
        layout_tarjeta.setSpacing(20)
        
        # --- BUSCADOR ---
        self.txt_buscador = QLineEdit()
        self.txt_buscador.setPlaceholderText("Buscar por N° de Factura, Razón Social o Documento del cliente...")
        self.txt_buscador.setFixedHeight(45)
        self.txt_buscador.setStyleSheet("""
            QLineEdit { padding: 5px 15px; border: 1px solid #CBD5E1; border-radius: 6px; font-size: 14px; color: #0F172A; background-color: #F8FAFC; }
            QLineEdit:focus { border: 2px solid #38BDF8; background-color: #FFFFFF; }
        """)
        self.txt_buscador.textChanged.connect(self.cargar_facturas)
        layout_tarjeta.addWidget(self.txt_buscador)
        
        # --- TABLA PRINCIPAL: FACTURAS ---
        lbl_historial = QLabel("HISTORIAL DE FACTURAS EMITIDAS (ÚLTIMAS 50)")
        lbl_historial.setStyleSheet("font-size: 12px; font-weight: bold; color: #64748B; margin-top: 5px;")
        layout_tarjeta.addWidget(lbl_historial)
        
        self.tabla_facturas = QTableWidget()
        self.tabla_facturas.setColumnCount(5)
        self.tabla_facturas.setHorizontalHeaderLabels(["N° FACTURA", "FECHA Y HORA", "CLIENTE", "DOCUMENTO", "TOTAL PAGADO"])
        
        header_facturas = self.tabla_facturas.horizontalHeader()
        header_facturas.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_facturas.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header_facturas.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header_facturas.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header_facturas.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header_facturas.setStretchLastSection(False)
        
        self.tabla_facturas.verticalHeader().setVisible(False)
        self.tabla_facturas.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_facturas.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla_facturas.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_facturas.verticalHeader().setDefaultSectionSize(45)
        
        self.tabla_facturas.setStyleSheet("""
            QTableWidget { background-color: #FFFFFF; color: #334155; border: 1px solid #E2E8F0; border-radius: 6px; font-size: 13px; font-weight: bold;}
            QTableWidget::item { padding: 5px 15px; border-bottom: 1px solid #F1F5F9; }
            QTableWidget::item:selected { background-color: #EFF6FF; color: #0F172A; }
            QHeaderView::section { background-color: #F8FAFC; color: #64748B; font-weight: bold; font-size: 11px; padding: 12px; border: none; border-bottom: 2px solid #E2E8F0; text-transform: uppercase; }
        """)
        self.tabla_facturas.itemSelectionChanged.connect(self.seleccionar_factura)
        layout_tarjeta.addWidget(self.tabla_facturas)
        
        # --- TABLA SECUNDARIA: DETALLES (CON BOTÓN DE DEVOLVER) ---
        lbl_detalles = QLabel("PRODUCTOS CONTENIDOS EN LA FACTURA SELECCIONADA")
        lbl_detalles.setStyleSheet("font-size: 12px; font-weight: bold; color: #64748B; margin-top: 10px;")
        layout_tarjeta.addWidget(lbl_detalles)
        
        self.tabla_detalles = QTableWidget()
        self.tabla_detalles.setColumnCount(6)
        self.tabla_detalles.setHorizontalHeaderLabels(["CÓDIGO", "DESCRIPCIÓN DE PRODUCTO", "CANT.", "PRECIO", "SUBTOTAL", "ACCIÓN"])
        
        header_detalles = self.tabla_detalles.horizontalHeader()
        header_detalles.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_detalles.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header_detalles.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header_detalles.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header_detalles.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header_detalles.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed) 
        self.tabla_detalles.setColumnWidth(5, 110)
        header_detalles.setStretchLastSection(False)
        
        self.tabla_detalles.verticalHeader().setVisible(False)
        self.tabla_detalles.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_detalles.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_detalles.verticalHeader().setDefaultSectionSize(45)
        self.tabla_detalles.setFixedHeight(220)
        
        self.tabla_detalles.setStyleSheet("""
            QTableWidget { background-color: #F8FAFC; color: #475569; border: 1px solid #CBD5E1; border-radius: 6px; font-size: 13px; font-weight: bold; }
            QTableWidget::item { padding: 5px 15px; border-bottom: 1px solid #E2E8F0; }
            QHeaderView::section { background-color: #E2E8F0; color: #475569; font-weight: bold; font-size: 11px; padding: 10px; border: none; text-transform: uppercase;}
        """)
        layout_tarjeta.addWidget(self.tabla_detalles)
        
        # --- BOTÓN DE ACCIÓN (ANULAR TODA LA FACTURA) ---
        box_btn = QHBoxLayout()
        box_btn.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.btn_devolver = QPushButton("ANULAR FACTURA COMPLETA Y DEVOLVER TODO")
        self.btn_devolver.setEnabled(False) 
        self.btn_devolver.setFixedHeight(50)
        self.btn_devolver.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_devolver.setStyleSheet("""
            QPushButton { background-color: #DC2626; color: white; border-radius: 6px; font-weight: 900; font-size: 14px; padding: 0 30px; letter-spacing: 1px; } 
            QPushButton:hover { background-color: #B91C1C; }
            QPushButton:disabled { background-color: #F1F5F9; color: #94A3B8; border: 1px solid #E2E8F0; }
        """)
        self.btn_devolver.clicked.connect(self.procesar_devolucion_total)
        box_btn.addWidget(self.btn_devolver)
        
        layout_tarjeta.addLayout(box_btn)
        layout_principal.addWidget(tarjeta)

    # ================= FUNCIONES DE RENDERIZADO =================
    def cargar_datos(self):
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
            item_id.setForeground(QColor("#94A3B8"))
            item_id.setData(Qt.ItemDataRole.UserRole, f['id'])
            self.tabla_facturas.setItem(i, 0, item_id)
            self.tabla_facturas.setItem(i, 1, QTableWidgetItem(f['fecha_hora']))
            self.tabla_facturas.setItem(i, 2, QTableWidgetItem(f['cliente_nombre']))
            self.tabla_facturas.setItem(i, 3, QTableWidgetItem(f['cliente_doc']))
            
            total_str = f"{f['moneda_simbolo']} {f['total_venta']:.2f}"
            item_total = QTableWidgetItem(total_str)
            item_total.setForeground(QColor("#10B981"))
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
            
            item_codigo = QTableWidgetItem(d['codigo'])
            item_codigo.setForeground(QColor("#64748B"))
            self.tabla_detalles.setItem(i, 0, item_codigo)
            
            item_desc = QTableWidgetItem(d['nombre'])
            item_desc.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            item_desc.setForeground(QColor("#0F172A"))
            self.tabla_detalles.setItem(i, 1, item_desc)
            
            self.tabla_detalles.setItem(i, 2, QTableWidgetItem(str(d['cantidad'])))
            self.tabla_detalles.setItem(i, 3, QTableWidgetItem(f"${d['precio_unitario']:.2f}"))
            self.tabla_detalles.setItem(i, 4, QTableWidgetItem(f"${d['subtotal']:.2f}"))
            
            # Botón de devolución parcial en cada fila
            btn_rev = QPushButton(" Devolver")
            btn_rev.setIcon(qta.icon('fa5s.undo', color='white'))
            btn_rev.setStyleSheet("background-color: #DC2626; color: white; border-radius: 4px; padding: 6px; font-weight: bold; font-size: 11px;")
            btn_rev.setCursor(Qt.CursorShape.PointingHandCursor)
            
            btn_rev.clicked.connect(lambda checked, det_id=d['id'], max_cant=d['cantidad'], nom=d['nombre']: self.procesar_devolucion_parcial(det_id, max_cant, nom))
            
            widget_btn = QWidget()
            l_btn = QHBoxLayout(widget_btn)
            l_btn.setContentsMargins(4, 4, 4, 4)
            l_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l_btn.addWidget(btn_rev)
            self.tabla_detalles.setCellWidget(i, 5, widget_btn)

    # ================= 🔥 ALERTAS Y MENSAJES CORREGIDOS (BLANCO PURO) 🔥 =================
    def mostrar_mensaje(self, titulo, texto, tipo="info"):
        msg = QMessageBox(self)
        msg.setWindowTitle(titulo)
        msg.setText(texto)
        # Forzamos QWidget a blanco para sobreescribir la herencia oscura
        msg.setStyleSheet("""
            QWidget { background-color: #FFFFFF; color: #0F172A; } 
            QLabel { font-size: 13px; font-weight: bold; border: none; } 
            QPushButton { padding: 8px 20px; background-color: #0F172A; color: white; border-radius: 4px; font-weight: bold; } 
            QPushButton:hover { background-color: #1E293B; }
        """)
        if tipo == "error": msg.setIcon(QMessageBox.Icon.Warning)
        else: msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()

    def procesar_devolucion_parcial(self, detalle_id, max_cant, nombre_prod):
        # Usamos un QInputDialog instanciado en lugar de estático para poder forzar el color blanco
        dialog = QInputDialog(self)
        dialog.setWindowTitle("Devolución Parcial")
        dialog.setLabelText(f"¿Cuántas unidades de {nombre_prod} desea devolver al inventario?\n(Compró {max_cant} unidades)")
        dialog.setIntRange(1, int(max_cant))
        dialog.setIntValue(1)
        
        # Forzamos fondo blanco y elementos claros
        dialog.setStyleSheet("""
            QWidget { background-color: #FFFFFF; color: #0F172A; } 
            QLabel { font-size: 13px; font-weight: bold; border: none; } 
            QSpinBox { padding: 8px; border: 1px solid #CBD5E1; border-radius: 4px; font-size: 14px; font-weight: bold; }
            QPushButton { padding: 8px 20px; background-color: #0F172A; color: white; border-radius: 4px; font-weight: bold; } 
            QPushButton:hover { background-color: #1E293B; }
        """)
        
        if dialog.exec():
            cant_dev = dialog.intValue()
            exito, msg = db_returns.procesar_devolucion_parcial(self.factura_seleccionada, detalle_id, cant_dev, session.usuario_actual['id'])
            if exito:
                self.mostrar_mensaje("Devolución Exitosa", msg)
                self.cargar_facturas() 
            else:
                self.mostrar_mensaje("Error", msg, "error")

    def procesar_devolucion_total(self):
        if not self.factura_seleccionada: return
        
        msg_confirm = QMessageBox(self)
        msg_confirm.setWindowTitle("Atención: Anulación Total")
        msg_confirm.setText(f"¿Estás seguro que deseas ANULAR COMPLETAMENTE la factura #{self.factura_seleccionada:06d}?\n\nTodos los productos listados arriba volverán al inventario y se descontarán del dinero/deuda de la venta.")
        msg_confirm.setIcon(QMessageBox.Icon.Warning)
        msg_confirm.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        # Forzamos fondo blanco
        msg_confirm.setStyleSheet("""
            QWidget { background-color: #FFFFFF; color: #0F172A; } 
            QLabel { font-size: 13px; font-weight: bold; border: none; } 
            QPushButton { padding: 8px 20px; background-color: #DC2626; color: white; border-radius: 4px; font-weight: bold; } 
            QPushButton:hover { background-color: #B91C1C; }
        """)
        
        if msg_confirm.exec() == QMessageBox.StandardButton.Yes:
            exito, msg = db_returns.procesar_devolucion(self.factura_seleccionada)
            if exito:
                self.mostrar_mensaje("Anulación Exitosa", msg)
                self.cargar_facturas() 
            else:
                self.mostrar_mensaje("Error", msg, "error")