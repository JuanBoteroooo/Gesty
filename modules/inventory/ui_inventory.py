from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QDialog, QFormLayout, QMessageBox, QFrame, 
                             QAbstractItemView, QComboBox, QTabWidget, QSpinBox, QDoubleSpinBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from modules.inventory import db_inventory
from modules.settings import db_settings 
from modules.suppliers import db_suppliers 
from utils import session

class VistaInventario(QWidget):
    def __init__(self):
        super().__init__()
        self.producto_seleccionado = None
        self.listas_precios = [] 
        
        self.setup_ui()
        self.cargar_datos()

    def setup_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(40, 40, 40, 40)
        layout_principal.setSpacing(20)
        
        lbl_titulo = QLabel("Inventario de Productos")
        lbl_titulo.setStyleSheet("font-size: 28px; font-weight: 800; color: #0F172A; margin-bottom: 5px;")
        lbl_subtitulo = QLabel("Administra tu catálogo, realiza traspasos y consulta el Kardex de movimientos.")
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
        
        estilo_btn_base = "QPushButton { padding: 10px 15px; border-radius: 6px; font-weight: 600; font-size: 13px; }"
        
        btn_nuevo = QPushButton("➕ Nuevo")
        btn_nuevo.setStyleSheet(estilo_btn_base + "QPushButton { background-color: #2563EB; color: white; border: none; } QPushButton:hover { background-color: #1D4ED8; }")
        btn_nuevo.clicked.connect(lambda: self.abrir_modal_ficha("nuevo"))
        
        btn_editar = QPushButton("✏️ Ficha")
        btn_editar.setStyleSheet(estilo_btn_base + "QPushButton { background-color: #FFFFFF; color: #334155; border: 1px solid #CBD5E1; } QPushButton:hover { background-color: #F1F5F9; }")
        btn_editar.clicked.connect(lambda: self.abrir_modal_ficha("editar"))
        
        btn_traspaso = QPushButton("↔️ Traspaso")
        btn_traspaso.setStyleSheet(estilo_btn_base + "QPushButton { background-color: #F59E0B; color: white; border: none; } QPushButton:hover { background-color: #D97706; }")
        btn_traspaso.clicked.connect(self.abrir_modal_traspaso)
        
        btn_ajuste = QPushButton("⚖️ Ajuste")
        btn_ajuste.setStyleSheet(estilo_btn_base + "QPushButton { background-color: #8B5CF6; color: white; border: none; } QPushButton:hover { background-color: #7C3AED; }")
        btn_ajuste.clicked.connect(self.abrir_modal_ajuste)
        
        btn_kardex = QPushButton("📖 Kardex")
        btn_kardex.setStyleSheet(estilo_btn_base + "QPushButton { background-color: #10B981; color: white; border: none; } QPushButton:hover { background-color: #059669; }")
        btn_kardex.clicked.connect(self.abrir_modal_kardex)
        
        btn_eliminar = QPushButton("🗑️ Eliminar")
        btn_eliminar.setStyleSheet(estilo_btn_base + "QPushButton { background-color: #FEF2F2; color: #DC2626; border: 1px solid #FECACA; } QPushButton:hover { background-color: #FEE2E2; }")
        btn_eliminar.clicked.connect(self.eliminar)
        
        for btn in [btn_nuevo, btn_editar, btn_traspaso, btn_ajuste, btn_kardex, btn_eliminar]:
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            barra_herramientas.addWidget(btn)
        
        layout_tarjeta.addLayout(barra_herramientas)
        
        self.tabla = QTableWidget()
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
        self.producto_seleccionado = self.tabla.item(filas[0].row(), 0).data(Qt.ItemDataRole.UserRole) if filas else None

    def cargar_datos(self):
        columnas_finales = ["ID", "CÓDIGO", "DESCRIPCIÓN", "CATEGORÍA", "PROVEEDOR", "STOCK TOTAL"]
        
        self.tabla.setColumnCount(len(columnas_finales))
        self.tabla.setHorizontalHeaderLabels(columnas_finales)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) 

        self.tabla.setRowCount(0)
        self.producto_seleccionado = None
        
        termino = self.campo_busqueda.text().strip().lower()
        productos = db_inventory.obtener_productos()
        
        fila_idx = 0
        for p in productos:
            codigo = str(p.get("codigo") or "").lower()
            nombre = str(p.get("nombre") or "").lower()
            if termino and termino not in codigo and termino not in nombre: continue
            
            self.tabla.insertRow(fila_idx)
            item_id = QTableWidgetItem(str(p['id']))
            item_id.setData(Qt.ItemDataRole.UserRole, p) 
            
            self.tabla.setItem(fila_idx, 0, item_id)
            self.tabla.setItem(fila_idx, 1, QTableWidgetItem(p['codigo']))
            self.tabla.setItem(fila_idx, 2, QTableWidgetItem(p['nombre']))
            self.tabla.setItem(fila_idx, 3, QTableWidgetItem(p['categoria'] or "General"))
            self.tabla.setItem(fila_idx, 4, QTableWidgetItem(f"💼 {p['proveedor_nombre']}"))
            
            stock_total = float(p['stock_total'])
            stock_min = float(p['stock_minimo'])
            
            if stock_total <= stock_min:
                item_stock = QTableWidgetItem(f"⚠️ {stock_total} (¡Bajo!)")
                item_stock.setForeground(QColor("#DC2626"))
            else:
                item_stock = QTableWidgetItem(str(stock_total))
                item_stock.setForeground(QColor("#16A34A")) 
                
            self.tabla.setItem(fila_idx, 5, item_stock)
            fila_idx += 1

    # ================= MODALES DE MOVIMIENTO =================
    def abrir_modal_traspaso(self):
        if not self.producto_seleccionado: return self.mostrar_mensaje("Aviso", "Selecciona un producto.", "error")
        
        almacenes = db_settings.obtener_almacenes()
        if len(almacenes) < 2: return self.mostrar_mensaje("Error", "Necesitas al menos 2 almacenes para hacer un traspaso.", "error")

        dialog = QDialog(self)
        dialog.setWindowTitle(f"↔️ Traspaso: {self.producto_seleccionado['nombre']}")
        dialog.setFixedWidth(400)
        dialog.setStyleSheet("QDialog { background-color: #FFFFFF; } QLabel { color: #0F172A; font-weight: bold; } QComboBox, QSpinBox, QLineEdit { padding: 8px; border: 1px solid #CBD5E1; border-radius: 4px; background-color: #F8FAFC; color: black; font-weight: bold; }")
        
        layout = QFormLayout(dialog)
        
        combo_origen = QComboBox()
        combo_destino = QComboBox()
        for a in almacenes:
            combo_origen.addItem(a['nombre'], a['id'])
            combo_destino.addItem(a['nombre'], a['id'])
            
        spin_cant = QSpinBox()
        spin_cant.setMinimum(1)
        spin_cant.setMaximum(99999)
        
        txt_motivo = QLineEdit()
        txt_motivo.setPlaceholderText("Ej: Reposición de vitrina")
        
        layout.addRow("Sacar de (Origen):", combo_origen)
        layout.addRow("Enviar a (Destino):", combo_destino)
        layout.addRow("Cantidad a Mover:", spin_cant)
        layout.addRow("Motivo:", txt_motivo)
        
        btn_guardar = QPushButton("Confirmar Traspaso")
        btn_guardar.setStyleSheet("padding: 10px; background-color: #F59E0B; color: white; font-weight: bold; border-radius: 4px;")
        
        def procesar():
            if combo_origen.currentData() == combo_destino.currentData():
                return QMessageBox.warning(dialog, "Error", "El almacén de origen y destino no pueden ser el mismo.")
            
            exito, msg = db_inventory.registrar_movimiento(
                self.producto_seleccionado['id'], combo_origen.currentData(), combo_destino.currentData(),
                'TRASPASO', spin_cant.value(), txt_motivo.text() or "Traspaso manual", session.usuario_actual['id']
            )
            if exito:
                self.mostrar_mensaje("Éxito", msg)
                self.cargar_datos()
                dialog.accept()
            else: self.mostrar_mensaje("Error", msg, "error")
            
        btn_guardar.clicked.connect(procesar)
        layout.addRow(btn_guardar)
        dialog.exec()

    def abrir_modal_ajuste(self):
        if not self.producto_seleccionado: return self.mostrar_mensaje("Aviso", "Selecciona un producto.", "error")

        dialog = QDialog(self)
        dialog.setWindowTitle(f"⚖️ Ajuste: {self.producto_seleccionado['nombre']}")
        dialog.setFixedWidth(400)
        dialog.setStyleSheet("QDialog { background-color: #FFFFFF; } QLabel { color: #0F172A; font-weight: bold; } QComboBox, QSpinBox, QLineEdit { padding: 8px; border: 1px solid #CBD5E1; border-radius: 4px; background-color: #F8FAFC; color: black; font-weight: bold; }")
        
        layout = QFormLayout(dialog)
        
        combo_almacen = QComboBox()
        for a in db_settings.obtener_almacenes(): combo_almacen.addItem(a['nombre'], a['id'])
            
        combo_tipo = QComboBox()
        combo_tipo.addItem("Entrada (Suma Stock)", "AJUSTE_POSITIVO")
        combo_tipo.addItem("Salida / Merma (Resta Stock)", "AJUSTE_NEGATIVO")
            
        spin_cant = QSpinBox()
        spin_cant.setMinimum(1)
        spin_cant.setMaximum(99999)
        
        txt_motivo = QLineEdit()
        txt_motivo.setPlaceholderText("Ej: Mercancía dañada / Conteo manual")
        
        layout.addRow("Almacén Afectado:", combo_almacen)
        layout.addRow("Tipo de Ajuste:", combo_tipo)
        layout.addRow("Cantidad:", spin_cant)
        layout.addRow("Motivo (Obligatorio):", txt_motivo)
        
        btn_guardar = QPushButton("Registrar Ajuste")
        btn_guardar.setStyleSheet("padding: 10px; background-color: #8B5CF6; color: white; font-weight: bold; border-radius: 4px;")
        
        def procesar():
            if not txt_motivo.text().strip(): return QMessageBox.warning(dialog, "Error", "Debes especificar un motivo para el ajuste.")
            exito, msg = db_inventory.registrar_movimiento(
                self.producto_seleccionado['id'], combo_almacen.currentData(), None,
                combo_tipo.currentData(), spin_cant.value(), txt_motivo.text(), session.usuario_actual['id']
            )
            if exito:
                self.mostrar_mensaje("Éxito", msg)
                self.cargar_datos()
                dialog.accept()
            else: self.mostrar_mensaje("Error", msg, "error")
            
        btn_guardar.clicked.connect(procesar)
        layout.addRow(btn_guardar)
        dialog.exec()

    def abrir_modal_kardex(self):
        if not self.producto_seleccionado: return self.mostrar_mensaje("Aviso", "Selecciona un producto.", "error")
        
        historial = db_inventory.obtener_historial_kardex(self.producto_seleccionado['id'])
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"📖 Kardex (Auditoría): {self.producto_seleccionado['nombre']}")
        dialog.setFixedWidth(800)
        dialog.setStyleSheet("QDialog { background-color: #FFFFFF; }")
        
        layout = QVBoxLayout(dialog)
        
        tabla = QTableWidget()
        tabla.setColumnCount(6)
        tabla.setHorizontalHeaderLabels(["FECHA", "TIPO", "CANT.", "ALMACÉN", "MOTIVO", "USUARIO"])
        tabla.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        tabla.verticalHeader().setVisible(False)
        tabla.setStyleSheet("QTableWidget { background-color: #F8FAFC; color: black; font-weight: bold; font-size: 12px; }")
        
        tabla.setRowCount(len(historial))
        for i, h in enumerate(historial):
            tabla.setItem(i, 0, QTableWidgetItem(h['fecha']))
            
            item_tipo = QTableWidgetItem(h['tipo_movimiento'])
            if "POSITIVO" in h['tipo_movimiento'] or "ENTRADA" in h['tipo_movimiento']: item_tipo.setForeground(QColor("#16A34A"))
            elif "NEGATIVO" in h['tipo_movimiento'] or "SALIDA" in h['tipo_movimiento']: item_tipo.setForeground(QColor("#DC2626"))
            else: item_tipo.setForeground(QColor("#F59E0B"))
            
            tabla.setItem(i, 1, item_tipo)
            tabla.setItem(i, 2, QTableWidgetItem(str(h['cantidad'])))
            
            if h['tipo_movimiento'] == 'TRASPASO': 
                almacen_texto = f"{h['almacen_origen']} ➡️ {h['almacen_destino']}"
            else:
                almacen_texto = h['almacen_origen'] or h['almacen_destino'] or "N/A"
            
            tabla.setItem(i, 3, QTableWidgetItem(almacen_texto))
            tabla.setItem(i, 4, QTableWidgetItem(h['motivo'] or ""))
            tabla.setItem(i, 5, QTableWidgetItem(h['usuario']))
            
        layout.addWidget(tabla)
        dialog.exec()

    # ================= MODAL FICHA TÉCNICA (CREAR/EDITAR) =================
    def abrir_modal_ficha(self, modo="nuevo"):
        if modo == "editar" and not self.producto_seleccionado:
            return self.mostrar_mensaje("Aviso", "Selecciona un producto.", "error")

        self.listas_precios = db_settings.obtener_listas_precios()
        departamentos = db_settings.obtener_departamentos()
        proveedores = db_suppliers.obtener_proveedores()
        almacenes = db_settings.obtener_almacenes()
        
        if not proveedores or not almacenes or not departamentos:
            return self.mostrar_mensaje("¡Atención!", "Debes registrar al menos 1 Proveedor, 1 Departamento y 1 Almacén en Ajustes/Proveedores.", "error")

        dialog = QDialog(self)
        dialog.setWindowTitle("Ficha Técnica del Producto" if modo == "editar" else "Nuevo Producto")
        dialog.setFixedWidth(550)
        
        dialog.setStyleSheet("""
            QDialog { background-color: #FFFFFF; }
            QLabel { color: #0F172A; font-weight: 600; font-size: 13px; }
            QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox { padding: 8px; border: 1px solid #CBD5E1; border-radius: 4px; color: #000000; background-color: #F8FAFC; font-size: 14px; font-weight: bold; }
            QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus, QSpinBox:focus { border: 2px solid #3B82F6; background-color: #FFFFFF; }
            QTabWidget::pane { border: 1px solid #CBD5E1; background: #FFFFFF; border-radius: 4px; }
            QTabBar::tab { background: #F1F5F9; color: #64748B; padding: 10px 20px; font-weight: bold; margin-right: 2px; }
            QTabBar::tab:selected { background: #FFFFFF; color: #2563EB; border-bottom: 3px solid #2563EB; }
        """)
        
        layout_principal = QVBoxLayout(dialog)
        tabs = QTabWidget()
        tab_general = QWidget()
        tab_precios = QWidget()
        tab_stock = QWidget()
        
        tabs.addTab(tab_general, "📋 Datos Generales")
        tabs.addTab(tab_precios, "💰 Costos y Precios")
        tabs.addTab(tab_stock, "📦 Cantidades (Stock)")
        layout_principal.addWidget(tabs)

        form_general = QFormLayout(tab_general)
        campo_codigo = QLineEdit()
        campo_nombre = QLineEdit()
        combo_categoria = QComboBox() 
        combo_proveedor = QComboBox() 
        campo_stock_min = QSpinBox()
        campo_stock_min.setMaximum(9999)

        for d in departamentos: combo_categoria.addItem(d['nombre'], d['id'])
        for prov in proveedores: combo_proveedor.addItem(prov['nombre'], prov['id'])
            
        form_general.addRow("Código / SKU:", campo_codigo)
        form_general.addRow("Descripción:", campo_nombre)
        form_general.addRow("Departamento:", combo_categoria)
        form_general.addRow("Proveedor Principal:", combo_proveedor)
        form_general.addRow("Alerta Stock Mínimo:", campo_stock_min)

        form_precios = QFormLayout(tab_precios)
        monedas = db_settings.obtener_monedas()
        moneda_base = next((m for m in monedas if m['es_principal']), {'simbolo': '$', 'tasa_cambio': 1.0})
        moneda_sec = next((m for m in monedas if not m['es_principal']), {'simbolo': 'Bs', 'tasa_cambio': 40.0})
        tasa_actual = float(moneda_sec['tasa_cambio'])

        def crear_cajas_duales(valor_inicial, es_venta=True):
            fila = QHBoxLayout()
            caja_base = QDoubleSpinBox()
            caja_sec = QDoubleSpinBox()
            color_texto = "#16A34A" if es_venta else "#DC2626"
            caja_base.setMaximum(999999.99)
            caja_base.setPrefix(f"{moneda_base['simbolo']} ")
            caja_base.setStyleSheet(f"color: {color_texto}; background-color: #FFFFFF;")
            caja_sec.setMaximum(99999999.99)
            caja_sec.setPrefix(f"{moneda_sec['simbolo']} ")
            caja_sec.setStyleSheet(f"color: {color_texto}; background-color: #F8FAFC;")
            
            valor_seguro = float(valor_inicial or 0)
            caja_base.setValue(valor_seguro)
            caja_sec.setValue(valor_seguro * tasa_actual)
            
            def on_base_change(val):
                caja_sec.blockSignals(True)
                caja_sec.setValue(val * tasa_actual)
                caja_sec.blockSignals(False)
            def on_sec_change(val):
                caja_base.blockSignals(True)
                caja_base.setValue(val / tasa_actual)
                caja_base.blockSignals(False)
                
            caja_base.valueChanged.connect(on_base_change)
            caja_sec.valueChanged.connect(on_sec_change)
            fila.addWidget(caja_base)
            fila.addWidget(caja_sec)
            return fila, caja_base
        
        valor_costo_ini = float(self.producto_seleccionado.get("costo") or 0) if modo == "editar" else 0
        layout_costo, self.caja_costo_base = crear_cajas_duales(valor_costo_ini, False)
        form_precios.addRow("Costo de Compra:", layout_costo)
        
        self.campos_precios_dict = {} 
        precios_actuales = db_inventory.obtener_precios_producto(self.producto_seleccionado['id']) if modo == "editar" else {}
            
        for lista in self.listas_precios:
            valor_ini = float(precios_actuales.get(lista['id']) or 0)
            layout_precio, caja_base = crear_cajas_duales(valor_ini, True)
            self.campos_precios_dict[lista['id']] = caja_base
            form_precios.addRow(f"Precio {lista['nombre']}:", layout_precio)

        form_stock = QFormLayout(tab_stock)
        self.campos_stock_dict = {}
        stock_actual = db_inventory.obtener_stock_por_almacen(self.producto_seleccionado['id']) if modo == "editar" else {}
            
        for alm in almacenes:
            spin_stock = QSpinBox()
            spin_stock.setMaximum(99999)
            spin_stock.setValue(int(stock_actual.get(alm['id'], 0)))
            self.campos_stock_dict[alm['id']] = spin_stock
            form_stock.addRow(f"📦 {alm['nombre']}:", spin_stock)

        if modo == "editar":
            campo_codigo.setText(str(self.producto_seleccionado.get("codigo", "")))
            campo_nombre.setText(str(self.producto_seleccionado.get("nombre", "")))
            campo_stock_min.setValue(int(self.producto_seleccionado.get("stock_minimo", 5)))
            idx_dep = combo_categoria.findData(self.producto_seleccionado.get("departamento_id"))
            if idx_dep >= 0: combo_categoria.setCurrentIndex(idx_dep)
            idx_prov = combo_proveedor.findData(self.producto_seleccionado.get("proveedor_id"))
            if idx_prov >= 0: combo_proveedor.setCurrentIndex(idx_prov)
            
            # 🔥 AQUÍ QUITAMOS EL BLOQUEO DEL STOCK PARA QUE PUEDAS EDITARLO MANUALMENTE 🔥

        box_botones = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet("padding: 10px 15px; background-color: #F1F5F9; color: #475569; border-radius: 4px; font-weight: bold;")
        btn_guardar = QPushButton("💾 Guardar Cambios")
        btn_guardar.setStyleSheet("padding: 10px 15px; background-color: #2563EB; color: white; border-radius: 4px; font-weight: bold;")
        btn_cancelar.clicked.connect(dialog.reject)
        
        def guardar():
            codigo = campo_codigo.text().strip()
            nombre = campo_nombre.text().strip()
            departamento_id = combo_categoria.currentData()
            proveedor_id = combo_proveedor.currentData()
            costo = self.caja_costo_base.value() 
            stock_min = campo_stock_min.value()
            
            if not codigo or not nombre: return self.mostrar_mensaje("Error", "Código y Descripción son obligatorios.", "error")
            if not departamento_id or not proveedor_id: return self.mostrar_mensaje("Error", "Selecciona Departamento y Proveedor.", "error")
            
            precios_a_guardar = {l_id: spin.value() for l_id, spin in self.campos_precios_dict.items()}
            stock_a_guardar = {a_id: spin.value() for a_id, spin in self.campos_stock_dict.items()}
            
            if modo == "nuevo": exito, msg = db_inventory.guardar_producto(codigo, nombre, departamento_id, proveedor_id, costo, precios_a_guardar, stock_a_guardar, stock_min)
            else: exito, msg = db_inventory.editar_producto(self.producto_seleccionado["id"], codigo, nombre, departamento_id, proveedor_id, costo, precios_a_guardar, stock_a_guardar, stock_min)
                
            if exito:
                self.mostrar_mensaje("Éxito", msg)
                self.cargar_datos() 
                dialog.accept()
            else: self.mostrar_mensaje("Error", msg, "error")
                
        btn_guardar.clicked.connect(guardar)
        box_botones.addWidget(btn_cancelar)
        box_botones.addWidget(btn_guardar)
        layout_principal.addLayout(box_botones)
        dialog.exec()

    def eliminar(self):
        if not self.producto_seleccionado: return self.mostrar_mensaje("Aviso", "Selecciona un producto.", "error")
        if QMessageBox.question(self, "Confirmar", f"¿Eliminar {self.producto_seleccionado['nombre']}?") == QMessageBox.StandardButton.Yes:
            exito, msg = db_inventory.eliminar_producto(self.producto_seleccionado["id"])
            if exito:
                self.mostrar_mensaje("Éxito", msg)
                self.cargar_datos()
            else: self.mostrar_mensaje("Error", msg, "error")