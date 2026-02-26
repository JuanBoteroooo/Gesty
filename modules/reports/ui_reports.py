import qtawesome as qta
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QAbstractItemView, QTabWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from modules.reports import db_reports
from modules.settings import db_settings

class VistaReportes(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(30, 30, 30, 30)
        layout_principal.setSpacing(20)
        
        # --- Encabezado ---
        header_layout = QVBoxLayout()
        lbl_titulo = QLabel("MÉTRICAS Y REPORTES DE NEGOCIO")
        lbl_titulo.setStyleSheet("font-size: 24px; font-weight: 900; color: #0F172A; letter-spacing: 1px;")
        lbl_subtitulo = QLabel("Análisis detallado del rendimiento de la empresa durante el mes en curso.")
        lbl_subtitulo.setStyleSheet("font-size: 14px; color: #64748B;")
        header_layout.addWidget(lbl_titulo)
        header_layout.addWidget(lbl_subtitulo)
        layout_principal.addLayout(header_layout)
        
        # ================= TABS DE NAVEGACIÓN =================
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #E2E8F0; background: #FFFFFF; border-radius: 8px; top: -1px; }
            QTabBar::tab { background: #F1F5F9; color: #64748B; padding: 12px 25px; border-top-left-radius: 8px; border-top-right-radius: 8px; font-weight: bold; font-size: 13px; margin-right: 4px; }
            QTabBar::tab:selected { background: #FFFFFF; color: #0F172A; border-top: 3px solid #38BDF8; border-bottom: 1px solid #FFFFFF; }
        """)
        
        self.tab_finanzas = QWidget()
        self.tab_inventario = QWidget()
        self.tab_clientes = QWidget()
        
        self.setup_tab_finanzas()
        self.setup_tab_inventario()
        self.setup_tab_clientes()
        
        self.tabs.addTab(self.tab_finanzas, qta.icon('fa5s.chart-pie', color='#64748B'), "Finanzas y Ganancias")
        self.tabs.addTab(self.tab_inventario, qta.icon('fa5s.box-open', color='#64748B'), "Rotación de Inventario")
        self.tabs.addTab(self.tab_clientes, qta.icon('fa5s.users', color='#64748B'), "Rendimiento de Clientes")
        
        layout_principal.addWidget(self.tabs)

    # ================= PESTAÑA 1: FINANZAS =================
    def setup_tab_finanzas(self):
        layout = QVBoxLayout(self.tab_finanzas)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # KPIs Superiores
        layout_kpis = QHBoxLayout()
        layout_kpis.setSpacing(15)
        self.tarjeta_ventas = self.crear_tarjeta_kpi("Ventas Brutas Totales", "$0.00", "#2563EB", "fa5s.money-bill-wave") 
        self.tarjeta_costos = self.crear_tarjeta_kpi("Costo Total de Mercancía", "$0.00", "#DC2626", "fa5s.shopping-cart") 
        self.tarjeta_ganancia = self.crear_tarjeta_kpi("Ganancia Neta Estimada", "$0.00", "#10B981", "fa5s.chart-line") 
        layout_kpis.addWidget(self.tarjeta_ventas['widget'])
        layout_kpis.addWidget(self.tarjeta_costos['widget'])
        layout_kpis.addWidget(self.tarjeta_ganancia['widget'])
        layout.addLayout(layout_kpis)
        
        # Tabla Flujo
        layout.addWidget(QLabel("<b>💵 Flujo de Caja por Método de Pago</b>", styleSheet="font-size: 16px; color: #0F172A; margin-top: 10px;"))
        self.tabla_metodos = self.crear_tabla(["MÉTODO DE PAGO", "MONEDA", "TOTAL RECAUDADO (MES ACTUAL)"])
        layout.addWidget(self.tabla_metodos)

    # ================= PESTAÑA 2: INVENTARIO =================
    def setup_tab_inventario(self):
        layout = QHBoxLayout(self.tab_inventario)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(25)
        
        # Izquierda: Top Productos
        panel_izq = QVBoxLayout()
        panel_izq.addWidget(QLabel("<b>🔥 Top 10 Productos Más Vendidos</b>", styleSheet="font-size: 16px; color: #0F172A;"))
        self.tabla_top = self.crear_tabla(["CÓDIGO", "PRODUCTO", "CANT. VENDIDA", "DINERO GENERADO"])
        self.tabla_top.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        panel_izq.addWidget(self.tabla_top)
        
        # Derecha: Stock Crítico
        panel_der = QVBoxLayout()
        panel_der.addWidget(QLabel("<b>⚠️ Alertas de Stock Crítico (Reabastecer)</b>", styleSheet="font-size: 16px; color: #DC2626;"))
        self.tabla_stock = self.crear_tabla(["CÓDIGO", "PRODUCTO", "STOCK ACTUAL", "MÍNIMO IDEAL"])
        self.tabla_stock.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        panel_der.addWidget(self.tabla_stock)
        
        layout.addLayout(panel_izq, stretch=60)
        layout.addLayout(panel_der, stretch=40)

    # ================= PESTAÑA 3: CLIENTES =================
    def setup_tab_clientes(self):
        layout = QVBoxLayout(self.tab_clientes)
        layout.setContentsMargins(20, 20, 20, 20)
        
        lbl_info = QLabel("<b>🏆 Los 10 Mejores Clientes del Mes</b>")
        lbl_info.setStyleSheet("font-size: 16px; color: #0F172A; margin-bottom: 10px;")
        layout.addWidget(lbl_info)
        
        self.tabla_clientes = self.crear_tabla(["DOCUMENTO", "NOMBRE DEL CLIENTE", "FACTURAS EMITIDAS", "DINERO GASTADO EN LA TIENDA"])
        self.tabla_clientes.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tabla_clientes)

    # ================= FUNCIONES DE DISEÑO =================
    def crear_tarjeta_kpi(self, titulo, valor_inicial, color_borde, icono_name):
        frame = QFrame()
        frame.setStyleSheet(f"QFrame {{ background-color: #FFFFFF; border-radius: 8px; border: 1px solid #E2E8F0; border-bottom: 4px solid {color_borde}; }}")
        frame.setFixedHeight(120)
        
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(25, 20, 25, 20)
        
        box_textos = QVBoxLayout()
        lbl_titulo = QLabel(titulo.upper())
        lbl_titulo.setStyleSheet("font-size: 12px; color: #64748B; font-weight: bold; border: none; letter-spacing: 1px;")
        lbl_valor = QLabel(valor_inicial)
        lbl_valor.setStyleSheet("font-size: 28px; font-weight: 900; color: #0F172A; border: none;")
        box_textos.addWidget(lbl_titulo)
        box_textos.addWidget(lbl_valor)
        
        lbl_icono = QLabel()
        lbl_icono.setPixmap(qta.icon(icono_name, color=color_borde).pixmap(40, 40))
        lbl_icono.setStyleSheet("border: none; background: transparent;")
        
        layout.addLayout(box_textos)
        layout.addStretch()
        layout.addWidget(lbl_icono)
        
        return {'widget': frame, 'lbl_valor': lbl_valor}

    def crear_tabla(self, columnas):
        tabla = QTableWidget()
        tabla.setColumnCount(len(columnas))
        tabla.setHorizontalHeaderLabels(columnas)
        tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tabla.verticalHeader().setVisible(False)
        tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tabla.verticalHeader().setDefaultSectionSize(45)
        tabla.setStyleSheet("""
            QTableWidget { background-color: #FFFFFF; color: #334155; border: 1px solid #E2E8F0; border-radius: 6px; font-size: 13px; font-weight: bold; }
            QTableWidget::item { padding: 5px 15px; border-bottom: 1px solid #F1F5F9; }
            QTableWidget::item:selected { background-color: #F8FAFC; color: #0F172A; }
            QHeaderView::section { background-color: #F8FAFC; color: #64748B; font-weight: 700; font-size: 11px; padding: 12px; border: none; border-bottom: 2px solid #E2E8F0; text-transform: uppercase; }
        """)
        return tabla

    # ================= LLENADO DE DATOS =================
    def cargar_datos(self):
        """Llamado automáticamente por main.py"""
        monedas = db_settings.obtener_monedas()
        simbolo_base = next((m['simbolo'] for m in monedas if m['es_principal']), "$")
        
        # 1. KPIs Finanzas
        kpis = db_reports.obtener_kpis_mes_actual()
        self.tarjeta_ventas['lbl_valor'].setText(f"{simbolo_base} {kpis['venta_total']:,.2f}")
        self.tarjeta_costos['lbl_valor'].setText(f"{simbolo_base} {kpis['costo_total']:,.2f}")
        self.tarjeta_ganancia['lbl_valor'].setText(f"{simbolo_base} {kpis['ganancia']:,.2f}")
        
        # 2. Flujo por Método
        ingresos = db_reports.obtener_ingresos_por_metodo()
        self.tabla_metodos.setRowCount(0)
        for i, row in enumerate(ingresos):
            self.tabla_metodos.insertRow(i)
            self.tabla_metodos.setItem(i, 0, QTableWidgetItem(row['metodo']))
            self.tabla_metodos.setItem(i, 1, QTableWidgetItem(row['simbolo']))
            
            item_monto = QTableWidgetItem(f"{row['total_recaudado']:,.2f}")
            item_monto.setForeground(QColor("#10B981")) # Verde
            self.tabla_metodos.setItem(i, 2, item_monto)

        # 3. Top Productos
        top_prods = db_reports.obtener_top_productos()
        self.tabla_top.setRowCount(0)
        for i, row in enumerate(top_prods):
            self.tabla_top.insertRow(i)
            self.tabla_top.setItem(i, 0, QTableWidgetItem(row['codigo'] or "-"))
            self.tabla_top.setItem(i, 1, QTableWidgetItem(row['nombre']))
            self.tabla_top.setItem(i, 2, QTableWidgetItem(str(row['total_vendido'])))
            self.tabla_top.setItem(i, 3, QTableWidgetItem(f"{simbolo_base} {row['dinero_generado']:,.2f}"))

        # 4. Stock Crítico
        stock_critico = db_reports.obtener_stock_critico()
        self.tabla_stock.setRowCount(0)
        for i, row in enumerate(stock_critico):
            self.tabla_stock.insertRow(i)
            self.tabla_stock.setItem(i, 0, QTableWidgetItem(row['codigo'] or "-"))
            self.tabla_stock.setItem(i, 1, QTableWidgetItem(row['nombre']))
            
            item_act = QTableWidgetItem(str(row['stock_actual']))
            item_act.setForeground(QColor("#DC2626")) # Rojo
            self.tabla_stock.setItem(i, 2, item_act)
            
            self.tabla_stock.setItem(i, 3, QTableWidgetItem(str(row['cantidad_minima'])))

        # 5. Top Clientes
        top_clientes = db_reports.obtener_top_clientes()
        self.tabla_clientes.setRowCount(0)
        for i, row in enumerate(top_clientes):
            self.tabla_clientes.insertRow(i)
            self.tabla_clientes.setItem(i, 0, QTableWidgetItem(row['documento']))
            self.tabla_clientes.setItem(i, 1, QTableWidgetItem(row['nombre']))
            self.tabla_clientes.setItem(i, 2, QTableWidgetItem(f"{row['total_compras']} facturas"))
            
            item_dinero = QTableWidgetItem(f"{simbolo_base} {row['dinero_gastado']:,.2f}")
            item_dinero.setForeground(QColor("#2563EB")) # Azul
            self.tabla_clientes.setItem(i, 3, item_dinero)