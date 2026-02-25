from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QDialog, QFormLayout, QMessageBox, QFrame, 
                             QAbstractItemView, QComboBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from modules.customers import db_customers
from modules.settings import db_settings  

class VistaClientes(QWidget):
    def __init__(self):
        super().__init__()
        self.cliente_seleccionado = None
        self.setup_ui()
        self.cargar_datos()

    def setup_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(40, 40, 40, 40)
        layout_principal.setSpacing(25)
        
        # ==========================================
        # CABECERA DEL MÓDULO
        # ==========================================
        header_layout = QVBoxLayout()
        header_layout.setSpacing(5)
        
        lbl_titulo = QLabel("DIRECTORIO DE CLIENTES")
        lbl_titulo.setStyleSheet("font-size: 24px; font-weight: 900; color: #0F172A; letter-spacing: 1px;")
        
        lbl_subtitulo = QLabel("Administración de cartera de clientes, datos de contacto y tarifas asignadas.")
        lbl_subtitulo.setStyleSheet("font-size: 14px; color: #64748B;")
        
        header_layout.addWidget(lbl_titulo)
        header_layout.addWidget(lbl_subtitulo)
        layout_principal.addLayout(header_layout)
        
        # ==========================================
        # TARJETA PRINCIPAL (CONTENEDOR)
        # ==========================================
        tarjeta = QFrame()
        tarjeta.setStyleSheet("""
            QFrame { 
                background-color: #FFFFFF; 
                border-radius: 8px; 
                border: 1px solid #E2E8F0; 
            }
        """)
        layout_tarjeta = QVBoxLayout(tarjeta)
        layout_tarjeta.setContentsMargins(25, 25, 25, 25)
        layout_tarjeta.setSpacing(20)
        
        # --- BARRA DE BÚSQUEDA Y BOTONES ---
        barra_herramientas = QHBoxLayout()
        barra_herramientas.setSpacing(10)
        
        self.campo_busqueda = QLineEdit()
        self.campo_busqueda.setPlaceholderText("Buscar por documento o razón social...")
        self.campo_busqueda.setFixedHeight(40)
        self.campo_busqueda.setStyleSheet("""
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
        self.campo_busqueda.textChanged.connect(self.cargar_datos) 
        barra_herramientas.addWidget(self.campo_busqueda, stretch=1)
        
        # Estilos corporativos para los botones
        estilo_btn_primario = """
            QPushButton { padding: 10px 15px; border-radius: 6px; font-weight: bold; font-size: 13px; background-color: #0F172A; color: white; border: none; }
            QPushButton:hover { background-color: #1E293B; }
        """
        estilo_btn_secundario = """
            QPushButton { padding: 10px 15px; border-radius: 6px; font-weight: bold; font-size: 13px; background-color: #F1F5F9; color: #334155; border: 1px solid #E2E8F0; }
            QPushButton:hover { background-color: #E2E8F0; }
        """
        estilo_btn_peligro = """
            QPushButton { padding: 10px 15px; border-radius: 6px; font-weight: bold; font-size: 13px; background-color: #FEF2F2; color: #DC2626; border: 1px solid #FECACA; }
            QPushButton:hover { background-color: #FEE2E2; }
        """
        
        btn_nuevo = QPushButton("Nuevo Cliente")
        btn_nuevo.setStyleSheet(estilo_btn_primario)
        btn_nuevo.clicked.connect(lambda: self.abrir_modal("nuevo"))
        btn_nuevo.setCursor(Qt.CursorShape.PointingHandCursor)
        
        btn_editar = QPushButton("Editar Cliente")
        btn_editar.setStyleSheet(estilo_btn_secundario)
        btn_editar.clicked.connect(lambda: self.abrir_modal("editar"))
        btn_editar.setCursor(Qt.CursorShape.PointingHandCursor)
        
        btn_eliminar = QPushButton("Eliminar")
        btn_eliminar.setStyleSheet(estilo_btn_peligro)
        btn_eliminar.clicked.connect(self.eliminar)
        btn_eliminar.setCursor(Qt.CursorShape.PointingHandCursor)
        
        barra_herramientas.addWidget(btn_nuevo)
        barra_herramientas.addWidget(btn_editar)
        barra_herramientas.addWidget(btn_eliminar)
        
        layout_tarjeta.addLayout(barra_herramientas)
        
        # --- TABLA DE DATOS ---
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["ID", "DOCUMENTO", "RAZÓN SOCIAL / NOMBRE", "TELÉFONO", "TARIFA ASIGNADA"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setShowGrid(False)
        self.tabla.verticalHeader().setDefaultSectionSize(45)
        
        self.tabla.setStyleSheet("""
            QTableWidget { 
                background-color: #FFFFFF; 
                color: #334155; 
                border: 1px solid #E2E8F0; 
                border-radius: 6px; 
                font-size: 13px; 
            }
            QTableWidget::item { 
                padding: 5px 10px; 
                border-bottom: 1px solid #F1F5F9; 
            }
            QTableWidget::item:selected { 
                background-color: #F8FAFC; 
                color: #0F172A; 
                font-weight: bold;
            }
            QHeaderView::section { 
                background-color: #F8FAFC; 
                color: #64748B; 
                font-weight: bold; 
                font-size: 12px; 
                padding: 12px; 
                border: none; 
                border-bottom: 2px solid #E2E8F0; 
                text-transform: uppercase;
            }
        """)
        
        self.tabla.itemSelectionChanged.connect(self.seleccionar)
        layout_tarjeta.addWidget(self.tabla)
        
        layout_principal.addWidget(tarjeta)

    # ================= MENSAJES GLOBALES (FONDO BLANCO) =================
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
            
            # ID Formateado (Ej: 00001)
            item_id = QTableWidgetItem(f"{c['id']:05d}")
            item_id.setForeground(QColor("#94A3B8"))
            item_id.setData(Qt.ItemDataRole.UserRole, c) 
            self.tabla.setItem(fila_idx, 0, item_id)
            
            self.tabla.setItem(fila_idx, 1, QTableWidgetItem(c['documento']))
            
            # Nombre en negrita
            item_nombre = QTableWidgetItem(c['nombre'])
            item_nombre.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            item_nombre.setForeground(QColor("#0F172A"))
            self.tabla.setItem(fila_idx, 2, item_nombre)
            
            self.tabla.setItem(fila_idx, 3, QTableWidgetItem(c['telefono'] or "N/A"))
            
            tarifa = c.get('lista_precio') or "Sin asignar"
            self.tabla.setItem(fila_idx, 4, QTableWidgetItem(tarifa))
            
            fila_idx += 1

    # ================= MODAL FORMULARIO =================
    def abrir_modal(self, modo="nuevo"):
        if modo == "editar" and not self.cliente_seleccionado:
            return self.mostrar_mensaje("Aviso", "Seleccione un cliente en la tabla para editar.", "error")

        dialog = QDialog(self)
        dialog.setWindowTitle("Registro de Cliente" if modo == "nuevo" else "Actualización de Cliente")
        dialog.setFixedWidth(450)
        
        # Estilo corporativo para el modal
        dialog.setStyleSheet("""
            QDialog { background-color: #FFFFFF; }
            QLabel { color: #334155; font-weight: bold; font-size: 13px; }
            QLineEdit, QComboBox { 
                padding: 10px; border: 1px solid #CBD5E1; border-radius: 4px; 
                background-color: #F8FAFC; color: #0F172A; font-size: 14px; 
            }
            QLineEdit:focus, QComboBox:focus { border: 2px solid #38BDF8; background-color: #FFFFFF; }
            QComboBox QAbstractItemView { background-color: #FFFFFF; color: #0F172A; selection-background-color: #EFF6FF; }
        """)
        
        layout_form = QFormLayout(dialog)
        layout_form.setSpacing(15)
        layout_form.setContentsMargins(25, 25, 25, 25)
        
        campo_documento = QLineEdit()
        campo_documento.setPlaceholderText("Ej: J-12345678-9")
        
        campo_nombre = QLineEdit()
        campo_nombre.setPlaceholderText("Razón social completa")
        
        campo_telefono = QLineEdit()
        campo_telefono.setPlaceholderText("Número de contacto")
        
        campo_direccion = QLineEdit()
        campo_direccion.setPlaceholderText("Dirección principal")
        
        combo_tarifa = QComboBox()
        
        # Llenar el Dropdown de Listas de Precios
        listas = db_settings.obtener_listas_precios()
        for l in listas:
            combo_tarifa.addItem(l['nombre'], l['id']) 
        
        # Modo Editar: Llenar datos previos
        if modo == "editar":
            campo_documento.setText(str(self.cliente_seleccionado.get("documento", "")))
            campo_nombre.setText(str(self.cliente_seleccionado.get("nombre", "")))
            campo_telefono.setText(str(self.cliente_seleccionado.get("telefono", "")))
            campo_direccion.setText(str(self.cliente_seleccionado.get("direccion", "")))
            
            idx_lista = combo_tarifa.findData(self.cliente_seleccionado.get("lista_precio_id"))
            if idx_lista >= 0:
                combo_tarifa.setCurrentIndex(idx_lista)
            
        layout_form.addRow("Documento / RIF:", campo_documento)
        layout_form.addRow("Razón Social:", campo_nombre)
        layout_form.addRow("Teléfono:", campo_telefono)
        layout_form.addRow("Dirección Física:", campo_direccion)
        layout_form.addRow("Tarifa de Precios:", combo_tarifa)
        
        box_botones = QHBoxLayout()
        btn_cancelar = QPushButton("Descartar")
        btn_cancelar.setStyleSheet("padding: 12px 20px; background-color: #FFFFFF; color: #334155; border: 1px solid #CBD5E1; border-radius: 6px; font-weight: bold;")
        btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        
        btn_guardar = QPushButton("Guardar Registro")
        btn_guardar.setStyleSheet("padding: 12px 20px; background-color: #0F172A; color: white; border-radius: 6px; font-weight: bold;")
        btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        
        btn_cancelar.clicked.connect(dialog.reject)
        
        def guardar():
            doc = campo_documento.text().strip()
            nom = campo_nombre.text().strip()
            lista_id = combo_tarifa.currentData() 
            
            if not doc or not nom or not lista_id:
                return self.mostrar_mensaje("Error", "Los campos Documento, Nombre y Tarifa son obligatorios.", "error")
            
            if modo == "nuevo":
                exito, msg = db_customers.guardar_cliente(doc, nom, campo_telefono.text().strip(), campo_direccion.text().strip(), lista_id)
            else:
                exito, msg = db_customers.editar_cliente(self.cliente_seleccionado["id"], doc, nom, campo_telefono.text().strip(), campo_direccion.text().strip(), lista_id)
                
            if exito:
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
            return self.mostrar_mensaje("Aviso", "Seleccione un cliente en la tabla para eliminar.", "error")
            
        # Regla de Negocio: No borrar al Cliente General/Mostrador
        if self.cliente_seleccionado["id"] == 1:
            return self.mostrar_mensaje("Acción Denegada", "No es posible eliminar al 'Cliente General' (ID 1) ya que es requerido por el sistema para ventas por defecto.", "error")
            
        # Alerta de confirmación con estilo corporativo
        msg_confirm = QMessageBox(self)
        msg_confirm.setWindowTitle("Confirmar Baja")
        msg_confirm.setText(f"¿Está seguro de eliminar el registro de:\n{self.cliente_seleccionado['nombre']}?")
        msg_confirm.setIcon(QMessageBox.Icon.Question)
        msg_confirm.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_confirm.setStyleSheet("""
            QMessageBox { background-color: #FFFFFF; }
            QLabel { color: #0F172A; font-size: 13px; font-weight: bold; } 
            QPushButton { padding: 6px 20px; background-color: #DC2626; color: white; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #B91C1C; }
        """)
                                         
        if msg_confirm.exec() == QMessageBox.StandardButton.Yes:
            exito, msg = db_customers.eliminar_cliente(self.cliente_seleccionado["id"])
            if exito:
                self.cargar_datos()
            else:
                self.mostrar_mensaje("Error", msg, "error")