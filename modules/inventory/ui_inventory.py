from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QDialog, QFormLayout, QMessageBox, QFrame, 
                             QAbstractItemView, QComboBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from modules.inventory import db_inventory
from modules.settings import db_settings 

class VistaInventario(QWidget):
    def __init__(self):
        super().__init__()
        self.producto_seleccionado = None
        self.listas_precios = [] # Guardaremos las listas de precios dinámicas
        
        self.setup_ui()
        self.cargar_datos()

    def setup_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(40, 40, 40, 40)
        layout_principal.setSpacing(20)
        
        lbl_titulo = QLabel("Inventario de Productos")
        lbl_titulo.setStyleSheet("font-size: 28px; font-weight: 800; color: #0F172A; margin-bottom: 5px;")
        lbl_subtitulo = QLabel("Administra tu catálogo, controla tus costos, múltiples precios y stock mínimo.")
        lbl_subtitulo.setStyleSheet("font-size: 14px; color: #64748B; margin-bottom: 15px;")
        
        layout_principal.addWidget(lbl_titulo)
        layout_principal.addWidget(lbl_subtitulo)
        
        tarjeta = QFrame()
        tarjeta.setStyleSheet("QFrame { background-color: #FFFFFF; border-radius: 12px; border: 1px solid #E2E8F0; }")
        layout_tarjeta = QVBoxLayout(tarjeta)
        layout_tarjeta.setContentsMargins(20, 20, 20, 20)
        layout_tarjeta.setSpacing(15)
        
        barra_herramientas = QHBoxLayout()
        self.campo_busqueda = QLineEdit()
        self.campo_busqueda.setPlaceholderText("🔍 Buscar por código o descripción...")
        self.campo_busqueda.setFixedHeight(42)
        self.campo_busqueda.setStyleSheet("padding: 5px 15px; border: 1px solid #CBD5E1; border-radius: 6px; font-size: 14px; color: #000000; background-color: #F8FAFC;")
        self.campo_busqueda.textChanged.connect(self.cargar_datos) 
        barra_herramientas.addWidget(self.campo_busqueda)
        
        estilo_btn_base = "QPushButton { padding: 10px 18px; border-radius: 6px; font-weight: 600; font-size: 13px; }"
        
        btn_nuevo = QPushButton("➕ Nuevo")
        btn_nuevo.setStyleSheet(estilo_btn_base + "QPushButton { background-color: #2563EB; color: white; border: none; } QPushButton:hover { background-color: #1D4ED8; }")
        btn_nuevo.clicked.connect(lambda: self.abrir_modal("nuevo"))
        btn_nuevo.setCursor(Qt.CursorShape.PointingHandCursor)
        
        btn_editar = QPushButton("✏️ Editar")
        btn_editar.setStyleSheet(estilo_btn_base + "QPushButton { background-color: #FFFFFF; color: #334155; border: 1px solid #CBD5E1; } QPushButton:hover { background-color: #F1F5F9; color: #0F172A; }")
        btn_editar.clicked.connect(lambda: self.abrir_modal("editar"))
        btn_editar.setCursor(Qt.CursorShape.PointingHandCursor)
        
        btn_eliminar = QPushButton("🗑️ Eliminar")
        btn_eliminar.setStyleSheet(estilo_btn_base + "QPushButton { background-color: #FEF2F2; color: #DC2626; border: 1px solid #FECACA; } QPushButton:hover { background-color: #FEE2E2; border: 1px solid #F87171; }")
        btn_eliminar.clicked.connect(self.eliminar)
        btn_eliminar.setCursor(Qt.CursorShape.PointingHandCursor)
        
        barra_herramientas.addWidget(btn_nuevo)
        barra_herramientas.addWidget(btn_editar)
        barra_herramientas.addWidget(btn_eliminar)
        
        layout_tarjeta.addLayout(barra_herramientas)
        
        # ================= TABLA DINÁMICA =================
        # 1. Cargamos las listas de precios reales desde BD
        self.listas_precios = db_settings.obtener_listas_precios()
        
        # 2. Construimos las columnas dinámicamente
        columnas_base = ["ID", "CÓDIGO", "DESCRIPCIÓN", "CATEGORÍA", "PROVEEDOR"]
        columnas_dinamicas = [f"PRECIO ({l['nombre'].upper()})" for l in self.listas_precios]
        columnas_finales = columnas_base + columnas_dinamicas + ["STOCK ACTUAL"]
        
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(len(columnas_finales))
        self.tabla.setHorizontalHeaderLabels(columnas_finales)
        
        # Ajuste de tamaño: que se adapten al texto, pero la descripción sea ancha
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) # Descripción
        
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setShowGrid(False)
        
        self.tabla.setStyleSheet("""
            QTableWidget { background-color: #FFFFFF; color: #000000; border: 1px solid #E2E8F0; border-radius: 6px; font-size: 13px; font-weight: bold; }
            QTableWidget::item { padding: 10px; border-bottom: 1px solid #F1F5F9; }
            QTableWidget::item:selected { background-color: #EFF6FF; color: #1E3A8A; }
            QHeaderView::section { background-color: #F8FAFC; color: #64748B; font-weight: 700; font-size: 12px; padding: 12px; border: none; border-bottom: 2px solid #E2E8F0; }
        """)
        
        self.tabla.itemSelectionChanged.connect(self.seleccionar)
        layout_tarjeta.addWidget(self.tabla)
        
        layout_principal.addWidget(tarjeta)

    def mostrar_mensaje(self, titulo, texto, tipo="info"):
        msg = QMessageBox(self)
        msg.setWindowTitle(titulo)
        msg.setText(texto)
        msg.setStyleSheet("QLabel { color: #000000; font-size: 14px; } QPushButton { padding: 5px 15px; background-color: #2563EB; color: white; border-radius: 4px; }")
        if tipo == "error": msg.setIcon(QMessageBox.Icon.Warning)
        else: msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()

    def seleccionar(self):
        filas = self.tabla.selectedItems()
        if filas:
            self.producto_seleccionado = self.tabla.item(filas[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        else:
            self.producto_seleccionado = None

    def cargar_datos(self):
        self.tabla.setRowCount(0)
        self.producto_seleccionado = None
        termino_busqueda = self.campo_busqueda.text().strip().lower()
        productos = db_inventory.obtener_productos()
        
        fila_idx = 0
        for p in productos:
            codigo = str(p.get("codigo") or "").lower()
            nombre = str(p.get("nombre") or "").lower()
            
            if termino_busqueda and termino_busqueda not in codigo and termino_busqueda not in nombre:
                continue
            
            self.tabla.insertRow(fila_idx)
            item_id = QTableWidgetItem(str(p['id']))
            item_id.setData(Qt.ItemDataRole.UserRole, p) 
            
            # --- Columnas Base ---
            self.tabla.setItem(fila_idx, 0, item_id)
            self.tabla.setItem(fila_idx, 1, QTableWidgetItem(p['codigo']))
            self.tabla.setItem(fila_idx, 2, QTableWidgetItem(p['nombre']))
            self.tabla.setItem(fila_idx, 3, QTableWidgetItem(p['categoria'] or "General"))
            self.tabla.setItem(fila_idx, 4, QTableWidgetItem(f"💼 {p['proveedor_nombre']}"))
            
            # --- Columnas de Precios Dinámicas ---
            columna_actual = 5
            for lista in self.listas_precios:
                precio_val = p['precios'].get(lista['id'], 0.0) # Busca el precio en el diccionario o pone 0
                item_precio = QTableWidgetItem(f"${float(precio_val):.2f}")
                item_precio.setForeground(QColor("#2563EB")) # Azules para destacar
                self.tabla.setItem(fila_idx, columna_actual, item_precio)
                columna_actual += 1
            
            # --- Columna Final: Stock ---
            stock_actual = float(p['stock'])
            stock_min = float(p['stock_minimo'])
            
            if stock_actual <= stock_min:
                item_stock = QTableWidgetItem(f"⚠️ {stock_actual} (¡Bajo!)")
                item_stock.setForeground(QColor("#DC2626"))
            else:
                item_stock = QTableWidgetItem(str(stock_actual))
                item_stock.setForeground(QColor("#16A34A")) 
                
            self.tabla.setItem(fila_idx, columna_actual, item_stock)
            fila_idx += 1

    def abrir_modal(self, modo="nuevo"):
        if modo == "editar" and not self.producto_seleccionado:
            return self.mostrar_mensaje("Aviso", "Selecciona un producto de la tabla para editar.", "error")

        dialog = QDialog(self)
        dialog.setWindowTitle("Nuevo Producto" if modo == "nuevo" else "Editar Producto")
        dialog.setFixedWidth(450)
        
        # 🔥 SOLUCIÓN A LOS DROPDOWNS NEGROS: QComboBox QAbstractItemView
        dialog.setStyleSheet("""
            QDialog { background-color: #FFFFFF; }
            QLabel { color: #0F172A; font-weight: 600; font-size: 13px; }
            QLineEdit, QComboBox { padding: 8px; border: 1px solid #CBD5E1; border-radius: 4px; color: #000000; background-color: #F8FAFC; font-size: 14px; }
            QLineEdit:focus, QComboBox:focus { border: 2px solid #3B82F6; background-color: #FFFFFF; }
            QComboBox QAbstractItemView { background-color: #FFFFFF; color: #000000; selection-background-color: #EFF6FF; selection-color: #1E3A8A; }
        """)
        
        layout_form = QFormLayout(dialog)
        layout_form.setSpacing(15)
        layout_form.setContentsMargins(25, 25, 25, 25)
        
        campo_codigo = QLineEdit()
        campo_nombre = QLineEdit()
        combo_categoria = QComboBox() 
        combo_proveedor = QComboBox() 
        campo_costo = QLineEdit()
        campo_stock = QLineEdit()
        campo_stock_min = QLineEdit()

        departamentos = db_inventory.obtener_departamentos()
        for d in departamentos: combo_categoria.addItem(d['nombre'], d['id'])
            
        proveedores = db_inventory.obtener_proveedores()
        for prov in proveedores: combo_proveedor.addItem(prov['nombre'], prov['id'])
        
        if not proveedores:
            return self.mostrar_mensaje("¡Atención!", "Debes registrar al menos un Proveedor en el módulo de 'Proveedores' antes de crear productos.", "error")

        self.campos_precios_dict = {} 
        precios_actuales = {}
        
        if modo == "editar":
            campo_codigo.setText(str(self.producto_seleccionado.get("codigo", "")))
            campo_nombre.setText(str(self.producto_seleccionado.get("nombre", "")))
            campo_costo.setText(str(self.producto_seleccionado.get("costo", "0")))
            campo_stock.setText(str(self.producto_seleccionado.get("stock", "0")))
            campo_stock_min.setText(str(self.producto_seleccionado.get("stock_minimo", "0")))
            
            idx_dep = combo_categoria.findData(self.producto_seleccionado.get("departamento_id"))
            if idx_dep >= 0: combo_categoria.setCurrentIndex(idx_dep)
                
            idx_prov = combo_proveedor.findData(self.producto_seleccionado.get("proveedor_id"))
            if idx_prov >= 0: combo_proveedor.setCurrentIndex(idx_prov)
            
            precios_actuales = db_inventory.obtener_precios_producto(self.producto_seleccionado['id'])
        else:
            campo_costo.setText("0.00")
            campo_stock.setText("0")
            campo_stock_min.setText("5")
            
        layout_form.addRow("Código / SKU:", campo_codigo)
        layout_form.addRow("Descripción:", campo_nombre)
        layout_form.addRow("Departamento:", combo_categoria)
        layout_form.addRow("Proveedor Principal:", combo_proveedor)
        layout_form.addRow("Costo de Compra:", campo_costo)
        
        lbl_separador = QLabel("--- Tarifas de Venta ---")
        lbl_separador.setStyleSheet("color: #2563EB; font-weight: bold; margin-top: 10px;")
        layout_form.addRow(lbl_separador)
        
        for lista in self.listas_precios:
            txt_precio = QLineEdit()
            txt_precio.setText(str(precios_actuales.get(lista['id'], "0.00")))
            self.campos_precios_dict[lista['id']] = txt_precio
            layout_form.addRow(f"Precio {lista['nombre']}:", txt_precio)
            
        lbl_separador2 = QLabel("--- Inventario ---")
        lbl_separador2.setStyleSheet("color: #2563EB; font-weight: bold; margin-top: 10px;")
        layout_form.addRow(lbl_separador2)
        
        layout_form.addRow("Stock Actual:", campo_stock)
        layout_form.addRow("Alerta Stock Mínimo:", campo_stock_min)
        
        box_botones = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet("padding: 8px 15px; background-color: #F1F5F9; color: #475569; border-radius: 4px; font-weight: bold;")
        btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        
        btn_guardar = QPushButton("Guardar Producto")
        btn_guardar.setStyleSheet("padding: 8px 15px; background-color: #2563EB; color: white; border-radius: 4px; font-weight: bold;")
        btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        
        btn_cancelar.clicked.connect(dialog.reject)
        
        def guardar():
            try:
                codigo = campo_codigo.text().strip()
                nombre = campo_nombre.text().strip()
                departamento_id = combo_categoria.currentData()
                proveedor_id = combo_proveedor.currentData()
                costo = float(campo_costo.text().strip() or 0)
                stock = float(campo_stock.text().strip() or 0)
                stock_min = float(campo_stock_min.text().strip() or 0)
                
                precios_a_guardar = {}
                for lista_id, input_precio in self.campos_precios_dict.items():
                    precios_a_guardar[lista_id] = float(input_precio.text().strip() or 0)
                    
            except ValueError:
                return self.mostrar_mensaje("Error", "Costo, precios y stocks deben ser números válidos.", "error")
            
            if not codigo or not nombre:
                return self.mostrar_mensaje("Error", "Código y Descripción son obligatorios.", "error")
            
            if modo == "nuevo":
                exito, msg = db_inventory.guardar_producto(codigo, nombre, departamento_id, proveedor_id, costo, precios_a_guardar, stock, stock_min)
            else:
                exito, msg = db_inventory.editar_producto(self.producto_seleccionado["id"], codigo, nombre, departamento_id, proveedor_id, costo, precios_a_guardar, stock, stock_min)
                
            if exito:
                self.mostrar_mensaje("Éxito", msg)
                self.cargar_datos()
                dialog.accept()
            else:
                self.mostrar_mensaje("Error", msg, "error")
                
        btn_guardar.clicked.connect(guardar)
        box_botones.addWidget(btn_cancelar)
        box_botones.addWidget(btn_guardar)
        layout_form.addRow(box_botones)
        
        dialog.exec()

    def eliminar(self):
        if not self.producto_seleccionado:
            return self.mostrar_mensaje("Aviso", "Selecciona un producto de la tabla para eliminar.", "error")
            
        respuesta = QMessageBox.question(
            self, "Confirmar", 
            f"¿Seguro que deseas eliminar el producto '{self.producto_seleccionado['nombre']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
                                         
        if respuesta == QMessageBox.StandardButton.Yes:
            exito, msg = db_inventory.eliminar_producto(self.producto_seleccionado["id"])
            if exito:
                self.mostrar_mensaje("Éxito", msg)
                self.cargar_datos()
            else:
                self.mostrar_mensaje("Error", msg, "error")