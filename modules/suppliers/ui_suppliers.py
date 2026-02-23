from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QDialog, QFormLayout, QMessageBox, QFrame, 
                             QAbstractItemView, QTabWidget, QComboBox, QSpinBox, QDoubleSpinBox)
from PyQt6.QtCore import Qt
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
        # Instalar filtro de eventos global para esta vista
        self.installEventFilter(self)
        
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(40, 40, 40, 40)
        layout_principal.setSpacing(20)
        
        lbl_titulo = QLabel("Proveedores y Compras")
        lbl_titulo.setStyleSheet("font-size: 28px; font-weight: 800; color: #0F172A; margin-bottom: 5px;")
        lbl_subtitulo = QLabel("Administra tus proveedores e ingresa nuevas facturas de compra para alimentar el inventario.")
        lbl_subtitulo.setStyleSheet("font-size: 14px; color: #64748B; margin-bottom: 15px;")
        
        layout_principal.addWidget(lbl_titulo)
        layout_principal.addWidget(lbl_subtitulo)
        
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #E2E8F0; background: #FFFFFF; border-radius: 8px; }
            QTabBar::tab { background: #F8FAFC; color: #64748B; padding: 12px 25px; border: 1px solid #E2E8F0; border-bottom: none; border-top-left-radius: 8px; border-top-right-radius: 8px; font-weight: bold; margin-right: 5px; font-size: 14px; }
            QTabBar::tab:selected { background: #FFFFFF; color: #2563EB; border-bottom: 3px solid #2563EB; }
            QTabBar::tab:hover:!selected { background: #F1F5F9; }
        """)
        
        self.tab_directorio = QWidget()
        self.tab_compras = QWidget()
        
        self.setup_tab_directorio()
        self.setup_tab_compras()
        
        self.tabs.addTab(self.tab_compras, "📥 Ingresar Factura de Compra")
        self.tabs.addTab(self.tab_directorio, "🏢 Directorio de Proveedores")
        
        layout_principal.addWidget(self.tabs)

    # ================= EVENTOS DE TECLADO (ATAJOS) =================
    def eventFilter(self, source, event):
        if event.type() == event.Type.KeyPress:
            # 1. Bajar a la tabla desde el buscador
            if source is self.txt_buscador_compra and event.key() == Qt.Key.Key_Down:
                if self.tabla_busqueda_compra.rowCount() > 0:
                    self.tabla_busqueda_compra.setFocus()
                    self.tabla_busqueda_compra.selectRow(0) 
                    return True 
                    
            # 2. Seleccionar de la tabla con Enter
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
        msg.setStyleSheet("QLabel { color: #000000; font-size: 14px; } QPushButton { padding: 5px 15px; background-color: #2563EB; color: white; border-radius: 4px; font-weight: bold; }")
        if tipo == "error": msg.setIcon(QMessageBox.Icon.Warning)
        else: msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()

    # ================= PESTAÑA 1: DIRECTORIO DE PROVEEDORES =================
    def setup_tab_directorio(self):
        layout = QVBoxLayout(self.tab_directorio)
        layout.setContentsMargins(20, 20, 20, 20)
        barra = QHBoxLayout()
        barra.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        btn_nuevo = QPushButton("➕ Nuevo Proveedor")
        btn_nuevo.setStyleSheet("QPushButton { padding: 8px 15px; border-radius: 6px; font-weight: 600; font-size: 13px; background-color: #2563EB; color: white; border: none; } QPushButton:hover { background-color: #1D4ED8; }")
        btn_nuevo.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_nuevo.clicked.connect(self.abrir_modal_proveedor)
        
        btn_eliminar = QPushButton("🗑️ Eliminar")
        btn_eliminar.setStyleSheet("QPushButton { padding: 8px 15px; border-radius: 6px; font-weight: 600; font-size: 13px; background-color: #FEF2F2; color: #DC2626; border: 1px solid #FECACA; } QPushButton:hover { background-color: #FEE2E2; }")
        btn_eliminar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_eliminar.clicked.connect(self.eliminar_proveedor)
        
        barra.addWidget(btn_nuevo)
        barra.addWidget(btn_eliminar)
        layout.addLayout(barra)
        
        self.tabla_prov = QTableWidget()
        self.tabla_prov.setColumnCount(4)
        self.tabla_prov.setHorizontalHeaderLabels(["DOCUMENTO (RIF)", "RAZÓN SOCIAL", "TELÉFONO", "DIRECCIÓN"])
        self.tabla_prov.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla_prov.verticalHeader().setVisible(False)
        self.tabla_prov.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_prov.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla_prov.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_prov.setShowGrid(False)
        self.tabla_prov.setStyleSheet("""
            QTableWidget { background-color: #FFFFFF; color: #334155; border: none; font-size: 13px; font-weight: bold; }
            QTableWidget::item { padding: 10px; border-bottom: 1px solid #F1F5F9; }
            QTableWidget::item:selected { background-color: #EFF6FF; color: #1E3A8A; }
            QHeaderView::section { background-color: #F8FAFC; color: #64748B; font-weight: 700; font-size: 12px; padding: 12px; border: none; border-bottom: 2px solid #E2E8F0; }
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
            self.tabla_prov.setItem(i, 0, item_doc)
            self.tabla_prov.setItem(i, 1, QTableWidgetItem(p['nombre']))
            self.tabla_prov.setItem(i, 2, QTableWidgetItem(p['telefono'] or ""))
            self.tabla_prov.setItem(i, 3, QTableWidgetItem(p['direccion'] or ""))

    def seleccionar_proveedor(self):
        filas = self.tabla_prov.selectedItems()
        self.proveedor_seleccionado = self.tabla_prov.item(filas[0].row(), 0).data(Qt.ItemDataRole.UserRole) if filas else None

    def abrir_modal_proveedor(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Nuevo Proveedor")
        dialog.setFixedWidth(400)
        dialog.setStyleSheet("QDialog { background-color: #FFFFFF; } QLabel { color: #0F172A; font-weight: 600; font-size: 13px; } QLineEdit { padding: 8px; border: 1px solid #CBD5E1; border-radius: 4px; background-color: #F8FAFC; color: #000000; font-size: 14px; } QLineEdit:focus { border: 2px solid #3B82F6; background-color: #FFFFFF; }")
        
        layout_form = QFormLayout(dialog)
        campo_doc = QLineEdit()
        campo_nom = QLineEdit()
        campo_tel = QLineEdit()
        campo_dir = QLineEdit()
        layout_form.addRow("Documento / RIF:", campo_doc)
        layout_form.addRow("Razón Social:", campo_nom)
        layout_form.addRow("Teléfono:", campo_tel)
        layout_form.addRow("Dirección:", campo_dir)
        
        btn_guardar = QPushButton("Guardar Proveedor")
        btn_guardar.setStyleSheet("padding: 10px; background-color: #2563EB; color: white; font-weight: bold; border-radius: 4px; margin-top: 10px;")
        
        def guardar():
            doc, nom = campo_doc.text().strip(), campo_nom.text().strip()
            if not doc or not nom: return self.mostrar_mensaje("Error", "RIF y Nombre obligatorios.", "error")
            exito, msg = db_suppliers.guardar_proveedor(doc, nom, campo_tel.text().strip(), campo_dir.text().strip())
            if exito:
                self.mostrar_mensaje("Éxito", msg)
                self.cargar_datos() 
                dialog.accept()
            else: self.mostrar_mensaje("Error", msg, "error")
            
        btn_guardar.clicked.connect(guardar)
        layout_form.addRow(btn_guardar)
        dialog.exec()

    def eliminar_proveedor(self):
        if not self.proveedor_seleccionado: return self.mostrar_mensaje("Aviso", "Selecciona un proveedor.", "error")
        if QMessageBox.question(self, "Confirmar", f"¿Eliminar a {self.proveedor_seleccionado['nombre']}?") == QMessageBox.StandardButton.Yes:
            exito, msg = db_suppliers.eliminar_proveedor(self.proveedor_seleccionado['id'])
            if exito:
                self.mostrar_mensaje("Éxito", msg)
                self.cargar_datos()
            else: self.mostrar_mensaje("Error", msg, "error")

    # ================= PESTAÑA 2: INGRESO DE COMPRAS =================
    def setup_tab_compras(self):
        layout_principal = QHBoxLayout(self.tab_compras)
        layout_principal.setContentsMargins(20, 20, 20, 20)
        layout_principal.setSpacing(20)
        
        # --- PANEL IZQUIERDO ---
        panel_izq = QVBoxLayout()
        
        self.txt_buscador_compra = QLineEdit()
        self.txt_buscador_compra.setPlaceholderText("🔎 Buscar producto a ingresar (Flecha Abajo para seleccionar, Enter para agregar)...")
        self.txt_buscador_compra.setFixedHeight(45)
        self.txt_buscador_compra.setStyleSheet("padding: 5px 15px; border: 2px solid #CBD5E1; border-radius: 6px; font-size: 15px; color: #000000; background-color: #FFFFFF;")
        self.txt_buscador_compra.textChanged.connect(self.buscar_productos_compra)
        self.txt_buscador_compra.installEventFilter(self) # 🔥 Atento al teclado
        panel_izq.addWidget(self.txt_buscador_compra)
        
        self.tabla_busqueda_compra = QTableWidget()
        self.tabla_busqueda_compra.setColumnCount(3)
        self.tabla_busqueda_compra.setHorizontalHeaderLabels(["ID", "PRODUCTO", "ÚLTIMO COSTO ($)"])
        self.tabla_busqueda_compra.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla_busqueda_compra.verticalHeader().setVisible(False)
        self.tabla_busqueda_compra.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_busqueda_compra.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla_busqueda_compra.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_busqueda_compra.setFixedHeight(150)
        self.tabla_busqueda_compra.setStyleSheet("QTableWidget { background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px; color: #000000; font-weight: bold; }")
        self.tabla_busqueda_compra.itemDoubleClicked.connect(self.agregar_al_carrito_compra)
        self.tabla_busqueda_compra.installEventFilter(self) # 🔥 Atento al teclado
        panel_izq.addWidget(self.tabla_busqueda_compra)
        
        lbl_carrito = QLabel("📦 Mercancía a Ingresar (Factura)")
        lbl_carrito.setStyleSheet("font-size: 16px; font-weight: bold; color: #0F172A; margin-top: 10px;")
        panel_izq.addWidget(lbl_carrito)
        
        self.tabla_carrito_compra = QTableWidget()
        self.tabla_carrito_compra.setColumnCount(6)
        self.tabla_carrito_compra.setHorizontalHeaderLabels(["ID", "PRODUCTO", "CANTIDAD LLEGADA", "COSTO U. ($)", "SUBTOTAL ($)", "QUITAR"])
        self.tabla_carrito_compra.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla_carrito_compra.verticalHeader().setVisible(False)
        self.tabla_carrito_compra.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_carrito_compra.setStyleSheet("QTableWidget { background-color: #FFFFFF; color: #000000; border: 1px solid #E2E8F0; border-radius: 6px; font-size: 14px; font-weight: bold; } QHeaderView::section { background-color: #F8FAFC; color: #64748B; font-weight: bold; padding: 10px; border: none; border-bottom: 2px solid #E2E8F0; }")
        panel_izq.addWidget(self.tabla_carrito_compra)
        
        # --- PANEL DERECHO ---
        panel_der = QFrame()
        panel_der.setFixedWidth(350)
        panel_der.setStyleSheet("QFrame { background-color: #F8FAFC; border-radius: 10px; border: 1px solid #E2E8F0; }")
        layout_der = QVBoxLayout(panel_der)
        layout_der.setContentsMargins(20, 20, 20, 20)
        layout_der.setSpacing(15)
        
        estilo_lbl = "font-size: 13px; font-weight: bold; color: #64748B;"
        estilo_input = "padding: 10px; border: 1px solid #CBD5E1; border-radius: 6px; background-color: #FFFFFF; color: black; font-weight: bold;"
        
        layout_der.addWidget(QLabel("🏢 Proveedor Emisor:", styleSheet=estilo_lbl))
        self.combo_prov_compra = QComboBox()
        self.combo_prov_compra.setStyleSheet(estilo_input)
        layout_der.addWidget(self.combo_prov_compra)
        
        layout_der.addWidget(QLabel("📄 Nro. Factura Proveedor (Opcional):", styleSheet=estilo_lbl))
        self.txt_nro_factura = QLineEdit()
        self.txt_nro_factura.setStyleSheet(estilo_input)
        layout_der.addWidget(self.txt_nro_factura)
        
        layout_der.addWidget(QLabel("🏭 Recibir en Almacén:", styleSheet=estilo_lbl))
        self.combo_almacen_compra = QComboBox()
        self.combo_almacen_compra.setStyleSheet(estilo_input)
        layout_der.addWidget(self.combo_almacen_compra)
        
        layout_der.addStretch()
        
        self.lbl_total_compra = QLabel("TOTAL: $0.00")
        self.lbl_total_compra.setStyleSheet("font-size: 26px; font-weight: 900; color: #DC2626; text-align: center;")
        self.lbl_total_compra.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_der.addWidget(self.lbl_total_compra)
        
        btn_procesar = QPushButton("📥 INGRESAR AL INVENTARIO")
        btn_procesar.setFixedHeight(55)
        btn_procesar.setStyleSheet("QPushButton { background-color: #16A34A; color: white; border-radius: 8px; font-weight: 900; font-size: 16px; } QPushButton:hover { background-color: #15803D; }")
        btn_procesar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_procesar.clicked.connect(self.procesar_compra_final)
        layout_der.addWidget(btn_procesar)
        
        layout_principal.addLayout(panel_izq, stretch=70)
        layout_principal.addWidget(panel_der, stretch=30)

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
            item_id = QTableWidgetItem(str(prod['id']))
            item_id.setData(Qt.ItemDataRole.UserRole, prod) 
            self.tabla_busqueda_compra.setItem(i, 0, item_id)
            self.tabla_busqueda_compra.setItem(i, 1, QTableWidgetItem(prod['nombre']))
            self.tabla_busqueda_compra.setItem(i, 2, QTableWidgetItem(f"${prod['costo_actual']:.2f}"))

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
        self.txt_buscador_compra.setFocus() # 🔥 Devuelve el foco al buscador
        self.renderizar_carrito_compra()

    def renderizar_carrito_compra(self):
        self.tabla_carrito_compra.setRowCount(0)
        
        for prod_id, data in self.carrito_compra.items():
            fila = self.tabla_carrito_compra.rowCount()
            self.tabla_carrito_compra.insertRow(fila)
            
            self.tabla_carrito_compra.setItem(fila, 0, QTableWidgetItem(str(data['id'])))
            self.tabla_carrito_compra.setItem(fila, 1, QTableWidgetItem(data['nombre']))
            
            spin_cant = QSpinBox()
            spin_cant.setMinimum(1)
            spin_cant.setMaximum(99999)
            spin_cant.setValue(data['cantidad'])
            spin_cant.setStyleSheet("background-color: white; color: black; font-weight: bold;")
            # 🔥 Llama a la función que actualiza visualmente sin redibujar todo
            spin_cant.valueChanged.connect(lambda val, p_id=prod_id: self.actualizar_item_compra(p_id, val, 'cantidad'))
            self.tabla_carrito_compra.setCellWidget(fila, 2, spin_cant)
            
            spin_costo = QDoubleSpinBox()
            spin_costo.setMinimum(0.01)
            spin_costo.setMaximum(99999.99)
            spin_costo.setValue(data['costo'])
            spin_costo.setPrefix("$ ")
            spin_costo.setStyleSheet("background-color: white; color: #DC2626; font-weight: bold;")
            # 🔥 Llama a la función que actualiza visualmente sin redibujar todo
            spin_costo.valueChanged.connect(lambda val, p_id=prod_id: self.actualizar_item_compra(p_id, val, 'costo'))
            self.tabla_carrito_compra.setCellWidget(fila, 3, spin_costo)
            
            subtotal = data['cantidad'] * data['costo']
            self.tabla_carrito_compra.setItem(fila, 4, QTableWidgetItem(f"${subtotal:.2f}"))
            
            btn_quitar = QPushButton("❌")
            btn_quitar.setStyleSheet("background-color: transparent; border: none; font-size: 14px;")
            btn_quitar.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_quitar.clicked.connect(lambda checked, p_id=prod_id: self.quitar_del_carrito_compra(p_id))
            self.tabla_carrito_compra.setCellWidget(fila, 5, btn_quitar)
            
        self.actualizar_subtotales_visuales_compra()

    # 🔥 CORRECCIÓN: Ahora solo actualiza los datos en memoria y repinta el subtotal
    def actualizar_item_compra(self, prod_id, valor, campo):
        if prod_id in self.carrito_compra:
            self.carrito_compra[prod_id][campo] = valor
            self.actualizar_subtotales_visuales_compra()

    # 🔥 NUEVO: Recalcula solo la columna de subtotales sin borrar el foco de los spinbox
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
                    self.tabla_carrito_compra.setItem(fila, 4, QTableWidgetItem(f"${subtotal:.2f}"))
        
        self.lbl_total_compra.setText(f"TOTAL: ${total_dolares:.2f}")

    def quitar_del_carrito_compra(self, prod_id):
        if prod_id in self.carrito_compra:
            del self.carrito_compra[prod_id]
            self.renderizar_carrito_compra()
            self.txt_buscador_compra.setFocus()

    def procesar_compra_final(self):
        if not self.carrito_compra: return self.mostrar_mensaje("Error", "El carrito de compras está vacío.", "error")
        prov_id = self.combo_prov_compra.currentData()
        alm_id = self.combo_almacen_compra.currentData()
        if not prov_id or not alm_id: return self.mostrar_mensaje("Error", "Selecciona Proveedor y Almacén.", "error")
        
        nro_factura = self.txt_nro_factura.text().strip()
        total_compra = sum(item['cantidad'] * item['costo'] for item in self.carrito_compra.values())
        
        respuesta = QMessageBox.question(self, "Confirmar Ingreso", f"¿Confirmas el ingreso de mercancía por ${total_compra:.2f}?\nEsto modificará el stock y los costos.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if respuesta == QMessageBox.StandardButton.Yes:
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