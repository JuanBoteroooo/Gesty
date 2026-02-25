import os
import webbrowser 
import qtawesome as qta
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QComboBox, QFrame, QAbstractItemView, QMessageBox, 
                             QSpinBox, QDoubleSpinBox, QDialog, QFormLayout, QCompleter, 
                             QStackedWidget, QInputDialog, QAbstractSpinBox)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QFont
from datetime import datetime, timedelta
from modules.sales import db_sales
from modules.customers import db_customers 
from utils import session

class VistaVentas(QWidget):
    def __init__(self):
        super().__init__()
        self.carrito = {} 
        self.clientes = []
        self.monedas = []
        self.listas = []
        self.metodos_pago = [] 
        self.almacenes = [] 
        self.moneda_actual = None
        self.cliente_actual = None
        self.tasa_secundaria = 1.0 
        self.simbolo_secundario = "Bs"
        self.sesion_caja_actual = None 
        
        self.setup_ui()
        self.verificar_estado_caja()

    # ================= ALERTAS GLOBALES BLANCAS =================
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

    def mostrar_confirmacion(self, titulo, texto):
        msg = QMessageBox(self)
        msg.setWindowTitle(titulo)
        msg.setText(texto)
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setStyleSheet("""
            QMessageBox { background-color: #FFFFFF; }
            QLabel { color: #0F172A; font-size: 13px; font-weight: bold; } 
            QPushButton { padding: 6px 20px; background-color: #DC2626; color: white; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #B91C1C; }
        """)
        return msg.exec() == QMessageBox.StandardButton.Yes

    def setup_ui(self):
        layout_maestro = QVBoxLayout(self)
        layout_maestro.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget()
        layout_maestro.addWidget(self.stack)
        
        # ================= VISTA 1: CAJA CERRADA =================
        self.vista_cerrada = QWidget()
        self.vista_cerrada.setStyleSheet("background-color: #F8FAFC;")
        layout_cerrada = QVBoxLayout(self.vista_cerrada)
        layout_cerrada.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_bloqueo = QLabel("LA CAJA SE ENCUENTRA CERRADA")
        lbl_bloqueo.setStyleSheet("font-size: 28px; font-weight: 900; color: #DC2626; letter-spacing: 1px;")
        lbl_bloqueo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_sub_bloqueo = QLabel("Aperture un nuevo turno y registre el fondo base para iniciar operaciones.")
        lbl_sub_bloqueo.setStyleSheet("font-size: 14px; color: #64748B; margin-bottom: 25px;")
        lbl_sub_bloqueo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        btn_abrir_caja = QPushButton("ABRIR TURNO DE CAJA")
        btn_abrir_caja.setFixedSize(320, 55)
        btn_abrir_caja.setStyleSheet("""
            QPushButton { background-color: #0F172A; color: white; border-radius: 6px; font-weight: 900; font-size: 16px; letter-spacing: 1px; } 
            QPushButton:hover { background-color: #1E293B; }
        """)
        btn_abrir_caja.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_abrir_caja.clicked.connect(self.modal_abrir_caja)
        
        layout_cerrada.addWidget(lbl_bloqueo)
        layout_cerrada.addWidget(lbl_sub_bloqueo)
        layout_cerrada.addWidget(btn_abrir_caja, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # ================= VISTA 2: TERMINAL DE VENTAS (POS) =================
        self.vista_pos = QWidget()
        layout_pos_principal = QVBoxLayout(self.vista_pos)
        layout_pos_principal.setContentsMargins(30, 30, 30, 30)
        layout_pos_principal.setSpacing(20)
        
        # --- CABECERA ---
        cabecera_pos = QHBoxLayout()
        
        textos_cabecera = QVBoxLayout()
        textos_cabecera.setSpacing(2)
        lbl_titulo = QLabel("TERMINAL DE VENTAS (POS)")
        lbl_titulo.setStyleSheet("font-size: 24px; font-weight: 900; color: #0F172A; letter-spacing: 1px;")
        lbl_sub = QLabel("Facturación rápida, presupuestos y control de inventario en tiempo real.")
        lbl_sub.setStyleSheet("font-size: 14px; color: #64748B;")
        textos_cabecera.addWidget(lbl_titulo)
        textos_cabecera.addWidget(lbl_sub)
        
        cabecera_pos.addLayout(textos_cabecera)
        cabecera_pos.addStretch()

        btn_reimprimir = QPushButton("Reimprimir Ticket")
        btn_reimprimir.setStyleSheet("padding: 10px 20px; background-color: #F1F5F9; color: #334155; border: 1px solid #CBD5E1; border-radius: 6px; font-weight: bold; font-size: 13px; margin-right: 10px;")
        btn_reimprimir.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_reimprimir.clicked.connect(self.modal_reimprimir)
        cabecera_pos.addWidget(btn_reimprimir)

        btn_cerrar_caja = QPushButton("Cerrar Turno (Z)")
        btn_cerrar_caja.setStyleSheet("padding: 10px 20px; background-color: #FEF2F2; color: #DC2626; border: 1px solid #FECACA; border-radius: 6px; font-weight: bold; font-size: 13px;")
        btn_cerrar_caja.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cerrar_caja.clicked.connect(self.modal_cerrar_caja)
        
        cabecera_pos.addWidget(btn_cerrar_caja)
        layout_pos_principal.addLayout(cabecera_pos)
        
        cuerpo_pos = QHBoxLayout()
        cuerpo_pos.setSpacing(20)
        
        # === PANEL IZQUIERDO ===
        panel_izq = QFrame()
        layout_izq = QVBoxLayout(panel_izq)
        layout_izq.setContentsMargins(0, 0, 0, 0)
        layout_izq.setSpacing(15)
        
        self.txt_buscador = QLineEdit()
        self.txt_buscador.setPlaceholderText("Buscar producto... (Presiona ↓ para seleccionar en la tabla)")
        self.txt_buscador.setFixedHeight(45)
        self.txt_buscador.setStyleSheet("""
            QLineEdit { padding: 5px 15px; border: 1px solid #CBD5E1; border-radius: 6px; font-size: 14px; color: #0F172A; background-color: #FFFFFF; }
            QLineEdit:focus { border: 2px solid #38BDF8; }
        """)
        self.txt_buscador.textChanged.connect(self.buscar_productos)
        self.txt_buscador.installEventFilter(self) 
        layout_izq.addWidget(self.txt_buscador)
        
        # TABLA BÚSQUEDA
        self.tabla_busqueda = QTableWidget()
        self.tabla_busqueda.setColumnCount(4)
        self.tabla_busqueda.setHorizontalHeaderLabels(["ID", "DESCRIPCIÓN DEL PRODUCTO", "PRECIO", "STOCK DISP."])
        
        header_busq = self.tabla_busqueda.horizontalHeader()
        header_busq.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_busq.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header_busq.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header_busq.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header_busq.setStretchLastSection(False)
        
        self.tabla_busqueda.verticalHeader().setVisible(False)
        self.tabla_busqueda.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_busqueda.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla_busqueda.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_busqueda.verticalHeader().setDefaultSectionSize(40)
        self.tabla_busqueda.setFixedHeight(140) 
        self.tabla_busqueda.setStyleSheet("""
            QTableWidget { background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px; color: #334155; font-size: 13px; font-weight: bold; }
            QTableWidget::item { padding: 5px 15px; border-bottom: 1px solid #F1F5F9; }
            QTableWidget::item:selected { background-color: #EFF6FF; color: #0F172A; }
            QHeaderView::section { background-color: #F8FAFC; color: #64748B; font-weight: bold; font-size: 11px; padding: 10px; border: none; border-bottom: 2px solid #E2E8F0; text-transform: uppercase; }
        """)
        self.tabla_busqueda.itemDoubleClicked.connect(self.agregar_al_carrito)
        self.tabla_busqueda.installEventFilter(self) 
        layout_izq.addWidget(self.tabla_busqueda)
        
        lbl_carrito = QLabel("DETALLE DE VENTA")
        lbl_carrito.setStyleSheet("font-size: 13px; font-weight: 800; color: #64748B; margin-top: 5px;")
        layout_izq.addWidget(lbl_carrito)
        
        # TABLA CARRITO
        self.tabla_carrito = QTableWidget()
        self.tabla_carrito.setColumnCount(7) 
        self.tabla_carrito.setHorizontalHeaderLabels(["ID", "PRODUCTO", "CANT.", "PRECIO ($)", "PRECIO (Bs)", "SUBT.", ""])
        
        header_carrito = self.tabla_carrito.horizontalHeader()
        header_carrito.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_carrito.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) 
        # 🔥 FIJAMOS EL ANCHO DE CANTIDAD Y PAPELERA PARA QUE JAMÁS SE CORTEN 🔥
        header_carrito.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.tabla_carrito.setColumnWidth(2, 85) 
        header_carrito.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header_carrito.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header_carrito.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header_carrito.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.tabla_carrito.setColumnWidth(6, 60) 
        header_carrito.setStretchLastSection(False)
        
        self.tabla_carrito.verticalHeader().setVisible(False)
        self.tabla_carrito.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_carrito.verticalHeader().setDefaultSectionSize(55) 
        
        self.tabla_carrito.setStyleSheet("""
            QTableWidget { background-color: #FFFFFF; color: #334155; border: 1px solid #E2E8F0; border-radius: 6px; font-size: 13px; font-weight: bold; } 
            QTableWidget::item { padding: 5px 10px; border-bottom: 1px solid #F1F5F9; } 
            QTableWidget::item:selected { background-color: #EFF6FF; color: #0F172A; }
            QHeaderView::section { background-color: #F8FAFC; color: #64748B; font-weight: bold; padding: 12px; border: none; border-bottom: 2px solid #E2E8F0; font-size: 11px; text-transform: uppercase; }
        """)
        layout_izq.addWidget(self.tabla_carrito)
        
        btn_limpiar = QPushButton("Vaciar Carrito")
        btn_limpiar.setStyleSheet("padding: 8px 15px; background-color: #FFFFFF; color: #DC2626; border: 1px solid #FECACA; border-radius: 6px; font-weight: bold; font-size: 13px;")
        btn_limpiar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_limpiar.clicked.connect(self.limpiar_carrito)
        layout_izq.addWidget(btn_limpiar, alignment=Qt.AlignmentFlag.AlignRight)
        
        # === PANEL DERECHO ===
        panel_der = QFrame()
        panel_der.setFixedWidth(380)
        panel_der.setStyleSheet("QFrame { background-color: #FFFFFF; border-radius: 12px; border: 1px solid #E2E8F0; }")
        layout_der = QVBoxLayout(panel_der)
        layout_der.setContentsMargins(25, 25, 25, 25)
        layout_der.setSpacing(15)
        
        estilo_dropdown = "QComboBox { padding: 12px; border: 1px solid #CBD5E1; border-radius: 6px; color: #0F172A; font-size: 14px; background-color: #F8FAFC; font-weight: bold; } QComboBox:focus { border: 2px solid #38BDF8; background-color: #FFFFFF; } QComboBox QAbstractItemView { background-color: #FFFFFF; color: #0F172A; font-size: 13px; selection-background-color: #EFF6FF; }"
        estilo_titulo_opcion = "font-size: 12px; font-weight: bold; color: #64748B; text-transform: uppercase;"
        
        layout_der.addWidget(QLabel("ALMACÉN DE DESPACHO:", styleSheet=estilo_titulo_opcion))
        self.combo_almacenes = QComboBox()
        self.combo_almacenes.setStyleSheet(estilo_dropdown)
        self.combo_almacenes.currentIndexChanged.connect(self.cambiar_almacen)
        layout_der.addWidget(self.combo_almacenes)

        layout_der.addWidget(QLabel("CLIENTE ASIGNADO:", styleSheet=estilo_titulo_opcion))
        fila_cliente = QHBoxLayout()
        self.combo_clientes = QComboBox()
        self.combo_clientes.setEditable(True) 
        self.combo_clientes.setStyleSheet(estilo_dropdown)
        self.combo_clientes.currentIndexChanged.connect(self.cambiar_cliente)
        
        btn_nuevo_cliente = QPushButton()
        btn_nuevo_cliente.setIcon(qta.icon('fa5s.user-plus', color='white'))
        btn_nuevo_cliente.setStyleSheet("background-color: #0F172A; border-radius: 6px; padding: 12px;")
        btn_nuevo_cliente.setFixedWidth(45)
        btn_nuevo_cliente.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_nuevo_cliente.clicked.connect(self.abrir_modal_cliente_rapido)
        
        fila_cliente.addWidget(self.combo_clientes)
        fila_cliente.addWidget(btn_nuevo_cliente)
        layout_der.addLayout(fila_cliente)
        
        layout_der.addWidget(QLabel("TARIFA A APLICAR:", styleSheet=estilo_titulo_opcion))
        self.combo_tarifas = QComboBox()
        self.combo_tarifas.setStyleSheet(estilo_dropdown)
        self.combo_tarifas.currentIndexChanged.connect(self.cambiar_tarifa)
        layout_der.addWidget(self.combo_tarifas)
        
        layout_der.addWidget(QLabel("MONEDA DE FACTURACIÓN:", styleSheet=estilo_titulo_opcion))
        self.combo_monedas = QComboBox()
        self.combo_monedas.setStyleSheet(estilo_dropdown)
        self.combo_monedas.currentIndexChanged.connect(self.cambiar_moneda)
        layout_der.addWidget(self.combo_monedas)
        
        layout_der.addStretch()
        
        panel_total = QFrame()
        panel_total.setStyleSheet("background-color: #F8FAFC; border-radius: 8px; border: 1px solid #CBD5E1;")
        layout_totales = QVBoxLayout(panel_total)
        
        self.lbl_total_base = QLabel("Ref: $ 0.00")
        self.lbl_total_base.setStyleSheet("font-size: 14px; color: #64748B; font-weight: bold;")
        self.lbl_total_base.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_total_pagar = QLabel("$ 0.00") 
        self.lbl_total_pagar.setStyleSheet("font-size: 38px; color: #10B981; font-weight: 900; letter-spacing: -1px;")
        self.lbl_total_pagar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout_totales.addWidget(self.lbl_total_base)
        layout_totales.addWidget(self.lbl_total_pagar)
        layout_der.addWidget(panel_total)
        
        btn_procesar = QPushButton("COBRAR (F12)")
        btn_procesar.setFixedHeight(65)
        btn_procesar.setStyleSheet("QPushButton { background-color: #10B981; color: white; border-radius: 8px; font-weight: 900; font-size: 18px; letter-spacing: 1px; } QPushButton:hover { background-color: #059669; }")
        btn_procesar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_procesar.clicked.connect(self.abrir_modal_pago)
        layout_der.addWidget(btn_procesar)
        
        # BOTONES DE PRESUPUESTO
        fila_presupuestos = QHBoxLayout()
        btn_guardar_presupuesto = QPushButton("Crear Presupuesto")
        btn_guardar_presupuesto.setFixedHeight(45)
        btn_guardar_presupuesto.setStyleSheet("QPushButton { background-color: #F1F5F9; color: #334155; border: 1px solid #CBD5E1; border-radius: 6px; font-weight: bold; font-size: 13px; } QPushButton:hover { background-color: #E2E8F0; }")
        btn_guardar_presupuesto.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_guardar_presupuesto.clicked.connect(self.guardar_presupuesto)
        
        btn_cargar_presupuesto = QPushButton("Cargar Pendiente")
        btn_cargar_presupuesto.setFixedHeight(45)
        btn_cargar_presupuesto.setStyleSheet("QPushButton { background-color: #0F172A; color: white; border-radius: 6px; font-weight: bold; font-size: 13px; } QPushButton:hover { background-color: #1E293B; }")
        btn_cargar_presupuesto.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cargar_presupuesto.clicked.connect(self.abrir_modal_buscar_presupuesto)
        
        fila_presupuestos.addWidget(btn_guardar_presupuesto)
        fila_presupuestos.addWidget(btn_cargar_presupuesto)
        layout_der.addLayout(fila_presupuestos)
        
        cuerpo_pos.addWidget(panel_izq, stretch=65)
        cuerpo_pos.addWidget(panel_der, stretch=35)
        
        layout_pos_principal.addLayout(cuerpo_pos)
        
        self.stack.addWidget(self.vista_cerrada) 
        self.stack.addWidget(self.vista_pos)     
        
        self.installEventFilter(self)

    # ================= LOGICA DE ESTADO DE CAJA =================
    def verificar_estado_caja(self):
        self.sesion_caja_actual = db_sales.verificar_caja_abierta()
        if self.sesion_caja_actual:
            self.stack.setCurrentIndex(1)
            self.cargar_configuracion()
        else:
            self.stack.setCurrentIndex(0)

    def modal_abrir_caja(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Apertura de Turno")
        dialog.setFixedWidth(350)
        dialog.setStyleSheet("QDialog { background-color: #FFFFFF; } QLabel { color: #334155; font-weight: bold; font-size: 13px; }")
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(25, 25, 25, 25)
        
        layout.addWidget(QLabel("Monto base en caja (Fondo para vueltos):"))
        
        spin_monto = QDoubleSpinBox()
        spin_monto.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        spin_monto.setMaximum(99999.99)
        spin_monto.setPrefix("$ ")
        spin_monto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        spin_monto.setStyleSheet("padding: 10px; border: 1px solid #CBD5E1; border-radius: 6px; color: #10B981; background-color: #F8FAFC; font-size: 22px; font-weight: 900;")
        layout.addWidget(spin_monto)
        
        layout.addSpacing(10)
        btn_abrir = QPushButton("Iniciar Operaciones")
        btn_abrir.setStyleSheet("padding: 12px; background-color: #0F172A; color: white; border-radius: 6px; font-weight: bold; font-size: 14px;")
        btn_abrir.setCursor(Qt.CursorShape.PointingHandCursor)
        
        def procesar_apertura():
            exito, msg = db_sales.abrir_caja(spin_monto.value(), session.usuario_actual['id'])
            if exito:
                self.mostrar_mensaje("Apertura Exitosa", msg)
                dialog.accept()
                self.verificar_estado_caja()
            else:
                self.mostrar_mensaje("Error", msg, "error")
                
        btn_abrir.clicked.connect(procesar_apertura)
        layout.addWidget(btn_abrir)
        dialog.exec()

    def modal_cerrar_caja(self):
        if len(self.carrito) > 0:
            return self.mostrar_mensaje("Transacción Activa", "Debe vaciar el carrito o completar la venta en curso antes de realizar el corte de caja.", "error")
            
        dialog = QDialog(self)
        dialog.setWindowTitle("Corte de Caja (Reporte Z)")
        dialog.setFixedWidth(400)
        dialog.setStyleSheet("QDialog { background-color: #FFFFFF; } QLabel { color: #0F172A; font-size: 13px; }")
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(25, 25, 25, 25)
        
        lbl_titulo = QLabel("RESUMEN DE INGRESOS DEL TURNO")
        lbl_titulo.setStyleSheet("font-size: 14px; font-weight: 900; color: #334155; margin-bottom: 10px;")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_titulo)
        
        resumen = db_sales.obtener_resumen_caja(self.sesion_caja_actual['id'])
        monto_ini = self.sesion_caja_actual['monto_inicial']
        
        tabla = QTableWidget()
        tabla.setColumnCount(2)
        tabla.setHorizontalHeaderLabels(["CONCEPTO", "MONTO RECAUDADO"])
        tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        tabla.verticalHeader().setVisible(False)
        tabla.setStyleSheet("""
            QTableWidget { background-color: #F8FAFC; color: #334155; font-weight: bold; border: 1px solid #E2E8F0; border-radius: 6px; }
            QHeaderView::section { background-color: #E2E8F0; color: #64748B; font-weight: bold; border: none; font-size: 11px; padding: 8px;}
        """)
        
        tabla.setRowCount(len(resumen) + 1)
        
        tabla.setItem(0, 0, QTableWidgetItem("Fondo de Caja (Apertura)"))
        item_ini = QTableWidgetItem(f"$ {monto_ini:.2f}")
        item_ini.setForeground(QColor("#64748B"))
        tabla.setItem(0, 1, item_ini)
        
        fila_actual = 1
        for fila in resumen:
            tabla.setItem(fila_actual, 0, QTableWidgetItem(fila['metodo']))
            item_val = QTableWidgetItem(f"{fila['simbolo']} {fila['total']:.2f}")
            item_val.setForeground(QColor("#10B981"))
            tabla.setItem(fila_actual, 1, item_val)
            fila_actual += 1
            
        layout.addWidget(tabla)
        
        layout.addSpacing(10)
        btn_cerrar = QPushButton("CONFIRMAR Y CERRAR CAJA")
        btn_cerrar.setStyleSheet("padding: 15px; background-color: #DC2626; color: white; border-radius: 6px; font-weight: bold; font-size: 14px; letter-spacing: 1px;")
        btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        
        def procesar_cierre():
            if self.mostrar_confirmacion("Confirmar Cierre", "¿Está seguro de realizar el cierre Z? Esta acción finalizará el turno y no podrá registrar más ventas hasta abrir uno nuevo."):
                exito, msg = db_sales.cerrar_caja(self.sesion_caja_actual['id'])
                if exito:
                    self.mostrar_mensaje("Corte Exitoso", "El turno de caja se ha cerrado correctamente.")
                    dialog.accept()
                    self.verificar_estado_caja()
                else:
                    self.mostrar_mensaje("Error", msg, "error")
                    
        btn_cerrar.clicked.connect(procesar_cierre)
        layout.addWidget(btn_cerrar)
        dialog.exec()

    # ================= LOGICA DE REIMPRESIÓN =================
    def modal_reimprimir(self):
        ventas = db_sales.obtener_ventas_recientes()
        if not ventas:
            return self.mostrar_mensaje("Aviso", "No hay registros de ventas recientes para reimprimir.")

        dialog = QDialog(self)
        dialog.setWindowTitle("Reimpresión de Comprobante")
        dialog.setFixedWidth(550)
        dialog.setStyleSheet("QDialog { background-color: #FFFFFF; }")
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(25, 25, 25, 25)

        lbl = QLabel("Seleccione la factura que desea imprimir:")
        lbl.setStyleSheet("font-weight: bold; font-size: 13px; color: #334155; margin-bottom: 10px;")
        layout.addWidget(lbl)

        tabla = QTableWidget()
        tabla.setColumnCount(4)
        tabla.setHorizontalHeaderLabels(["NRO.", "FECHA", "CLIENTE", "TOTAL ($)"])
        
        header_reim = tabla.horizontalHeader()
        header_reim.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_reim.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header_reim.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header_reim.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header_reim.setStretchLastSection(False)
        
        tabla.verticalHeader().setVisible(False)
        tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tabla.setStyleSheet("""
            QTableWidget { background-color: #F8FAFC; color: #334155; font-size: 13px; border: 1px solid #E2E8F0; border-radius: 6px; }
            QTableWidget::item { padding: 5px; border-bottom: 1px solid #E2E8F0; }
            QTableWidget::item:selected { background-color: #EFF6FF; color: #0F172A; font-weight: bold; }
            QHeaderView::section { background-color: #E2E8F0; color: #64748B; font-weight: bold; font-size: 11px; padding: 10px; border: none; }
        """)

        tabla.setRowCount(len(ventas))
        for i, v in enumerate(ventas):
            item_id = QTableWidgetItem(f"{v['id']:06d}")
            item_id.setData(Qt.ItemDataRole.UserRole, v['id'])
            item_id.setForeground(QColor("#94A3B8"))
            
            tabla.setItem(i, 0, item_id)
            tabla.setItem(i, 1, QTableWidgetItem(v['fecha_hora'].split(" ")[0]))
            tabla.setItem(i, 2, QTableWidgetItem(v['cliente_nombre']))
            
            item_tot = QTableWidgetItem(f"{v['total_venta']:.2f}")
            item_tot.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            tabla.setItem(i, 3, item_tot)

        layout.addWidget(tabla)

        btn_imprimir = QPushButton("Imprimir Documento Seleccionado")
        btn_imprimir.setStyleSheet("padding: 12px; background-color: #0F172A; color: white; border-radius: 6px; font-weight: bold; font-size: 14px; margin-top: 10px;")
        btn_imprimir.setCursor(Qt.CursorShape.PointingHandCursor)

        def imprimir():
            filas = tabla.selectedItems()
            if not filas: return self.mostrar_mensaje("Error", "Seleccione una factura de la lista.", "error")
            v_id = tabla.item(filas[0].row(), 0).data(Qt.ItemDataRole.UserRole)
            self.generar_ticket(v_id)
            dialog.accept()

        btn_imprimir.clicked.connect(imprimir)
        layout.addWidget(btn_imprimir)
        dialog.exec()

    # ================= LOGICA DE PRESUPUESTOS =================
    def guardar_presupuesto(self):
        if not self.carrito:
            return self.mostrar_mensaje("Operación Inválida", "Debe agregar productos al detalle para poder generar una cotización.", "error")
        
        idx_cliente = self.combo_clientes.currentIndex()
        if idx_cliente < 0: return self.mostrar_mensaje("Error", "Seleccione un cliente válido para asignar la cotización.", "error")
        
        total_venta_base = sum(item['cantidad'] * item['precio'] for item in self.carrito.values())
        
        exito, resp = db_sales.guardar_presupuesto(self.cliente_actual['id'], self.moneda_actual['id'], total_venta_base, list(self.carrito.values()))
        
        if exito:
            self.generar_ticket_presupuesto(resp)
            self.limpiar_carrito()
            self.mostrar_mensaje("Cotización Generada", "El documento ha sido guardado y procesado para impresión correctamente.")
        else:
            self.mostrar_mensaje("Error del Sistema", str(resp), "error")

    def abrir_modal_buscar_presupuesto(self):
        presupuestos = db_sales.obtener_presupuestos_activos()
        if not presupuestos:
            return self.mostrar_mensaje("Resultado", "No se encontraron cotizaciones pendientes en el sistema.")
            
        dialog = QDialog(self)
        dialog.setWindowTitle("Cotizaciones Pendientes")
        dialog.setFixedWidth(550)
        dialog.setStyleSheet("QDialog { background-color: #FFFFFF; }")
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(25, 25, 25, 25)
        
        lbl = QLabel("Seleccione la cotización que desea facturar:")
        lbl.setStyleSheet("font-weight: bold; font-size: 13px; color: #334155; margin-bottom: 10px;")
        layout.addWidget(lbl)
        
        tabla = QTableWidget()
        tabla.setColumnCount(4)
        tabla.setHorizontalHeaderLabels(["NRO.", "FECHA EMISIÓN", "CLIENTE", "MONTO ESTIMADO ($)"])
        
        header_presq = tabla.horizontalHeader()
        header_presq.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_presq.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header_presq.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header_presq.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header_presq.setStretchLastSection(False)
        
        tabla.verticalHeader().setVisible(False)
        tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tabla.setStyleSheet("""
            QTableWidget { background-color: #F8FAFC; color: #334155; font-size: 13px; border: 1px solid #E2E8F0; border-radius: 6px; }
            QTableWidget::item { padding: 5px; border-bottom: 1px solid #E2E8F0; }
            QTableWidget::item:selected { background-color: #EFF6FF; color: #0F172A; font-weight: bold; }
            QHeaderView::section { background-color: #E2E8F0; color: #64748B; font-weight: bold; font-size: 11px; padding: 10px; border: none; }
        """)
        
        tabla.setRowCount(len(presupuestos))
        for i, p in enumerate(presupuestos):
            item_id = QTableWidgetItem(f"{p['id']:06d}")
            item_id.setData(Qt.ItemDataRole.UserRole, p['id'])
            item_id.setForeground(QColor("#94A3B8"))
            
            tabla.setItem(i, 0, item_id)
            tabla.setItem(i, 1, QTableWidgetItem(p['fecha_hora'].split(" ")[0]))
            tabla.setItem(i, 2, QTableWidgetItem(p['cliente_nombre']))
            
            item_tot = QTableWidgetItem(f"{p['total_presupuesto']:.2f}")
            item_tot.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            tabla.setItem(i, 3, item_tot)
            
        layout.addWidget(tabla)
        
        btn_cargar = QPushButton("Cargar Detalles al POS")
        btn_cargar.setStyleSheet("padding: 12px; background-color: #0F172A; color: white; border-radius: 6px; font-weight: bold; font-size: 14px; margin-top: 10px;")
        
        def cargar():
            filas = tabla.selectedItems()
            if not filas: return self.mostrar_mensaje("Error", "Seleccione un registro de la lista.", "error")
            p_id = tabla.item(filas[0].row(), 0).data(Qt.ItemDataRole.UserRole)
            
            detalles = db_sales.cargar_detalle_presupuesto(p_id)
            self.limpiar_carrito()
            
            for d in detalles:
                stock_maximo = d['stock_max'] if d['stock_max'] is not None else 0
                costo_real = d['costo'] if d['costo'] is not None else 0
                
                self.carrito[d['id']] = {
                    'id': d['id'], 'nombre': d['nombre'], 'precio': d['precio'],
                    'costo': costo_real, 'cantidad': d['cantidad'], 'stock_max': stock_maximo
                }
            
            db_sales.marcar_presupuesto_procesado(p_id)
            self.renderizar_carrito()
            dialog.accept()
            self.mostrar_mensaje("Datos Importados", "Los productos se han cargado correctamente. Proceda con el cobro.")
            
        btn_cargar.clicked.connect(cargar)
        layout.addWidget(btn_cargar)
        dialog.exec()

    # ================= LOGICA DE TICKETS E IMPRESION =================
    def generar_ticket_presupuesto(self, presupuesto_id):
        venta, detalles = db_sales.obtener_datos_ticket_presupuesto(presupuesto_id)
        if not os.path.exists("tickets"): os.makedirs("tickets")
        ruta_archivo = os.path.abspath(f"tickets/Presupuesto_{presupuesto_id}.html")
        
        html = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: 'Courier New', Courier, monospace; width: 300px; margin: 0 auto; padding: 10px; color: #000; }}
                h2, h3 {{ text-align: center; margin: 5px 0; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 12px; }}
                th, td {{ border-bottom: 1px dashed #000; padding: 5px 0; text-align: left; }}
                .right {{ text-align: right; }}
                .center {{ text-align: center; }}
                .total {{ font-weight: bold; font-size: 16px; margin-top: 10px; text-align: right; }}
                .alerta {{ text-align: center; font-weight: bold; border: 1px dashed #000; padding: 5px; margin-top: 10px; font-size: 11px; }}
            </style>
        </head>
        <body>
            <h2>FERRETERÍA GESTY</h2>
            <div class="center">RIF: J-12345678-9</div>
            <hr style="border:1px dashed #000;">
            <h3 style="margin: 10px 0;">*** PRESUPUESTO ***</h3>
            <div><b>N° Documento:</b> {presupuesto_id:06d}</div>
            <div><b>Fecha:</b> {venta['fecha_hora']}</div>
            <div><b>Válido hasta:</b> {venta['fecha_vencimiento']}</div>
            <div><b>Cliente:</b> {venta['cliente_nombre']}</div>
            <div><b>Doc:</b> {venta['cliente_doc']}</div>
            <hr style="border:1px dashed #000;">
            <table>
                <tr><th>CANT</th><th>DESCRIPCIÓN</th><th class="right">SUBT</th></tr>
        """
        for d in detalles: html += f"<tr><td>{d['cantidad']}</td><td>{d['nombre']}</td><td class='right'>${d['subtotal']:.2f}</td></tr>"
        html += f"""
            </table>
            <div class="total">TOTAL ESTIMADO: ${venta['total_presupuesto']:.2f}</div>
            <div class="alerta">DOCUMENTO NO VÁLIDO COMO FACTURA.<br>Los precios pueden variar luego de su vencimiento.</div>
            <hr style="border:1px dashed #000;">
            <script>window.print();</script>
        </body></html>
        """
        with open(ruta_archivo, "w", encoding="utf-8") as f: f.write(html)
        webbrowser.open(f"file://{ruta_archivo}")

    def generar_ticket(self, venta_id):
        venta, detalles = db_sales.obtener_datos_ticket(venta_id)
        if not os.path.exists("tickets"): os.makedirs("tickets")
        ruta_archivo = os.path.abspath(f"tickets/Ticket_{venta_id}.html")
        
        html = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: 'Courier New', Courier, monospace; width: 300px; margin: 0 auto; padding: 10px; color: #000; }}
                h2, h3 {{ text-align: center; margin: 5px 0; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 12px; }}
                th, td {{ border-bottom: 1px dashed #000; padding: 5px 0; text-align: left; }}
                .right {{ text-align: right; }}
                .center {{ text-align: center; }}
                .total {{ font-weight: bold; font-size: 16px; margin-top: 10px; text-align: right; }}
            </style>
        </head>
        <body>
            <h2>FERRETERÍA GESTY</h2>
            <div class="center">RIF: J-12345678-9</div>
            <hr style="border:1px dashed #000;">
            <div><b>Nota N°:</b> {venta_id:06d}</div>
            <div><b>Fecha:</b> {venta['fecha_hora']}</div>
            <div><b>Cliente:</b> {venta['cliente_nombre']}</div>
            <div><b>Doc:</b> {venta['cliente_doc']}</div>
            <hr style="border:1px dashed #000;">
            <table>
                <tr><th>CANT</th><th>DESCRIPCIÓN</th><th class="right">SUBT</th></tr>
        """
        for d in detalles: html += f"<tr><td>{d['cantidad']}</td><td>{d['nombre']}</td><td class='right'>${d['subtotal']:.2f}</td></tr>"
        html += f"""
            </table>
            <div class="total">TOTAL: ${venta['total_venta']:.2f}</div>
            <hr style="border:1px dashed #000;">
            <div class="center" style="margin-top: 10px;">¡Gracias por su compra!</div>
            <script>window.print();</script>
        </body></html>
        """
        with open(ruta_archivo, "w", encoding="utf-8") as f: f.write(html)
        webbrowser.open(f"file://{ruta_archivo}")

    # ================= EVENTOS DE TECLADO =================
    def eventFilter(self, source, event):
        if event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_F12 and self.sesion_caja_actual is not None:
                self.abrir_modal_pago()
                return True
                
            if source is self.txt_buscador and event.key() == Qt.Key.Key_Down:
                if self.tabla_busqueda.rowCount() > 0:
                    self.tabla_busqueda.setFocus()
                    self.tabla_busqueda.selectRow(0) 
                    return True 
                    
            elif source is self.tabla_busqueda and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                item = self.tabla_busqueda.currentItem()
                if item:
                    self.agregar_al_carrito(item)
                    return True
                    
        return super().eventFilter(source, event)

    # ================= LOGICA PRINCIPAL =================
    def cargar_configuracion(self):
        self.clientes, self.monedas, self.listas, self.metodos_pago, self.almacenes = db_sales.obtener_datos_configuracion()
        
        moneda_sec = next((m for m in self.monedas if not m['es_principal']), None)
        if moneda_sec:
            self.tasa_secundaria = float(moneda_sec['tasa_cambio'])
            self.simbolo_secundario = moneda_sec['simbolo']

        self.combo_almacenes.blockSignals(True)
        self.combo_almacenes.clear()
        for a in self.almacenes: self.combo_almacenes.addItem(a['nombre'], a['id'])
        self.combo_almacenes.blockSignals(False)
        
        self.combo_tarifas.blockSignals(True)
        self.combo_tarifas.clear()
        for l in self.listas: self.combo_tarifas.addItem(l['nombre'], l['id'])
        self.combo_tarifas.blockSignals(False)
        
        self.combo_clientes.blockSignals(True)
        self.combo_clientes.clear()
        for c in self.clientes: self.combo_clientes.addItem(c['nombre'], c)
        self.combo_clientes.blockSignals(False)
        
        completer = self.combo_clientes.completer()
        if completer:
            completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
            completer.setFilterMode(Qt.MatchFlag.MatchContains) 
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        
        if self.clientes: 
            self.cliente_actual = self.clientes[0]
            self.sincronizar_tarifa_cliente()
            
        self.combo_monedas.blockSignals(True)
        self.combo_monedas.clear()
        for m in self.monedas:
            self.combo_monedas.addItem(f"{m['nombre']} ({m['simbolo']})", m)
            if m['es_principal']:
                self.combo_monedas.setCurrentIndex(self.combo_monedas.count() - 1)
                self.moneda_actual = m
        self.combo_monedas.blockSignals(False)
        
        self.tabla_carrito.setHorizontalHeaderItem(4, QTableWidgetItem(f"PRECIO ({self.simbolo_secundario})"))
        self.actualizar_totales()
        self.txt_buscador.setFocus()

    def cambiar_almacen(self):
        if len(self.carrito) > 0:
            if self.mostrar_confirmacion("Cambio de Origen", "Cambiar de almacén vaciará los productos actuales del carrito. ¿Desea continuar?"):
                self.limpiar_carrito()
            else:
                self.combo_almacenes.blockSignals(True)
                self.combo_almacenes.blockSignals(False)
                return
        self.buscar_productos()

    def sincronizar_tarifa_cliente(self):
        if not self.cliente_actual: return
        idx = self.combo_tarifas.findData(self.cliente_actual['lista_precio_id'])
        if idx >= 0: self.combo_tarifas.setCurrentIndex(idx)

    def cambiar_cliente(self):
        idx = self.combo_clientes.currentIndex()
        if idx >= 0:
            self.cliente_actual = self.combo_clientes.itemData(idx)
            self.sincronizar_tarifa_cliente() 
            self.buscar_productos()

    def cambiar_tarifa(self):
        self.buscar_productos()

    def cambiar_moneda(self):
        self.moneda_actual = self.combo_monedas.currentData()
        self.actualizar_totales()

    def buscar_productos(self):
        termino = self.txt_buscador.text().strip()
        if len(termino) < 1:
            self.tabla_busqueda.setRowCount(0)
            return
            
        lista_id = self.combo_tarifas.currentData() or 1
        almacen_id = self.combo_almacenes.currentData() or 1 
        
        resultados = db_sales.buscar_productos(termino, lista_id, almacen_id)
        
        self.tabla_busqueda.setRowCount(0)
        for i, prod in enumerate(resultados):
            self.tabla_busqueda.insertRow(i)
            
            item_id = QTableWidgetItem(f"{prod['id']:05d}")
            item_id.setForeground(QColor("#94A3B8"))
            item_id.setData(Qt.ItemDataRole.UserRole, prod) 
            self.tabla_busqueda.setItem(i, 0, item_id)
            
            item_nom = QTableWidgetItem(prod['nombre'])
            item_nom.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.tabla_busqueda.setItem(i, 1, item_nom)
            
            item_prec = QTableWidgetItem(f"${prod['precio']:.2f}")
            item_prec.setForeground(QColor("#10B981"))
            self.tabla_busqueda.setItem(i, 2, item_prec)
            
            item_stock = QTableWidgetItem(str(prod['stock']))
            if prod['stock'] <= 0: item_stock.setForeground(QColor("#DC2626")) 
            self.tabla_busqueda.setItem(i, 3, item_stock)

    def agregar_al_carrito(self, item=None):
        if not item: return
        fila = item.row()
        prod = self.tabla_busqueda.item(fila, 0).data(Qt.ItemDataRole.UserRole)
        
        if prod['stock'] <= 0: return self.mostrar_mensaje("Stock Agotado", "Este producto no posee existencias en el almacén seleccionado.", "error")
            
        prod_id = prod['id']
        if prod_id in self.carrito:
            if self.carrito[prod_id]['cantidad'] < prod['stock']: self.carrito[prod_id]['cantidad'] += 1
            else: self.mostrar_mensaje("Límite de Inventario", "No hay más unidades disponibles para agregar.", "error")
        else:
            self.carrito[prod_id] = {
                'id': prod['id'], 'nombre': prod['nombre'], 'precio': prod['precio'],
                'costo': prod['costo'], 'cantidad': 1, 'stock_max': prod['stock']
            }
        
        self.txt_buscador.clear()
        self.txt_buscador.setFocus() 
        self.renderizar_carrito()

    def quitar_del_carrito(self, prod_id):
        if prod_id in self.carrito:
            del self.carrito[prod_id]
            self.renderizar_carrito()
            self.txt_buscador.setFocus()

    def renderizar_carrito(self):
        self.tabla_carrito.setRowCount(0)
        for prod_id, data in self.carrito.items():
            fila = self.tabla_carrito.rowCount()
            self.tabla_carrito.insertRow(fila)
            
            item_id = QTableWidgetItem(f"{data['id']:05d}")
            item_id.setForeground(QColor("#94A3B8"))
            self.tabla_carrito.setItem(fila, 0, item_id)
            
            item_nom = QTableWidgetItem(data['nombre'])
            item_nom.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            item_nom.setToolTip(data['nombre']) 
            self.tabla_carrito.setItem(fila, 1, item_nom)
            
            spin_cant = QSpinBox()
            spin_cant.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
            spin_cant.setMinimum(1)
            spin_cant.setMaximum(int(data['stock_max']))
            spin_cant.setValue(data['cantidad'])
            spin_cant.setAlignment(Qt.AlignmentFlag.AlignCenter)
            spin_cant.setMinimumWidth(60) 
            spin_cant.setFixedHeight(30) 
            spin_cant.setStyleSheet("background-color: #FFFFFF; color: #0F172A; font-weight: bold; font-size: 13px; border: 1px solid #CBD5E1; border-radius: 4px;")
            spin_cant.valueChanged.connect(lambda val, p_id=prod_id: self.actualizar_cantidad(p_id, val))
            
            widget_cant = QWidget()
            layout_cant = QHBoxLayout(widget_cant)
            layout_cant.setContentsMargins(4, 0, 4, 0)
            layout_cant.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout_cant.addWidget(spin_cant)
            self.tabla_carrito.setCellWidget(fila, 2, widget_cant)
            
            spin_precio_base = QDoubleSpinBox()
            spin_precio_base.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
            spin_precio_base.setMinimum(0.01)
            spin_precio_base.setMaximum(999999.99)
            spin_precio_base.setValue(data['precio'])
            spin_precio_base.setPrefix("$ ")
            spin_precio_base.setAlignment(Qt.AlignmentFlag.AlignCenter)
            spin_precio_base.setMinimumWidth(70) 
            spin_precio_base.setFixedHeight(30) 
            spin_precio_base.setStyleSheet("background-color: #FFFFFF; color: #2563EB; font-weight: bold; font-size: 13px; border: 1px solid #CBD5E1; border-radius: 4px;")
            
            spin_precio_sec = QDoubleSpinBox()
            spin_precio_sec.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
            spin_precio_sec.setMinimum(0.01)
            spin_precio_sec.setMaximum(99999999.99)
            spin_precio_sec.setValue(data['precio'] * self.tasa_secundaria)
            spin_precio_sec.setPrefix(f"{self.simbolo_secundario} ")
            spin_precio_sec.setAlignment(Qt.AlignmentFlag.AlignCenter)
            spin_precio_sec.setMinimumWidth(75) 
            spin_precio_sec.setFixedHeight(30) 
            spin_precio_sec.setStyleSheet("background-color: #F8FAFC; color: #2563EB; font-weight: bold; font-size: 13px; border: 1px solid #CBD5E1; border-radius: 4px;")
            
            def crear_conexiones(p_id, c_base, c_sec):
                def cambio_base(val):
                    c_sec.blockSignals(True)
                    c_sec.setValue(val * self.tasa_secundaria)
                    c_sec.blockSignals(False)
                    self.actualizar_precio_manual(p_id, val)
                
                def cambio_sec(val):
                    nuevo_base = val / self.tasa_secundaria
                    c_base.blockSignals(True)
                    c_base.setValue(nuevo_base)
                    c_base.blockSignals(False)
                    self.actualizar_precio_manual(p_id, nuevo_base)
                
                c_base.valueChanged.connect(cambio_base)
                c_sec.valueChanged.connect(cambio_sec)

            crear_conexiones(prod_id, spin_precio_base, spin_precio_sec)
            
            widget_pbase = QWidget()
            layout_pbase = QHBoxLayout(widget_pbase)
            layout_pbase.setContentsMargins(4, 0, 4, 0)
            layout_pbase.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout_pbase.addWidget(spin_precio_base)
            self.tabla_carrito.setCellWidget(fila, 3, widget_pbase)
            
            widget_psec = QWidget()
            layout_psec = QHBoxLayout(widget_psec)
            layout_psec.setContentsMargins(4, 0, 4, 0)
            layout_psec.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout_psec.addWidget(spin_precio_sec)
            self.tabla_carrito.setCellWidget(fila, 4, widget_psec)
            
            subtotal = data['cantidad'] * data['precio']
            item_sub = QTableWidgetItem(f"${subtotal:.2f}")
            item_sub.setForeground(QColor("#0F172A"))
            item_sub.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.tabla_carrito.setItem(fila, 5, item_sub)
            
            btn_quitar = QPushButton()
            btn_quitar.setIcon(qta.icon('fa5s.trash-alt', color='#DC2626'))
            btn_quitar.setIconSize(QSize(16, 16))
            btn_quitar.setFixedSize(32, 32)
            btn_quitar.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_quitar.setStyleSheet("QPushButton { background-color: #FEE2E2; border: none; border-radius: 4px; } QPushButton:hover { background-color: #FECACA; }")
            btn_quitar.clicked.connect(lambda checked, p_id=prod_id: self.quitar_del_carrito(p_id))
            
            widget_btn = QWidget()
            layout_btn = QHBoxLayout(widget_btn)
            layout_btn.setContentsMargins(0, 0, 0, 0)
            layout_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout_btn.addWidget(btn_quitar)
            self.tabla_carrito.setCellWidget(fila, 6, widget_btn)
            
        self.actualizar_totales()

    def actualizar_cantidad(self, prod_id, nueva_cantidad):
        if prod_id in self.carrito:
            self.carrito[prod_id]['cantidad'] = nueva_cantidad
            self.actualizar_subtotales_visuales()
            self.actualizar_totales()

    def actualizar_precio_manual(self, prod_id, nuevo_precio):
        if prod_id in self.carrito:
            self.carrito[prod_id]['precio'] = nuevo_precio
            self.actualizar_subtotales_visuales()
            self.actualizar_totales()

    def actualizar_subtotales_visuales(self):
        for fila in range(self.tabla_carrito.rowCount()):
            item_id = self.tabla_carrito.item(fila, 0)
            if item_id:
                prod_id = int(item_id.text())
                if prod_id in self.carrito:
                    data = self.carrito[prod_id]
                    subtotal = data['cantidad'] * data['precio']
                    
                    item_sub = QTableWidgetItem(f"${subtotal:.2f}")
                    item_sub.setForeground(QColor("#0F172A"))
                    item_sub.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                    self.tabla_carrito.setItem(fila, 5, item_sub)

    def limpiar_carrito(self):
        self.carrito.clear()
        self.renderizar_carrito()
        self.txt_buscador.setFocus()

    def actualizar_totales(self):
        total_base = sum(item['cantidad'] * item['precio'] for item in self.carrito.values())
        moneda_prin = next((m for m in self.monedas if m['es_principal']), None)
        
        if moneda_prin:
            self.lbl_total_base.setText(f"Referencia: {moneda_prin['simbolo']} {total_base:.2f}")
            
        if self.moneda_actual:
            tasa = float(self.moneda_actual['tasa_cambio'])
            total_convertido = total_base * tasa
            self.lbl_total_pagar.setText(f"{self.moneda_actual['simbolo']} {total_convertido:.2f}")

    # ================= 🔥 REDISEÑO TOTAL: MODAL DE PAGO 🔥 =================
    def abrir_modal_pago(self):
        if not self.carrito:
            return self.mostrar_mensaje("Requisito", "No hay productos en la orden de venta.", "error")
            
        idx_cliente = self.combo_clientes.currentIndex()
        if idx_cliente < 0: return self.mostrar_mensaje("Error", "Seleccione un perfil de cliente válido.", "error")

        moneda_base = next((m for m in self.monedas if m['es_principal']), None)
        if not moneda_base: return self.mostrar_mensaje("Error Crítico", "No existe una moneda base configurada en el sistema.", "error")

        almacen_id = self.combo_almacenes.currentData() 
        if not almacen_id: return self.mostrar_mensaje("Error", "Indique el almacén del cual se descontará la mercancía.", "error")

        total_venta_base = sum(item['cantidad'] * item['precio'] for item in self.carrito.values())
        pagos_ingresados = [] 

        dialog = QDialog(self)
        dialog.setWindowTitle("Punto de Cobro")
        dialog.setFixedWidth(800) 
        
        estilo_modal = """
            QDialog { background-color: #F1F5F9; } 
            QLabel { color: #334155; font-size: 14px; } 
            QLineEdit { padding: 12px; border: 1px solid #CBD5E1; border-radius: 6px; color: #0F172A; background-color: #FFFFFF; font-size: 18px; font-weight: bold; text-align: right;} 
            QLineEdit:focus { border: 2px solid #38BDF8; }
            QComboBox { padding: 12px; border: 1px solid #CBD5E1; border-radius: 6px; color: #0F172A; font-size: 14px; font-weight: bold; background-color: #FFFFFF;}
            QComboBox QAbstractItemView { background-color: #FFFFFF; color: #0F172A; selection-background-color: #F8FAFC; }
        """
        dialog.setStyleSheet(estilo_modal)

        layout_principal = QVBoxLayout(dialog)
        layout_principal.setContentsMargins(25, 25, 25, 25)
        layout_principal.setSpacing(20)
        
        lbl_header = QLabel("REGISTRO DE PAGOS")
        lbl_header.setStyleSheet("font-size: 18px; font-weight: 900; color: #0F172A;")
        layout_principal.addWidget(lbl_header)

        layout_cuerpo = QHBoxLayout()
        layout_cuerpo.setSpacing(20)

        tasa_facturacion = float(self.moneda_actual['tasa_cambio'])
        total_venta_mostrado = total_venta_base * tasa_facturacion

        # --- PANEL IZQUIERDO (INGRESO DE PAGO) ---
        panel_izq = QFrame()
        panel_izq.setStyleSheet("background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 8px;")
        layout_izq = QVBoxLayout(panel_izq)
        layout_izq.setContentsMargins(20, 20, 20, 20)
        layout_izq.setSpacing(15)
        
        lbl_titulo_izq = QLabel("1. MÉTODO DE PAGO")
        lbl_titulo_izq.setStyleSheet("font-size: 12px; font-weight: bold; color: #64748B; margin-bottom: 5px;")
        layout_izq.addWidget(lbl_titulo_izq)
        
        layout_izq.addWidget(QLabel("Moneda Recibida:", styleSheet="font-weight: bold;"))
        combo_moneda_pago = QComboBox()
        for m in self.monedas:
            combo_moneda_pago.addItem(f"{m['nombre']} ({m['simbolo']})", m)
        layout_izq.addWidget(combo_moneda_pago)
        
        layout_izq.addWidget(QLabel("Forma de Pago:", styleSheet="font-weight: bold; margin-top: 5px;"))
        combo_metodo_pago = QComboBox()
        layout_izq.addWidget(combo_metodo_pago)
        
        layout_izq.addWidget(QLabel("Monto Recibido:", styleSheet="font-weight: bold; margin-top: 5px;"))
        txt_monto_pago = QLineEdit()
        txt_monto_pago.setStyleSheet("font-size: 24px; font-weight: 900; color: #10B981;")
        layout_izq.addWidget(txt_monto_pago)
        
        btn_agregar_pago = QPushButton("Agregar Pago al Recibo")
        btn_agregar_pago.setStyleSheet("background-color: #0F172A; color: white; border-radius: 6px; font-weight: bold; font-size: 15px; padding: 15px; margin-top: 10px;")
        btn_agregar_pago.setCursor(Qt.CursorShape.PointingHandCursor)
        layout_izq.addWidget(btn_agregar_pago)
        
        layout_izq.addStretch()

        # --- PANEL DERECHO (RESUMEN) ---
        panel_der = QFrame()
        panel_der.setStyleSheet("background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 8px;")
        layout_der = QVBoxLayout(panel_der)
        layout_der.setContentsMargins(20, 20, 20, 20)
        layout_der.setSpacing(10)
        
        lbl_titulo_der = QLabel("2. RESUMEN DE LA CUENTA")
        lbl_titulo_der.setStyleSheet("font-size: 12px; font-weight: bold; color: #64748B; margin-bottom: 5px;")
        layout_der.addWidget(lbl_titulo_der)
        
        lbl_resumen = QLabel(f"{self.moneda_actual['simbolo']} {total_venta_mostrado:.2f}")
        lbl_resumen.setStyleSheet("font-size: 40px; color: #0F172A; text-align: center; font-weight: 900; margin-bottom: 10px; letter-spacing: -1px;")
        lbl_resumen.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_der.addWidget(lbl_resumen)

        layout_der.addWidget(QLabel("Pagos Ingresados:", styleSheet="font-weight: bold; font-size: 12px; color: #64748B;"))
        tabla_pagos = QTableWidget()
        tabla_pagos.setColumnCount(4)
        tabla_pagos.setHorizontalHeaderLabels(["DIVISA", "MÉTODO", "MONTO", ""])
        
        header_pago = tabla_pagos.horizontalHeader()
        header_pago.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_pago.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header_pago.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header_pago.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        tabla_pagos.setColumnWidth(3, 40)
        header_pago.setStretchLastSection(False)
        
        tabla_pagos.verticalHeader().setVisible(False)
        tabla_pagos.verticalHeader().setDefaultSectionSize(40)
        tabla_pagos.setFixedHeight(120)
        tabla_pagos.setStyleSheet("""
            QTableWidget { background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; color: #334155; font-size: 13px; font-weight: bold; }
            QHeaderView::section { background-color: #F8FAFC; color: #64748B; font-weight: bold; font-size: 11px; padding: 8px; border: none; text-transform: uppercase;}
        """)
        layout_der.addWidget(tabla_pagos)

        self.lbl_restante = QLabel("FALTA POR PAGAR:\n$ 0.00   -   Bs 0.00")
        self.lbl_restante.setStyleSheet("font-size: 18px; font-weight: 900; color: #DC2626; margin-top: 10px;")
        self.lbl_restante.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_der.addWidget(self.lbl_restante)
        
        layout_cuerpo.addWidget(panel_izq, stretch=45)
        layout_cuerpo.addWidget(panel_der, stretch=55)
        layout_principal.addLayout(layout_cuerpo)

        # --- BOTONES DE CIERRE DE MODAL ---
        fila_botones_finales = QHBoxLayout()
        
        btn_credito = QPushButton("OTORGAR A CRÉDITO")
        btn_credito.setStyleSheet("""
            QPushButton { background-color: #3B82F6; color: white; border-radius: 6px; font-weight: bold; font-size: 14px; padding: 15px; } 
            QPushButton:disabled { background-color: #CBD5E1; color: #94A3B8;}
            QPushButton:hover:!disabled { background-color: #2563EB; }
        """)
        
        self.btn_confirmar_final = QPushButton("GENERAR FACTURA")
        self.btn_confirmar_final.setEnabled(False)
        self.btn_confirmar_final.setStyleSheet("""
            QPushButton { background-color: #10B981; color: white; border-radius: 6px; font-weight: bold; font-size: 14px; padding: 15px; } 
            QPushButton:disabled { background-color: #CBD5E1; color: #94A3B8;}
            QPushButton:hover:!disabled { background-color: #059669; }
        """)
        
        fila_botones_finales.addWidget(btn_credito)
        fila_botones_finales.addWidget(self.btn_confirmar_final)
        layout_principal.addLayout(fila_botones_finales)

        # ---- FUNCIONES INTERNAS DEL MODAL ----
        def sugerir_monto():
            pagado_base = sum((p['monto'] / p['tasa']) for p in pagos_ingresados)
            resta_base = total_venta_base - pagado_base
            moneda_sel = combo_moneda_pago.currentData()
            
            if moneda_sel and resta_base > 0:
                sugerido = resta_base * float(moneda_sel['tasa_cambio'])
                txt_monto_pago.setText(f"{sugerido:.2f}")
            else:
                txt_monto_pago.setText("0.00")

        def actualizar_metodos():
            moneda_sel = combo_moneda_pago.currentData()
            combo_metodo_pago.clear()
            if not moneda_sel: return
            for mp in self.metodos_pago:
                if mp['moneda_id'] == moneda_sel['id']:
                    combo_metodo_pago.addItem(mp['nombre'], mp)
            sugerir_monto() 

        def renderizar_tabla():
            tabla_pagos.setRowCount(0)
            pagado_base = 0.0

            for i, pago in enumerate(pagos_ingresados):
                tabla_pagos.insertRow(i)
                tabla_pagos.setItem(i, 0, QTableWidgetItem(pago['simbolo']))
                tabla_pagos.setItem(i, 1, QTableWidgetItem(pago['nombre_metodo']))
                
                item_monto = QTableWidgetItem(f"{pago['monto']:.2f}")
                item_monto.setForeground(QColor("#0F172A"))
                tabla_pagos.setItem(i, 2, item_monto)

                btn_quitar = QPushButton()
                btn_quitar.setIcon(qta.icon('fa5s.times', color='#DC2626'))
                btn_quitar.setStyleSheet("background-color: transparent; border: none;")
                btn_quitar.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_quitar.clicked.connect(lambda checked, idx=i: quitar_pago(idx))
                
                widget_del = QWidget()
                l_del = QHBoxLayout(widget_del)
                l_del.setContentsMargins(0,0,0,0)
                l_del.setAlignment(Qt.AlignmentFlag.AlignCenter)
                l_del.addWidget(btn_quitar)
                tabla_pagos.setCellWidget(i, 3, widget_del)

                pagado_base += (pago['monto'] / pago['tasa'])

            resta_base = total_venta_base - pagado_base
            tasa_fac = float(self.moneda_actual['tasa_cambio'])
            
            # 🔥 CÁLCULO DE VUELTO O DEUDA EN AMBAS MONEDAS 🔥
            if resta_base <= 0.01:
                vuelto_base = abs(resta_base)
                vuelto_principal = vuelto_base * tasa_fac
                vuelto_secundario = vuelto_base * self.tasa_secundaria
                
                texto_vuelto = f"VUELTO A ENTREGAR:\n{self.moneda_actual['simbolo']} {vuelto_principal:.2f}   -   {self.simbolo_secundario} {vuelto_secundario:.2f}"
                self.lbl_restante.setText(texto_vuelto)
                self.lbl_restante.setStyleSheet("font-size: 18px; font-weight: 900; color: #10B981;")
                
                self.btn_confirmar_final.setEnabled(True)
                btn_credito.setEnabled(False) 
                self.btn_confirmar_final.setFocus() 
                txt_monto_pago.setText("0.00")
            else:
                resta_principal = resta_base * tasa_fac
                resta_secundaria = resta_base * self.tasa_secundaria
                
                texto_falta = f"FALTA POR PAGAR:\n{self.moneda_actual['simbolo']} {resta_principal:.2f}   -   {self.simbolo_secundario} {resta_secundaria:.2f}"
                self.lbl_restante.setText(texto_falta)
                self.lbl_restante.setStyleSheet("font-size: 18px; font-weight: 900; color: #DC2626;")
                
                self.btn_confirmar_final.setEnabled(False)
                btn_credito.setEnabled(True if self.cliente_actual['id'] != 1 else False) 
                sugerir_monto()
                txt_monto_pago.setFocus() 

        def quitar_pago(idx):
            pagos_ingresados.pop(idx)
            renderizar_tabla()

        def agregar_pago():
            try:
                monto = float(txt_monto_pago.text())
                if monto <= 0: return
                
                metodo = combo_metodo_pago.currentData()
                moneda = combo_moneda_pago.currentData()
                if not metodo: return self.mostrar_mensaje("Error", "Seleccione un método válido.", "error")

                pagos_ingresados.append({
                    'metodo_id': metodo['id'],
                    'nombre_metodo': metodo['nombre'],
                    'simbolo': moneda['simbolo'],
                    'monto': monto,
                    'tasa': float(moneda['tasa_cambio'])
                })
                renderizar_tabla()
            except ValueError:
                pass

        def confirmar(es_credito=False):
            vencimiento = None
            if es_credito:
                if self.cliente_actual['id'] == 1: 
                    return self.mostrar_mensaje("Operación Restringida", "El 'Cliente General' no es sujeto de crédito. Asigne un cliente nominal.", "error")
                
                dias, ok = QInputDialog.getInt(dialog, "Condiciones de Crédito", "¿Cuántos días de plazo otorgará para el pago?", 15, 1, 365)
                if not ok: return
                vencimiento = (datetime.now() + timedelta(days=dias)).strftime('%Y-%m-%d %H:%M:%S')

            exito, resp = db_sales.procesar_venta_completa(
                self.cliente_actual['id'], 
                self.moneda_actual['id'], 
                float(self.moneda_actual['tasa_cambio']),
                total_venta_base, 
                list(self.carrito.values()), 
                pagos_ingresados, 
                almacen_id,
                self.sesion_caja_actual['id'],
                es_credito=es_credito, 
                fecha_vencimiento=vencimiento
            )
            if exito:
                self.generar_ticket(resp)
                self.limpiar_carrito()
                dialog.accept()
            else:
                self.mostrar_mensaje("Fallo Transaccional", str(resp), "error")

        combo_moneda_pago.currentIndexChanged.connect(actualizar_metodos)
        btn_agregar_pago.clicked.connect(agregar_pago)
        self.btn_confirmar_final.clicked.connect(lambda: confirmar(False))
        btn_credito.clicked.connect(lambda: confirmar(True))
        
        txt_monto_pago.returnPressed.connect(agregar_pago)

        actualizar_metodos() 
        renderizar_tabla() 
        txt_monto_pago.setFocus() 
        dialog.exec()

    # ================= CLIENTE RÁPIDO =================
    def abrir_modal_cliente_rapido(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Registro Express")
        dialog.setFixedWidth(350)
        dialog.setStyleSheet("""
            QDialog { background-color: #FFFFFF; } 
            QLabel { color: #334155; font-weight: bold; font-size: 13px; } 
            QLineEdit { padding: 10px; border: 1px solid #CBD5E1; border-radius: 4px; color: #0F172A; background-color: #F8FAFC; font-size: 14px; } 
            QLineEdit:focus { border: 2px solid #38BDF8; }
        """)
        layout_form = QFormLayout(dialog)
        layout_form.setSpacing(15)
        layout_form.setContentsMargins(25, 25, 25, 25)
        
        campo_doc = QLineEdit()
        campo_nom = QLineEdit()
        campo_tel = QLineEdit()
        layout_form.addRow("Documento / RIF:", campo_doc)
        layout_form.addRow("Razón Social:", campo_nom)
        layout_form.addRow("Teléfono:", campo_tel)
        
        box_botones = QHBoxLayout()
        btn_cancelar = QPushButton("Descartar")
        btn_cancelar.setStyleSheet("padding: 10px 15px; background-color: #F1F5F9; color: #475569; border-radius: 6px; font-weight: bold;")
        btn_guardar = QPushButton("Registrar")
        btn_guardar.setStyleSheet("padding: 10px 15px; background-color: #0F172A; color: white; border-radius: 6px; font-weight: bold;")
        btn_cancelar.clicked.connect(dialog.reject)
        
        def guardar():
            doc = campo_doc.text().strip()
            nom = campo_nom.text().strip()
            if not doc or not nom: return self.mostrar_mensaje("Aviso", "Documento y Nombre son campos requeridos.", "error")
            exito, msg = db_customers.guardar_cliente(doc, nom, campo_tel.text().strip(), "N/A", 1)
            if exito:
                self.cargar_configuracion() 
                idx = self.combo_clientes.findText(nom)
                if idx >= 0: self.combo_clientes.setCurrentIndex(idx)
                dialog.accept()
            else:
                self.mostrar_mensaje("Error", msg, "error")
                
        btn_guardar.clicked.connect(guardar)
        box_botones.addWidget(btn_cancelar)
        box_botones.addWidget(btn_guardar)
        layout_form.addRow(box_botones)
        dialog.exec()