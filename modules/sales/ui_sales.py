import os
import webbrowser 
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QComboBox, QFrame, QAbstractItemView, QMessageBox, 
                             QSpinBox, QDoubleSpinBox, QDialog, QFormLayout, QCompleter, QStackedWidget, QInputDialog)
from PyQt6.QtCore import Qt
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

    def setup_ui(self):
        layout_maestro = QVBoxLayout(self)
        layout_maestro.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget()
        layout_maestro.addWidget(self.stack)
        
        # ================= VISTA 1: CAJA CERRADA =================
        self.vista_cerrada = QWidget()
        layout_cerrada = QVBoxLayout(self.vista_cerrada)
        layout_cerrada.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_bloqueo = QLabel("🔒 LA CAJA ESTÁ CERRADA")
        lbl_bloqueo.setStyleSheet("font-size: 36px; font-weight: 900; color: #DC2626;")
        lbl_bloqueo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_sub_bloqueo = QLabel("Debes abrir un turno e ingresar el fondo de caja para empezar a facturar.")
        lbl_sub_bloqueo.setStyleSheet("font-size: 16px; color: #64748B; margin-bottom: 20px;")
        lbl_sub_bloqueo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        btn_abrir_caja = QPushButton("💰 ABRIR TURNO DE CAJA")
        btn_abrir_caja.setFixedSize(300, 60)
        btn_abrir_caja.setStyleSheet("QPushButton { background-color: #2563EB; color: white; border-radius: 8px; font-weight: 900; font-size: 18px; } QPushButton:hover { background-color: #1D4ED8; }")
        btn_abrir_caja.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_abrir_caja.clicked.connect(self.modal_abrir_caja)
        
        layout_cerrada.addWidget(lbl_bloqueo)
        layout_cerrada.addWidget(lbl_sub_bloqueo)
        layout_cerrada.addWidget(btn_abrir_caja, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # ================= VISTA 2: TERMINAL DE VENTAS (POS) =================
        self.vista_pos = QWidget()
        layout_pos_principal = QVBoxLayout(self.vista_pos)
        layout_pos_principal.setContentsMargins(30, 30, 30, 30)
        
        cabecera_pos = QHBoxLayout()
        lbl_titulo = QLabel("🛒 Terminal de Ventas (POS)")
        lbl_titulo.setStyleSheet("font-size: 26px; font-weight: 900; color: #0F172A;")
        
        cabecera_pos.addWidget(lbl_titulo)
        cabecera_pos.addStretch()

        # 🔥 BOTÓN DE REIMPRIMIR FACTURA
        btn_reimprimir = QPushButton("🖨️ Reimprimir")
        btn_reimprimir.setStyleSheet("padding: 10px 20px; background-color: #3B82F6; color: white; border-radius: 6px; font-weight: bold; font-size: 14px; margin-right: 15px;")
        btn_reimprimir.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_reimprimir.clicked.connect(self.modal_reimprimir)
        cabecera_pos.addWidget(btn_reimprimir)

        btn_cerrar_caja = QPushButton("🔒 CERRAR TURNO (REPORTE Z)")
        btn_cerrar_caja.setStyleSheet("padding: 10px 20px; background-color: #FEF2F2; color: #DC2626; border: 2px solid #DC2626; border-radius: 6px; font-weight: bold; font-size: 14px;")
        btn_cerrar_caja.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cerrar_caja.clicked.connect(self.modal_cerrar_caja)
        
        cabecera_pos.addWidget(btn_cerrar_caja)
        layout_pos_principal.addLayout(cabecera_pos)
        
        cuerpo_pos = QHBoxLayout()
        cuerpo_pos.setSpacing(20)
        
        # === PANEL IZQUIERDO ===
        panel_izq = QFrame()
        layout_izq = QVBoxLayout(panel_izq)
        layout_izq.setContentsMargins(0, 10, 0, 0)
        
        self.txt_buscador = QLineEdit()
        self.txt_buscador.setPlaceholderText("🔎 Buscar producto... (Flecha Abajo para seleccionar, Enter para agregar)")
        self.txt_buscador.setFixedHeight(45)
        self.txt_buscador.setStyleSheet("padding: 5px 15px; border: 2px solid #CBD5E1; border-radius: 6px; font-size: 15px; color: #000000; background-color: #FFFFFF;")
        self.txt_buscador.textChanged.connect(self.buscar_productos)
        self.txt_buscador.installEventFilter(self) 
        layout_izq.addWidget(self.txt_buscador)
        
        self.tabla_busqueda = QTableWidget()
        self.tabla_busqueda.setColumnCount(4)
        self.tabla_busqueda.setHorizontalHeaderLabels(["ID", "DESCRIPCIÓN", "PRECIO", "STOCK"])
        self.tabla_busqueda.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla_busqueda.verticalHeader().setVisible(False)
        self.tabla_busqueda.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_busqueda.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla_busqueda.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_busqueda.setFixedHeight(150) 
        self.tabla_busqueda.setStyleSheet("QTableWidget { background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px; color: #000000; font-weight: bold; font-size: 13px; }")
        self.tabla_busqueda.itemDoubleClicked.connect(self.agregar_al_carrito)
        self.tabla_busqueda.installEventFilter(self) 
        layout_izq.addWidget(self.tabla_busqueda)
        
        lbl_carrito = QLabel("📦 Carrito de Compras")
        lbl_carrito.setStyleSheet("font-size: 18px; font-weight: 900; color: #0F172A; margin-top: 10px;")
        layout_izq.addWidget(lbl_carrito)
        
        self.tabla_carrito = QTableWidget()
        self.tabla_carrito.setColumnCount(7) 
        self.tabla_carrito.setHorizontalHeaderLabels(["ID", "PRODUCTO", "CANTIDAD", "PRECIO ($)", "PRECIO (Bs)", "SUBTOTAL ($)", "QUITAR"])
        self.tabla_carrito.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla_carrito.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla_carrito.verticalHeader().setVisible(False)
        
        # 🔥 MEJORA DE ALTURA EN EL CARRITO
        self.tabla_carrito.verticalHeader().setDefaultSectionSize(50) 
        self.tabla_carrito.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_carrito.setStyleSheet("QTableWidget { background-color: #FFFFFF; color: #000000; border: 1px solid #E2E8F0; border-radius: 6px; font-size: 14px; font-weight: bold; } QTableWidget::item { padding: 5px; border-bottom: 1px solid #F1F5F9; } QHeaderView::section { background-color: #F8FAFC; color: #64748B; font-weight: bold; padding: 10px; border: none; border-bottom: 2px solid #E2E8F0; font-size: 12px; }")
        layout_izq.addWidget(self.tabla_carrito)
        
        btn_limpiar = QPushButton("🧹 Vaciar TODO el Carrito")
        btn_limpiar.setStyleSheet("padding: 10px 15px; background-color: #FEF2F2; color: #DC2626; border-radius: 6px; font-weight: bold; font-size: 14px;")
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
        
        estilo_dropdown = "QComboBox { padding: 10px; border: 1px solid #CBD5E1; border-radius: 6px; color: #000000; font-size: 15px; background-color: #F8FAFC; font-weight: bold; } QComboBox QAbstractItemView { background-color: #FFFFFF; color: #000000; font-size: 14px; selection-background-color: #EFF6FF; }"
        estilo_titulo_opcion = "font-size: 14px; font-weight: 900; color: #64748B; margin-top: 5px;"
        
        layout_der.addWidget(QLabel("🏭 Almacén de Despacho:", styleSheet=estilo_titulo_opcion))
        self.combo_almacenes = QComboBox()
        self.combo_almacenes.setStyleSheet(estilo_dropdown)
        self.combo_almacenes.currentIndexChanged.connect(self.cambiar_almacen)
        layout_der.addWidget(self.combo_almacenes)

        layout_der.addWidget(QLabel("👤 Cliente:", styleSheet=estilo_titulo_opcion))
        fila_cliente = QHBoxLayout()
        self.combo_clientes = QComboBox()
        self.combo_clientes.setEditable(True) 
        self.combo_clientes.setStyleSheet(estilo_dropdown)
        self.combo_clientes.currentIndexChanged.connect(self.cambiar_cliente)
        
        btn_nuevo_cliente = QPushButton("➕")
        btn_nuevo_cliente.setStyleSheet("background-color: #2563EB; color: white; border-radius: 6px; font-weight: bold; font-size: 16px; padding: 8px;")
        btn_nuevo_cliente.setFixedWidth(40)
        btn_nuevo_cliente.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_nuevo_cliente.clicked.connect(self.abrir_modal_cliente_rapido)
        
        fila_cliente.addWidget(self.combo_clientes)
        fila_cliente.addWidget(btn_nuevo_cliente)
        layout_der.addLayout(fila_cliente)
        
        layout_der.addWidget(QLabel("🏷️ Tarifa a Aplicar:", styleSheet=estilo_titulo_opcion))
        self.combo_tarifas = QComboBox()
        self.combo_tarifas.setStyleSheet(estilo_dropdown)
        self.combo_tarifas.currentIndexChanged.connect(self.cambiar_tarifa)
        layout_der.addWidget(self.combo_tarifas)
        
        layout_der.addWidget(QLabel("💵 Moneda de Facturación:", styleSheet=estilo_titulo_opcion))
        self.combo_monedas = QComboBox()
        self.combo_monedas.setStyleSheet(estilo_dropdown)
        self.combo_monedas.currentIndexChanged.connect(self.cambiar_moneda)
        layout_der.addWidget(self.combo_monedas)
        
        layout_der.addStretch()
        
        panel_total = QFrame()
        panel_total.setStyleSheet("background-color: #F8FAFC; border-radius: 8px; border: 1px solid #E2E8F0;")
        layout_totales = QVBoxLayout(panel_total)
        
        self.lbl_total_base = QLabel("Referencia: $0.00")
        self.lbl_total_base.setStyleSheet("font-size: 16px; color: #64748B; font-weight: bold;")
        self.lbl_total_base.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_total_pagar = QLabel("$0.00") 
        self.lbl_total_pagar.setStyleSheet("font-size: 40px; color: #16A34A; font-weight: 900;")
        self.lbl_total_pagar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout_totales.addWidget(self.lbl_total_base)
        layout_totales.addWidget(self.lbl_total_pagar)
        layout_der.addWidget(panel_total)
        
        btn_procesar = QPushButton("💰 COBRAR (F12)")
        btn_procesar.setFixedHeight(60)
        btn_procesar.setStyleSheet("QPushButton { background-color: #16A34A; color: white; border-radius: 8px; font-weight: 900; font-size: 20px; } QPushButton:hover { background-color: #15803D; }")
        btn_procesar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_procesar.clicked.connect(self.abrir_modal_pago)
        layout_der.addWidget(btn_procesar)
        
        # BOTONES DE PRESUPUESTO
        fila_presupuestos = QHBoxLayout()
        btn_guardar_presupuesto = QPushButton("📝 Crear\nPresupuesto")
        btn_guardar_presupuesto.setFixedHeight(45)
        btn_guardar_presupuesto.setStyleSheet("QPushButton { background-color: #3B82F6; color: white; border-radius: 6px; font-weight: bold; font-size: 14px; } QPushButton:hover { background-color: #2563EB; }")
        btn_guardar_presupuesto.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_guardar_presupuesto.clicked.connect(self.guardar_presupuesto)
        
        btn_cargar_presupuesto = QPushButton("📂 Buscar\nPresupuesto")
        btn_cargar_presupuesto.setFixedHeight(45)
        btn_cargar_presupuesto.setStyleSheet("QPushButton { background-color: #F59E0B; color: white; border-radius: 6px; font-weight: bold; font-size: 14px; } QPushButton:hover { background-color: #D97706; }")
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
        dialog.setWindowTitle("Apertura de Caja")
        dialog.setFixedWidth(350)
        dialog.setStyleSheet("QDialog { background-color: #FFFFFF; } QLabel { color: #0F172A; font-weight: bold; font-size: 14px; }")
        layout = QVBoxLayout(dialog)
        
        layout.addWidget(QLabel("¿Con cuánto efectivo en la moneda principal estás abriendo la caja para dar vueltos?"))
        
        spin_monto = QDoubleSpinBox()
        spin_monto.setMaximum(99999.99)
        spin_monto.setPrefix("$ ")
        spin_monto.setStyleSheet("padding: 10px; border: 1px solid #CBD5E1; border-radius: 4px; color: #16A34A; background-color: #F8FAFC; font-size: 20px; font-weight: bold;")
        layout.addWidget(spin_monto)
        
        btn_abrir = QPushButton("✅ ABRIR CAJA")
        btn_abrir.setStyleSheet("padding: 15px; background-color: #16A34A; color: white; border-radius: 6px; font-weight: bold; font-size: 16px;")
        btn_abrir.setCursor(Qt.CursorShape.PointingHandCursor)
        
        def procesar_apertura():
            exito, msg = db_sales.abrir_caja(spin_monto.value(), session.usuario_actual['id'])
            if exito:
                QMessageBox.information(self, "Caja Abierta", msg)
                dialog.accept()
                self.verificar_estado_caja()
            else:
                QMessageBox.critical(self, "Error", msg)
                
        btn_abrir.clicked.connect(procesar_apertura)
        layout.addWidget(btn_abrir)
        dialog.exec()

    def modal_cerrar_caja(self):
        if len(self.carrito) > 0:
            return QMessageBox.warning(self, "Atención", "Debes vaciar el carrito o terminar la venta actual antes de cerrar la caja.")
            
        dialog = QDialog(self)
        dialog.setWindowTitle("Cierre de Caja (Reporte Z)")
        dialog.setFixedWidth(450)
        dialog.setStyleSheet("QDialog { background-color: #FFFFFF; } QLabel { color: #0F172A; font-size: 14px; }")
        layout = QVBoxLayout(dialog)
        
        lbl_titulo = QLabel("<b>RESUMEN DE VENTAS DEL TURNO</b>")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_titulo)
        
        resumen = db_sales.obtener_resumen_caja(self.sesion_caja_actual['id'])
        monto_ini = self.sesion_caja_actual['monto_inicial']
        
        tabla = QTableWidget()
        tabla.setColumnCount(2)
        tabla.setHorizontalHeaderLabels(["CONCEPTO", "MONTO RECAUDADO"])
        tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tabla.verticalHeader().setVisible(False)
        tabla.setStyleSheet("QTableWidget { background-color: #F8FAFC; color: black; font-weight: bold; }")
        
        tabla.setRowCount(len(resumen) + 1)
        
        tabla.setItem(0, 0, QTableWidgetItem("💵 Fondo de Caja (Inicial)"))
        tabla.setItem(0, 1, QTableWidgetItem(f"$ {monto_ini:.2f}"))
        
        fila_actual = 1
        for fila in resumen:
            tabla.setItem(fila_actual, 0, QTableWidgetItem(fila['metodo']))
            item_val = QTableWidgetItem(f"{fila['simbolo']} {fila['total']:.2f}")
            item_val.setForeground(QColor("#16A34A"))
            tabla.setItem(fila_actual, 1, item_val)
            fila_actual += 1
            
        layout.addWidget(tabla)
        
        btn_cerrar = QPushButton("🔒 CONFIRMAR Y CERRAR TURNO")
        btn_cerrar.setStyleSheet("padding: 15px; background-color: #DC2626; color: white; border-radius: 6px; font-weight: bold; font-size: 16px;")
        btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        
        def procesar_cierre():
            respuesta = QMessageBox.question(dialog, "Confirmar", "¿Estás seguro de cerrar la caja? Ya no podrás facturar en este turno.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if respuesta == QMessageBox.StandardButton.Yes:
                exito, msg = db_sales.cerrar_caja(self.sesion_caja_actual['id'])
                if exito:
                    QMessageBox.information(self, "Caja Cerrada", "El turno ha finalizado correctamente.")
                    dialog.accept()
                    self.verificar_estado_caja()
                else:
                    QMessageBox.critical(self, "Error", msg)
                    
        btn_cerrar.clicked.connect(procesar_cierre)
        layout.addWidget(btn_cerrar)
        dialog.exec()

    # ================= LOGICA DE REIMPRESIÓN =================
    def modal_reimprimir(self):
        ventas = db_sales.obtener_ventas_recientes()
        if not ventas:
            return QMessageBox.information(self, "Aviso", "No hay ventas registradas en el historial.")

        dialog = QDialog(self)
        dialog.setWindowTitle("Reimprimir Factura")
        dialog.setFixedWidth(550)
        dialog.setStyleSheet("QDialog { background-color: #FFFFFF; }")
        layout = QVBoxLayout(dialog)

        lbl = QLabel("Selecciona la factura que deseas reimprimir:")
        lbl.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(lbl)

        tabla = QTableWidget()
        tabla.setColumnCount(4)
        tabla.setHorizontalHeaderLabels(["NRO.", "FECHA", "CLIENTE", "TOTAL ($)"])
        tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tabla.setStyleSheet("QTableWidget { background-color: #F8FAFC; color: black; font-weight: bold; }")

        tabla.setRowCount(len(ventas))
        for i, v in enumerate(ventas):
            item_id = QTableWidgetItem(f"{v['id']:06d}")
            item_id.setData(Qt.ItemDataRole.UserRole, v['id'])
            tabla.setItem(i, 0, item_id)
            tabla.setItem(i, 1, QTableWidgetItem(v['fecha_hora'].split(" ")[0]))
            tabla.setItem(i, 2, QTableWidgetItem(v['cliente_nombre']))
            tabla.setItem(i, 3, QTableWidgetItem(f"{v['total_venta']:.2f}"))

        layout.addWidget(tabla)

        btn_imprimir = QPushButton("🖨️ Imprimir Seleccionada")
        btn_imprimir.setStyleSheet("padding: 10px; background-color: #2563EB; color: white; border-radius: 6px; font-weight: bold; font-size: 14px;")
        btn_imprimir.setCursor(Qt.CursorShape.PointingHandCursor)

        def imprimir():
            filas = tabla.selectedItems()
            if not filas: return QMessageBox.warning(dialog, "Error", "Selecciona una factura de la lista.")
            v_id = tabla.item(filas[0].row(), 0).data(Qt.ItemDataRole.UserRole)
            self.generar_ticket(v_id)
            dialog.accept()

        btn_imprimir.clicked.connect(imprimir)
        layout.addWidget(btn_imprimir)
        dialog.exec()

    # ================= LOGICA DE PRESUPUESTOS =================
    def guardar_presupuesto(self):
        if not self.carrito:
            return QMessageBox.warning(self, "Carrito Vacío", "Agrega productos para crear un presupuesto.")
        
        idx_cliente = self.combo_clientes.currentIndex()
        if idx_cliente < 0: return QMessageBox.warning(self, "Error", "Selecciona un cliente válido.")
        
        total_venta_base = sum(item['cantidad'] * item['precio'] for item in self.carrito.values())
        
        exito, resp = db_sales.guardar_presupuesto(self.cliente_actual['id'], self.moneda_actual['id'], total_venta_base, list(self.carrito.values()))
        
        if exito:
            self.generar_ticket_presupuesto(resp)
            self.limpiar_carrito()
            QMessageBox.information(self, "Éxito", f"Presupuesto guardado correctamente.")
        else:
            QMessageBox.critical(self, "Error", str(resp))

    def abrir_modal_buscar_presupuesto(self):
        presupuestos = db_sales.obtener_presupuestos_activos()
        if not presupuestos:
            return QMessageBox.information(self, "Aviso", "No hay presupuestos pendientes activos.")
            
        dialog = QDialog(self)
        dialog.setWindowTitle("Buscar Presupuesto Pendiente")
        dialog.setFixedWidth(500)
        dialog.setStyleSheet("QDialog { background-color: #FFFFFF; }")
        layout = QVBoxLayout(dialog)
        
        tabla = QTableWidget()
        tabla.setColumnCount(4)
        tabla.setHorizontalHeaderLabels(["NRO.", "FECHA", "CLIENTE", "TOTAL ESTIMADO ($)"])
        tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tabla.setStyleSheet("QTableWidget { background-color: #F8FAFC; color: black; font-weight: bold; }")
        
        tabla.setRowCount(len(presupuestos))
        for i, p in enumerate(presupuestos):
            item_id = QTableWidgetItem(f"{p['id']:06d}")
            item_id.setData(Qt.ItemDataRole.UserRole, p['id'])
            tabla.setItem(i, 0, item_id)
            tabla.setItem(i, 1, QTableWidgetItem(p['fecha_hora'].split(" ")[0]))
            tabla.setItem(i, 2, QTableWidgetItem(p['cliente_nombre']))
            tabla.setItem(i, 3, QTableWidgetItem(f"{p['total_presupuesto']:.2f}"))
            
        layout.addWidget(tabla)
        
        btn_cargar = QPushButton("📥 Cargar al Carrito (y Facturar)")
        btn_cargar.setStyleSheet("padding: 10px; background-color: #2563EB; color: white; border-radius: 6px; font-weight: bold;")
        
        def cargar():
            filas = tabla.selectedItems()
            if not filas: return QMessageBox.warning(dialog, "Error", "Selecciona un presupuesto de la lista.")
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
            QMessageBox.information(self, "Cargado", "El presupuesto se ha transferido al carrito. Ahora puedes proceder a Cobrar.")
            
        btn_cargar.clicked.connect(cargar)
        layout.addWidget(btn_cargar)
        dialog.exec()

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
            respuesta = QMessageBox.question(
                self, "Advertencia", 
                "Cambiar de almacén vaciará el carrito actual. ¿Deseas continuar?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if respuesta == QMessageBox.StandardButton.Yes:
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
            item_id = QTableWidgetItem(str(prod['id']))
            item_id.setData(Qt.ItemDataRole.UserRole, prod) 
            self.tabla_busqueda.setItem(i, 0, item_id)
            self.tabla_busqueda.setItem(i, 1, QTableWidgetItem(prod['nombre']))
            self.tabla_busqueda.setItem(i, 2, QTableWidgetItem(f"${prod['precio']:.2f}"))
            item_stock = QTableWidgetItem(str(prod['stock']))
            if prod['stock'] <= 0: item_stock.setForeground(QColor("#DC2626")) 
            self.tabla_busqueda.setItem(i, 3, item_stock)

    def agregar_al_carrito(self, item=None):
        if not item: return
        fila = item.row()
        prod = self.tabla_busqueda.item(fila, 0).data(Qt.ItemDataRole.UserRole)
        
        if prod['stock'] <= 0: return QMessageBox.warning(self, "Sin Stock", "No puedes vender un producto sin stock en este almacén.")
            
        prod_id = prod['id']
        if prod_id in self.carrito:
            if self.carrito[prod_id]['cantidad'] < prod['stock']: self.carrito[prod_id]['cantidad'] += 1
            else: QMessageBox.warning(self, "Límite", "Límite de stock alcanzado.")
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
            
            self.tabla_carrito.setItem(fila, 0, QTableWidgetItem(str(data['id'])))
            self.tabla_carrito.setItem(fila, 1, QTableWidgetItem(data['nombre']))
            
            spin_cant = QSpinBox()
            spin_cant.setMinimum(1)
            spin_cant.setMaximum(int(data['stock_max']))
            spin_cant.setValue(data['cantidad'])
            spin_cant.setStyleSheet("background-color: white; color: black; font-weight: bold;")
            spin_cant.valueChanged.connect(lambda val, p_id=prod_id: self.actualizar_cantidad(p_id, val))
            self.tabla_carrito.setCellWidget(fila, 2, spin_cant)
            
            spin_precio_base = QDoubleSpinBox()
            spin_precio_sec = QDoubleSpinBox()
            
            spin_precio_base.setMinimum(0.01)
            spin_precio_base.setMaximum(999999.99)
            spin_precio_base.setValue(data['precio'])
            spin_precio_base.setPrefix("$ ")
            spin_precio_base.setStyleSheet("background-color: white; color: #2563EB; font-weight: bold; border: 1px solid #CBD5E1;")
            
            spin_precio_sec.setMinimum(0.01)
            spin_precio_sec.setMaximum(99999999.99)
            spin_precio_sec.setValue(data['precio'] * self.tasa_secundaria)
            spin_precio_sec.setPrefix(f"{self.simbolo_secundario} ")
            spin_precio_sec.setStyleSheet("background-color: #F8FAFC; color: #2563EB; font-weight: bold; border: 1px solid #CBD5E1;")
            
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
            
            self.tabla_carrito.setCellWidget(fila, 3, spin_precio_base)
            self.tabla_carrito.setCellWidget(fila, 4, spin_precio_sec)
            
            subtotal = data['cantidad'] * data['precio']
            self.tabla_carrito.setItem(fila, 5, QTableWidgetItem(f"{subtotal:.2f}"))
            
            btn_quitar = QPushButton("❌")
            btn_quitar.setStyleSheet("background-color: transparent; border: none; font-size: 14px;")
            btn_quitar.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_quitar.clicked.connect(lambda checked, p_id=prod_id: self.quitar_del_carrito(p_id))
            self.tabla_carrito.setCellWidget(fila, 6, btn_quitar)
            
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
                    self.tabla_carrito.setItem(fila, 5, QTableWidgetItem(f"{subtotal:.2f}"))

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

    # ================= 🔥 MODAL DE PAGOS CON OPCIÓN DE CRÉDITO 🔥 =================
    def abrir_modal_pago(self):
        if not self.carrito:
            return QMessageBox.warning(self, "Carrito Vacío", "Agrega productos para cobrar.")
            
        idx_cliente = self.combo_clientes.currentIndex()
        if idx_cliente < 0: return QMessageBox.warning(self, "Error", "Selecciona un cliente válido.")

        moneda_base = next((m for m in self.monedas if m['es_principal']), None)
        if not moneda_base: return QMessageBox.warning(self, "Configuración", "Debes configurar una moneda principal.")

        almacen_id = self.combo_almacenes.currentData() 
        if not almacen_id: return QMessageBox.warning(self, "Error", "Selecciona un almacén de despacho válido.")

        total_venta_base = sum(item['cantidad'] * item['precio'] for item in self.carrito.values())
        pagos_ingresados = [] 

        dialog = QDialog(self)
        dialog.setWindowTitle("Registrar Pagos de la Factura")
        dialog.setFixedWidth(550)
        
        estilo_modal = """
            QDialog { background-color: #FFFFFF; } 
            QLabel { color: #0F172A; font-weight: bold; font-size: 14px; } 
            QLineEdit { padding: 10px; border: 1px solid #CBD5E1; border-radius: 4px; color: #000000; background-color: #FFFFFF; font-size: 18px; font-weight: bold; text-align: right;} 
            QLineEdit:focus { border: 2px solid #3B82F6; }
            QComboBox { padding: 10px; border: 1px solid #CBD5E1; border-radius: 4px; color: #000000; font-size: 14px; font-weight: bold; background-color: #FFFFFF;}
            QComboBox QAbstractItemView { background-color: #FFFFFF; color: #000000; selection-background-color: #EFF6FF; }
        """
        dialog.setStyleSheet(estilo_modal)

        layout = QVBoxLayout(dialog)
        
        lbl_instruccion = QLabel("¿Cómo desea pagar el cliente?")
        lbl_instruccion.setStyleSheet("font-size: 14px; color: #64748B; text-align: center; margin-bottom: 5px;")
        lbl_instruccion.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_instruccion)

        tasa_facturacion = float(self.moneda_actual['tasa_cambio'])
        total_venta_mostrado = total_venta_base * tasa_facturacion

        lbl_resumen = QLabel(f"{self.moneda_actual['simbolo']} {total_venta_mostrado:.2f}")
        lbl_resumen.setStyleSheet("font-size: 40px; color: #0F172A; text-align: center; font-weight: 900; margin-bottom: 10px;")
        lbl_resumen.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_resumen)

        panel_nuevo = QFrame()
        panel_nuevo.setStyleSheet("background-color: #F1F5F9; border: 1px solid #E2E8F0; border-radius: 8px;")
        layout_nuevo = QVBoxLayout(panel_nuevo)
        
        layout_nuevo.addWidget(QLabel("1️⃣ Selecciona la moneda que te está entregando:"))
        combo_moneda_pago = QComboBox()
        for m in self.monedas:
            combo_moneda_pago.addItem(f"{m['nombre']} ({m['simbolo']})", m)
        layout_nuevo.addWidget(combo_moneda_pago)
        
        layout_nuevo.addWidget(QLabel("2️⃣ Selecciona el método:"))
        combo_metodo_pago = QComboBox()
        layout_nuevo.addWidget(combo_metodo_pago)
        
        layout_nuevo.addWidget(QLabel("3️⃣ Escribe el monto recibido (Presiona Enter):"))
        fila_monto = QHBoxLayout()
        txt_monto_pago = QLineEdit()
        
        btn_agregar_pago = QPushButton("⬇️ Agregar al Recibo")
        btn_agregar_pago.setStyleSheet("background-color: #2563EB; color: white; border-radius: 4px; font-weight: bold; font-size: 14px; padding: 10px 15px;")
        btn_agregar_pago.setCursor(Qt.CursorShape.PointingHandCursor)
        
        fila_monto.addWidget(txt_monto_pago)
        fila_monto.addWidget(btn_agregar_pago)
        layout_nuevo.addLayout(fila_monto)
        
        layout.addWidget(panel_nuevo)

        layout.addWidget(QLabel("Pagos Registrados en esta Factura:"))
        tabla_pagos = QTableWidget()
        tabla_pagos.setColumnCount(4)
        tabla_pagos.setHorizontalHeaderLabels(["MONEDA", "MÉTODO", "MONTO", ""])
        tabla_pagos.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        tabla_pagos.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        tabla_pagos.verticalHeader().setVisible(False)
        tabla_pagos.setFixedHeight(120)
        tabla_pagos.setStyleSheet("QTableWidget { background-color: #FFFFFF; border: 1px solid #E2E8F0; color: black; font-weight: bold; }")
        layout.addWidget(tabla_pagos)

        lbl_restante = QLabel("Falta: $0.00")
        lbl_restante.setStyleSheet("font-size: 22px; font-weight: 900; color: #DC2626;")
        lbl_restante.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_restante)

        fila_botones_finales = QHBoxLayout()
        
        btn_credito = QPushButton("⏳ DAR A CRÉDITO")
        btn_credito.setStyleSheet("QPushButton { background-color: #8B5CF6; color: white; border-radius: 6px; font-weight: bold; font-size: 16px; padding: 15px; } QPushButton:disabled { background-color: #94A3B8; }")
        
        btn_confirmar = QPushButton("✅ IMPRIMIR FACTURA")
        btn_confirmar.setEnabled(False)
        btn_confirmar.setStyleSheet("QPushButton { background-color: #16A34A; color: white; border-radius: 6px; font-weight: bold; font-size: 16px; padding: 15px; } QPushButton:disabled { background-color: #94A3B8; }")
        
        fila_botones_finales.addWidget(btn_credito)
        fila_botones_finales.addWidget(btn_confirmar)
        layout.addLayout(fila_botones_finales)

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
                tabla_pagos.setItem(i, 2, QTableWidgetItem(f"{pago['monto']:.2f}"))

                btn_quitar = QPushButton("❌")
                btn_quitar.setStyleSheet("background-color: transparent; border: none; color: red; font-size: 16px;")
                btn_quitar.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_quitar.clicked.connect(lambda checked, idx=i: quitar_pago(idx))
                tabla_pagos.setCellWidget(i, 3, btn_quitar)

                pagado_base += (pago['monto'] / pago['tasa'])

            resta_base = total_venta_base - pagado_base
            tasa_fac = float(self.moneda_actual['tasa_cambio'])
            resta_convertida = resta_base * tasa_fac

            if resta_base <= 0.01:
                lbl_restante.setText(f"VUELTO A ENTREGAR:\n{self.moneda_actual['simbolo']} {abs(resta_convertida):.2f}")
                lbl_restante.setStyleSheet("font-size: 20px; font-weight: 900; color: #16A34A;")
                btn_confirmar.setEnabled(True)
                btn_credito.setEnabled(False) 
                btn_confirmar.setFocus() 
                txt_monto_pago.setText("0.00")
            else:
                lbl_restante.setText(f"AÚN FALTA:\n{self.moneda_actual['simbolo']} {resta_convertida:.2f}")
                lbl_restante.setStyleSheet("font-size: 20px; font-weight: 900; color: #DC2626;")
                btn_confirmar.setEnabled(False)
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
                if not metodo: return QMessageBox.warning(dialog, "Error", "Seleccione un método válido.")

                pagos_ingresados.append({
                    'metodo_id': metodo['id'],
                    'nombre_metodo': metodo['nombre'],
                    'simbolo': moneda['simbolo'],
                    'monto': monto,
                    'tasa': float(moneda['tasa_cambio'])
                })
                renderizar_tabla()
            except ValueError:
                QMessageBox.warning(dialog, "Error", "Monto inválido.")

        def confirmar(es_credito=False):
            vencimiento = None
            if es_credito:
                if self.cliente_actual['id'] == 1: 
                    return QMessageBox.warning(dialog, "Denegado", "No puedes darle crédito al 'Cliente General'. Selecciona un cliente registrado.")
                
                dias, ok = QInputDialog.getInt(dialog, "Días de Crédito", "¿Cuántos días tiene el cliente para pagar la deuda?", 15, 1, 365)
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
                QMessageBox.critical(dialog, "Error", str(resp))

        combo_moneda_pago.currentIndexChanged.connect(actualizar_metodos)
        btn_agregar_pago.clicked.connect(agregar_pago)
        btn_confirmar.clicked.connect(lambda: confirmar(False))
        btn_credito.clicked.connect(lambda: confirmar(True))
        
        txt_monto_pago.returnPressed.connect(agregar_pago)

        actualizar_metodos() 
        renderizar_tabla() 
        txt_monto_pago.setFocus() 
        dialog.exec()

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

    def abrir_modal_cliente_rapido(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Registro Rápido de Cliente")
        dialog.setFixedWidth(350)
        dialog.setStyleSheet("QDialog { background-color: #FFFFFF; } QLabel { color: #0F172A; font-weight: bold; font-size: 14px; } QLineEdit { padding: 10px; border: 1px solid #CBD5E1; border-radius: 4px; color: #000000; background-color: #F8FAFC; font-size: 14px; } QLineEdit:focus { border: 2px solid #3B82F6; }")
        layout_form = QFormLayout(dialog)
        campo_doc = QLineEdit()
        campo_nom = QLineEdit()
        campo_tel = QLineEdit()
        layout_form.addRow("Cédula/RIF:", campo_doc)
        layout_form.addRow("Nombre:", campo_nom)
        layout_form.addRow("Teléfono:", campo_tel)
        box_botones = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet("padding: 10px 15px; background-color: #F1F5F9; color: #475569; border-radius: 6px; font-weight: bold;")
        btn_guardar = QPushButton("Guardar y Seleccionar")
        btn_guardar.setStyleSheet("padding: 10px 15px; background-color: #2563EB; color: white; border-radius: 6px; font-weight: bold;")
        btn_cancelar.clicked.connect(dialog.reject)
        
        def guardar():
            doc = campo_doc.text().strip()
            nom = campo_nom.text().strip()
            if not doc or not nom: return QMessageBox.warning(dialog, "Error", "Documento y Nombre son obligatorios.")
            exito, msg = db_customers.guardar_cliente(doc, nom, campo_tel.text().strip(), "N/A", 1)
            if exito:
                self.cargar_configuracion() 
                idx = self.combo_clientes.findText(nom)
                if idx >= 0: self.combo_clientes.setCurrentIndex(idx)
                dialog.accept()
            else:
                QMessageBox.critical(dialog, "Error", msg)
                
        btn_guardar.clicked.connect(guardar)
        box_botones.addWidget(btn_cancelar)
        box_botones.addWidget(btn_guardar)
        layout_form.addRow(box_botones)
        dialog.exec()