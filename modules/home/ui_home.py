from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
                             QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView)
from PyQt6.QtCore import Qt, QTimer, QDateTime
from modules.home import db_home
from utils import session

class VistaInicio(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.cargar_datos()
        
        # Iniciar el reloj en tiempo real
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.actualizar_reloj)
        self.timer.start(1000) # Se actualiza cada 1000 ms (1 segundo)
        self.actualizar_reloj()

    def setup_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(40, 40, 40, 40)
        layout_principal.setSpacing(30)
        
        # ==========================================
        # BANNER DE BIENVENIDA Y RELOJ (ESTILO CORPORATIVO)
        # ==========================================
        panel_bienvenida = QFrame()
        panel_bienvenida.setStyleSheet("""
            QFrame {
                background-color: #1E293B; /* Azul pizarra muy oscuro */
                border-radius: 12px;
                border-left: 6px solid #38BDF8; /* Acento azul claro */
            }
        """)
        panel_bienvenida.setFixedHeight(130)
        layout_bienvenida = QHBoxLayout(panel_bienvenida)
        layout_bienvenida.setContentsMargins(40, 20, 40, 20)
        
        # Textos de Bienvenida
        box_textos = QVBoxLayout()
        nombre_usuario = session.usuario_actual['nombre'] if session.usuario_actual else "Usuario"
        lbl_hola = QLabel(f"Bienvenido, {nombre_usuario}")
        lbl_hola.setStyleSheet("font-size: 28px; font-weight: 800; color: #FFFFFF; border: none; letter-spacing: 1px;")
        lbl_sub = QLabel("Panel de control y resumen de operaciones en tiempo real.")
        lbl_sub.setStyleSheet("font-size: 14px; color: #94A3B8; border: none;")
        
        box_textos.addWidget(lbl_hola)
        box_textos.addWidget(lbl_sub)
        box_textos.addStretch()
        
        # Reloj 
        self.lbl_reloj = QLabel("00:00:00")
        self.lbl_reloj.setStyleSheet("font-size: 34px; font-weight: bold; color: #F8FAFC; border: none; letter-spacing: 2px;")
        self.lbl_reloj.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        self.lbl_fecha = QLabel("Fecha")
        self.lbl_fecha.setStyleSheet("font-size: 13px; font-weight: 600; color: #38BDF8; border: none; text-transform: uppercase;")
        self.lbl_fecha.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        box_reloj = QVBoxLayout()
        box_reloj.addWidget(self.lbl_reloj)
        box_reloj.addWidget(self.lbl_fecha)
        box_reloj.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        layout_bienvenida.addLayout(box_textos)
        layout_bienvenida.addLayout(box_reloj)
        
        layout_principal.addWidget(panel_bienvenida)

        # ==========================================
        # TARJETAS DE RESUMEN (MÉTRICAS CLAVE)
        # ==========================================
        lbl_resumen = QLabel("Métricas Generales")
        lbl_resumen.setStyleSheet("font-size: 18px; font-weight: 800; color: #0F172A; margin-top: 10px; margin-bottom: 5px;")
        layout_principal.addWidget(lbl_resumen)

        layout_tarjetas = QHBoxLayout()
        layout_tarjetas.setSpacing(25)
        
        # Tarjetas rediseñadas sin emojis, usando colores limpios y tipografía fuerte
        self.tarjeta_ingresos = self.crear_tarjeta("Ingresos Hoy", "$ 0.00", "#10B981") # Verde Esmeralda
        self.tarjeta_ventas = self.crear_tarjeta("Facturas Emitidas", "0", "#2563EB")   # Azul Royal
        self.tarjeta_cxc = self.crear_tarjeta("Cuentas x Cobrar", "$ 0.00", "#8B5CF6")  # Púrpura
        self.tarjeta_alertas = self.crear_tarjeta("Alertas de Stock", "0", "#EF4444")   # Rojo
        
        layout_tarjetas.addWidget(self.tarjeta_ingresos['widget'])
        layout_tarjetas.addWidget(self.tarjeta_ventas['widget'])
        layout_tarjetas.addWidget(self.tarjeta_cxc['widget'])
        layout_tarjetas.addWidget(self.tarjeta_alertas['widget'])
        
        layout_principal.addLayout(layout_tarjetas)

        # ==========================================
        # TABLA DE ACTIVIDAD RECIENTE
        # ==========================================
        lbl_actividad = QLabel("Últimos Movimientos de Venta")
        lbl_actividad.setStyleSheet("font-size: 18px; font-weight: 800; color: #0F172A; margin-top: 20px; margin-bottom: 5px;")
        layout_principal.addWidget(lbl_actividad)

        self.tabla_recientes = QTableWidget()
        self.tabla_recientes.setColumnCount(4)
        self.tabla_recientes.setHorizontalHeaderLabels(["NRO. DOCUMENTO", "FECHA Y HORA", "CLIENTE", "MONTO TOTAL"])
        self.tabla_recientes.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tabla_recientes.verticalHeader().setVisible(False)
        self.tabla_recientes.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_recientes.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_recientes.setShowGrid(False)
        
        # Estilo de tabla SaaS: bordes muy finos, cabeceras en mayúscula, texto claro
        self.tabla_recientes.setStyleSheet("""
            QTableWidget { 
                background-color: #FFFFFF; 
                border-radius: 8px; 
                border: 1px solid #E2E8F0; 
                font-size: 14px; 
                color: #334155; 
            }
            QTableWidget::item { 
                padding: 12px; 
                border-bottom: 1px solid #F1F5F9; 
            }
            QTableWidget::item:selected { 
                background-color: #F8FAFC; 
                color: #0F172A; 
            }
            QHeaderView::section { 
                background-color: #F8FAFC; 
                color: #64748B; 
                font-weight: bold; 
                font-size: 12px;
                padding: 15px; 
                border: none; 
                border-bottom: 2px solid #E2E8F0; 
            }
        """)
        self.tabla_recientes.setFixedHeight(280)
        
        layout_principal.addWidget(self.tabla_recientes)
        layout_principal.addStretch()

    def crear_tarjeta(self, titulo, valor_inicial, color_acento):
        """Genera un componente de tarjeta minimalista y corporativo"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{ 
                background-color: #FFFFFF; 
                border-radius: 10px; 
                border: 1px solid #E2E8F0; 
                border-top: 4px solid {color_acento}; 
            }}
        """)
        frame.setFixedHeight(115)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(25, 20, 25, 20)
        
        lbl_titulo = QLabel(titulo.upper())
        lbl_titulo.setStyleSheet("font-size: 12px; color: #64748B; font-weight: bold; background: transparent; border: none; letter-spacing: 1px;")
        
        lbl_valor = QLabel(valor_inicial)
        lbl_valor.setStyleSheet("font-size: 32px; font-weight: 900; color: #0F172A; background: transparent; border: none;")
        
        layout.addWidget(lbl_titulo)
        layout.addWidget(lbl_valor)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        return {'widget': frame, 'lbl_valor': lbl_valor}

    def actualizar_reloj(self):
        ahora = QDateTime.currentDateTime()
        hora_formateada = ahora.toString("hh:mm:ss AP")
        fecha_formateada = ahora.toString("dddd, dd 'de' MMMM 'de' yyyy")
        
        self.lbl_reloj.setText(hora_formateada)
        self.lbl_fecha.setText(fecha_formateada)

    def cargar_datos(self):
        """Se ejecuta al abrir la app o al cambiar a esta pestaña"""
        try:
            datos = db_home.obtener_resumen_dashboard()
            
            # 1. Actualizar Tarjetas
            self.tarjeta_ingresos['lbl_valor'].setText(f"$ {datos['ingresos_hoy']:.2f}")
            self.tarjeta_ventas['lbl_valor'].setText(str(datos['ventas_hoy']))
            self.tarjeta_cxc['lbl_valor'].setText(f"$ {datos['por_cobrar']:.2f}")
            self.tarjeta_alertas['lbl_valor'].setText(str(datos['alertas_stock']))
            
            # Alertas visuales dinámicas
            if datos['alertas_stock'] > 0:
                self.tarjeta_alertas['lbl_valor'].setStyleSheet("font-size: 32px; font-weight: 900; color: #EF4444; background: transparent; border: none;")
            else:
                self.tarjeta_alertas['lbl_valor'].setStyleSheet("font-size: 32px; font-weight: 900; color: #0F172A; background: transparent; border: none;")

            # 2. Actualizar Tabla de Últimas Ventas
            ventas = datos['ultimas_ventas']
            self.tabla_recientes.setRowCount(len(ventas))
            
            for i, v in enumerate(ventas):
                # ID Formateado
                item_id = QTableWidgetItem(f"#{v['id']:06d}")
                item_id.setForeground(QColor("#64748B"))
                self.tabla_recientes.setItem(i, 0, item_id)
                
                self.tabla_recientes.setItem(i, 1, QTableWidgetItem(v['fecha_hora']))
                self.tabla_recientes.setItem(i, 2, QTableWidgetItem(v['cliente']))
                
                # Total con fuente pesada
                item_total = QTableWidgetItem(f"$ {v['total_venta']:.2f}")
                font_bold = item_total.font()
                font_bold.setBold(True)
                item_total.setFont(font_bold)
                item_total.setForeground(QColor("#0F172A")) 
                self.tabla_recientes.setItem(i, 3, item_total)
                
        except Exception as e:
            print(f"Error cargando dashboard: {e}")