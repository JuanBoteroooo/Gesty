from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QDialog, QFormLayout, QMessageBox, QFrame, 
                             QAbstractItemView, QComboBox)
from PyQt6.QtCore import Qt
from modules.customers import db_customers
from modules.settings import db_settings  # Importamos para leer las Listas de Precios

class VistaClientes(QWidget):
    def __init__(self):
        super().__init__()
        self.cliente_seleccionado = None
        self.setup_ui()
        self.cargar_datos()

    def setup_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(40, 40, 40, 40)
        layout_principal.setSpacing(20)
        
        # ================= ENCABEZADO =================
        lbl_titulo = QLabel("Directorio de Clientes")
        lbl_titulo.setStyleSheet("font-size: 28px; font-weight: 800; color: #0F172A; margin-bottom: 5px;")
        lbl_subtitulo = QLabel("Administra los datos y tarifas asignadas a tus compradores.")
        lbl_subtitulo.setStyleSheet("font-size: 14px; color: #64748B; margin-bottom: 15px;")
        
        layout_principal.addWidget(lbl_titulo)
        layout_principal.addWidget(lbl_subtitulo)
        
        # ================= TARJETA BLANCA =================
        tarjeta = QFrame()
        tarjeta.setStyleSheet("QFrame { background-color: #FFFFFF; border-radius: 12px; border: 1px solid #E2E8F0; }")
        layout_tarjeta = QVBoxLayout(tarjeta)
        layout_tarjeta.setContentsMargins(20, 20, 20, 20)
        layout_tarjeta.setSpacing(15)
        
        # ================= BARRA DE HERRAMIENTAS Y BUSCADOR =================
        barra_herramientas = QHBoxLayout()
        
        self.campo_busqueda = QLineEdit()
        self.campo_busqueda.setPlaceholderText("🔍 Buscar por documento o nombre...")
        self.campo_busqueda.setFixedHeight(42)
        self.campo_busqueda.setStyleSheet("""
            QLineEdit { padding: 5px 15px; border: 1px solid #CBD5E1; border-radius: 6px; font-size: 14px; color: #1E293B; background-color: #F8FAFC; }
            QLineEdit:focus { border: 2px solid #3B82F6; background-color: #FFFFFF; }
        """)
        self.campo_busqueda.textChanged.connect(self.cargar_datos) 
        barra_herramientas.addWidget(self.campo_busqueda)
        
        # Botones
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
        
        # ================= TABLA =================
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["ID", "DOCUMENTO", "NOMBRE", "TELÉFONO", "TARIFA ASIGNADA"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.verticalHeader().setVisible(False) # Adiós franja negra
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setShowGrid(False)
        
        self.tabla.setStyleSheet("""
            QTableWidget { background-color: #FFFFFF; color: #334155; border: 1px solid #E2E8F0; border-radius: 6px; font-size: 13px; }
            QTableWidget::item { padding: 10px; border-bottom: 1px solid #F1F5F9; }
            QTableWidget::item:selected { background-color: #EFF6FF; color: #1E3A8A; font-weight: bold; }
            QHeaderView::section { background-color: #F8FAFC; color: #64748B; font-weight: 700; font-size: 12px; padding: 12px; border: none; border-bottom: 2px solid #E2E8F0; }
        """)
        
        self.tabla.itemSelectionChanged.connect(self.seleccionar)
        layout_tarjeta.addWidget(self.tabla)
        
        layout_principal.addWidget(tarjeta)

    # ================= MENSAJES GLOBALES =================
    def mostrar_mensaje(self, titulo, texto, tipo="info"):
        msg = QMessageBox(self)
        msg.setWindowTitle(titulo)
        msg.setText(texto)
        msg.setStyleSheet("QLabel { color: #000000; font-size: 14px; } QPushButton { padding: 5px 15px; background-color: #2563EB; color: white; border-radius: 4px; }")
        if tipo == "error": msg.setIcon(QMessageBox.Icon.Warning)
        else: msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()

    # ================= SELECCIÓN =================
    def seleccionar(self):
        filas = self.tabla.selectedItems()
        if filas:
            self.cliente_seleccionado = self.tabla.item(filas[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        else:
            self.cliente_seleccionado = None

    # ================= CARGAR DATOS =================
    def cargar_datos(self):
        self.tabla.setRowCount(0)
        self.cliente_seleccionado = None
        termino_busqueda = self.campo_busqueda.text().strip().lower()
        clientes = db_customers.obtener_clientes()
        
        fila_idx = 0
        for c in clientes:
            documento = str(c.get("documento") or "").lower()
            nombre = str(c.get("nombre") or "").lower()
            
            # Filtro
            if termino_busqueda and termino_busqueda not in documento and termino_busqueda not in nombre:
                continue
            
            self.tabla.insertRow(fila_idx)
            item_id = QTableWidgetItem(str(c['id']))
            item_id.setData(Qt.ItemDataRole.UserRole, c) 
            
            self.tabla.setItem(fila_idx, 0, item_id)
            self.tabla.setItem(fila_idx, 1, QTableWidgetItem(c['documento']))
            self.tabla.setItem(fila_idx, 2, QTableWidgetItem(c['nombre']))
            self.tabla.setItem(fila_idx, 3, QTableWidgetItem(c['telefono'] or "N/A"))
            
            # Formatear visualmente la tarifa
            tarifa = c.get('lista_precio') or "Sin asignar"
            item_tarifa = QTableWidgetItem(f"🏷️ {tarifa}")
            self.tabla.setItem(fila_idx, 4, item_tarifa)
            
            fila_idx += 1

    # ================= MODAL FORMULARIO =================
    def abrir_modal(self, modo="nuevo"):
        if modo == "editar" and not self.cliente_seleccionado:
            return self.mostrar_mensaje("Aviso", "Selecciona un cliente de la tabla para editar.", "error")

        dialog = QDialog(self)
        dialog.setWindowTitle("Nuevo Cliente" if modo == "nuevo" else "Editar Cliente")
        dialog.setFixedWidth(450)
        
        # Estilo para inputs negros y Combobox desplegable
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
        
        campo_documento = QLineEdit()
        campo_nombre = QLineEdit()
        campo_telefono = QLineEdit()
        campo_direccion = QLineEdit()
        combo_tarifa = QComboBox()
        
        # Llenar el Dropdown de Listas de Precios
        listas = db_settings.obtener_listas_precios()
        for l in listas:
            combo_tarifa.addItem(l['nombre'], l['id']) # El texto se ve, el ID se esconde
        
        # Modo Editar: Llenar datos previos
        if modo == "editar":
            campo_documento.setText(str(self.cliente_seleccionado.get("documento", "")))
            campo_nombre.setText(str(self.cliente_seleccionado.get("nombre", "")))
            campo_telefono.setText(str(self.cliente_seleccionado.get("telefono", "")))
            campo_direccion.setText(str(self.cliente_seleccionado.get("direccion", "")))
            
            # Buscar el ID de la lista en el combobox para dejarlo seleccionado
            idx_lista = combo_tarifa.findData(self.cliente_seleccionado.get("lista_precio_id"))
            if idx_lista >= 0:
                combo_tarifa.setCurrentIndex(idx_lista)
            
        layout_form.addRow("Documento:", campo_documento)
        layout_form.addRow("Razón Social:", campo_nombre)
        layout_form.addRow("Teléfono:", campo_telefono)
        layout_form.addRow("Dirección:", campo_direccion)
        layout_form.addRow("Tarifa de Precio:", combo_tarifa)
        
        box_botones = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet("padding: 8px 15px; background-color: #F1F5F9; color: #475569; border-radius: 4px; font-weight: bold;")
        btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        
        btn_guardar = QPushButton("Guardar Cliente")
        btn_guardar.setStyleSheet("padding: 8px 15px; background-color: #2563EB; color: white; border-radius: 4px; font-weight: bold;")
        btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        
        btn_cancelar.clicked.connect(dialog.reject)
        
        def guardar():
            doc = campo_documento.text().strip()
            nom = campo_nombre.text().strip()
            lista_id = combo_tarifa.currentData() # Extraemos el ID escondido
            
            if not doc or not nom or not lista_id:
                return self.mostrar_mensaje("Error", "Documento, Nombre y Tarifa son obligatorios.", "error")
            
            if modo == "nuevo":
                exito, msg = db_customers.guardar_cliente(doc, nom, campo_telefono.text().strip(), campo_direccion.text().strip(), lista_id)
            else:
                exito, msg = db_customers.editar_cliente(self.cliente_seleccionado["id"], doc, nom, campo_telefono.text().strip(), campo_direccion.text().strip(), lista_id)
                
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

    # ================= ELIMINAR =================
    def eliminar(self):
        if not self.cliente_seleccionado:
            return self.mostrar_mensaje("Aviso", "Selecciona un cliente de la tabla para eliminar.", "error")
            
        # Regla de Negocio: No borrar al Cliente Mostrador
        if self.cliente_seleccionado["id"] == 1:
            return self.mostrar_mensaje("Protección", "No puedes eliminar al 'Cliente Mostrador' (ID 1), es el cliente por defecto.", "error")
            
        respuesta = QMessageBox.question(
            self, "Confirmar", 
            f"¿Seguro que deseas eliminar al cliente '{self.cliente_seleccionado['nombre']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
                                         
        if respuesta == QMessageBox.StandardButton.Yes:
            exito, msg = db_customers.eliminar_cliente(self.cliente_seleccionado["id"])
            if exito:
                self.mostrar_mensaje("Éxito", msg)
                self.cargar_datos()
            else:
                self.mostrar_mensaje("Error", msg, "error")