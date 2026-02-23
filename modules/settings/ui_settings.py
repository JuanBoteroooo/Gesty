from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QDialog, QFormLayout, QMessageBox, QFrame, 
                             QAbstractItemView, QTabWidget, QCheckBox, QComboBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor  # 🔥 Importante para los colores de los roles
from modules.settings import db_settings

class VistaAjustes(QWidget):
    def __init__(self):
        super().__init__()
        self.moneda_seleccionada = None
        self.lista_seleccionada = None
        self.departamento_seleccionado = None
        self.metodo_seleccionado = None 
        self.almacen_seleccionado = None 
        self.usuario_seleccionado = None # 🔥 NUEVO
        
        self.setup_ui()
        self.actualizar_todo() 

    def actualizar_todo(self):
        self.cargar_monedas()
        self.cargar_listas()
        self.cargar_departamentos()
        self.cargar_metodos() 
        self.cargar_almacenes() 
        self.cargar_usuarios() # 🔥 NUEVO

    def setup_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(40, 40, 40, 40)
        layout_principal.setSpacing(20)
        
        lbl_titulo = QLabel("Ajustes y Parámetros")
        lbl_titulo.setStyleSheet("font-size: 28px; font-weight: 800; color: #0F172A; margin-bottom: 5px;")
        lbl_subtitulo = QLabel("Configura las reglas de negocio, divisas, listas, departamentos, almacenes, métodos de pago y usuarios.")
        lbl_subtitulo.setStyleSheet("font-size: 14px; color: #64748B; margin-bottom: 15px;")
        
        layout_principal.addWidget(lbl_titulo)
        layout_principal.addWidget(lbl_subtitulo)
        
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #E2E8F0; background: #FFFFFF; border-radius: 8px; }
            QTabBar::tab { background: #F8FAFC; color: #64748B; padding: 10px 20px; border: 1px solid #E2E8F0; border-bottom: none; border-top-left-radius: 8px; border-top-right-radius: 8px; font-weight: bold; margin-right: 5px; }
            QTabBar::tab:selected { background: #FFFFFF; color: #2563EB; border-bottom: 2px solid #2563EB; }
            QTabBar::tab:hover:!selected { background: #F1F5F9; }
        """)
        
        self.tab_monedas = QWidget()
        self.tab_listas = QWidget()
        self.tab_deptos = QWidget()
        self.tab_metodos = QWidget() 
        self.tab_almacenes = QWidget() 
        self.tab_usuarios = QWidget() # 🔥 NUEVA PESTAÑA
        
        self.setup_tab_monedas()
        self.setup_tab_listas()
        self.setup_tab_departamentos()
        self.setup_tab_metodos() 
        self.setup_tab_almacenes() 
        self.setup_tab_usuarios() # 🔥 CONFIGURARLA
        
        self.tabs.addTab(self.tab_monedas, "💵 Divisas y Tasas")
        self.tabs.addTab(self.tab_listas, "📋 Listas de Precios")
        self.tabs.addTab(self.tab_deptos, "📂 Departamentos")
        self.tabs.addTab(self.tab_almacenes, "🏭 Almacenes") 
        self.tabs.addTab(self.tab_metodos, "💳 Métodos de Pago") 
        self.tabs.addTab(self.tab_usuarios, "👥 Accesos y Roles") # 🔥 AÑADIRLA AL MENÚ
        
        layout_principal.addWidget(self.tabs)

    def obtener_estilo_tabla(self):
        return """
            QTableWidget { background-color: #FFFFFF; color: #334155; border: none; font-size: 13px; font-weight: bold; }
            QTableWidget::item { padding: 10px; border-bottom: 1px solid #F1F5F9; }
            QTableWidget::item:selected { background-color: #EFF6FF; color: #1E3A8A; }
            QHeaderView::section { background-color: #F8FAFC; color: #64748B; font-weight: 700; font-size: 12px; padding: 12px; border: none; border-bottom: 2px solid #E2E8F0; text-transform: uppercase; }
        """

    def obtener_estilo_btn(self, tipo="azul"):
        if tipo == "azul": return "QPushButton { padding: 8px 15px; border-radius: 6px; font-weight: 600; font-size: 13px; background-color: #2563EB; color: white; border: none; } QPushButton:hover { background-color: #1D4ED8; }"
        elif tipo == "blanco": return "QPushButton { padding: 8px 15px; border-radius: 6px; font-weight: 600; font-size: 13px; background-color: #FFFFFF; color: #334155; border: 1px solid #CBD5E1; } QPushButton:hover { background-color: #F1F5F9; color: #0F172A; }"
        elif tipo == "rojo": return "QPushButton { padding: 8px 15px; border-radius: 6px; font-weight: 600; font-size: 13px; background-color: #FEF2F2; color: #DC2626; border: 1px solid #FECACA; } QPushButton:hover { background-color: #FEE2E2; border: 1px solid #F87171; }"

    def obtener_estilo_modal(self):
        return """
            QDialog { background-color: #FFFFFF; } 
            QLabel { color: #0F172A; font-weight: 600; font-size: 13px; } 
            QLineEdit, QComboBox { padding: 8px; border: 1px solid #CBD5E1; border-radius: 4px; background-color: #F8FAFC; color: #000000; font-size: 14px; } 
            QLineEdit:focus, QComboBox:focus { border: 2px solid #3B82F6; background-color: #FFFFFF; } 
            QCheckBox { color: #000000; font-weight: bold; font-size: 13px; }
            QComboBox QAbstractItemView { background-color: #FFFFFF; color: #000000; selection-background-color: #EFF6FF; }
        """

    # ================= PESTAÑA 1: MONEDAS =================
    def setup_tab_monedas(self):
        layout = QVBoxLayout(self.tab_monedas)
        layout.setContentsMargins(20, 20, 20, 20)
        barra = QHBoxLayout()
        barra.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        btn_nuevo = QPushButton("➕ Nueva Divisa")
        btn_nuevo.setStyleSheet(self.obtener_estilo_btn("azul"))
        btn_nuevo.clicked.connect(lambda: self.abrir_modal_moneda("nuevo"))
        btn_nuevo.setCursor(Qt.CursorShape.PointingHandCursor)
        
        btn_editar = QPushButton("✏️ Actualizar Tasa")
        btn_editar.setStyleSheet(self.obtener_estilo_btn("blanco"))
        btn_editar.clicked.connect(lambda: self.abrir_modal_moneda("editar"))
        btn_editar.setCursor(Qt.CursorShape.PointingHandCursor)
        
        btn_eliminar = QPushButton("🗑️ Eliminar")
        btn_eliminar.setStyleSheet(self.obtener_estilo_btn("rojo"))
        btn_eliminar.clicked.connect(self.eliminar_moneda)
        btn_eliminar.setCursor(Qt.CursorShape.PointingHandCursor)
        
        barra.addWidget(btn_nuevo)
        barra.addWidget(btn_editar)
        barra.addWidget(btn_eliminar)
        layout.addLayout(barra)
        
        self.tabla_monedas = QTableWidget()
        self.tabla_monedas.setColumnCount(5)
        self.tabla_monedas.setHorizontalHeaderLabels(["ID", "DIVISA", "SÍMBOLO", "TASA DE CAMBIO", "ESTADO"])
        self.tabla_monedas.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_monedas.verticalHeader().setVisible(False)
        self.tabla_monedas.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_monedas.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla_monedas.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_monedas.setShowGrid(False)
        self.tabla_monedas.setStyleSheet(self.obtener_estilo_tabla())
        self.tabla_monedas.itemSelectionChanged.connect(self.seleccionar_moneda)
        layout.addWidget(self.tabla_monedas)

    def cargar_monedas(self):
        self.tabla_monedas.setRowCount(0)
        self.moneda_seleccionada = None
        for fila_idx, m in enumerate(db_settings.obtener_monedas()):
            self.tabla_monedas.insertRow(fila_idx)
            item_id = QTableWidgetItem(str(m['id']))
            item_id.setData(Qt.ItemDataRole.UserRole, m)
            estado_texto = "⭐ PRINCIPAL" if m['es_principal'] else "Secundaria"
            self.tabla_monedas.setItem(fila_idx, 0, item_id)
            self.tabla_monedas.setItem(fila_idx, 1, QTableWidgetItem(m['nombre']))
            self.tabla_monedas.setItem(fila_idx, 2, QTableWidgetItem(m['simbolo']))
            self.tabla_monedas.setItem(fila_idx, 3, QTableWidgetItem(str(m['tasa_cambio'])))
            self.tabla_monedas.setItem(fila_idx, 4, QTableWidgetItem(estado_texto))

    def seleccionar_moneda(self):
        filas = self.tabla_monedas.selectedItems()
        self.moneda_seleccionada = self.tabla_monedas.item(filas[0].row(), 0).data(Qt.ItemDataRole.UserRole) if filas else None

    def abrir_modal_moneda(self, modo="nuevo"):
        if modo == "editar" and not self.moneda_seleccionada: return self.mostrar_mensaje("Aviso", "Selecciona una moneda.", "error")
        dialog = QDialog(self)
        dialog.setWindowTitle("Divisa")
        dialog.setFixedWidth(400)
        dialog.setStyleSheet(self.obtener_estilo_modal())
        layout_form = QFormLayout(dialog)
        layout_form.setSpacing(15)
        campo_nombre = QLineEdit()
        campo_simbolo = QLineEdit()
        campo_tasa = QLineEdit()
        chk_principal = QCheckBox("Convertir en Moneda Principal")
        
        if modo == "editar":
            campo_nombre.setText(self.moneda_seleccionada['nombre'])
            campo_simbolo.setText(self.moneda_seleccionada['simbolo'])
            campo_tasa.setText(str(self.moneda_seleccionada['tasa_cambio']))
            chk_principal.setChecked(bool(self.moneda_seleccionada['es_principal']))
            
        layout_form.addRow("Nombre:", campo_nombre)
        layout_form.addRow("Símbolo:", campo_simbolo)
        layout_form.addRow("Tasa de Cambio:", campo_tasa)
        layout_form.addRow("", chk_principal)
        
        box_botones = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet(self.obtener_estilo_btn("blanco"))
        btn_guardar = QPushButton("Guardar")
        btn_guardar.setStyleSheet(self.obtener_estilo_btn("azul"))
        btn_cancelar.clicked.connect(dialog.reject)
        
        def guardar():
            nombre = campo_nombre.text().strip()
            simbolo = campo_simbolo.text().strip()
            es_principal = 1 if chk_principal.isChecked() else 0
            try: tasa = float(campo_tasa.text().strip())
            except ValueError: return self.mostrar_mensaje("Error", "Tasa inválida.", "error")
            if not nombre or not simbolo: return self.mostrar_mensaje("Error", "Campos obligatorios.", "error")
            
            if modo == "nuevo": exito, msg = db_settings.guardar_moneda(nombre, simbolo, tasa, es_principal)
            else: exito, msg = db_settings.actualizar_moneda(self.moneda_seleccionada['id'], nombre, simbolo, tasa, es_principal)
            if exito:
                self.mostrar_mensaje("Éxito", msg)
                self.cargar_monedas()
                dialog.accept()
            else: self.mostrar_mensaje("Error", msg, "error")
        btn_guardar.clicked.connect(guardar)
        box_botones.addWidget(btn_cancelar)
        box_botones.addWidget(btn_guardar)
        layout_form.addRow(box_botones)
        dialog.exec()

    def eliminar_moneda(self):
        if not self.moneda_seleccionada: return self.mostrar_mensaje("Aviso", "Selecciona una moneda.", "error")
        if QMessageBox.question(self, "Confirmar", f"¿Eliminar {self.moneda_seleccionada['nombre']}?") == QMessageBox.StandardButton.Yes:
            exito, msg = db_settings.eliminar_moneda(self.moneda_seleccionada['id'])
            if exito:
                self.mostrar_mensaje("Éxito", msg)
                self.cargar_monedas()
            else: self.mostrar_mensaje("Error", msg, "error")

    # ================= PESTAÑA 2: LISTAS DE PRECIOS =================
    def setup_tab_listas(self):
        layout = QVBoxLayout(self.tab_listas)
        layout.setContentsMargins(20, 20, 20, 20)
        barra = QHBoxLayout()
        barra.setAlignment(Qt.AlignmentFlag.AlignRight)
        btn_nuevo = QPushButton("➕ Nueva Lista")
        btn_nuevo.setStyleSheet(self.obtener_estilo_btn("azul"))
        btn_nuevo.clicked.connect(self.abrir_modal_lista)
        btn_eliminar = QPushButton("🗑️ Eliminar")
        btn_eliminar.setStyleSheet(self.obtener_estilo_btn("rojo"))
        btn_eliminar.clicked.connect(self.eliminar_lista)
        barra.addWidget(btn_nuevo)
        barra.addWidget(btn_eliminar)
        layout.addLayout(barra)
        
        self.tabla_listas = QTableWidget()
        self.tabla_listas.setColumnCount(2)
        self.tabla_listas.setHorizontalHeaderLabels(["ID", "NOMBRE DE LA LISTA"])
        self.tabla_listas.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_listas.verticalHeader().setVisible(False)
        self.tabla_listas.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_listas.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla_listas.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_listas.setShowGrid(False)
        self.tabla_listas.setStyleSheet(self.obtener_estilo_tabla())
        self.tabla_listas.itemSelectionChanged.connect(self.seleccionar_lista)
        layout.addWidget(self.tabla_listas)

    def cargar_listas(self):
        self.tabla_listas.setRowCount(0)
        self.lista_seleccionada = None
        for fila_idx, l in enumerate(db_settings.obtener_listas_precios()):
            self.tabla_listas.insertRow(fila_idx)
            item_id = QTableWidgetItem(str(l['id']))
            item_id.setData(Qt.ItemDataRole.UserRole, l)
            self.tabla_listas.setItem(fila_idx, 0, item_id)
            self.tabla_listas.setItem(fila_idx, 1, QTableWidgetItem(l['nombre']))

    def seleccionar_lista(self):
        filas = self.tabla_listas.selectedItems()
        self.lista_seleccionada = self.tabla_listas.item(filas[0].row(), 0).data(Qt.ItemDataRole.UserRole) if filas else None

    def abrir_modal_lista(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Nueva Lista de Precios")
        dialog.setFixedWidth(350)
        dialog.setStyleSheet(self.obtener_estilo_modal())
        layout_form = QFormLayout(dialog)
        campo_nombre = QLineEdit()
        layout_form.addRow("Nombre:", campo_nombre)
        box_botones = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet(self.obtener_estilo_btn("blanco"))
        btn_guardar = QPushButton("Guardar")
        btn_guardar.setStyleSheet(self.obtener_estilo_btn("azul"))
        btn_cancelar.clicked.connect(dialog.reject)
        
        def guardar():
            nombre = campo_nombre.text().strip()
            if not nombre: return self.mostrar_mensaje("Error", "Nombre obligatorio.", "error")
            exito, msg = db_settings.guardar_lista_precio(nombre)
            if exito:
                self.mostrar_mensaje("Éxito", msg)
                self.cargar_listas()
                dialog.accept()
            else: self.mostrar_mensaje("Error", msg, "error")
        btn_guardar.clicked.connect(guardar)
        box_botones.addWidget(btn_cancelar)
        box_botones.addWidget(btn_guardar)
        layout_form.addRow(box_botones)
        dialog.exec()

    def eliminar_lista(self):
        if not self.lista_seleccionada: return self.mostrar_mensaje("Aviso", "Selecciona una lista.", "error")
        if QMessageBox.question(self, "Confirmar", f"¿Eliminar lista {self.lista_seleccionada['nombre']}?") == QMessageBox.StandardButton.Yes:
            exito, msg = db_settings.eliminar_lista_precio(self.lista_seleccionada['id'])
            if exito:
                self.mostrar_mensaje("Éxito", msg)
                self.cargar_listas()
            else: self.mostrar_mensaje("Error", msg, "error")

    # ================= PESTAÑA 3: DEPARTAMENTOS =================
    def setup_tab_departamentos(self):
        layout = QVBoxLayout(self.tab_deptos)
        layout.setContentsMargins(20, 20, 20, 20)
        barra = QHBoxLayout()
        barra.setAlignment(Qt.AlignmentFlag.AlignRight)
        btn_nuevo = QPushButton("➕ Nuevo Depto.")
        btn_nuevo.setStyleSheet(self.obtener_estilo_btn("azul"))
        btn_nuevo.clicked.connect(self.abrir_modal_departamento)
        btn_eliminar = QPushButton("🗑️ Eliminar")
        btn_eliminar.setStyleSheet(self.obtener_estilo_btn("rojo"))
        btn_eliminar.clicked.connect(self.eliminar_departamento)
        barra.addWidget(btn_nuevo)
        barra.addWidget(btn_eliminar)
        layout.addLayout(barra)
        
        self.tabla_deptos = QTableWidget()
        self.tabla_deptos.setColumnCount(3)
        self.tabla_deptos.setHorizontalHeaderLabels(["ID", "NOMBRE DEPARTAMENTO", "DESCRIPCIÓN"])
        self.tabla_deptos.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_deptos.verticalHeader().setVisible(False)
        self.tabla_deptos.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_deptos.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla_deptos.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_deptos.setShowGrid(False)
        self.tabla_deptos.setStyleSheet(self.obtener_estilo_tabla())
        self.tabla_deptos.itemSelectionChanged.connect(self.seleccionar_departamento)
        layout.addWidget(self.tabla_deptos)

    def cargar_departamentos(self):
        self.tabla_deptos.setRowCount(0)
        self.departamento_seleccionado = None
        for fila_idx, d in enumerate(db_settings.obtener_departamentos()):
            self.tabla_deptos.insertRow(fila_idx)
            item_id = QTableWidgetItem(str(d['id']))
            item_id.setData(Qt.ItemDataRole.UserRole, d)
            self.tabla_deptos.setItem(fila_idx, 0, item_id)
            self.tabla_deptos.setItem(fila_idx, 1, QTableWidgetItem(d['nombre']))
            self.tabla_deptos.setItem(fila_idx, 2, QTableWidgetItem(d['descripcion'] or ""))

    def seleccionar_departamento(self):
        filas = self.tabla_deptos.selectedItems()
        self.departamento_seleccionado = self.tabla_deptos.item(filas[0].row(), 0).data(Qt.ItemDataRole.UserRole) if filas else None

    def abrir_modal_departamento(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Nuevo Departamento")
        dialog.setFixedWidth(350)
        dialog.setStyleSheet(self.obtener_estilo_modal())
        layout_form = QFormLayout(dialog)
        campo_nombre = QLineEdit()
        campo_desc = QLineEdit()
        layout_form.addRow("Nombre:", campo_nombre)
        layout_form.addRow("Descripción:", campo_desc)
        box_botones = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet(self.obtener_estilo_btn("blanco"))
        btn_guardar = QPushButton("Guardar")
        btn_guardar.setStyleSheet(self.obtener_estilo_btn("azul"))
        btn_cancelar.clicked.connect(dialog.reject)
        
        def guardar():
            nombre = campo_nombre.text().strip()
            desc = campo_desc.text().strip()
            if not nombre: return self.mostrar_mensaje("Error", "Nombre obligatorio.", "error")
            exito, msg = db_settings.guardar_departamento(nombre, desc)
            if exito:
                self.mostrar_mensaje("Éxito", msg)
                self.cargar_departamentos()
                dialog.accept()
            else: self.mostrar_mensaje("Error", msg, "error")
            
        btn_guardar.clicked.connect(guardar)
        box_botones.addWidget(btn_cancelar)
        box_botones.addWidget(btn_guardar)
        layout_form.addRow(box_botones)
        dialog.exec()

    def eliminar_departamento(self):
        if not self.departamento_seleccionado: return self.mostrar_mensaje("Aviso", "Selecciona un departamento.", "error")
        if QMessageBox.question(self, "Confirmar", f"¿Eliminar departamento {self.departamento_seleccionado['nombre']}?") == QMessageBox.StandardButton.Yes:
            exito, msg = db_settings.eliminar_departamento(self.departamento_seleccionado['id'])
            if exito:
                self.mostrar_mensaje("Éxito", msg)
                self.cargar_departamentos()
            else: self.mostrar_mensaje("Error", msg, "error")

    # ================= PESTAÑA 4: MÉTODOS DE PAGO =================
    def setup_tab_metodos(self):
        layout = QVBoxLayout(self.tab_metodos)
        layout.setContentsMargins(20, 20, 20, 20)
        barra = QHBoxLayout()
        barra.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        btn_nuevo = QPushButton("➕ Nuevo Método")
        btn_nuevo.setStyleSheet(self.obtener_estilo_btn("azul"))
        btn_nuevo.clicked.connect(self.abrir_modal_metodo)
        btn_eliminar = QPushButton("🗑️ Eliminar")
        btn_eliminar.setStyleSheet(self.obtener_estilo_btn("rojo"))
        btn_eliminar.clicked.connect(self.eliminar_metodo)
        
        barra.addWidget(btn_nuevo)
        barra.addWidget(btn_eliminar)
        layout.addLayout(barra)
        
        self.tabla_metodos = QTableWidget()
        self.tabla_metodos.setColumnCount(3)
        self.tabla_metodos.setHorizontalHeaderLabels(["ID", "NOMBRE DEL MÉTODO", "MONEDA ASOCIADA"])
        self.tabla_metodos.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_metodos.verticalHeader().setVisible(False)
        self.tabla_metodos.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_metodos.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla_metodos.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_metodos.setShowGrid(False)
        self.tabla_metodos.setStyleSheet(self.obtener_estilo_tabla())
        self.tabla_metodos.itemSelectionChanged.connect(self.seleccionar_metodo)
        layout.addWidget(self.tabla_metodos)

    def cargar_metodos(self):
        self.tabla_metodos.setRowCount(0)
        self.metodo_seleccionado = None
        for fila_idx, m in enumerate(db_settings.obtener_metodos_pago()):
            self.tabla_metodos.insertRow(fila_idx)
            item_id = QTableWidgetItem(str(m['id']))
            item_id.setData(Qt.ItemDataRole.UserRole, m)
            self.tabla_metodos.setItem(fila_idx, 0, item_id)
            self.tabla_metodos.setItem(fila_idx, 1, QTableWidgetItem(m['nombre']))
            self.tabla_metodos.setItem(fila_idx, 2, QTableWidgetItem(f"{m['moneda_nombre']} ({m['simbolo']})"))

    def seleccionar_metodo(self):
        filas = self.tabla_metodos.selectedItems()
        self.metodo_seleccionado = self.tabla_metodos.item(filas[0].row(), 0).data(Qt.ItemDataRole.UserRole) if filas else None

    def abrir_modal_metodo(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Nuevo Método de Pago")
        dialog.setFixedWidth(350)
        dialog.setStyleSheet(self.obtener_estilo_modal())
        
        layout_form = QFormLayout(dialog)
        campo_nombre = QLineEdit()
        combo_moneda = QComboBox()
        
        monedas = db_settings.obtener_monedas()
        for m in monedas:
            combo_moneda.addItem(f"{m['nombre']} ({m['simbolo']})", m['id'])
            
        layout_form.addRow("Nombre (Ej: Binance):", campo_nombre)
        layout_form.addRow("Moneda Asociada:", combo_moneda)
        
        box_botones = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet(self.obtener_estilo_btn("blanco"))
        btn_guardar = QPushButton("Guardar")
        btn_guardar.setStyleSheet(self.obtener_estilo_btn("azul"))
        btn_cancelar.clicked.connect(dialog.reject)
        
        def guardar():
            nombre = campo_nombre.text().strip()
            moneda_id = combo_moneda.currentData()
            
            if not nombre: return self.mostrar_mensaje("Error", "El nombre es obligatorio.", "error")
            exito, msg = db_settings.guardar_metodo_pago(nombre, moneda_id)
            if exito:
                self.mostrar_mensaje("Éxito", msg)
                self.cargar_metodos()
                dialog.accept()
            else: self.mostrar_mensaje("Error", msg, "error")
            
        btn_guardar.clicked.connect(guardar)
        box_botones.addWidget(btn_cancelar)
        box_botones.addWidget(btn_guardar)
        layout_form.addRow(box_botones)
        dialog.exec()

    def eliminar_metodo(self):
        if not self.metodo_seleccionado: return self.mostrar_mensaje("Aviso", "Selecciona un método de pago de la tabla.", "error")
        if QMessageBox.question(self, "Confirmar", f"¿Seguro que deseas eliminar '{self.metodo_seleccionado['nombre']}'?") == QMessageBox.StandardButton.Yes:
            exito, msg = db_settings.eliminar_metodo_pago(self.metodo_seleccionado['id'])
            if exito:
                self.mostrar_mensaje("Éxito", msg)
                self.cargar_metodos()
            else: self.mostrar_mensaje("Error", msg, "error")

    # ================= PESTAÑA 5: ALMACENES =================
    def setup_tab_almacenes(self):
        layout = QVBoxLayout(self.tab_almacenes)
        layout.setContentsMargins(20, 20, 20, 20)
        barra = QHBoxLayout()
        barra.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        btn_nuevo = QPushButton("➕ Nuevo Almacén")
        btn_nuevo.setStyleSheet(self.obtener_estilo_btn("azul"))
        btn_nuevo.clicked.connect(self.abrir_modal_almacen)
        btn_eliminar = QPushButton("🗑️ Eliminar")
        btn_eliminar.setStyleSheet(self.obtener_estilo_btn("rojo"))
        btn_eliminar.clicked.connect(self.eliminar_almacen)
        
        barra.addWidget(btn_nuevo)
        barra.addWidget(btn_eliminar)
        layout.addLayout(barra)
        
        self.tabla_almacenes = QTableWidget()
        self.tabla_almacenes.setColumnCount(3)
        self.tabla_almacenes.setHorizontalHeaderLabels(["ID", "NOMBRE DEL ALMACÉN", "UBICACIÓN / DESCRIPCIÓN"])
        self.tabla_almacenes.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_almacenes.verticalHeader().setVisible(False)
        self.tabla_almacenes.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_almacenes.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla_almacenes.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_almacenes.setShowGrid(False)
        self.tabla_almacenes.setStyleSheet(self.obtener_estilo_tabla())
        self.tabla_almacenes.itemSelectionChanged.connect(self.seleccionar_almacen)
        layout.addWidget(self.tabla_almacenes)

    def cargar_almacenes(self):
        self.tabla_almacenes.setRowCount(0)
        self.almacen_seleccionado = None
        for fila_idx, d in enumerate(db_settings.obtener_almacenes()):
            self.tabla_almacenes.insertRow(fila_idx)
            item_id = QTableWidgetItem(str(d['id']))
            item_id.setData(Qt.ItemDataRole.UserRole, d)
            self.tabla_almacenes.setItem(fila_idx, 0, item_id)
            self.tabla_almacenes.setItem(fila_idx, 1, QTableWidgetItem(d['nombre']))
            self.tabla_almacenes.setItem(fila_idx, 2, QTableWidgetItem(d['ubicacion'] or ""))

    def seleccionar_almacen(self):
        filas = self.tabla_almacenes.selectedItems()
        self.almacen_seleccionado = self.tabla_almacenes.item(filas[0].row(), 0).data(Qt.ItemDataRole.UserRole) if filas else None

    def abrir_modal_almacen(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Nuevo Almacén")
        dialog.setFixedWidth(350)
        dialog.setStyleSheet(self.obtener_estilo_modal())
        
        layout_form = QFormLayout(dialog)
        campo_nombre = QLineEdit()
        campo_desc = QLineEdit()
        layout_form.addRow("Nombre (Ej: Depósito B):", campo_nombre)
        layout_form.addRow("Ubicación/Desc:", campo_desc)
        
        box_botones = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet(self.obtener_estilo_btn("blanco"))
        btn_guardar = QPushButton("Guardar")
        btn_guardar.setStyleSheet(self.obtener_estilo_btn("azul"))
        btn_cancelar.clicked.connect(dialog.reject)
        
        def guardar():
            nombre = campo_nombre.text().strip()
            desc = campo_desc.text().strip()
            if not nombre: return self.mostrar_mensaje("Error", "El nombre es obligatorio.", "error")
            exito, msg = db_settings.guardar_almacen(nombre, desc)
            if exito:
                self.mostrar_mensaje("Éxito", msg)
                self.cargar_almacenes()
                dialog.accept()
            else: self.mostrar_mensaje("Error", msg, "error")
            
        btn_guardar.clicked.connect(guardar)
        box_botones.addWidget(btn_cancelar)
        box_botones.addWidget(btn_guardar)
        layout_form.addRow(box_botones)
        dialog.exec()

    def eliminar_almacen(self):
        if not self.almacen_seleccionado: return self.mostrar_mensaje("Aviso", "Selecciona un almacén de la tabla.", "error")
        if QMessageBox.question(self, "Confirmar", f"¿Seguro que deseas eliminar '{self.almacen_seleccionado['nombre']}'?") == QMessageBox.StandardButton.Yes:
            exito, msg = db_settings.eliminar_almacen(self.almacen_seleccionado['id'])
            if exito:
                self.mostrar_mensaje("Éxito", msg)
                self.cargar_almacenes()
            else: self.mostrar_mensaje("Error", msg, "error")

    # ================= 🔥 PESTAÑA 6: USUARIOS Y PERMISOS 🔥 =================
    def setup_tab_usuarios(self):
        layout = QVBoxLayout(self.tab_usuarios)
        layout.setContentsMargins(20, 20, 20, 20)
        barra = QHBoxLayout()
        barra.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        btn_nuevo = QPushButton("➕ Nuevo Usuario")
        btn_nuevo.setStyleSheet(self.obtener_estilo_btn("azul"))
        btn_nuevo.clicked.connect(self.abrir_modal_usuario)
        
        btn_eliminar = QPushButton("🗑️ Eliminar")
        btn_eliminar.setStyleSheet(self.obtener_estilo_btn("rojo"))
        btn_eliminar.clicked.connect(self.eliminar_usuario)
        
        barra.addWidget(btn_nuevo)
        barra.addWidget(btn_eliminar)
        layout.addLayout(barra)
        
        self.tabla_usuarios = QTableWidget()
        self.tabla_usuarios.setColumnCount(4)
        self.tabla_usuarios.setHorizontalHeaderLabels(["ID", "NOMBRE COMPLETO", "USUARIO (LOGIN)", "ROL DE PERMISOS"])
        self.tabla_usuarios.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_usuarios.verticalHeader().setVisible(False)
        self.tabla_usuarios.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_usuarios.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla_usuarios.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_usuarios.setShowGrid(False)
        self.tabla_usuarios.setStyleSheet(self.obtener_estilo_tabla())
        self.tabla_usuarios.itemSelectionChanged.connect(self.seleccionar_usuario)
        layout.addWidget(self.tabla_usuarios)

    def cargar_usuarios(self):
        self.tabla_usuarios.setRowCount(0)
        self.usuario_seleccionado = None
        for fila_idx, u in enumerate(db_settings.obtener_usuarios()):
            self.tabla_usuarios.insertRow(fila_idx)
            item_id = QTableWidgetItem(str(u['id']))
            item_id.setData(Qt.ItemDataRole.UserRole, u)
            
            self.tabla_usuarios.setItem(fila_idx, 0, item_id)
            self.tabla_usuarios.setItem(fila_idx, 1, QTableWidgetItem(u['nombre']))
            self.tabla_usuarios.setItem(fila_idx, 2, QTableWidgetItem(f"👤 {u['usuario']}"))
            
            # Decoración de Roles
            item_rol = QTableWidgetItem(u['rol_nombre'])
            if u['rol_id'] == 1: item_rol.setForeground(QColor("#DC2626")) # Admin (Rojo)
            elif u['rol_id'] == 2: item_rol.setForeground(QColor("#D97706")) # Gerente (Naranja)
            else: item_rol.setForeground(QColor("#16A34A")) # Cajero (Verde)
                
            self.tabla_usuarios.setItem(fila_idx, 3, item_rol)

    def seleccionar_usuario(self):
        filas = self.tabla_usuarios.selectedItems()
        self.usuario_seleccionado = self.tabla_usuarios.item(filas[0].row(), 0).data(Qt.ItemDataRole.UserRole) if filas else None

    def abrir_modal_usuario(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Nuevo Usuario")
        dialog.setFixedWidth(380)
        dialog.setStyleSheet(self.obtener_estilo_modal())
        
        layout_form = QFormLayout(dialog)
        campo_nombre = QLineEdit()
        campo_usuario = QLineEdit()
        campo_password = QLineEdit()
        campo_password.setEchoMode(QLineEdit.EchoMode.Password)
        combo_rol = QComboBox()
        
        # Traer roles de la BD (Admin, Gerente, Cajero)
        for r in db_settings.obtener_roles():
            combo_rol.addItem(f"{r['nombre']}", r['id'])
            
        layout_form.addRow("Nombre Empleado:", campo_nombre)
        layout_form.addRow("Usuario (Para Login):", campo_usuario)
        layout_form.addRow("Contraseña:", campo_password)
        layout_form.addRow("Nivel de Acceso:", combo_rol)
        
        box_botones = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet(self.obtener_estilo_btn("blanco"))
        btn_guardar = QPushButton("Guardar y Asignar")
        btn_guardar.setStyleSheet(self.obtener_estilo_btn("azul"))
        btn_cancelar.clicked.connect(dialog.reject)
        
        def guardar():
            nombre = campo_nombre.text().strip()
            usuario = campo_usuario.text().strip()
            password = campo_password.text().strip()
            rol_id = combo_rol.currentData()
            
            if not nombre or not usuario or not password: 
                return self.mostrar_mensaje("Error", "Todos los campos son obligatorios.", "error")
                
            exito, msg = db_settings.guardar_usuario(nombre, usuario, password, rol_id)
            if exito:
                self.mostrar_mensaje("Éxito", msg)
                self.cargar_usuarios()
                dialog.accept()
            else: self.mostrar_mensaje("Error", msg, "error")
            
        btn_guardar.clicked.connect(guardar)
        box_botones.addWidget(btn_cancelar)
        box_botones.addWidget(btn_guardar)
        layout_form.addRow(box_botones)
        dialog.exec()

    def eliminar_usuario(self):
        if not self.usuario_seleccionado: return self.mostrar_mensaje("Aviso", "Selecciona un usuario de la tabla.", "error")
        
        respuesta = QMessageBox.question(self, "Confirmar", f"¿Seguro que deseas eliminar el acceso al usuario '{self.usuario_seleccionado['usuario']}'?")
        if respuesta == QMessageBox.StandardButton.Yes:
            exito, msg = db_settings.eliminar_usuario(self.usuario_seleccionado['id'])
            if exito:
                self.mostrar_mensaje("Éxito", msg)
                self.cargar_usuarios()
            else: self.mostrar_mensaje("Error", msg, "error")

    # ================= MENSAJES GLOBALES =================
    def mostrar_mensaje(self, titulo, texto, tipo="info"):
        msg = QMessageBox(self)
        msg.setWindowTitle(titulo)
        msg.setText(texto)
        msg.setStyleSheet("QLabel { color: #000000; font-size: 14px; } QPushButton { padding: 5px 15px; background-color: #2563EB; color: white; border-radius: 4px; }")
        if tipo == "error": msg.setIcon(QMessageBox.Icon.Warning)
        else: msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()