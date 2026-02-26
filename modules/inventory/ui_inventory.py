import qtawesome as qta
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QDialog, QFormLayout, QMessageBox, QFrame, 
                             QAbstractItemView, QComboBox, QTabWidget, QSpinBox, QDoubleSpinBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
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
        layout_principal.setSpacing(25)
        
        # ==========================================
        # CABECERA DEL MÓDULO
        # ==========================================
        header_layout = QVBoxLayout()
        header_layout.setSpacing(5)
        
        lbl_titulo = QLabel("INVENTARIO Y STOCK")
        lbl_titulo.setStyleSheet("font-size: 24px; font-weight: 900; color: #0F172A; letter-spacing: 1px;")
        
        lbl_subtitulo = QLabel("Gestión centralizada de catálogo, movimientos y auditoría de Kardex.")
        lbl_subtitulo.setStyleSheet("font-size: 14px; color: #64748B;")
        
        header_layout.addWidget(lbl_titulo)
        header_layout.addWidget(lbl_subtitulo)
        layout_principal.addLayout(header_layout)
        
        # ==========================================
        # TARJETA PRINCIPAL (CONTENEDOR DE TABLA)
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
        self.campo_busqueda.setPlaceholderText("Buscar por código o descripción...")
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
        
        btn_nuevo = QPushButton("Nuevo Producto")
        btn_nuevo.setStyleSheet(estilo_btn_primario)
        btn_nuevo.clicked.connect(lambda: self.abrir_modal_ficha("nuevo"))
        
        btn_editar = QPushButton("Editar Ficha")
        btn_editar.setStyleSheet(estilo_btn_secundario)
        btn_editar.clicked.connect(lambda: self.abrir_modal_ficha("editar"))
        
        btn_traspaso = QPushButton("Traspaso")
        btn_traspaso.setStyleSheet(estilo_btn_secundario)
        btn_traspaso.clicked.connect(self.abrir_modal_traspaso)
        
        btn_ajuste = QPushButton("Ajuste Manual")
        btn_ajuste.setStyleSheet(estilo_btn_secundario)
        btn_ajuste.clicked.connect(self.abrir_modal_ajuste)
        
        btn_kardex = QPushButton("Ver Kardex")
        btn_kardex.setStyleSheet(estilo_btn_secundario)
        btn_kardex.clicked.connect(self.abrir_modal_kardex)
        
        btn_eliminar = QPushButton("Eliminar")
        btn_eliminar.setStyleSheet(estilo_btn_peligro)
        btn_eliminar.clicked.connect(self.eliminar)
        
        for btn in [btn_nuevo, btn_editar, btn_traspaso, btn_ajuste, btn_kardex, btn_eliminar]:
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            barra_herramientas.addWidget(btn)
        
        layout_tarjeta.addLayout(barra_herramientas)
        
        # --- TABLA DE DATOS ---
        self.tabla = QTableWidget()
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
            
            item_id = QTableWidgetItem(f"{p['id']:05d}")
            item_id.setForeground(QColor("#94A3B8"))
            item_id.setData(Qt.ItemDataRole.UserRole, p) 
            self.tabla.setItem(fila_idx, 0, item_id)
            
            self.tabla.setItem(fila_idx, 1, QTableWidgetItem(p['codigo']))
            
            item_desc = QTableWidgetItem(p['nombre'])
            item_desc.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.tabla.setItem(fila_idx, 2, item_desc)
            
            self.tabla.setItem(fila_idx, 3, QTableWidgetItem(p['categoria'] or "General"))
            self.tabla.setItem(fila_idx, 4, QTableWidgetItem(p['proveedor_nombre']))
            
            stock_total = float(p['stock_total'])
            stock_min = float(p['stock_minimo'])
            
            if stock_total <= stock_min:
                item_stock = QTableWidgetItem(f"{stock_total} (Alerta)")
                item_stock.setForeground(QColor("#DC2626"))
                item_stock.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            else:
                item_stock = QTableWidgetItem(str(stock_total))
                item_stock.setForeground(QColor("#10B981")) 
                item_stock.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                
            self.tabla.setItem(fila_idx, 5, item_stock)
            fila_idx += 1

    # ================= MODALES DE MOVIMIENTO =================
    def aplicar_estilo_modal(self, dialog):
        dialog.setStyleSheet("""
            QDialog { background-color: #FFFFFF; } 
            QLabel { color: #334155; font-weight: bold; font-size: 13px; } 
            QComboBox, QSpinBox, QLineEdit { 
                padding: 10px; border: 1px solid #CBD5E1; border-radius: 4px; 
                background-color: #F8FAFC; color: #0F172A; font-size: 14px; 
            }
            QComboBox:focus, QSpinBox:focus, QLineEdit:focus { border: 2px solid #38BDF8; background-color: #FFFFFF;}
            QPushButton.accion { padding: 12px; background-color: #0F172A; color: white; font-weight: bold; border-radius: 4px; }
            QPushButton.accion:hover { background-color: #1E293B; }
        """)

    def abrir_modal_traspaso(self):
        if not self.producto_seleccionado: return self.mostrar_mensaje("Aviso", "Seleccione un producto en la tabla.")
        
        almacenes = db_settings.obtener_almacenes()
        if len(almacenes) < 2: return self.mostrar_mensaje("Aviso", "Se requieren al menos 2 almacenes para realizar traspasos.", "error")

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Traspaso de Mercancía: {self.producto_seleccionado['nombre']}")
        dialog.setFixedWidth(400)
        self.aplicar_estilo_modal(dialog)
        
        layout = QFormLayout(dialog)
        layout.setVerticalSpacing(15)
        
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
        
        layout.addRow("Almacén de Origen:", combo_origen)
        layout.addRow("Almacén de Destino:", combo_destino)
        layout.addRow("Cantidad a Mover:", spin_cant)
        layout.addRow("Motivo del Traspaso:", txt_motivo)
        
        btn_guardar = QPushButton("Confirmar Traspaso")
        btn_guardar.setProperty("class", "accion")
        
        def procesar():
            if combo_origen.currentData() == combo_destino.currentData():
                self.mostrar_mensaje("Error", "El origen y destino no pueden ser el mismo almacén.", "error")
                return
            
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
        if not self.producto_seleccionado: return self.mostrar_mensaje("Aviso", "Seleccione un producto en la tabla.")

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Ajuste de Inventario: {self.producto_seleccionado['nombre']}")
        dialog.setFixedWidth(400)
        self.aplicar_estilo_modal(dialog)
        
        layout = QFormLayout(dialog)
        layout.setVerticalSpacing(15)
        
        combo_almacen = QComboBox()
        for a in db_settings.obtener_almacenes(): combo_almacen.addItem(a['nombre'], a['id'])
            
        combo_tipo = QComboBox()
        combo_tipo.addItem("Entrada (Sumar Stock)", "AJUSTE_POSITIVO")
        combo_tipo.addItem("Salida / Merma (Restar Stock)", "AJUSTE_NEGATIVO")
            
        spin_cant = QSpinBox()
        spin_cant.setMinimum(1)
        spin_cant.setMaximum(99999)
        
        txt_motivo = QLineEdit()
        txt_motivo.setPlaceholderText("Ej: Diferencia en conteo físico")
        
        layout.addRow("Almacén Afectado:", combo_almacen)
        layout.addRow("Tipo de Operación:", combo_tipo)
        layout.addRow("Cantidad a Ajustar:", spin_cant)
        layout.addRow("Motivo (Obligatorio):", txt_motivo)
        
        btn_guardar = QPushButton("Registrar Ajuste")
        btn_guardar.setProperty("class", "accion")
        
        def procesar():
            if not txt_motivo.text().strip(): 
                self.mostrar_mensaje("Error", "El motivo es obligatorio para la auditoría.", "error")
                return
                
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
        if not self.producto_seleccionado: return self.mostrar_mensaje("Aviso", "Seleccione un producto.")
        
        historial = db_inventory.obtener_historial_kardex(self.producto_seleccionado['id'])
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Auditoría de Kardex: {self.producto_seleccionado['nombre']}")
        dialog.setFixedWidth(800)
        dialog.setStyleSheet("QDialog { background-color: #FFFFFF; }")
        
        layout = QVBoxLayout(dialog)
        
        lbl_info = QLabel("Registro detallado de entradas y salidas")
        lbl_info.setStyleSheet("color: #64748B; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(lbl_info)
        
        tabla = QTableWidget()
        tabla.setColumnCount(6)
        tabla.setHorizontalHeaderLabels(["FECHA", "OPERACIÓN", "CANT.", "ALMACÉN", "REFERENCIA", "USUARIO"])
        tabla.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        tabla.verticalHeader().setVisible(False)
        tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tabla.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        tabla.setStyleSheet("""
            QTableWidget { background-color: #FFFFFF; border: 1px solid #E2E8F0; font-size: 13px; color: #334155;}
            QHeaderView::section { background-color: #F8FAFC; color: #64748B; font-weight: bold; padding: 10px; border: none; border-bottom: 2px solid #E2E8F0; }
        """)
        
        tabla.setRowCount(len(historial))
        for i, h in enumerate(historial):
            tabla.setItem(i, 0, QTableWidgetItem(h['fecha']))
            
            item_tipo = QTableWidgetItem(h['tipo_movimiento'].replace("_", " "))
            if "POSITIVO" in h['tipo_movimiento'] or "ENTRADA" in h['tipo_movimiento']: item_tipo.setForeground(QColor("#10B981"))
            elif "NEGATIVO" in h['tipo_movimiento'] or "SALIDA" in h['tipo_movimiento']: item_tipo.setForeground(QColor("#DC2626"))
            else: item_tipo.setForeground(QColor("#F59E0B"))
            
            tabla.setItem(i, 1, item_tipo)
            
            item_cant = QTableWidgetItem(str(h['cantidad']))
            item_cant.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            tabla.setItem(i, 2, item_cant)
            
            if h['tipo_movimiento'] == 'TRASPASO': 
                almacen_texto = f"{h['almacen_origen']} -> {h['almacen_destino']}"
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
            return self.mostrar_mensaje("Aviso", "Seleccione un producto en la tabla.")

        self.listas_precios = db_settings.obtener_listas_precios()
        departamentos = db_settings.obtener_departamentos()
        proveedores = db_suppliers.obtener_proveedores()
        almacenes = db_settings.obtener_almacenes()
        
        if not proveedores or not almacenes or not departamentos:
            return self.mostrar_mensaje("Requisito", "Debe registrar al menos 1 Proveedor, 1 Departamento y 1 Almacén en la configuración antes de crear productos.", "error")

        dialog = QDialog(self)
        dialog.setWindowTitle("Ficha del Producto" if modo == "editar" else "Nuevo Producto")
        dialog.setFixedWidth(600)
        
        dialog.setStyleSheet("""
            QDialog { background-color: #F8FAFC; }
            QLabel { color: #334155; font-weight: bold; font-size: 13px; }
            QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox { padding: 10px; border: 1px solid #CBD5E1; border-radius: 6px; background-color: #FFFFFF; font-size: 14px; color: #0F172A; }
            QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus, QSpinBox:focus { border: 2px solid #38BDF8; }
            QTabWidget::pane { border: 1px solid #CBD5E1; background: #FFFFFF; border-radius: 6px; }
            QTabBar::tab { background: #E2E8F0; color: #64748B; padding: 12px 25px; font-weight: bold; border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 2px;}
            QTabBar::tab:selected { background: #FFFFFF; color: #0F172A; border-bottom: 3px solid #38BDF8; }
        """)
        
        layout_principal = QVBoxLayout(dialog)
        layout_principal.setContentsMargins(20, 20, 20, 20)
        
        tabs = QTabWidget()
        tab_general = QWidget()
        tab_precios = QWidget()
        tab_stock = QWidget()
        
        tabs.addTab(tab_general, "General")
        tabs.addTab(tab_precios, "Finanzas")
        tabs.addTab(tab_stock, "Existencias")
        layout_principal.addWidget(tabs)

        # ==========================================
        # TAB GENERAL CON BOTÓN DE CÓDIGO DE BARRAS
        # ==========================================
        form_general = QFormLayout(tab_general)
        form_general.setVerticalSpacing(15)
        form_general.setContentsMargins(20, 20, 20, 20)
        
        campo_codigo = QLineEdit()
        campo_codigo.setPlaceholderText("Ej: 75912345 (Deje en blanco para auto-generar)")
        
        # 🔥 BOTÓN DE IMPRESIÓN DE ETIQUETA 🔥
        btn_imprimir_codigo = QPushButton(" Ver Etiqueta")
        btn_imprimir_codigo.setIcon(qta.icon('fa5s.barcode', color='#0F172A'))
        btn_imprimir_codigo.setStyleSheet("""
            QPushButton { padding: 10px 15px; background-color: #F1F5F9; border: 1px solid #CBD5E1; border-radius: 6px; font-weight: bold; color: #0F172A;}
            QPushButton:hover { background-color: #E2E8F0; }
        """)
        btn_imprimir_codigo.setCursor(Qt.CursorShape.PointingHandCursor)
        
        campo_nombre = QLineEdit()
        
        def imprimir_codigo():
            cod = campo_codigo.text().strip()
            nom = campo_nombre.text().strip() or "Producto"
            
            if not cod:
                self.mostrar_mensaje("Aviso", "Primero escriba un código o Guarde el producto para que el sistema le genere uno automáticamente antes de imprimir.", "error")
                return
                
            try:
                import os
                from utils.barcode_gen import generar_e_imprimir_codigo
                ruta = generar_e_imprimir_codigo(cod, nom)
                os.startfile(os.path.abspath(ruta))
            except Exception as e:
                self.mostrar_mensaje("Error", f"No se pudo generar o abrir la etiqueta:\n{str(e)}", "error")

        btn_imprimir_codigo.clicked.connect(imprimir_codigo)

        fila_codigo = QHBoxLayout()
        fila_codigo.addWidget(campo_codigo, stretch=1)
        fila_codigo.addWidget(btn_imprimir_codigo)
        
        combo_categoria = QComboBox() 
        combo_proveedor = QComboBox() 
        campo_stock_min = QSpinBox()
        campo_stock_min.setMaximum(9999)

        for d in departamentos: combo_categoria.addItem(d['nombre'], d['id'])
        for prov in proveedores: combo_proveedor.addItem(prov['nombre'], prov['id'])
            
        form_general.addRow("Código / Barras:", fila_codigo)
        form_general.addRow("Descripción Comercial:", campo_nombre)
        form_general.addRow("Departamento:", combo_categoria)
        form_general.addRow("Proveedor de Origen:", combo_proveedor)
        form_general.addRow("Alerta Stock Mínimo:", campo_stock_min)

        # TAB PRECIOS
        form_precios = QFormLayout(tab_precios)
        form_precios.setVerticalSpacing(15)
        form_precios.setContentsMargins(20, 20, 20, 20)
        
        monedas = db_settings.obtener_monedas()
        moneda_base = next((m for m in monedas if m['es_principal']), {'simbolo': '$', 'tasa_cambio': 1.0})
        moneda_sec = next((m for m in monedas if not m['es_principal']), {'simbolo': 'Bs', 'tasa_cambio': 40.0})
        tasa_actual = float(moneda_sec['tasa_cambio'])

        def crear_cajas_duales(valor_inicial, es_venta=True):
            fila = QHBoxLayout()
            caja_base = QDoubleSpinBox()
            caja_sec = QDoubleSpinBox()
            
            caja_base.setMaximum(999999.99)
            caja_base.setPrefix(f"{moneda_base['simbolo']} ")
            caja_sec.setMaximum(99999999.99)
            caja_sec.setPrefix(f"{moneda_sec['simbolo']} ")
            caja_sec.setStyleSheet("background-color: #F1F5F9; color: #64748B;")
            
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
        form_precios.addRow("Costo de Adquisición:", layout_costo)
        
        self.campos_precios_dict = {} 
        precios_actuales = db_inventory.obtener_precios_producto(self.producto_seleccionado['id']) if modo == "editar" else {}
            
        for lista in self.listas_precios:
            valor_ini = float(precios_actuales.get(lista['id']) or 0)
            layout_precio, caja_base = crear_cajas_duales(valor_ini, True)
            self.campos_precios_dict[lista['id']] = caja_base
            form_precios.addRow(f"Precio: {lista['nombre']}", layout_precio)

        # TAB STOCK
        form_stock = QFormLayout(tab_stock)
        form_stock.setVerticalSpacing(15)
        form_stock.setContentsMargins(20, 20, 20, 20)
        
        lbl_info_stock = QLabel("Nota: Modificar el stock aquí creará un registro de 'Ajuste Manual' en el Kardex." if modo == "editar" else "Ingrese el inventario físico inicial para cada almacén.")
        lbl_info_stock.setStyleSheet("color: #64748B; font-weight: normal; font-style: italic;")
        form_stock.addRow(lbl_info_stock)
        
        self.campos_stock_dict = {}
        stock_actual = db_inventory.obtener_stock_por_almacen(self.producto_seleccionado['id']) if modo == "editar" else {}
            
        for alm in almacenes:
            spin_stock = QSpinBox()
            spin_stock.setMaximum(99999)
            spin_stock.setValue(int(stock_actual.get(alm['id'], 0)))
            self.campos_stock_dict[alm['id']] = spin_stock
            form_stock.addRow(f"Almacén: {alm['nombre']}", spin_stock)

        if modo == "editar":
            campo_codigo.setText(str(self.producto_seleccionado.get("codigo", "")))
            campo_nombre.setText(str(self.producto_seleccionado.get("nombre", "")))
            campo_stock_min.setValue(int(self.producto_seleccionado.get("stock_minimo", 5)))
            idx_dep = combo_categoria.findData(self.producto_seleccionado.get("departamento_id"))
            if idx_dep >= 0: combo_categoria.setCurrentIndex(idx_dep)
            idx_prov = combo_proveedor.findData(self.producto_seleccionado.get("proveedor_id"))
            if idx_prov >= 0: combo_proveedor.setCurrentIndex(idx_prov)

        box_botones = QHBoxLayout()
        btn_cancelar = QPushButton("Descartar")
        btn_cancelar.setStyleSheet("padding: 12px 20px; background-color: #FFFFFF; color: #334155; border: 1px solid #CBD5E1; border-radius: 6px; font-weight: bold;")
        btn_guardar = QPushButton("Guardar Ficha Técnica")
        btn_guardar.setStyleSheet("padding: 12px 20px; background-color: #0F172A; color: white; border-radius: 6px; font-weight: bold;")
        btn_cancelar.clicked.connect(dialog.reject)
        
        def guardar():
            codigo = campo_codigo.text().strip()
            nombre = campo_nombre.text().strip()
            departamento_id = combo_categoria.currentData()
            proveedor_id = combo_proveedor.currentData()
            costo = self.caja_costo_base.value() 
            stock_min = campo_stock_min.value()
            
            if not nombre: return self.mostrar_mensaje("Error", "La Descripción Comercial es obligatoria.", "error")
            
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
        if not self.producto_seleccionado: return self.mostrar_mensaje("Aviso", "Seleccione un producto en la tabla.")
        
        msg_confirm = QMessageBox(self)
        msg_confirm.setWindowTitle("Confirmar Baja")
        msg_confirm.setText(f"¿Está seguro de eliminar el registro de:\n{self.producto_seleccionado['nombre']}?")
        msg_confirm.setIcon(QMessageBox.Icon.Question)
        msg_confirm.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_confirm.setStyleSheet("""
            QMessageBox { background-color: #FFFFFF; }
            QLabel { color: #0F172A; font-size: 13px; font-weight: bold; } 
            QPushButton { padding: 6px 20px; background-color: #DC2626; color: white; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #B91C1C; }
        """)
        
        if msg_confirm.exec() == QMessageBox.StandardButton.Yes:
            exito, msg = db_inventory.eliminar_producto(self.producto_seleccionado["id"])
            if exito:
                self.mostrar_mensaje("Éxito", msg)
                self.cargar_datos()
            else: self.mostrar_mensaje("Error", msg, "error")