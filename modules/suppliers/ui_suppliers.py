from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QDialog, QFormLayout, QMessageBox, QFrame, QAbstractItemView)
from PyQt6.QtCore import Qt
from modules.suppliers import db_suppliers

class VistaProveedores(QWidget):
    def __init__(self):
        super().__init__()
        self.proveedor_seleccionado = None
        self.setup_ui()
        self.cargar_datos()

    def setup_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(40, 40, 40, 40) # Márgenes amplios y modernos
        layout_principal.setSpacing(20)
        
        # ================= ENCABEZADO =================
        lbl_titulo = QLabel("Directorio de Proveedores")
        lbl_titulo.setStyleSheet("""
            font-size: 28px; 
            font-weight: 800; 
            color: #0F172A; /* Gris súper oscuro, casi negro */
            margin-bottom: 5px;
        """)
        
        lbl_subtitulo = QLabel("Gestiona las empresas que te surten mercancía.")
        lbl_subtitulo.setStyleSheet("font-size: 14px; color: #64748B; margin-bottom: 15px;")
        
        layout_principal.addWidget(lbl_titulo)
        layout_principal.addWidget(lbl_subtitulo)
        
        # ================= CONTENEDOR TIPO TARJETA =================
        # Metemos todo en una tarjeta blanca para que resalte sobre el fondo gris claro del main
        tarjeta = QFrame()
        tarjeta.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 12px;
                border: 1px solid #E2E8F0;
            }
        """)
        layout_tarjeta = QVBoxLayout(tarjeta)
        layout_tarjeta.setContentsMargins(20, 20, 20, 20)
        layout_tarjeta.setSpacing(15)
        
        # ================= BARRA DE HERRAMIENTAS =================
        barra_herramientas = QHBoxLayout()
        
        self.campo_busqueda = QLineEdit()
        self.campo_busqueda.setPlaceholderText("🔍 Buscar por documento o nombre...")
        self.campo_busqueda.setFixedHeight(42)
        # Estilo de input moderno (borde claro, texto oscuro)
        self.campo_busqueda.setStyleSheet("""
            QLineEdit {
                padding: 5px 15px; 
                border: 1px solid #CBD5E1; 
                border-radius: 6px;
                font-size: 14px;
                color: #1E293B;
                background-color: #F8FAFC;
            }
            QLineEdit:focus {
                border: 2px solid #3B82F6;
                background-color: #FFFFFF;
            }
        """)
        self.campo_busqueda.textChanged.connect(self.cargar_datos) 
        barra_herramientas.addWidget(self.campo_busqueda)
        
        # Estilos de botones
        estilo_btn_base = """
            QPushButton {
                padding: 10px 18px; 
                border-radius: 6px; 
                font-weight: 600; 
                font-size: 13px;
            }
        """
        
        btn_nuevo = QPushButton("➕ Nuevo")
        btn_nuevo.setStyleSheet(estilo_btn_base + """
            QPushButton { background-color: #2563EB; color: white; border: none; }
            QPushButton:hover { background-color: #1D4ED8; }
        """)
        btn_nuevo.clicked.connect(lambda: self.abrir_modal("nuevo"))
        btn_nuevo.setCursor(Qt.CursorShape.PointingHandCursor)
        
        btn_editar = QPushButton("✏️ Editar")
        btn_editar.setStyleSheet(estilo_btn_base + """
            QPushButton { background-color: #FFFFFF; color: #334155; border: 1px solid #CBD5E1; }
            QPushButton:hover { background-color: #F1F5F9; color: #0F172A; }
        """)
        btn_editar.clicked.connect(lambda: self.abrir_modal("editar"))
        btn_editar.setCursor(Qt.CursorShape.PointingHandCursor)
        
        btn_eliminar = QPushButton("🗑️ Eliminar")
        btn_eliminar.setStyleSheet(estilo_btn_base + """
            QPushButton { background-color: #FEF2F2; color: #DC2626; border: 1px solid #FECACA; }
            QPushButton:hover { background-color: #FEE2E2; border: 1px solid #F87171; }
        """)
        btn_eliminar.clicked.connect(self.eliminar)
        btn_eliminar.setCursor(Qt.CursorShape.PointingHandCursor)
        
        barra_herramientas.addWidget(btn_nuevo)
        barra_herramientas.addWidget(btn_editar)
        barra_herramientas.addWidget(btn_eliminar)
        
        layout_tarjeta.addLayout(barra_herramientas)
        
        # ================= TABLA MODERNA =================
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["ID", "DOCUMENTO", "NOMBRE COMERCIAL", "TELÉFONO", "DIRECCIÓN"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setShowGrid(False) # Quitamos la cuadrícula fea de Excel
        self.tabla.verticalHeader().setVisible(False)

        
        # Estilo de la tabla para alto contraste
        self.tabla.setStyleSheet("""
            QTableWidget {
                background-color: #FFFFFF;
                color: #334155;
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 10px;
                border-bottom: 1px solid #F1F5F9; /* Líneas separadoras suaves */
            }
            QTableWidget::item:selected {
                background-color: #EFF6FF; /* Fondo azul claro al seleccionar */
                color: #1E3A8A; /* Texto azul oscuro legible */
                font-weight: bold;
            }
            QHeaderView::section {
                background-color: #F8FAFC;
                color: #64748B;
                font-weight: 700;
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

    # ================= FUNCIONES LÓGICAS (Intactas) =================
    def mostrar_mensaje(self, titulo, texto, tipo="info"):
        msg = QMessageBox(self)
        msg.setWindowTitle(titulo)
        msg.setText(texto)
        msg.setStyleSheet("QLabel { color: #1E293B; font-size: 14px; } QPushButton { padding: 5px 15px; background-color: #2563EB; color: white; border-radius: 4px; }")
        if tipo == "error": msg.setIcon(QMessageBox.Icon.Warning)
        else: msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()

    def seleccionar(self):
        filas_seleccionadas = self.tabla.selectedItems()
        if filas_seleccionadas:
            fila = filas_seleccionadas[0].row()
            self.proveedor_seleccionado = self.tabla.item(fila, 0).data(Qt.ItemDataRole.UserRole)
        else:
            self.proveedor_seleccionado = None

    def cargar_datos(self):
        self.tabla.setRowCount(0)
        self.proveedor_seleccionado = None
        termino_busqueda = self.campo_busqueda.text().strip().lower()
        proveedores = db_suppliers.obtener_proveedores()
        
        fila_idx = 0
        for p in proveedores:
            documento = str(p.get("documento") or "").lower()
            nombre = str(p.get("nombre") or "").lower()
            
            if termino_busqueda and termino_busqueda not in documento and termino_busqueda not in nombre:
                continue
            
            self.tabla.insertRow(fila_idx)
            item_id = QTableWidgetItem(str(p.get("id", "")))
            item_id.setData(Qt.ItemDataRole.UserRole, p) 
            
            self.tabla.setItem(fila_idx, 0, item_id)
            self.tabla.setItem(fila_idx, 1, QTableWidgetItem(str(p.get("documento") or "")))
            self.tabla.setItem(fila_idx, 2, QTableWidgetItem(str(p.get("nombre") or "")))
            self.tabla.setItem(fila_idx, 3, QTableWidgetItem(str(p.get("telefono") or "N/A")))
            self.tabla.setItem(fila_idx, 4, QTableWidgetItem(str(p.get("direccion") or "N/A")))
            fila_idx += 1

    def abrir_modal(self, modo="nuevo"):
        if modo == "editar" and not self.proveedor_seleccionado:
            self.mostrar_mensaje("Aviso", "Selecciona un proveedor de la tabla para editar.", "error")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Nuevo Proveedor" if modo == "nuevo" else "Editar Proveedor")
        dialog.setFixedWidth(450)
        dialog.setStyleSheet("""
            QDialog { background-color: #FFFFFF; }
            QLabel { color: #334155; font-weight: 600; font-size: 13px; }
            QLineEdit { padding: 8px; border: 1px solid #CBD5E1; border-radius: 4px; color: #0F172A; background-color: #F8FAFC; }
            QLineEdit:focus { border: 2px solid #3B82F6; background-color: #FFFFFF; }
        """)
        
        layout_form = QFormLayout(dialog)
        layout_form.setSpacing(15)
        layout_form.setContentsMargins(25, 25, 25, 25)
        
        campo_documento = QLineEdit()
        campo_nombre = QLineEdit()
        campo_telefono = QLineEdit()
        campo_direccion = QLineEdit()
        
        if modo == "editar":
            campo_documento.setText(str(self.proveedor_seleccionado.get("documento", "")))
            campo_nombre.setText(str(self.proveedor_seleccionado.get("nombre", "")))
            campo_telefono.setText(str(self.proveedor_seleccionado.get("telefono", "")))
            campo_direccion.setText(str(self.proveedor_seleccionado.get("direccion", "")))
            
        layout_form.addRow("Documento:", campo_documento)
        layout_form.addRow("Razón Social:", campo_nombre)
        layout_form.addRow("Teléfono:", campo_telefono)
        layout_form.addRow("Dirección:", campo_direccion)
        
        box_botones = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet("padding: 8px 15px; background-color: #F1F5F9; color: #475569; border-radius: 4px; font-weight: bold;")
        btn_guardar = QPushButton("Guardar Proveedor")
        btn_guardar.setStyleSheet("padding: 8px 15px; background-color: #2563EB; color: white; border-radius: 4px; font-weight: bold;")
        
        btn_cancelar.clicked.connect(dialog.reject)
        
        def guardar():
            data = {
                "documento": campo_documento.text().strip(),
                "nombre": campo_nombre.text().strip(),
                "telefono": campo_telefono.text().strip(),
                "direccion": campo_direccion.text().strip(),
            }
            if not data["documento"] or not data["nombre"]:
                self.mostrar_mensaje("Error", "Documento y Nombre son obligatorios.", "error")
                return
            
            if modo == "nuevo": exito, msg = db_suppliers.crear_proveedor(data)
            else: exito, msg = db_suppliers.actualizar_proveedor(self.proveedor_seleccionado["id"], data)
                
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
        if not self.proveedor_seleccionado:
            self.mostrar_mensaje("Aviso", "Selecciona un proveedor de la tabla para eliminar.", "error")
            return
            
        respuesta = QMessageBox.question(
            self, "Confirmar", 
            f"¿Seguro que deseas eliminar al proveedor '{self.proveedor_seleccionado['nombre']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
                                         
        if respuesta == QMessageBox.StandardButton.Yes:
            exito, msg = db_suppliers.eliminar_proveedor(self.proveedor_seleccionado["id"])
            if exito:
                self.mostrar_mensaje("Éxito", msg)
                self.cargar_datos()
            else:
                self.mostrar_mensaje("Error", msg, "error")