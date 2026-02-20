from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QAbstractItemView)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from modules.reports import db_reports
from modules.settings import db_settings # Para traer la moneda principal

class VistaReportes(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(40, 40, 40, 40)
        layout_principal.setSpacing(20)
        
        # --- Encabezado ---
        lbl_titulo = QLabel("📊 Panel de Control (Dashboard)")
        lbl_titulo.setStyleSheet("font-size: 28px; font-weight: 900; color: #0F172A; margin-bottom: 5px;")
        lbl_subtitulo = QLabel("Resumen de rendimiento y métricas del MES ACTUAL.")
        lbl_subtitulo.setStyleSheet("font-size: 14px; color: #64748B; margin-bottom: 15px;")
        layout_principal.addWidget(lbl_titulo)
        layout_principal.addWidget(lbl_subtitulo)
        
        # ================= SECCIÓN 1: TARJETAS DE MÉTRICAS (KPIs) =================
        layout_kpis = QHBoxLayout()
        layout_kpis.setSpacing(15)
        
        self.tarjeta_ventas = self.crear_tarjeta_kpi("Ventas Brutas", "$0.00", "#2563EB") # Azul
        self.tarjeta_costos = self.crear_tarjeta_kpi("Costo de Mercancía", "$0.00", "#DC2626") # Rojo
        self.tarjeta_ganancia = self.crear_tarjeta_kpi("Ganancia Neta", "$0.00", "#16A34A") # Verde
        
        layout_kpis.addWidget(self.tarjeta_ventas['widget'])
        layout_kpis.addWidget(self.tarjeta_costos['widget'])
        layout_kpis.addWidget(self.tarjeta_ganancia['widget'])
        
        layout_principal.addLayout(layout_kpis)
        
        # ================= SECCIÓN 2: TABLAS DE ANÁLISIS =================
        layout_tablas = QHBoxLayout()
        layout_tablas.setSpacing(20)
        
        # --- Izquierda: Top Productos y Cajas ---
        panel_izq = QVBoxLayout()
        
        # Tabla Ingresos por Método
        panel_izq.addWidget(QLabel("<b>💵 Flujo de Caja por Método de Pago</b>", styleSheet="font-size: 15px; color: #0F172A; margin-top: 10px;"))
        self.tabla_metodos = self.crear_tabla(["MÉTODO", "MONEDA", "TOTAL RECAUDADO"])
        panel_izq.addWidget(self.tabla_metodos, stretch=1)
        
        # Tabla Top Productos
        panel_izq.addWidget(QLabel("<b>🔥 Top 10 Productos Más Vendidos</b>", styleSheet="font-size: 15px; color: #0F172A; margin-top: 10px;"))
        self.tabla_top = self.crear_tabla(["CÓDIGO", "PRODUCTO", "CANT. VENDIDA", "GENERADO"])
        panel_izq.addWidget(self.tabla_top, stretch=2)
        
        # --- Derecha: Alertas de Stock ---
        panel_der = QVBoxLayout()
        panel_der.addWidget(QLabel("<b>⚠️ Alerta de Stock Crítico (Reabastecer)</b>", styleSheet="font-size: 15px; color: #DC2626; margin-top: 10px;"))
        self.tabla_stock = self.crear_tabla(["CÓDIGO", "PRODUCTO", "ACTUAL", "MÍNIMO"])
        panel_der.addWidget(self.tabla_stock)
        
        layout_tablas.addLayout(panel_izq, stretch=60)
        layout_tablas.addLayout(panel_der, stretch=40)
        
        layout_principal.addLayout(layout_tablas)

    def crear_tarjeta_kpi(self, titulo, valor_inicial, color_borde):
        frame = QFrame()
        frame.setStyleSheet(f"QFrame {{ background-color: #FFFFFF; border-radius: 8px; border: 1px solid #E2E8F0; border-bottom: 4px solid {color_borde}; }}")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 20, 20, 20)
        
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setStyleSheet("font-size: 14px; color: #64748B; font-weight: bold; border: none;")
        
        lbl_valor = QLabel(valor_inicial)
        lbl_valor.setStyleSheet("font-size: 26px; font-weight: 900; color: #0F172A; border: none;")
        
        layout.addWidget(lbl_titulo)
        layout.addWidget(lbl_valor)
        
        return {'widget': frame, 'lbl_valor': lbl_valor}

    def crear_tabla(self, columnas):
        tabla = QTableWidget()
        tabla.setColumnCount(len(columnas))
        tabla.setHorizontalHeaderLabels(columnas)
        tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tabla.verticalHeader().setVisible(False)
        tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tabla.setStyleSheet("""
            QTableWidget { background-color: #FFFFFF; color: #334155; border: 1px solid #E2E8F0; border-radius: 6px; font-size: 13px; font-weight: bold; }
            QTableWidget::item { padding: 8px; border-bottom: 1px solid #F1F5F9; }
            QHeaderView::section { background-color: #F8FAFC; color: #64748B; font-weight: 700; font-size: 11px; padding: 10px; border: none; border-bottom: 2px solid #E2E8F0; text-transform: uppercase; }
        """)
        return tabla

    def cargar_datos(self):
        """Esta función es llamada automáticamente por main.py al entrar a la pestaña"""
        # Traer el símbolo de la moneda base
        monedas = db_settings.obtener_monedas()
        simbolo_base = next((m['simbolo'] for m in monedas if m['es_principal']), "$")
        
        # 1. Cargar KPIs Superiores
        kpis = db_reports.obtener_kpis_mes_actual()
        self.tarjeta_ventas['lbl_valor'].setText(f"{simbolo_base} {kpis['venta_total']:,.2f}")
        self.tarjeta_costos['lbl_valor'].setText(f"{simbolo_base} {kpis['costo_total']:,.2f}")
        self.tarjeta_ganancia['lbl_valor'].setText(f"{simbolo_base} {kpis['ganancia']:,.2f}")
        
        # 2. Cargar Flujo por Método
        ingresos = db_reports.obtener_ingresos_por_metodo()
        self.tabla_metodos.setRowCount(0)
        for i, row in enumerate(ingresos):
            self.tabla_metodos.insertRow(i)
            self.tabla_metodos.setItem(i, 0, QTableWidgetItem(row['metodo']))
            self.tabla_metodos.setItem(i, 1, QTableWidgetItem(row['simbolo']))
            self.tabla_metodos.setItem(i, 2, QTableWidgetItem(f"{row['total_recaudado']:,.2f}"))

        # 3. Cargar Top Productos
        top_prods = db_reports.obtener_top_productos()
        self.tabla_top.setRowCount(0)
        self.tabla_top.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # Descripción ancha
        for i, row in enumerate(top_prods):
            self.tabla_top.insertRow(i)
            self.tabla_top.setItem(i, 0, QTableWidgetItem(row['codigo']))
            self.tabla_top.setItem(i, 1, QTableWidgetItem(row['nombre']))
            self.tabla_top.setItem(i, 2, QTableWidgetItem(str(row['total_vendido'])))
            self.tabla_top.setItem(i, 3, QTableWidgetItem(f"{simbolo_base} {row['dinero_generado']:,.2f}"))

        # 4. Cargar Stock Crítico
        stock_critico = db_reports.obtener_stock_critico()
        self.tabla_stock.setRowCount(0)
        self.tabla_stock.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for i, row in enumerate(stock_critico):
            self.tabla_stock.insertRow(i)
            self.tabla_stock.setItem(i, 0, QTableWidgetItem(row['codigo']))
            self.tabla_stock.setItem(i, 1, QTableWidgetItem(row['nombre']))
            
            item_act = QTableWidgetItem(str(row['stock_actual']))
            item_act.setForeground(QColor("#DC2626")) # Rojo para resaltar peligro
            self.tabla_stock.setItem(i, 2, item_act)
            
            self.tabla_stock.setItem(i, 3, QTableWidgetItem(str(row['cantidad_minima'])))