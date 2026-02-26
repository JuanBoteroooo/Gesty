import qtawesome as qta
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QAbstractItemView, QDialog, 
                             QFormLayout, QDoubleSpinBox, QComboBox, QMessageBox, QFrame, QTabWidget, QSpinBox, QInputDialog, QAbstractSpinBox)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QFont
from modules.customers import db_cxc
from modules.sales import db_sales
from utils import session

class VistaCXC(QWidget):
    def __init__(self):
        super().__init__()
        self.factura_seleccionada = None
        self.cuenta_abierta_seleccionada = None
        self.setup_ui()
        self.cargar_datos_refresh()

    def setup_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(30, 30, 30, 30)
        layout_principal.setSpacing(20)
        
        header_layout = QVBoxLayout()
        lbl_titulo = QLabel("CRÉDITOS Y CUENTAS CORRIENTES")
        lbl_titulo.setStyleSheet("font-size: 24px; font-weight: 900; color: #0F172A; letter-spacing: 1px;")
        lbl_subtitulo = QLabel("Administración de Facturas a Crédito y Gestión de Cuentas Abiertas (Cuaderno).")
        lbl_subtitulo.setStyleSheet("font-size: 14px; color: #64748B;")
        header_layout.addWidget(lbl_titulo)
        header_layout.addWidget(lbl_subtitulo)
        layout_principal.addLayout(header_layout)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #E2E8F0; background: #FFFFFF; border-radius: 8px; top: -1px; }
            QTabBar::tab { background: #F1F5F9; color: #64748B; padding: 12px 25px; border-top-left-radius: 8px; border-top-right-radius: 8px; font-weight: bold; font-size: 13px; margin-right: 4px; }
            QTabBar::tab:selected { background: #FFFFFF; color: #0F172A; border-top: 3px solid #38BDF8; border-bottom: 1px solid #FFFFFF; }
        """)
        
        self.tab_facturas = QWidget()
        self.tab_infinita = QWidget()
        
        self.setup_tab_facturas_ui()
        self.setup_tab_infinita_ui()
        
        self.tabs.addTab(self.tab_facturas, qta.icon('fa5s.file-invoice-dollar', color='#64748B'), "Facturas a Crédito")
        self.tabs.addTab(self.tab_infinita, qta.icon('fa5s.book-open', color='#64748B'), "Cuentas Abiertas (El Cuaderno)")
        
        layout_principal.addWidget(self.tabs)

    def get_tabla_style(self):
        return """
            QTableWidget { background-color: #FFFFFF; color: #334155; border: 1px solid #E2E8F0; border-radius: 6px; font-size: 13px; }
            QTableWidget::item { padding: 5px 10px; border-bottom: 1px solid #F1F5F9; }
            QTableWidget::item:selected { background-color: #EFF6FF; color: #0F172A; font-weight: bold; }
            QHeaderView::section { background-color: #F8FAFC; color: #64748B; font-weight: bold; font-size: 11px; padding: 10px; border: none; border-bottom: 2px solid #E2E8F0; text-transform: uppercase; }
        """

    def mostrar_mensaje(self, titulo, texto, tipo="info"):
        msg = QMessageBox(self)
        msg.setWindowTitle(titulo)
        msg.setText(texto)
        msg.setStyleSheet("QMessageBox { background-color: #FFFFFF; } QLabel { color: #0F172A; font-weight: bold; } QPushButton { padding: 6px 20px; background-color: #0F172A; color: white; border-radius: 4px; }")
        if tipo == "error": msg.setIcon(QMessageBox.Icon.Warning)
        else: msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()

    def mostrar_confirmacion(self, titulo, texto):
        msg = QMessageBox(self)
        msg.setWindowTitle(titulo)
        msg.setText(texto)
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setStyleSheet("QMessageBox { background-color: #FFFFFF; } QLabel { color: #0F172A; font-weight: bold; } QPushButton { padding: 6px 20px; background-color: #DC2626; color: white; border-radius: 4px; font-weight: bold; }")
        return msg.exec() == QMessageBox.StandardButton.Yes

    def verificar_caja(self):
        sesion = db_sales.verificar_caja_abierta()
        if not sesion:
            self.mostrar_mensaje("Caja Cerrada", "Debe abrir un turno de caja en el POS para operar.", "error")
            return None
        return sesion

    def cargar_datos_refresh(self):
        self.cargar_tab_facturas()
        self.cargar_tab_infinitas()

    # ================= PESTAÑA 1: FACTURAS CLÁSICAS =================
    def setup_tab_facturas_ui(self):
        layout = QVBoxLayout(self.tab_facturas)
        layout.setContentsMargins(20, 20, 20, 20)

        barra_accion = QHBoxLayout()
        barra_accion.addStretch()
        btn_abonar_factura = QPushButton("Cobrar / Abonar Factura")
        btn_abonar_factura.setFixedHeight(40)
        btn_abonar_factura.setStyleSheet("QPushButton { background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; padding: 0 20px; }")
        btn_abonar_factura.clicked.connect(self.modal_abono_factura)
        barra_accion.addWidget(btn_abonar_factura)
        layout.addLayout(barra_accion)

        self.tabla_facturas = QTableWidget()
        self.tabla_facturas.setColumnCount(6)
        self.tabla_facturas.setHorizontalHeaderLabels(["N° VENTA", "CLIENTE", "FECHA EMISIÓN", "VENCIMIENTO", "MONTO ORIGINAL", "SALDO PENDIENTE"])
        
        # 🔥 AJUSTE PERFECTO DE COLUMNAS PARA QUE NO SE CORTEN 🔥
        header = self.tabla_facturas.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        
        self.tabla_facturas.verticalHeader().setVisible(False)
        self.tabla_facturas.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_facturas.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla_facturas.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_facturas.verticalHeader().setDefaultSectionSize(45)
        self.tabla_facturas.setStyleSheet(self.get_tabla_style())
        
        def seleccionar_factura():
            filas = self.tabla_facturas.selectedItems()
            self.factura_seleccionada = self.tabla_facturas.item(filas[0].row(), 0).data(Qt.ItemDataRole.UserRole) if filas else None
            
        self.tabla_facturas.itemSelectionChanged.connect(seleccionar_factura)
        layout.addWidget(self.tabla_facturas)

    def cargar_tab_facturas(self):
        self.tabla_facturas.setRowCount(0)
        datos = db_cxc.obtener_facturas_pendientes()
        for i, f in enumerate(datos):
            self.tabla_facturas.insertRow(i)
            item_id = QTableWidgetItem(f"#{f['venta_id']:06d}")
            item_id.setData(Qt.ItemDataRole.UserRole, f)
            self.tabla_facturas.setItem(i, 0, item_id)
            self.tabla_facturas.setItem(i, 1, QTableWidgetItem(f['cliente_nombre']))
            self.tabla_facturas.setItem(i, 2, QTableWidgetItem(f['fecha_venta'].split(' ')[0]))
            self.tabla_facturas.setItem(i, 3, QTableWidgetItem(f['fecha_vencimiento'] or "N/A"))
            self.tabla_facturas.setItem(i, 4, QTableWidgetItem(f"$ {f['monto_total']:.2f}"))
            
            item_saldo = QTableWidgetItem(f"$ {f['saldo_pendiente']:.2f}")
            item_saldo.setForeground(QColor("#DC2626"))
            item_saldo.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.tabla_facturas.setItem(i, 5, item_saldo)

    def modal_abono_factura(self):
        if not self.factura_seleccionada: return self.mostrar_mensaje("Aviso", "Seleccione una factura de la lista.", "error")
        sesion = self.verificar_caja()
        if not sesion: return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Abono a Factura #{self.factura_seleccionada['venta_id']:06d}")
        dialog.setFixedWidth(400)
        dialog.setStyleSheet("QDialog { background-color: #FFFFFF; } QLabel { font-weight: bold; color: #334155; } QDoubleSpinBox, QComboBox { padding: 8px; border: 1px solid #CBD5E1; }")
        
        layout = QFormLayout(dialog)
        layout.addRow(QLabel(f"Deuda Actual: $ {self.factura_seleccionada['saldo_pendiente']:.2f}", styleSheet="color: #DC2626; font-weight: bold; font-size: 16px;"))

        combo_metodo = QComboBox()
        _, monedas, _, metodos, _ = db_sales.obtener_datos_configuracion()
        monedas_dict = {m['id']: m for m in monedas}
        for m in metodos: combo_metodo.addItem(m['nombre'], m)

        spin_monto = QDoubleSpinBox()
        spin_monto.setMaximum(99999999.99)
        spin_monto.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        
        lbl_equivalente = QLabel("Equivalente: $ 0.00")
        lbl_equivalente.setStyleSheet("color: #10B981; font-weight: bold;")

        def actualizar_conversion():
            metodo = combo_metodo.currentData()
            if not metodo: return
            moneda = monedas_dict[metodo['moneda_id']]
            spin_monto.setPrefix(f"{moneda['simbolo']} ")
            
            equiv_usd = spin_monto.value() / float(moneda['tasa_cambio'])
            lbl_equivalente.setText(f"Equivalente: $ {equiv_usd:.2f}")

        combo_metodo.currentIndexChanged.connect(actualizar_conversion)
        spin_monto.valueChanged.connect(actualizar_conversion)
        actualizar_conversion()

        layout.addRow("Método de Pago:", combo_metodo)
        layout.addRow("Monto a Entregar:", spin_monto)
        layout.addRow("", lbl_equivalente)

        btn_confirmar = QPushButton("Abonar")
        btn_confirmar.setStyleSheet("background-color: #10B981; color: white; padding: 10px; font-weight: bold; border-radius: 4px;")
        
        def confirmar():
            metodo = combo_metodo.currentData()
            moneda = monedas_dict[metodo['moneda_id']]
            monto_usd = spin_monto.value() / float(moneda['tasa_cambio'])

            if monto_usd <= 0: return
            if monto_usd > self.factura_seleccionada['saldo_pendiente'] + 0.01:
                return self.mostrar_mensaje("Error", "El monto ingresado supera la deuda de la factura.", "error")

            exito, msg = db_cxc.registrar_abono_factura_especifica(self.factura_seleccionada['id'], monto_usd, metodo['id'], sesion['id'])
            if exito:
                self.mostrar_mensaje("Éxito", msg)
                self.cargar_datos_refresh()
                dialog.accept()
            else: self.mostrar_mensaje("Error", msg, "error")
            
        btn_confirmar.clicked.connect(confirmar)
        layout.addRow(btn_confirmar)
        dialog.exec()

    # ================= PESTAÑA 2: CUENTAS INFINITAS =================
    def setup_tab_infinita_ui(self):
        layout = QVBoxLayout(self.tab_infinita)
        layout.setContentsMargins(20, 20, 20, 20)

        barra = QHBoxLayout()
        barra.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        btn_nueva = QPushButton("Aperturar Cuaderno a Cliente")
        btn_nueva.setFixedHeight(40)
        btn_nueva.setStyleSheet("QPushButton { background-color: #0F172A; color: white; font-weight: bold; border-radius: 6px; padding: 0 20px; }")
        btn_nueva.clicked.connect(self.modal_crear_cuenta_infinita)
        
        btn_gestionar = QPushButton("GESTIONAR CUENTA (Mini-POS)")
        btn_gestionar.setFixedHeight(40)
        btn_gestionar.setStyleSheet("QPushButton { background-color: #3B82F6; color: white; font-weight: bold; border-radius: 6px; padding: 0 20px; }")
        btn_gestionar.clicked.connect(self.abrir_modal_gestion_infinita)
        
        barra.addWidget(btn_nueva)
        barra.addWidget(btn_gestionar)
        layout.addLayout(barra)

        self.tabla_infinita = QTableWidget()
        self.tabla_infinita.setColumnCount(4)
        self.tabla_infinita.setHorizontalHeaderLabels(["ID CUENTA", "CLIENTE (DUEÑO)", "FECHA APERTURA", "SALDO TOTAL ADEUDADO"])
        
        # 🔥 AJUSTE PERFECTO DE COLUMNAS PARA QUE NO SE CORTEN 🔥
        h_inf = self.tabla_infinita.horizontalHeader()
        h_inf.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        h_inf.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        h_inf.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        h_inf.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        self.tabla_infinita.verticalHeader().setVisible(False)
        self.tabla_infinita.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_infinita.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla_infinita.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_infinita.verticalHeader().setDefaultSectionSize(45)
        self.tabla_infinita.setStyleSheet(self.get_tabla_style())
        
        def seleccionar_infinita():
            filas = self.tabla_infinita.selectedItems()
            self.cuenta_abierta_seleccionada = self.tabla_infinita.item(filas[0].row(), 0).data(Qt.ItemDataRole.UserRole) if filas else None
            
        self.tabla_infinita.itemSelectionChanged.connect(seleccionar_infinita)
        layout.addWidget(self.tabla_infinita)

    def cargar_tab_infinitas(self):
        self.tabla_infinita.setRowCount(0)
        for i, c in enumerate(db_cxc.obtener_cuentas_infinitas()):
            self.tabla_infinita.insertRow(i)
            item_id = QTableWidgetItem(f"CTA-{c['cxc_id']:04d}")
            item_id.setForeground(QColor("#94A3B8"))
            item_id.setData(Qt.ItemDataRole.UserRole, c)
            self.tabla_infinita.setItem(i, 0, item_id)
            self.tabla_infinita.setItem(i, 1, QTableWidgetItem(f"{c['cliente_nombre']} ({c['documento']})"))
            self.tabla_infinita.setItem(i, 2, QTableWidgetItem(c['fecha_hora']))
            
            saldo = float(c['saldo_pendiente'])
            if saldo > 0:
                item_saldo = QTableWidgetItem(f"DEUDA: $ {saldo:.2f}")
                item_saldo.setForeground(QColor("#DC2626"))
            elif saldo < 0:
                item_saldo = QTableWidgetItem(f"A FAVOR: $ {abs(saldo):.2f}")
                item_saldo.setForeground(QColor("#10B981"))
            else:
                item_saldo = QTableWidgetItem(f"SOLVENTE: $ 0.00")
                item_saldo.setForeground(QColor("#64748B"))
                
            item_saldo.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            self.tabla_infinita.setItem(i, 3, item_saldo)

    def modal_crear_cuenta_infinita(self):
        sesion = self.verificar_caja()
        if not sesion: return

        dialog = QDialog(self)
        dialog.setWindowTitle("Apertura de Cuaderno")
        dialog.setFixedWidth(350)
        dialog.setStyleSheet("QDialog { background-color: #FFFFFF; }")
        layout = QVBoxLayout(dialog)
        
        layout.addWidget(QLabel("Seleccione el cliente autorizado:", styleSheet="font-weight: bold;"))
        combo_clientes = QComboBox()
        combo_clientes.setStyleSheet("padding: 8px; border: 1px solid #CBD5E1;")
        
        import sqlite3
        from database.connection import connect
        conn = connect()
        cur = conn.cursor()
        cur.execute("SELECT id, nombre FROM clientes WHERE id != 1") 
        for c in cur.fetchall(): combo_clientes.addItem(c['nombre'], c['id'])
        conn.close()
        
        layout.addWidget(combo_clientes)

        btn_crear = QPushButton("Abrir Cuenta")
        btn_crear.setStyleSheet("padding: 10px; background-color: #0F172A; color: white; border-radius: 4px; font-weight: bold; margin-top: 10px;")
        
        def crear():
            c_id = combo_clientes.currentData()
            if not c_id: return
            _, monedas, _, _, _ = db_sales.obtener_datos_configuracion()
            moneda_base = next((m for m in monedas if m['es_principal']), None)
            
            exito, msg = db_cxc.crear_cuenta_infinita(c_id, moneda_base['id'], sesion['id'])
            if exito:
                self.mostrar_mensaje("Éxito", msg)
                self.cargar_datos_refresh()
                dialog.accept()
            else: self.mostrar_mensaje("Error", msg, "error")
            
        btn_crear.clicked.connect(crear)
        layout.addWidget(btn_crear)
        dialog.exec()

    # ================= 🔥 MINI-POS: GESTIÓN DE CUENTA INFINITA 🔥 =================
    def abrir_modal_gestion_infinita(self):
        if not self.cuenta_abierta_seleccionada: return self.mostrar_mensaje("Aviso", "Seleccione una cuenta de la tabla.", "error")
        cuenta = self.cuenta_abierta_seleccionada
        sesion = self.verificar_caja()
        if not sesion: return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Mini POS (Cuaderno) - {cuenta['cliente_nombre']}")
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)
        dialog.showMaximized()
        dialog.setStyleSheet("QDialog { background-color: #F8FAFC; }")
        
        layout_principal = QVBoxLayout(dialog)
        layout_principal.setSpacing(20)
        layout_principal.setContentsMargins(30, 30, 30, 30)
        
        header = QHBoxLayout()
        lbl_nombre = QLabel(f"ESTADO DE CUENTA: {cuenta['cliente_nombre'].upper()}")
        lbl_nombre.setStyleSheet("font-size: 26px; font-weight: 900; color: #0F172A;")
        
        self.lbl_saldo_dinamico = QLabel()
        
        def actualizar_etiqueta_saldo(saldo):
            if saldo > 0:
                self.lbl_saldo_dinamico.setText(f"SALDO DEUDOR: $ {saldo:.2f}")
                self.lbl_saldo_dinamico.setStyleSheet("font-size: 26px; font-weight: 900; color: #DC2626; background: #FEE2E2; padding: 10px 25px; border-radius: 8px;")
            elif saldo < 0:
                self.lbl_saldo_dinamico.setText(f"SALDO A FAVOR: $ {abs(saldo):.2f}")
                self.lbl_saldo_dinamico.setStyleSheet("font-size: 26px; font-weight: 900; color: #10B981; background: #D1FAE5; padding: 10px 25px; border-radius: 8px;")
            else:
                self.lbl_saldo_dinamico.setText(f"CUENTA SOLVENTE: $ 0.00")
                self.lbl_saldo_dinamico.setStyleSheet("font-size: 26px; font-weight: 900; color: #64748B; background: #F1F5F9; padding: 10px 25px; border-radius: 8px;")

        actualizar_etiqueta_saldo(float(cuenta['saldo_pendiente']))

        header.addWidget(lbl_nombre)
        header.addStretch()
        header.addWidget(self.lbl_saldo_dinamico)
        layout_principal.addLayout(header)

        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(20)
        
        # ---------------- PANEL IZQUIERDO: BUSCADOR ----------------
        panel_izq = QFrame()
        panel_izq.setStyleSheet("QFrame { background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 8px; }")
        layout_izq = QVBoxLayout(panel_izq)
        layout_izq.setContentsMargins(20, 20, 20, 20)
        
        lbl_buscar = QLabel("🛒 BUSCAR Y AÑADIR PRODUCTO A LA DEUDA")
        lbl_buscar.setStyleSheet("font-weight: 900; color: #0F172A; border: none; font-size: 14px;")
        layout_izq.addWidget(lbl_buscar)

        fila_filtros = QHBoxLayout()
        _, _, listas, _, almacenes = db_sales.obtener_datos_configuracion()

        combo_almacen_mini = QComboBox()
        combo_almacen_mini.setStyleSheet("padding: 10px; border: 1px solid #CBD5E1; border-radius: 4px; font-weight: bold; background-color: #F8FAFC;")
        for a in almacenes: combo_almacen_mini.addItem(a['nombre'], a['id'])

        combo_tarifa_mini = QComboBox()
        combo_tarifa_mini.setStyleSheet("padding: 10px; border: 1px solid #CBD5E1; border-radius: 4px; font-weight: bold; background-color: #F8FAFC;")
        for l in listas: combo_tarifa_mini.addItem(l['nombre'], l['id'])

        fila_filtros.addWidget(QLabel("Almacén:", styleSheet="font-weight: bold; color: #64748B; border: none;"))
        fila_filtros.addWidget(combo_almacen_mini, stretch=1)
        fila_filtros.addWidget(QLabel("Tarifa:", styleSheet="font-weight: bold; color: #64748B; border: none;"))
        fila_filtros.addWidget(combo_tarifa_mini, stretch=1)

        layout_izq.addLayout(fila_filtros)

        txt_buscar = QLineEdit()
        txt_buscar.setPlaceholderText("Escriba para buscar y presione Enter o Doble Clic...")
        txt_buscar.setFixedHeight(45)
        txt_buscar.setStyleSheet("QLineEdit { padding: 10px 15px; border: 2px solid #E2E8F0; border-radius: 6px; font-size: 15px; color: #000; } QLineEdit:focus { border: 2px solid #3B82F6; }")
        layout_izq.addWidget(txt_buscar)

        tabla_busq = QTableWidget()
        tabla_busq.setColumnCount(4)
        tabla_busq.setHorizontalHeaderLabels(["ID", "PRODUCTO", "PRECIO", "STOCK"])
        
        h_busq = tabla_busq.horizontalHeader()
        h_busq.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        h_busq.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        h_busq.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        h_busq.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        h_busq.setStretchLastSection(False)
        
        tabla_busq.verticalHeader().setVisible(False)
        tabla_busq.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tabla_busq.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tabla_busq.verticalHeader().setDefaultSectionSize(45)
        tabla_busq.setStyleSheet(self.get_tabla_style())
        layout_izq.addWidget(tabla_busq)

        def buscar_mini():
            term = txt_buscar.text().strip()
            if not term:
                tabla_busq.setRowCount(0)
                return
            
            almacen_id = combo_almacen_mini.currentData() or 1
            lista_id = combo_tarifa_mini.currentData() or 1
            
            resultados = db_sales.buscar_productos(term, lista_id, almacen_id)
            tabla_busq.setRowCount(0)
            for i, p in enumerate(resultados):
                tabla_busq.insertRow(i)
                item_id = QTableWidgetItem(f"{p['id']:05d}")
                item_id.setData(Qt.ItemDataRole.UserRole, p)
                item_id.setForeground(QColor("#94A3B8"))
                tabla_busq.setItem(i, 0, item_id)
                
                item_nom = QTableWidgetItem(p['nombre'])
                item_nom.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
                item_nom.setToolTip(p['nombre'])
                tabla_busq.setItem(i, 1, item_nom)
                
                item_prec = QTableWidgetItem(f"${p['precio']:.2f}")
                item_prec.setForeground(QColor("#10B981"))
                item_prec.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
                tabla_busq.setItem(i, 2, item_prec)
                
                item_stock = QTableWidgetItem(str(p['stock']))
                if p['stock'] <= 0: item_stock.setForeground(QColor("#DC2626"))
                tabla_busq.setItem(i, 3, item_stock)

        txt_buscar.textChanged.connect(buscar_mini)
        combo_almacen_mini.currentIndexChanged.connect(buscar_mini)
        combo_tarifa_mini.currentIndexChanged.connect(buscar_mini)

        def agregar_prod(item=None):
            if not item: return
            p = tabla_busq.item(item.row(), 0).data(Qt.ItemDataRole.UserRole)
            if p['stock'] <= 0:
                return self.mostrar_mensaje("Sin Stock", "No hay unidades disponibles en el almacén seleccionado.", "error")
            
            almacen_id = combo_almacen_mini.currentData() or 1
            
            cant, ok = QInputDialog.getInt(dialog, "Cantidad a Entregar", f"¿Cuántas unidades de {p['nombre']} se lleva?", 1, 1, int(p['stock']))
            if ok:
                exito, msg = db_cxc.agregar_producto_cuenta(cuenta['cxc_id'], cuenta['venta_id'], p['id'], almacen_id, cant, p['precio'], session.usuario_actual['id'])
                if exito:
                    txt_buscar.clear()
                    recargar_tabla_y_saldo()
                    buscar_mini() 
                else: self.mostrar_mensaje("Error", msg, "error")

        tabla_busq.itemDoubleClicked.connect(agregar_prod)
        txt_buscar.returnPressed.connect(lambda: agregar_prod(tabla_busq.currentItem()) if tabla_busq.currentItem() else None)

        # ---------------- PANEL DERECHO: HISTORIAL (EL RECIBO) ----------------
        panel_der = QFrame()
        panel_der.setStyleSheet("QFrame { background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 8px; }")
        layout_der = QVBoxLayout(panel_der)
        layout_der.setContentsMargins(20, 20, 20, 20)

        lbl_historial = QLabel("📖 DETALLE DE LA CUENTA (Comprobante)")
        lbl_historial.setStyleSheet("font-weight: 900; color: #0F172A; border: none; font-size: 14px;")
        layout_der.addWidget(lbl_historial)

        self.tabla_infinita_detalle = QTableWidget()
        self.tabla_infinita_detalle.setColumnCount(7)
        self.tabla_infinita_detalle.setHorizontalHeaderLabels(["FECHA", "TIPO", "DESCRIPCIÓN", "CANT.", "PRECIO", "SUBTOTAL", "ACCIÓN"])
        
        h_inf = self.tabla_infinita_detalle.horizontalHeader()
        h_inf.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        h_inf.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        h_inf.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        h_inf.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        h_inf.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        h_inf.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        h_inf.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.tabla_infinita_detalle.setColumnWidth(6, 110) 
        h_inf.setStretchLastSection(False)
        
        self.tabla_infinita_detalle.verticalHeader().setVisible(False)
        self.tabla_infinita_detalle.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_infinita_detalle.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_infinita_detalle.verticalHeader().setDefaultSectionSize(45)
        self.tabla_infinita_detalle.setStyleSheet(self.get_tabla_style())
        layout_der.addWidget(self.tabla_infinita_detalle)

        def recargar_tabla_y_saldo():
            self.tabla_infinita_detalle.setRowCount(0)
            detalles = db_cxc.obtener_detalle_cuenta_infinita(cuenta['cxc_id'], cuenta['venta_id'])
            saldo_acumulado = 0.0
            
            for i, d in enumerate(detalles):
                self.tabla_infinita_detalle.insertRow(i)
                self.tabla_infinita_detalle.setItem(i, 0, QTableWidgetItem(d['fecha'].split(' ')[0]))
                
                item_tipo = QTableWidgetItem(d['tipo'])
                if d['tipo'] == 'PRODUCTO': item_tipo.setForeground(QColor("#F59E0B"))
                else: item_tipo.setForeground(QColor("#10B981"))
                self.tabla_infinita_detalle.setItem(i, 1, item_tipo)
                
                item_desc = QTableWidgetItem(d['descripcion'])
                item_desc.setToolTip(d['descripcion'])
                self.tabla_infinita_detalle.setItem(i, 2, item_desc)
                
                self.tabla_infinita_detalle.setItem(i, 3, QTableWidgetItem(str(d['cantidad']) if d['tipo'] == 'PRODUCTO' else "-"))
                self.tabla_infinita_detalle.setItem(i, 4, QTableWidgetItem(f"$ {d['precio']:.2f}"))
                
                if d['tipo'] == 'PRODUCTO':
                    item_monto = QTableWidgetItem(f"+ $ {d['subtotal']:.2f}")
                    item_monto.setForeground(QColor("#DC2626"))
                    item_monto.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
                    saldo_acumulado += d['subtotal']
                else:
                    item_monto = QTableWidgetItem(f"- $ {d['subtotal']:.2f}")
                    item_monto.setForeground(QColor("#10B981"))
                    item_monto.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
                    saldo_acumulado -= d['subtotal']
                    
                self.tabla_infinita_detalle.setItem(i, 5, item_monto)
                
                # 🔥 BOTONES DE ACCIÓN: DEVOLVER PRODUCTO o ANULAR ABONO 🔥
                if d['tipo'] == 'PRODUCTO':
                    btn_rev = QPushButton(" Devolver")
                    btn_rev.setIcon(qta.icon('fa5s.undo', color='white'))
                    btn_rev.setStyleSheet("background-color: #DC2626; color: white; border-radius: 4px; padding: 6px; font-weight: bold; font-size: 11px;")
                    btn_rev.setCursor(Qt.CursorShape.PointingHandCursor)
                    btn_rev.clicked.connect(lambda checked, det_id=d['item_id'], max_cant=d['cantidad']: procesar_devolucion_parcial(det_id, max_cant))
                    
                    widget_btn = QWidget()
                    l_btn = QHBoxLayout(widget_btn)
                    l_btn.setContentsMargins(4, 4, 4, 4)
                    l_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    l_btn.addWidget(btn_rev)
                    self.tabla_infinita_detalle.setCellWidget(i, 6, widget_btn)
                else:
                    # ES UN ABONO: Botón para anularlo y sumarlo a la deuda
                    btn_del = QPushButton(" Anular")
                    btn_del.setIcon(qta.icon('fa5s.trash-alt', color='white'))
                    btn_del.setStyleSheet("background-color: #DC2626; color: white; border-radius: 4px; padding: 6px; font-weight: bold; font-size: 11px;")
                    btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
                    btn_del.clicked.connect(lambda checked, abono_id=d['item_id']: procesar_anular_abono(abono_id))
                    
                    widget_btn = QWidget()
                    l_btn = QHBoxLayout(widget_btn)
                    l_btn.setContentsMargins(4, 4, 4, 4)
                    l_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    l_btn.addWidget(btn_del)
                    self.tabla_infinita_detalle.setCellWidget(i, 6, widget_btn)
                    
            actualizar_etiqueta_saldo(saldo_acumulado)
            self.cargar_datos_refresh() 

        def procesar_devolucion_parcial(detalle_id, max_cant):
            cant_dev, ok = QInputDialog.getInt(dialog, "Devolución Parcial", f"¿Cuántas unidades desea devolver al inventario? (Máx: {max_cant})", 1, 1, int(max_cant))
            if ok:
                exito, msg = db_cxc.devolver_producto_cuenta(detalle_id, cuenta['cxc_id'], cuenta['venta_id'], cant_dev, session.usuario_actual['id'])
                if exito: 
                    recargar_tabla_y_saldo()
                    buscar_mini() 
                else: 
                    self.mostrar_mensaje("Error", msg, "error")
                    
        def procesar_anular_abono(abono_id):
            if self.mostrar_confirmacion("Anular Abono", "¿Está seguro de eliminar este pago? El saldo deudor del cliente aumentará."):
                exito, msg = db_cxc.eliminar_abono_cuaderno(abono_id, cuenta['cxc_id'])
                if exito:
                    recargar_tabla_y_saldo()
                else:
                    self.mostrar_mensaje("Error", msg, "error")

        cuerpo.addWidget(panel_izq, stretch=45)
        cuerpo.addWidget(panel_der, stretch=55)
        layout_principal.addLayout(cuerpo)

        # ---------------- BARRA INFERIOR: ABONAR DINERO CON CONVERSIÓN ----------------
        panel_pay = QFrame()
        panel_pay.setStyleSheet("background-color: #FFFFFF; border: 2px solid #10B981; border-radius: 8px;")
        layout_pay = QHBoxLayout(panel_pay)
        layout_pay.setContentsMargins(20, 15, 20, 15)
        
        layout_pay.addWidget(QLabel("💵 RECIBIR ABONO AL CUADERNO:", styleSheet="font-weight: 900; color: #10B981; font-size: 16px; border: none;"))
        
        combo_mp = QComboBox()
        combo_mp.setStyleSheet("padding: 12px; border: 1px solid #CBD5E1; border-radius: 4px; font-weight: bold; font-size: 15px; background-color: #F8FAFC;")
        combo_mp.setMinimumWidth(250)
        
        _, monedas, _, metodos, _ = db_sales.obtener_datos_configuracion()
        monedas_dict = {m['id']: m for m in monedas}
        
        for m in metodos: 
            combo_mp.addItem(m['nombre'], m)

        spin_abono = QDoubleSpinBox()
        spin_abono.setMaximum(99999999.99)
        spin_abono.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        spin_abono.setStyleSheet("padding: 12px; font-weight: bold; font-size: 18px; border: 1px solid #CBD5E1; border-radius: 4px; color: #10B981; background-color: #F8FAFC;")
        spin_abono.setMinimumWidth(180)
        
        lbl_equivalente = QLabel("Equivale a: $ 0.00")
        lbl_equivalente.setStyleSheet("font-size: 15px; font-weight: bold; color: #64748B; border: none; margin-left: 10px;")
        
        def actualizar_conversion():
            metodo = combo_mp.currentData()
            if not metodo: return
            moneda = monedas_dict[metodo['moneda_id']]
            
            spin_abono.setPrefix(f"{moneda['simbolo']} ")
            monto_ingresado = spin_abono.value()
            equiv_usd = monto_ingresado / float(moneda['tasa_cambio'])
            
            lbl_equivalente.setText(f"Equivale a: $ {equiv_usd:.2f}")

        combo_mp.currentIndexChanged.connect(actualizar_conversion)
        spin_abono.valueChanged.connect(actualizar_conversion)
        actualizar_conversion()
        
        btn_pay = QPushButton(" Procesar Abono")
        btn_pay.setIcon(qta.icon('fa5s.check', color='white'))
        btn_pay.setStyleSheet("background-color: #10B981; color: white; font-weight: bold; font-size: 15px; border-radius: 6px; padding: 12px 40px; margin-left: 20px;")
        btn_pay.setCursor(Qt.CursorShape.PointingHandCursor)
        
        def procesar_pay():
            if spin_abono.value() <= 0: return
            
            metodo = combo_mp.currentData()
            moneda = monedas_dict[metodo['moneda_id']]
            monto_usd = spin_abono.value() / float(moneda['tasa_cambio'])
            
            exito, msg = db_cxc.registrar_abono_cuaderno(cuenta['cxc_id'], monto_usd, metodo['id'], sesion['id'])
            if exito:
                spin_abono.setValue(0)
                recargar_tabla_y_saldo()
            else: self.mostrar_mensaje("Error", msg, "error")

        btn_pay.clicked.connect(procesar_pay)
        
        layout_pay.addStretch()
        layout_pay.addWidget(combo_mp)
        layout_pay.addWidget(spin_abono)
        layout_pay.addWidget(lbl_equivalente)
        layout_pay.addWidget(btn_pay)
        
        layout_principal.addWidget(panel_pay)

        recargar_tabla_y_saldo()
        dialog.exec()