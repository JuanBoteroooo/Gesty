import qtawesome as qta
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QDialog, QFormLayout, QMessageBox, QFrame, 
                             QAbstractItemView, QTabWidget, QComboBox, QSpinBox, QDoubleSpinBox)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QFont
from modules.suppliers import db_suppliers
from utils import session

class VistaProveedores(QWidget):
    def __init__(self):
        super().__init__()
        self.proveedor_seleccionado = None
        self.carrito_compra = {}
        self.proveedores = []
        self.almacenes = []
        
        self.setup_ui()
        self.cargar_datos()

    def setup_ui(self):
        self.installEventFilter(self)
        
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(40, 40, 40, 40)
        layout_principal.setSpacing(25)
        
        # ==========================================
        # CABECERA DEL MÓDULO
        # ==========================================
        header_layout = QVBoxLayout()
        header_layout.setSpacing(5)
        
        lbl_titulo = QLabel("PROVEEDORES Y COMPRAS")
        lbl_titulo.setStyleSheet("font-size: 24px; font-weight: 900; color: #0F172A; letter-spacing: 1px;")
        lbl_subtitulo = QLabel("Gestión de proveedores e ingreso de facturas de compra al inventario.")
        lbl_subtitulo.setStyleSheet("font-size: 14px; color: #64748B;")
        
        header_layout.addWidget(lbl_titulo)
        header_layout.addWidget(lbl_subtitulo)
        layout_principal.addLayout(header_layout)
        
        # ==========================================
        # CONTENEDOR DE PESTAÑAS (TABS)
        # ==========================================
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { 
                border: 1px solid #E2E8F0; 
                background: #FFFFFF; 
                border-radius: 8px; 
            }
            QTabBar::tab { 
                background: #F1F5F9; 
                color: #64748B; 
                padding: 12px 30px; 
                border-top-left-radius: 8px; 
                border-top-right-radius: 8px; 
                font-weight: bold; 
                margin-right: 2px; 
                font-size: 13px; 
            }
            QTabBar::tab:selected { 
                background: #FFFFFF; 
                color: #0F172A; 
                border-top: 3px solid #38BDF8; 
                border-left: 1px solid #E2E8F0;
                border-right: 1px solid #E2E8F0;
                border-bottom: none;
            }
            QTabBar::tab:hover:!selected { 
                background: #E2E8F0; 
                color: #334155;
            }
        """)
        
        self.tab_compras = QWidget()
        self.tab_directorio = QWidget()
        
        self.setup_tab_compras()
        self.setup_tab_directorio()
        
        self.tabs.addTab(self.tab_compras, "Ingreso de Facturas de Compra")
        self.tabs.addTab(self.tab_directorio, "Directorio de Proveedores")
        
        layout_principal.addWidget(self.tabs)

    # ================= EVENTOS DE TECLADO =================
    def eventFilter(self, source, event):
        if event.type() == event.Type.KeyPress:
            if source is self.txt_buscador_compra and event.key() == Qt.Key.Key_Down:
                if self.tabla_busqueda_compra.rowCount() > 0:
                    self.tabla_busqueda_compra.setFocus()
                    self.tabla_busqueda_compra.selectRow(0) 
                    return True 
                    
            elif source is self.tabla_busqueda_compra and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                item = self.tabla_busqueda_compra.currentItem()
                if item:
                    self.agregar_al_carrito_compra(item)
                    return True
                    
        return super().eventFilter(source, event)

    # ================= MÉTODOS GLOBALES =================
    def cargar_datos(self):
        self.cargar_directorio()
        self.cargar_configuracion_compras()

    def mostrar_mensaje(self, titulo, texto, tipo="info"):
        msg = QMessageBox(self)
        msg.setWindowTitle(titulo)
        msg.setText(texto)
        msg.setStyleSheet("""
            QMessageBox { background-color: #FFFFFF; }
            QLabel { color: #0F172A; font-size: 13px; font-weight: bold; } 
            QPushButton { padding: 6px 20px; background-color: #0F172A; color: white; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #1E293B; }
        """)
        if tipo == "error": msg.setIcon(QMessageBox.Icon.Warning)
        else: msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()

    # ================= PESTAÑA 1: INGRESO DE COMPRAS =================
    def setup_tab_compras(self):
        layout_principal = QHBoxLayout(self.tab_compras)
        layout_principal.setContentsMargins(25, 25, 25, 25)
        layout_principal.setSpacing(20)
        
        # --- PANEL IZQUIERDO ---
        panel_izq = QVBoxLayout()
        panel_izq.setSpacing(15)
        
        self.txt_buscador_compra = QLineEdit()
        self.txt_buscador_compra.setPlaceholderText("Buscar producto a ingresar (Presiona ↓ para seleccionar)...")
        self.txt_buscador_compra.setFixedHeight(45)
        self.txt_buscador_compra.setStyleSheet("""
            QLineEdit {
                padding: 5px 15px; 
                border: 1px solid #CBD5E1; 
                border-radius: 6px; 
                font-size: 14px; 
                color: #0F172A; 
                background-color: #F8FAFC;
            }
            QLineEdit:focus {
                border: 2px solid #38BDF8;
                background-color: #FFFFFF;
            }
        """)
        self.txt_buscador_compra.textChanged.connect(self.buscar_productos_compra)
        self.txt_buscador_compra.installEventFilter(self)
        panel_izq.addWidget(self.txt_buscador_compra)
        
        # TABLA DE BÚSQUEDA
        self.tabla_busqueda_compra = QTableWidget()
        self.tabla_busqueda_compra.setColumnCount(3)
        self.tabla_busqueda_compra.setHorizontalHeaderLabels(["ID", "PRODUCTO", "ÚLTIMO COSTO"])
        
        header_busqueda = self.tabla_busqueda_compra.horizontalHeader()
        header_busqueda.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_busqueda.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header_busqueda.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header_busqueda.setStretchLastSection(False)
        
        self.tabla_busqueda_compra.verticalHeader().setVisible(False)
        self.tabla_busqueda_compra.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_busqueda_compra.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla_busqueda_compra.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_busqueda_compra.verticalHeader().setDefaultSectionSize(45)
        self.tabla_busqueda_compra.setFixedHeight(180)
        
        self.tabla_busqueda_compra.setStyleSheet("""
            QTableWidget { background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px; color: #334155; font-size: 13px; font-weight: bold; }
            QTableWidget::item { padding: 5px 15px; border-bottom: 1px solid #F1F5F9; }
            QTableWidget::item:selected { background-color: #EFF6FF; color: #0F172A; }
            QHeaderView::section { background-color: #F8FAFC; color: #64748B; font-weight: bold; font-size: 12px; padding: 12px; border: none; border-bottom: 2px solid #E2E8F0; text-transform: uppercase; }
        """)
        self.tabla_busqueda_compra.itemDoubleClicked.connect(self.agregar_al_carrito_compra)
        self.tabla_busqueda_compra.installEventFilter(self)
        panel_izq.addWidget(self.tabla_busqueda_compra)
        
        lbl_carrito = QLabel("DETALLE DE LA FACTURA A INGRESAR")
        lbl_carrito.setStyleSheet("font-size: 14px; font-weight: 800; color: #0F172A; margin-top: 10px;")
        panel_izq.addWidget(lbl_carrito)
        
        # TABLA DEL CARRITO
        self.tabla_carrito_compra = QTableWidget()
        self.tabla_carrito_compra.setColumnCount(6)
        # 🔥 EL SECRETO ESTÁ AQUÍ: Le damos un nombre a la última columna ("ACCIÓN") para que el borde gris se dibuje completo
        self.tabla_carrito_compra.setHorizontalHeaderLabels(["ID", "PRODUCTO", "CANTIDAD", "COSTO U. ($)", "SUBTOTAL ($)", "ACCIÓN"])
        
        header_carrito = self.tabla_carrito_compra.horizontalHeader()
        header_carrito.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) 
        header_carrito.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)          
        header_carrito.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) 
        header_carrito.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) 
        header_carrito.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents) 
        # 🔥 Y FIJAMOS EL ANCHO DE LA ACCIÓN A 80PX EXACTOS
        header_carrito.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed) 
        self.tabla_carrito_compra.setColumnWidth(5, 80) 
        header_carrito.setStretchLastSection(False) 
        
        self.tabla_carrito_compra.verticalHeader().setVisible(False)
        self.tabla_carrito_compra.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_carrito_compra.verticalHeader().setDefaultSectionSize(55) 
        
        self.tabla_carrito_compra.setStyleSheet("""
            QTableWidget { background-color: #FFFFFF; color: #334155; border: 1px solid #E2E8F0; border-radius: 6px; font-size: 14px; font-weight: bold; }
            QTableWidget::item { padding: 5px 15px; border-bottom: 1px solid #F1F5F9; }
            QTableWidget::item:selected { background-color: #EFF6FF; color: #0F172A; }
            QHeaderView::section { background-color: #F8FAFC; color: #64748B; font-weight: bold; font-size: 11px; padding: 12px; border: none; border-bottom: 2px solid #E2E8F0; text-transform: uppercase; }
        """)
        panel_izq.addWidget(self.tabla_carrito_compra)
        
        # --- PANEL DERECHO ---
        panel_der = QFrame()
        panel_der.setFixedWidth(350)
        panel_der.setStyleSheet("QFrame { background-color: #F8FAFC; border-radius: 8px; border: 1px solid #E2E8F0; }")
        layout_der = QVBoxLayout(panel_der)
        layout_der.setContentsMargins(25, 25, 25, 25)
        layout_der.setSpacing(20)
        
        estilo_lbl = "font-size: 13px; font-weight: bold; color: #64748B;"
        estilo_input = """
            QComboBox, QLineEdit {
                padding: 12px; border: 1px solid #CBD5E1; border-radius: 6px; 
                background-color: #FFFFFF; color: #0F172A; font-weight: bold; font-size: 14px;
            }
            QComboBox:focus, QLineEdit:focus { border: 2px solid #38BDF8; }
            QComboBox QAbstractItemView { background-color: #FFFFFF; color: #0F172A; selection-background-color: #F8FAFC; }
        """
        
        layout_der.addWidget(QLabel("Proveedor Emisor:", styleSheet=estilo_lbl))
        self.combo_prov_compra = QComboBox()
        self.combo_prov_compra.setStyleSheet(estilo_input)
        layout_der.addWidget(self.combo_prov_compra)
        
        layout_der.addWidget(QLabel("Nro. Factura Proveedor (Opcional):", styleSheet=estilo_lbl))
        self.txt_nro_factura = QLineEdit()
        self.txt_nro_factura.setStyleSheet(estilo_input)
        layout_der.addWidget(self.txt_nro_factura)
        
        layout_der.addWidget(QLabel("Almacén de Recepción:", styleSheet=estilo_lbl))
        self.combo_almacen_compra = QComboBox()
        self.combo_almacen_compra.setStyleSheet(estilo_input)
        layout_der.addWidget(self.combo_almacen_compra)
        
        layout_der.addStretch()
        
        self.lbl_total_compra = QLabel("TOTAL: $ 0.00")
        self.lbl_total_compra.setStyleSheet("font-size: 28px; font-weight: 900; color: #DC2626; text-align: center; margin-bottom: 10px;")
        self.lbl_total_compra.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_der.addWidget(self.lbl_total_compra)
        
        btn_procesar = QPushButton("Registrar Compra")
        btn_procesar.setFixedHeight(55)
        btn_procesar.setStyleSheet("""
            QPushButton { background-color: #0F172A; color: white; border-radius: 6px; font-weight: bold; font-size: 15px; } 
            QPushButton:hover { background-color: #1E293B; }
        """)
        btn_procesar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_procesar.clicked.connect(self.procesar_compra_final)
        layout_der.addWidget(btn_procesar)
        
        layout_principal.addLayout(panel_izq, stretch=70)
        layout_principal.addWidget(panel_der, stretch=30)

    # ================= PESTAÑA 2: DIRECTORIO DE PROVEEDORES =================
    def setup_tab_directorio(self):
        layout = QVBoxLayout(self.tab_directorio)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        barra = QHBoxLayout()
        barra.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        estilo_btn_primario = """
            QPushButton { padding: 10px 15px; border-radius: 6px; font-weight: bold; font-size: 13px; background-color: #0F172A; color: white; border: none; }
            QPushButton:hover { background-color: #1E293B; }
        """
        estilo_btn_peligro = """
            QPushButton { padding: 10px 15px; border-radius: 6px; font-weight: bold; font-size: 13px; background-color: #FEF2F2; color: #DC2626; border: 1px solid #FECACA; }
            QPushButton:hover { background-color: #FEE2E2; }
        """
        
        btn_nuevo = QPushButton("Nuevo Proveedor")
        btn_nuevo.setStyleSheet(estilo_btn_primario)
        btn_nuevo.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_nuevo.clicked.connect(self.abrir_modal_proveedor)
        
        btn_eliminar = QPushButton("Eliminar")
        btn_eliminar.setStyleSheet(estilo_btn_peligro)
        btn_eliminar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_eliminar.clicked.connect(self.eliminar_proveedor)
        
        barra.addWidget(btn_nuevo)
        barra.addWidget(btn_eliminar)
        layout.addLayout(barra)
        
        self.tabla_prov = QTableWidget()
        self.tabla_prov.setColumnCount(4)
        self.tabla_prov.setHorizontalHeaderLabels(["DOCUMENTO (RIF)", "RAZÓN SOCIAL", "TELÉFONO", "DIRECCIÓN"])
        
        header_dir = self.tabla_prov.horizontalHeader()
        header_dir.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_dir.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header_dir.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header_dir.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header_dir.setStretchLastSection(True) # Aquí sí queremos que la dirección estire hasta el final
        
        self.tabla_prov.verticalHeader().setVisible(False)
        self.tabla_prov.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_prov.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla_prov.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_prov.setShowGrid(False)
        self.tabla_prov.verticalHeader().setDefaultSectionSize(50)
        
        self.tabla_prov.setStyleSheet("""
            QTableWidget { background-color: #FFFFFF; color: #334155; border: 1px solid #E2E8F0; border-radius: 6px; font-size: 14px; }
            QTableWidget::item { padding: 5px 15px; border-bottom: 1px solid #F1F5F9; }
            QTableWidget::item:selected { background-color: #EFF6FF; color: #0F172A; font-weight: bold; }
            QHeaderView::section { background-color: #F8FAFC; color: #64748B; font-weight: bold; font-size: 12px; padding: 12px; border: none; border-bottom: 2px solid #E2E8F0; text-transform: uppercase; }
        """)
        self.tabla_prov.itemSelectionChanged.connect(self.seleccionar_proveedor)
        layout.addWidget(self.tabla_prov)

    def cargar_directorio(self):
        self.tabla_prov.setRowCount(0)
        self.proveedor_seleccionado = None
        for i, p in enumerate(db_suppliers.obtener_proveedores()):
            self.tabla_prov.insertRow(i)
            item_doc = QTableWidgetItem(p['documento'])
            item_doc.setData(Qt.ItemDataRole.UserRole, p)
            item_doc.setForeground(QColor("#64748B"))
            self.tabla_prov.setItem(i, 0, item_doc)
            
            item_nom = QTableWidgetItem(p['nombre'])
            item_nom.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            item_nom.setForeground(QColor("#0F172A"))
            
            self.tabla_prov.setItem(i, 1, item_nom)
            self.tabla_prov.setItem(i, 2, QTableWidgetItem(p['telefono'] or "N/A"))
            self.tabla_prov.setItem(i, 3, QTableWidgetItem(p['direccion'] or "N/A"))

    def seleccionar_proveedor(self):
        filas = self.tabla_prov.selectedItems()
        self.proveedor_seleccionado = self.tabla_prov.item(filas[0].row(), 0).data(Qt.ItemDataRole.UserRole) if filas else None

    def abrir_modal_proveedor(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Registro de Proveedor")
        dialog.setFixedWidth(400)
        dialog.setStyleSheet("""
            QDialog { background-color: #FFFFFF; } 
            QLabel { color: #334155; font-weight: bold; font-size: 13px; } 
            QLineEdit { padding: 10px; border: 1px solid #CBD5E1; border-radius: 4px; background-color: #F8FAFC; color: #0F172A; font-size: 14px; } 
            QLineEdit:focus { border: 2px solid #38BDF8; background-color: #FFFFFF; }
        """)
        
        layout_form = QFormLayout(dialog)
        layout_form.setSpacing(15)
        layout_form.setContentsMargins(25, 25, 25, 25)
        
        campo_doc = QLineEdit()
        campo_nom = QLineEdit()
        campo_tel = QLineEdit()
        campo_dir = QLineEdit()
        
        layout_form.addRow("Documento / RIF:", campo_doc)
        layout_form.addRow("Razón Social:", campo_nom)
        layout_form.addRow("Teléfono:", campo_tel)
        layout_form.addRow("Dirección:", campo_dir)
        
        box_botones = QHBoxLayout()
        btn_cancelar = QPushButton("Descartar")
        btn_cancelar.setStyleSheet("padding: 10px 15px; background-color: #FFFFFF; color: #334155; border: 1px solid #CBD5E1; border-radius: 4px; font-weight: bold;")
        btn_guardar = QPushButton("Guardar Proveedor")
        btn_guardar.setStyleSheet("padding: 10px 15px; background-color: #0F172A; color: white; font-weight: bold; border-radius: 4px;")
        
        btn_cancelar.clicked.connect(dialog.reject)
        
        def guardar():
            doc, nom = campo_doc.text().strip(), campo_nom.text().strip()
            if not doc or not nom: return self.mostrar_mensaje("Error", "RIF y Razón Social son obligatorios.", "error")
            exito, msg = db_suppliers.guardar_proveedor(doc, nom, campo_tel.text().strip(), campo_dir.text().strip())
            if exito:
                self.cargar_datos() 
                dialog.accept()
            else: self.mostrar_mensaje("Error", msg, "error")
            
        btn_guardar.clicked.connect(guardar)
        box_botones.addWidget(btn_cancelar)
        box_botones.addWidget(btn_guardar)
        layout_form.addRow(box_botones)
        dialog.exec()

    def eliminar_proveedor(self):
        if not self.proveedor_seleccionado: return self.mostrar_mensaje("Aviso", "Seleccione un proveedor en la tabla.", "error")
        
        msg_confirm = QMessageBox(self)
        msg_confirm.setWindowTitle("Confirmar Baja")
        msg_confirm.setText(f"¿Está seguro de eliminar al proveedor:\n{self.proveedor_seleccionado['nombre']}?")
        msg_confirm.setIcon(QMessageBox.Icon.Question)
        msg_confirm.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_confirm.setStyleSheet("""
            QMessageBox { background-color: #FFFFFF; }
            QLabel { color: #0F172A; font-size: 13px; font-weight: bold; } 
            QPushButton { padding: 6px 20px; background-color: #DC2626; color: white; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #B91C1C; }
        """)
        
        if msg_confirm.exec() == QMessageBox.StandardButton.Yes:
            exito, msg = db_suppliers.eliminar_proveedor(self.proveedor_seleccionado['id'])
            if exito:
                self.cargar_datos()
            else: self.mostrar_mensaje("Error", msg, "error")

    # ================= LÓGICA DE COMPRAS =================
    def cargar_configuracion_compras(self):
        self.proveedores, self.almacenes = db_suppliers.obtener_datos_configuracion_compras()
        
        self.combo_prov_compra.clear()
        for p in self.proveedores: self.combo_prov_compra.addItem(p['nombre'], p['id'])
            
        self.combo_almacen_compra.clear()
        for a in self.almacenes: self.combo_almacen_compra.addItem(a['nombre'], a['id'])

    def buscar_productos_compra(self):
        termino = self.txt_buscador_compra.text().strip()
        if len(termino) < 1:
            self.tabla_busqueda_compra.setRowCount(0)
            return
            
        resultados = db_suppliers.buscar_productos_compra(termino)
        self.tabla_busqueda_compra.setRowCount(0)
        
        for i, prod in enumerate(resultados):
            self.tabla_busqueda_compra.insertRow(i)
            
            item_id = QTableWidgetItem(f"{prod['id']:05d}")
            item_id.setForeground(QColor("#94A3B8"))
            item_id.setData(Qt.ItemDataRole.UserRole, prod) 
            self.tabla_busqueda_compra.setItem(i, 0, item_id)
            
            item_nom = QTableWidgetItem(prod['nombre'])
            item_nom.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.tabla_busqueda_compra.setItem(i, 1, item_nom)
            
            item_costo = QTableWidgetItem(f"${prod['costo_actual']:.2f}")
            item_costo.setForeground(QColor("#10B981"))
            self.tabla_busqueda_compra.setItem(i, 2, item_costo)

    def agregar_al_carrito_compra(self, item=None):
        if not item: return
        fila = item.row()
        prod = self.tabla_busqueda_compra.item(fila, 0).data(Qt.ItemDataRole.UserRole)
        prod_id = prod['id']
        
        if prod_id in self.carrito_compra:
            self.carrito_compra[prod_id]['cantidad'] += 1
        else:
            self.carrito_compra[prod_id] = {
                'id': prod['id'], 'nombre': prod['nombre'], 
                'costo': float(prod['costo_actual']), 'cantidad': 1
            }
        
        self.txt_buscador_compra.clear()
        self.txt_buscador_compra.setFocus() 
        self.renderizar_carrito_compra()

    def renderizar_carrito_compra(self):
        self.tabla_carrito_compra.setRowCount(0)
        
        for prod_id, data in self.carrito_compra.items():
            fila = self.tabla_carrito_compra.rowCount()
            self.tabla_carrito_compra.insertRow(fila)
            
            item_id = QTableWidgetItem(f"{data['id']:05d}")
            item_id.setForeground(QColor("#94A3B8"))
            self.tabla_carrito_compra.setItem(fila, 0, item_id)
            
            item_nom = QTableWidgetItem(data['nombre'])
            item_nom.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.tabla_carrito_compra.setItem(fila, 1, item_nom)
            
            spin_cant = QSpinBox()
            spin_cant.setMinimum(1)
            spin_cant.setMaximum(99999)
            spin_cant.setValue(data['cantidad'])
            spin_cant.setAlignment(Qt.AlignmentFlag.AlignCenter)
            spin_cant.setMinimumWidth(80) 
            spin_cant.setFixedHeight(35)   
            spin_cant.setStyleSheet("background-color: #FFFFFF; color: #0F172A; font-weight: bold; font-size: 14px; border: 1px solid #CBD5E1; border-radius: 4px;")
            spin_cant.valueChanged.connect(lambda val, p_id=prod_id: self.actualizar_item_compra(p_id, val, 'cantidad'))
            
            widget_cant = QWidget()
            layout_cant = QHBoxLayout(widget_cant)
            layout_cant.setContentsMargins(5, 0, 5, 0)
            layout_cant.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout_cant.addWidget(spin_cant)
            self.tabla_carrito_compra.setCellWidget(fila, 2, widget_cant)
            
            spin_costo = QDoubleSpinBox()
            spin_costo.setMinimum(0.01)
            spin_costo.setMaximum(99999.99)
            spin_costo.setValue(data['costo'])
            spin_costo.setPrefix("$ ")
            spin_costo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            spin_costo.setMinimumWidth(100) 
            spin_costo.setFixedHeight(35)   
            spin_costo.setStyleSheet("background-color: #F8FAFC; color: #DC2626; font-weight: bold; font-size: 14px; border: 1px solid #CBD5E1; border-radius: 4px;")
            spin_costo.valueChanged.connect(lambda val, p_id=prod_id: self.actualizar_item_compra(p_id, val, 'costo'))
            
            widget_costo = QWidget()
            layout_costo = QHBoxLayout(widget_costo)
            layout_costo.setContentsMargins(5, 0, 5, 0)
            layout_costo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout_costo.addWidget(spin_costo)
            self.tabla_carrito_compra.setCellWidget(fila, 3, widget_costo)
            
            subtotal = data['cantidad'] * data['costo']
            item_sub = QTableWidgetItem(f"${subtotal:.2f}")
            item_sub.setForeground(QColor("#0F172A"))
            item_sub.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.tabla_carrito_compra.setItem(fila, 4, item_sub)
            
            # 🔥 PAPELERA DE QTAWESOME (Centrada perfectamente y sin fallas de borde) 🔥
            btn_quitar = QPushButton() 
            btn_quitar.setIcon(qta.icon('fa5s.trash-alt', color='#DC2626'))
            btn_quitar.setIconSize(QSize(18, 18))
            btn_quitar.setFixedSize(36, 36)
            btn_quitar.setToolTip("Eliminar línea")
            btn_quitar.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_quitar.setStyleSheet("""
                QPushButton { background-color: #FEE2E2; border: none; border-radius: 6px; }
                QPushButton:hover { background-color: #FECACA; }
            """)
            btn_quitar.clicked.connect(lambda checked, p_id=prod_id: self.quitar_del_carrito_compra(p_id))
            
            widget_btn = QWidget()
            layout_btn = QHBoxLayout(widget_btn)
            layout_btn.setContentsMargins(0, 0, 0, 0)
            layout_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout_btn.addWidget(btn_quitar)
            self.tabla_carrito_compra.setCellWidget(fila, 5, widget_btn)
            
        self.actualizar_subtotales_visuales_compra()

    def actualizar_item_compra(self, prod_id, valor, campo):
        if prod_id in self.carrito_compra:
            self.carrito_compra[prod_id][campo] = valor
            self.actualizar_subtotales_visuales_compra()

    def actualizar_subtotales_visuales_compra(self):
        total_dolares = 0.0
        for fila in range(self.tabla_carrito_compra.rowCount()):
            item_id = self.tabla_carrito_compra.item(fila, 0)
            if item_id:
                prod_id = int(item_id.text())
                if prod_id in self.carrito_compra:
                    data = self.carrito_compra[prod_id]
                    subtotal = data['cantidad'] * data['costo']
                    total_dolares += subtotal
                    
                    item_sub = QTableWidgetItem(f"${subtotal:.2f}")
                    item_sub.setForeground(QColor("#0F172A"))
                    item_sub.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                    self.tabla_carrito_compra.setItem(fila, 4, item_sub)
        
        self.lbl_total_compra.setText(f"TOTAL: $ {total_dolares:.2f}")

    def quitar_del_carrito_compra(self, prod_id):
        if prod_id in self.carrito_compra:
            del self.carrito_compra[prod_id]
            self.renderizar_carrito_compra()
            self.txt_buscador_compra.setFocus()

    def procesar_compra_final(self):
        if not self.carrito_compra: return self.mostrar_mensaje("Error", "La lista de ingreso está vacía.", "error")
        prov_id = self.combo_prov_compra.currentData()
        alm_id = self.combo_almacen_compra.currentData()
        if not prov_id or not alm_id: return self.mostrar_mensaje("Error", "Seleccione el Proveedor Emisor y el Almacén de Recepción.", "error")
        
        nro_factura = self.txt_nro_factura.text().strip()
        total_compra = sum(item['cantidad'] * item['costo'] for item in self.carrito_compra.values())
        
        msg_confirm = QMessageBox(self)
        msg_confirm.setWindowTitle("Confirmar Ingreso")
        msg_confirm.setText(f"¿Registrar ingreso de mercancía por $ {total_compra:.2f}?\n\nEsta acción sumará los productos al inventario y actualizará sus costos de compra.")
        msg_confirm.setIcon(QMessageBox.Icon.Question)
        msg_confirm.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_confirm.setStyleSheet("""
            QMessageBox { background-color: #FFFFFF; }
            QLabel { color: #0F172A; font-size: 13px; font-weight: bold; } 
            QPushButton { padding: 6px 20px; background-color: #0F172A; color: white; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #1E293B; }
        """)
        
        if msg_confirm.exec() == QMessageBox.StandardButton.Yes:
            exito, msg = db_suppliers.procesar_compra(
                prov_id, nro_factura, alm_id, total_compra, 
                list(self.carrito_compra.values()), session.usuario_actual['id']
            )
            if exito:
                self.mostrar_mensaje("Éxito", msg)
                self.carrito_compra.clear()
                self.txt_nro_factura.clear()
                self.renderizar_carrito_compra()
                self.txt_buscador_compra.setFocus()
            else:
                self.mostrar_mensaje("Error", msg, "error")