import flet as ft
from utils.modbus_utils import build_modbus_ascii_command
from utils.address_utils import get_address
from services.modbus_service import ModbusService

class TestButtonsModule:
    def __init__(self, test_types, calculated_flows, on_test_selected, on_start_test, on_finish_test, on_view_history, on_end_session):
        self.test_types = test_types
        self.calculated_flows = calculated_flows
        self.on_test_selected = on_test_selected
        self.on_start_test = on_start_test
        self.on_finish_test = on_finish_test
        self.on_view_history = on_view_history
        self.on_end_session = on_end_session
        
        self.test_buttons = {}
        self.is_testing = False
        
        # Referencia a tabla (se asignará desde el exterior)
        self.table_widget = None
        
        self.create_buttons()
        
    def set_table_reference(self, table_widget):
        """Establece la referencia a la tabla para notificaciones"""
        self.table_widget = table_widget
        
    def send_bool_m(self, bit, callback_update=None, read_status_func=None):
        """Envía comando booleano al bit específico del Modbus"""
        try:
            info = get_address('M', bit)
            command_on = build_modbus_ascii_command(
                1, 5, int(info['high_byte'], 16), int(info['low_byte'], 16), value=1)
            command_off = build_modbus_ascii_command(
                1, 5, int(info['high_byte'], 16), int(info['low_byte'], 16), value=0)
            
            service = ModbusService()
            service.send_command(command_on)
            service.send_command(command_off)
            print(f"[MODBUS] Bit M{bit} activado/desactivado")
            
            # Ejecutar callbacks si están disponibles
            if callback_update and read_status_func:
                callback_update(read_status_func)
                
        except Exception as ex:
            print(f"❌ Error al enviar a M{bit}: {ex}")
    
    def create_test_button(self, name, bit):
        """Crea un botón de prueba con la lógica original"""
        def on_click(e):
            print(f"[BOTÓN] Presionado: {name} (M{bit})")
            
            # 🔥 DETECTAR TIPO DE PRUEBA Y NOTIFICAR INICIO
            test_type_mapping = {
                264: "Q1",  # Caudal Q1
                265: "Q2",  # Caudal Q2
                266: "Q3",  # Caudal Q3
                267: "Q4",  # Caudal Q4
            }
            
            # 🔥 SI ES UN BOTÓN DE CAUDAL, NOTIFICAR INICIO DE CONFIGURACIÓN
            if bit in test_type_mapping:
                test_type = test_type_mapping[bit]
                print(f"[TEST_BUTTONS] 🔧 Configurando prueba: {test_type}")
                
                # Notificar a la tabla que se inicia una nueva configuración
                if self.table_widget and hasattr(self.table_widget, 'notify_test_start'):
                    self.table_widget.notify_test_start(test_type)
                
                # Notificar al callback de selección de prueba
                self.on_test_selected(test_type)
            
            # 🔥 MANTENER EL SISTEMA DE ENVÍO ORIGINAL
            self.send_bool_m(bit)
            
        return ft.ElevatedButton(
            content=ft.Text(name, size=14, weight="bold"),
            width=180,
            height=50,
            on_click=on_click,
            style=ft.ButtonStyle(
                bgcolor="#005989",  # Color único para todos los botones
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=8),
            )
        )
        
    def create_buttons(self):
        """Crea solo los botones de prueba (Q1, Q2, Q3, Q4, Hidrostática)"""
        
        # Solo botones de tipos de prueba (sin iniciar ni finalizar)
        self.test_buttons["Q1"] = self.create_test_button("Caudal Q1", 264)
        self.test_buttons["Q2"] = self.create_test_button("Caudal Q2", 265)
        self.test_buttons["Q3"] = self.create_test_button("Caudal Q3", 266)
        self.test_buttons["Q4"] = self.create_test_button("Caudal Q4", 267)
        self.test_buttons["Hidrostática"] = self.create_test_button("Hidrostática", 268)
        
    def set_testing_state(self, is_testing):
        """Actualiza el estado de los botones según si hay prueba en curso"""
        self.is_testing = is_testing
        print(f"[TEST_BUTTONS] Estado de testing: {is_testing}")
        
    def update_available_tests(self, remaining_tests):
        """Actualiza información sobre pruebas restantes"""
        print(f"[TEST_BUTTONS] Pruebas restantes: {remaining_tests}")
        
    def build(self):
        """Construye el módulo con todos los botones en una sola fila"""
        return ft.Container(
            content=ft.Column([
                ft.Text("⚙️ Controles de prueba", weight="bold", text_align="center", size=16),
                
                # 🔥 NUEVA DISTRIBUCIÓN: 5 COLUMNAS EN UNA SOLA FILA
                ft.Row([
                    # Columna 1: Q1
                    ft.Container(
                        content=self.test_buttons["Q1"],
                        expand=1,
                        alignment=ft.alignment.center,
                    ),
                    
                    # Columna 2: Q2
                    ft.Container(
                        content=self.test_buttons["Q2"],
                        expand=1,
                        alignment=ft.alignment.center,
                    ),
                    
                    # Columna 3: Q3
                    ft.Container(
                        content=self.test_buttons["Q3"],
                        expand=1,
                        alignment=ft.alignment.center,
                    ),
                    
                    # Columna 4: Q4
                    ft.Container(
                        content=self.test_buttons["Q4"],
                        expand=1,
                        alignment=ft.alignment.center,
                    ),
                    
                    # Columna 5: Hidrostática
                    ft.Container(
                        content=self.test_buttons["Hidrostática"],
                        expand=1,
                        alignment=ft.alignment.center,
                    ),
                    
                ], alignment="spaceEvenly", spacing=15)
                
            ], spacing=15),
            padding=15,
            border_radius=12,
            border=ft.border.all(2, ft.Colors.BLUE_300),
            bgcolor=ft.Colors.BLUE_50,
        )

def create_test_buttons_module(test_types, calculated_flows, on_test_selected, on_start_test, on_finish_test, on_view_history, on_end_session):
    """Función factory para crear el módulo de botones"""
    module = TestButtonsModule(
        test_types, 
        calculated_flows, 
        on_test_selected, 
        on_start_test, 
        on_finish_test, 
        on_view_history, 
        on_end_session
    )
    return module