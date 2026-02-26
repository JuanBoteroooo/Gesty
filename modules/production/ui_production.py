import qtawesome as qta
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QMessageBox, QFrame, QAbstractItemView, QComboBox, QSpinBox, QInputDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from modules.production import db_production
from modules.settings import db_settings
from utils import session

class VistaProduccion(QWidget):
    def __init__(self):
        super().__init__()
        self.productos_memoria = [] 
        self.setup_ui()
        self.cargar_datos_iniciales()

    def setup_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(30, 30, 30, 30)
        layout_principal.setSpacing(15)
        
        # ==========================================
        # CABECERA
        # ==========================================
        header_layout = QVBoxLayout()
        lbl_titulo = QLabel("PRODUCCIÓN Y PREPARACIÓN DE PRODUCTOS")
        lbl_titulo.setStyleSheet("font-size: 24px; font-weight: 900; color: #0F172A; letter-spacing: 1px;")
        lbl_subtitulo = QLabel("Busque y agregue la materia prima a descontar (Izquierda) y los nuevos productos a sumar (Derecha).")
        lbl_subtitulo.setStyleSheet("font-size: 14px; color: #64748B;")
        header_layout.addWidget(lbl_titulo)
        header_layout.addWidget(lbl_subtitulo)
        layout_principal.addLayout(header_layout)

        # ==========================================
        # CONFIGURACIÓN GENERAL (Almacenes y Motivo)
        # ==========================================
        panel_config = QFrame()
        panel_config.setStyleSheet("QFrame { background-color: #FFFFFF; border-radius: 8px; border: 1px solid #CBD5E1; }")
        layout_config = QHBoxLayout(panel_config)
        layout_config.setContentsMargins(20, 15, 20, 15)

        self.combo_origen = QComboBox()
        self.combo_destino = QComboBox()
        self.txt_motivo = QLineEdit()
        self.txt_motivo.setPlaceholderText("Ej: Armado de Combos Navideños, Reempaquetado...")
        
        estilo_inputs = "padding: 8px; border: 1px solid #CBD5E1; border-radius: 4px; font-weight: bold; font-size: 13px; background-color: #F8FAFC;"
        self.combo_origen.setStyleSheet(estilo_inputs)
        self.combo_destino.setStyleSheet(estilo_inputs)
        self.txt_motivo.setStyleSheet(estilo_inputs)

        layout_config.addWidget(QLabel("Almacén Origen (Insumos):", styleSheet="font-weight: bold; border: none;"))
        layout_config.addWidget(self.combo_origen, stretch=1)
        layout_config.addWidget(QLabel("Almacén Destino (Nuevos):", styleSheet="font-weight: bold; border: none; margin-left: 15px;"))
        layout_config.addWidget(self.combo_destino, stretch=1)
        layout_config.addWidget(QLabel("Motivo:", styleSheet="font-weight: bold; border: none; margin-left: 15px;"))
        layout_config.addWidget(self.txt_motivo, stretch=2)
        
        layout_principal.addWidget(panel_config)

        # ==========================================
        # DOBLE COLUMNA (Insumos vs Generados)
        # ==========================================
        columnas_layout = QHBoxLayout()
        columnas_layout.setSpacing(20)
        
        # ------------------------------------------
        # COLUMNA IZQUIERDA: INSUMOS (🔴 RED)
        # ------------------------------------------
        panel_izq = QFrame()
        panel_izq.setStyleSheet("QFrame { background-color: #FFFFFF; border-radius: 8px; border: 1px solid #FECACA; }")
        layout_izq = QVBoxLayout(panel_izq)
        layout_izq.setContentsMargins(15, 15, 15, 15)
        
        lbl_izq = QLabel("🔴 INSUMOS A DESCONTAR")
        lbl_izq.setStyleSheet("font-size: 16px; font-weight: 900; color: #DC2626; border: none;")
        layout_izq.addWidget(lbl_izq)

        self.txt_busq_izq = QLineEdit()
        self.txt_busq_izq.setPlaceholderText("Buscar insumo por código o nombre...")
        self.txt_busq_izq.setStyleSheet(estilo_inputs)
        self.txt_busq_izq.textChanged.connect(self.filtrar_busqueda_izq)
        layout_izq.addWidget(self.txt_busq_izq)

        self.tabla_busq_izq = QTableWidget()
        self.tabla_busq_izq.setColumnCount(3)
        self.tabla_busq_izq.setHorizontalHeaderLabels(["ID", "CÓDIGO", "PRODUCTO"])
        self.configurar_tabla_busqueda(self.tabla_busq_izq)
        self.tabla_busq_izq.itemDoubleClicked.connect(lambda item: self.agregar_doble_clic(item, self.tabla_busq_izq, self.tabla_insumos))
        layout_izq.addWidget(self.tabla_busq_izq)

        fila_add_izq = QHBoxLayout()
        self.spin_insumo = QSpinBox()
        self.spin_insumo.setMinimum(1)
        self.spin_insumo.setMaximum(9999)
        self.spin_insumo.setStyleSheet(estilo_inputs)
        
        btn_add_insumo = QPushButton(" Añadir a Lista")
        btn_add_insumo.setIcon(qta.icon('fa5s.arrow-down', color='white'))
        btn_add_insumo.setStyleSheet("background-color: #DC2626; color: white; border-radius: 4px; padding: 8px 15px; font-weight: bold;")
        btn_add_insumo.clicked.connect(lambda: self.agregar_desde_boton(self.tabla_busq_izq, self.spin_insumo, self.tabla_insumos))
        
        fila_add_izq.addWidget(QLabel("Cant:", styleSheet="border:none; font-weight:bold;"))
        fila_add_izq.addWidget(self.spin_insumo)
        fila_add_izq.addWidget(btn_add_insumo, stretch=1)
        layout_izq.addLayout(fila_add_izq)

        self.tabla_insumos = QTableWidget()
        self.tabla_insumos.setColumnCount(4)
        self.tabla_insumos.setHorizontalHeaderLabels(["ID", "INSUMOS A RESTAR", "CANT.", "X"])
        self.configurar_tabla_carrito(self.tabla_insumos)
        layout_izq.addWidget(self.tabla_insumos)
        
        # ------------------------------------------
        # COLUMNA DERECHA: GENERADOS (🟢 GREEN)
        # ------------------------------------------
        panel_der = QFrame()
        panel_der.setStyleSheet("QFrame { background-color: #FFFFFF; border-radius: 8px; border: 1px solid #A7F3D0; }")
        layout_der = QVBoxLayout(panel_der)
        layout_der.setContentsMargins(15, 15, 15, 15)
        
        lbl_der = QLabel("🟢 PRODUCTOS CREADOS (A Sumar)")
        lbl_der.setStyleSheet("font-size: 16px; font-weight: 900; color: #10B981; border: none;")
        layout_der.addWidget(lbl_der)

        self.txt_busq_der = QLineEdit()
        self.txt_busq_der.setPlaceholderText("Buscar producto a generar por código o nombre...")
        self.txt_busq_der.setStyleSheet(estilo_inputs)
        self.txt_busq_der.textChanged.connect(self.filtrar_busqueda_der)
        layout_der.addWidget(self.txt_busq_der)

        self.tabla_busq_der = QTableWidget()
        self.tabla_busq_der.setColumnCount(3)
        self.tabla_busq_der.setHorizontalHeaderLabels(["ID", "CÓDIGO", "PRODUCTO"])
        self.configurar_tabla_busqueda(self.tabla_busq_der)
        self.tabla_busq_der.itemDoubleClicked.connect(lambda item: self.agregar_doble_clic(item, self.tabla_busq_der, self.tabla_generados))
        layout_der.addWidget(self.tabla_busq_der)

        fila_add_der = QHBoxLayout()
        self.spin_generado = QSpinBox()
        self.spin_generado.setMinimum(1)
        self.spin_generado.setMaximum(9999)
        self.spin_generado.setStyleSheet(estilo_inputs)
        
        btn_add_generado = QPushButton(" Añadir a Lista")
        btn_add_generado.setIcon(qta.icon('fa5s.arrow-down', color='white'))
        btn_add_generado.setStyleSheet("background-color: #10B981; color: white; border-radius: 4px; padding: 8px 15px; font-weight: bold;")
        btn_add_generado.clicked.connect(lambda: self.agregar_desde_boton(self.tabla_busq_der, self.spin_generado, self.tabla_generados))
        
        fila_add_der.addWidget(QLabel("Cant:", styleSheet="border:none; font-weight:bold;"))
        fila_add_der.addWidget(self.spin_generado)
        fila_add_der.addWidget(btn_add_generado, stretch=1)
        layout_der.addLayout(fila_add_der)

        self.tabla_generados = QTableWidget()
        self.tabla_generados.setColumnCount(4)
        self.tabla_generados.setHorizontalHeaderLabels(["ID", "NUEVOS PRODUCTOS", "CANT.", "X"])
        self.configurar_tabla_carrito(self.tabla_generados)
        layout_der.addWidget(self.tabla_generados)

        columnas_layout.addWidget(panel_izq)
        columnas_layout.addWidget(panel_der)
        layout_principal.addLayout(columnas_layout)

        # ==========================================
        # BOTÓN FINAL DE PROCESAMIENTO
        # ==========================================
        btn_procesar = QPushButton("🚀 PROCESAR Y ACTUALIZAR INVENTARIOS")
        btn_procesar.setFixedHeight(50)
        btn_procesar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_procesar.setStyleSheet("""
            QPushButton { background-color: #0F172A; color: white; font-weight: 900; font-size: 16px; border-radius: 8px; letter-spacing: 2px;}
            QPushButton:hover { background-color: #1E293B; }
        """)
        btn_procesar.clicked.connect(self.procesar_produccion)
        layout_principal.addWidget(btn_procesar)

    # ================= FUNCIONES DE CONFIGURACIÓN =================
    def configurar_tabla_busqueda(self, tabla):
        tabla.setFixedHeight(130) 
        header = tabla.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        tabla.verticalHeader().setVisible(False)
        tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        tabla.setStyleSheet("""
            QTableWidget { background-color: #F8FAFC; border: 1px solid #E2E8F0; font-size: 12px; color: #334155; }
            QTableWidget::item:selected { background-color: #DBEAFE; color: #0F172A; font-weight: bold; }
            QHeaderView::section { background-color: #E2E8F0; color: #475569; font-weight: bold; font-size: 10px; padding: 5px; border: none; }
        """)

    def configurar_tabla_carrito(self, tabla):
        header = tabla.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) # Espacio para el SpinBox
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed) # Papelera
        tabla.setColumnWidth(3, 50)
        tabla.verticalHeader().setVisible(False)
        tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tabla.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        tabla.verticalHeader().setDefaultSectionSize(45)
        tabla.setStyleSheet("""
            QTableWidget { background-color: #FFFFFF; border: none; font-size: 13px; color: #0F172A; font-weight: bold;}
            QHeaderView::section { background-color: #F1F5F9; color: #475569; font-weight: bold; font-size: 11px; padding: 10px; border: none; }
        """)

    def cargar_datos_iniciales(self):
        almacenes = db_settings.obtener_almacenes()
        self.combo_origen.clear()
        self.combo_destino.clear()
        for a in almacenes:
            self.combo_origen.addItem(a['nombre'], a['id'])
            self.combo_destino.addItem(a['nombre'], a['id'])
            
        self.productos_memoria = db_production.obtener_productos_basico()
        self.llenar_tabla_busqueda(self.tabla_busq_izq, self.productos_memoria)
        self.llenar_tabla_busqueda(self.tabla_busq_der, self.productos_memoria)

    # ================= LÓGICA DE BÚSQUEDA Y AGREGADO =================
    def llenar_tabla_busqueda(self, tabla, productos_filtrados):
        tabla.setRowCount(0)
        for i, p in enumerate(productos_filtrados):
            tabla.insertRow(i)
            
            item_id = QTableWidgetItem(f"{p['id']:04d}")
            item_id.setForeground(QColor("#94A3B8"))
            item_id.setData(Qt.ItemDataRole.UserRole, p)
            tabla.setItem(i, 0, item_id)
            
            tabla.setItem(i, 1, QTableWidgetItem(p['codigo'] or "-"))
            tabla.setItem(i, 2, QTableWidgetItem(p['nombre']))

    def filtrar_busqueda_izq(self):
        term = self.txt_busq_izq.text().lower()
        filtrados = [p for p in self.productos_memoria if term in (p['nombre'] or "").lower() or term in (p['codigo'] or "").lower()]
        self.llenar_tabla_busqueda(self.tabla_busq_izq, filtrados)

    def filtrar_busqueda_der(self):
        term = self.txt_busq_der.text().lower()
        filtrados = [p for p in self.productos_memoria if term in (p['nombre'] or "").lower() or term in (p['codigo'] or "").lower()]
        self.llenar_tabla_busqueda(self.tabla_busq_der, filtrados)

    # 🔥 NUEVO MÉTODO ROBUSTO PARA ELIMINAR DEL CARRITO 🔥
    def eliminar_del_carrito(self, tabla_carrito, producto_id):
        for row in range(tabla_carrito.rowCount()):
            item = tabla_carrito.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole)['id'] == producto_id:
                tabla_carrito.removeRow(row)
                break

    def agregar_al_carrito(self, tabla_carrito, producto, cantidad):
        # 1. Verificar si ya existe en la lista para sumarle al SpinBox
        for row in range(tabla_carrito.rowCount()):
            item_id = tabla_carrito.item(row, 0)
            if item_id and item_id.data(Qt.ItemDataRole.UserRole)['id'] == producto['id']:
                spin = tabla_carrito.cellWidget(row, 2)
                spin.setValue(spin.value() + cantidad)
                return 

        # 2. Si no existe, creamos la fila con su SpinBox
        row = tabla_carrito.rowCount()
        tabla_carrito.insertRow(row)
        
        item_id = QTableWidgetItem(f"#{producto['id']:04d}")
        item_id.setData(Qt.ItemDataRole.UserRole, producto)
        item_id.setForeground(QColor("#94A3B8"))
        tabla_carrito.setItem(row, 0, item_id)
        
        tabla_carrito.setItem(row, 1, QTableWidgetItem(producto['nombre']))
        
        # 🔥 CANTIDAD EDITABLE CON QSPINBOX 🔥
        spin_cant = QSpinBox()
        spin_cant.setMinimum(1)
        spin_cant.setMaximum(99999)
        spin_cant.setValue(cantidad)
        spin_cant.setStyleSheet("padding: 5px; border: 1px solid #CBD5E1; border-radius: 4px; font-weight: bold; font-size: 14px; background-color: #FFFFFF;")
        tabla_carrito.setCellWidget(row, 2, spin_cant)
        
        # 🔥 BOTÓN DE PAPELERA ROBUSTO 🔥
        btn_del = QPushButton()
        btn_del.setIcon(qta.icon('fa5s.trash-alt', color='white'))
        btn_del.setStyleSheet("background-color: #DC2626; color: white; border-radius: 4px; padding: 6px;")
        btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        # Pasamos el ID del producto para borrarlo sin importar en qué fila esté ahora
        btn_del.clicked.connect(lambda checked, p_id=producto['id']: self.eliminar_del_carrito(tabla_carrito, p_id))
        
        widget_btn = QWidget()
        l_btn = QHBoxLayout(widget_btn)
        l_btn.setContentsMargins(4, 4, 4, 4)
        l_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l_btn.addWidget(btn_del)
        tabla_carrito.setCellWidget(row, 3, widget_btn)

    def agregar_desde_boton(self, tabla_busqueda, spin_cantidad, tabla_carrito):
        filas = tabla_busqueda.selectedItems()
        if not filas:
            return self.mostrar_mensaje("Aviso", "Seleccione un producto de los resultados de búsqueda primero.", "error")
            
        producto = tabla_busqueda.item(filas[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        cantidad = spin_cantidad.value()
        
        self.agregar_al_carrito(tabla_carrito, producto, cantidad)
        spin_cantidad.setValue(1)
        tabla_busqueda.clearSelection()

    def agregar_doble_clic(self, item, tabla_busqueda, tabla_carrito):
        producto = tabla_busqueda.item(item.row(), 0).data(Qt.ItemDataRole.UserRole)
        
        # 🔥 FORZAMOS EL BLANCO EN EL POP-UP DE DOBLE CLIC 🔥
        dialog = QInputDialog(self)
        dialog.setWindowTitle("Agregar a la Lista")
        dialog.setLabelText(f"¿Cantidad de {producto['nombre']} a agregar?")
        dialog.setIntRange(1, 9999)
        dialog.setIntValue(1)
        dialog.setStyleSheet("""
            QWidget { background-color: #FFFFFF; color: #0F172A; }
            QLabel { font-weight: bold; font-size: 13px; border: none; }
            QSpinBox { padding: 8px; border: 1px solid #CBD5E1; border-radius: 4px; font-weight: bold; font-size: 14px; }
            QPushButton { padding: 8px 20px; background-color: #0F172A; color: white; border-radius: 4px; font-weight: bold; }
        """)
        
        if dialog.exec():
            cant = dialog.intValue()
            self.agregar_al_carrito(tabla_carrito, producto, cant)
            tabla_busqueda.clearSelection()

    # ================= ALERTAS Y PROCESAMIENTO =================
    def mostrar_mensaje(self, titulo, texto, tipo="info"):
        msg = QMessageBox(self)
        msg.setWindowTitle(titulo)
        msg.setText(texto)
        msg.setStyleSheet("""
            QWidget { background-color: #FFFFFF; color: #0F172A; } 
            QLabel { font-size: 13px; font-weight: bold; border: none; } 
            QPushButton { padding: 8px 20px; background-color: #0F172A; color: white; border-radius: 4px; font-weight: bold; }
        """)
        if tipo == "error": msg.setIcon(QMessageBox.Icon.Warning)
        else: msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()

    def procesar_produccion(self):
        insumos = []
        for row in range(self.tabla_insumos.rowCount()):
            # Extraemos la cantidad directamente del QSpinBox de esa fila
            spin = self.tabla_insumos.cellWidget(row, 2)
            insumos.append({
                'id': self.tabla_insumos.item(row, 0).data(Qt.ItemDataRole.UserRole)['id'],
                'cantidad': spin.value()
            })
            
        generados = []
        for row in range(self.tabla_generados.rowCount()):
            spin = self.tabla_generados.cellWidget(row, 2)
            generados.append({
                'id': self.tabla_generados.item(row, 0).data(Qt.ItemDataRole.UserRole)['id'],
                'cantidad': spin.value()
            })

        if not insumos or not generados:
            return self.mostrar_mensaje("Faltan Datos", "Debe agregar al menos un insumo a descontar (Izquierda) y un producto a generar (Derecha).", "error")

        motivo = self.txt_motivo.text().strip() or "Preparación interna de productos"
        origen_id = self.combo_origen.currentData()
        destino_id = self.combo_destino.currentData()

        exito, msg = db_production.procesar_produccion(origen_id, destino_id, insumos, generados, session.usuario_actual['id'], motivo)
        
        if exito:
            self.mostrar_mensaje("Producción Exitosa", msg)
            self.tabla_insumos.setRowCount(0)
            self.tabla_generados.setRowCount(0)
            self.txt_motivo.clear()
            self.txt_busq_izq.clear()
            self.txt_busq_der.clear()
        else:
            self.mostrar_mensaje("Error al procesar", msg, "error")