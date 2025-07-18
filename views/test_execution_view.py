import flet as ft
from views.modules.mode_selection_module import create_mode_selection_module
from views.modules.test_buttons_module import create_test_buttons_module
from views.modules.test_table_module import create_test_table_module
from views.modules.instant_values_module import create_instant_values_module
from views.modules.timer_module import create_timer_module
from views.modules.test_history_module import create_test_history_module
from views.results_summary_view import get_results_summary_view
import time

class TestExecutionView:
    def __init__(self, page, test_data):
        self.page = page
        self.test_data = test_data
        self.current_test = None
        self.current_test_index = 0
        self.completed_tests = []
        self.is_testing = False
        
        # Obtener configuraciones de prueba
        self.test_configurations = test_data.get("test_configurations", [])
        self.calculated_flows = test_data.get("calculated_flows", {})
        self.operation_mode = test_data.get("operation_mode", "automatic")
        
        # Crear tipos de pruebas únicos para botones
        self.test_types = list(set(config["test_type"] for config in self.test_configurations))
        
        print(f"[TEST_EXEC] 🚀 Inicializando ejecución de pruebas:")
        print(f"  • Modo: {self.operation_mode}")
        print(f"  • Total configuraciones: {len(self.test_configurations)}")
        print(f"  • Tipos de prueba: {self.test_types}")
        
        # Inicializar módulos
        self.init_modules()
        
    def init_modules(self):
        """Inicializa todos los módulos"""
        # 🔥 CREAR LA TABLA PRIMERO
        self.test_table = create_test_table_module(
            self.on_table_data_changed
        )
        
        # 🔥 CONFIGURAR CALLBACK MODBUS PARA LA TABLA
        def send_modbus_command(bit):
            """Callback para enviar comandos Modbus desde la tabla"""
            try:
                # Importar las funciones necesarias
                from utils.modbus_utils import build_modbus_ascii_command
                from utils.address_utils import get_address
                from services.modbus_service import ModbusService
                import threading
                import time
                
                info = get_address('M', bit)
                comand_on = build_modbus_ascii_command(
                    1, 5, int(info['high_byte'], 16), int(info['low_byte'], 16), value=1)
                comand_off = build_modbus_ascii_command(
                    1, 5, int(info['high_byte'], 16), int(info['low_byte'], 16), value=0)
                service = ModbusService()
                print(f"[TEST_EXEC] 📡 Enviando comando M{bit}")
                service.send_command(comand_on)
                time.sleep(0.1)
                service.send_command(comand_off)
                print(f"[TEST_EXEC] ✅ Comando M{bit} enviado")
            except Exception as ex:
                print(f"[TEST_EXEC] ❌ Error enviando comando M{bit}: {ex}")
        
        # 🔥 CONFIGURAR EL CALLBACK EN LA TABLA
        self.test_table.set_modbus_callback(send_modbus_command)
        
        # 🔥 CREAR MODE_SELECTION PASANDO LA REFERENCIA A LA TABLA
        self.mode_selection = create_mode_selection_module(
            self.operation_mode,
            self.on_mode_changed,
            table_widget=self.test_table  # 🔥 PASAR LA TABLA AQUÍ
        )
        
        # Módulo de botones de pruebas
        self.test_buttons = create_test_buttons_module(
            self.test_types,
            self.calculated_flows,
            self.on_test_selected,
            self.on_start_test,
            self.on_finish_test,
            self.on_view_history,
            self.on_end_session
        )
        
        # Módulo de valores instantáneos
        self.instant_values = create_instant_values_module()
        
        # Módulo de timer
        self.timer_module = create_timer_module(
            self.on_timer_finished
        )
        
        # Módulo de historial
        self.history_module = create_test_history_module(
            self.completed_tests
        )
    
    def on_mode_changed(self, new_mode):
        """Maneja cambios en el modo de operación"""
        self.operation_mode = new_mode
        print(f"[TEST_EXEC] 🔄 Modo cambiado a: {new_mode}")
    
    def on_test_selected(self, test_type):
        """Maneja selección de tipo de prueba"""
        if self.is_testing:
            self.show_warning("Debe finalizar la prueba actual antes de seleccionar otra")
            return
            
        # Buscar la siguiente prueba de este tipo
        next_test = self.find_next_test_of_type(test_type)
        if not next_test:
            self.show_warning(f"No hay más pruebas de tipo {test_type} configuradas")
            return
            
        self.current_test = next_test
        self.current_test_index = next_test["config_index"]
        
        # Actualizar tabla con datos de la prueba
        self.test_table.update_for_test(next_test)
        
        # Actualizar timer con tiempo estimado
        self.timer_module.set_time(next_test["estimated_time"])
        
        print(f"[TEST_EXEC] 🎯 Prueba seleccionada: {next_test['test_name']}")
        print(f"  • Volumen: {next_test['volume']}L")
        print(f"  • Tiempo estimado: {next_test['time_formatted']}")
        
    def on_start_test(self):
        """Inicia la prueba actual"""
        if not self.current_test:
            self.show_warning("Debe seleccionar una prueba primero")
            return
            
        if self.is_testing:
            self.show_warning("Ya hay una prueba en curso")
            return
            
        self.is_testing = True
        
        # Iniciar timer de cuenta regresiva
        self.timer_module.start_countdown()
        
        # Habilitar/deshabilitar botones según corresponda
        self.test_buttons.set_testing_state(True)
        
        print(f"[TEST_EXEC] ▶️ Iniciando prueba: {self.current_test['test_name']}")
        
    def on_finish_test(self):
        """Finaliza la prueba actual"""
        if not self.is_testing:
            self.show_warning("No hay ninguna prueba en curso")
            return
            
        # Obtener datos de la tabla
        test_data = self.test_table.get_test_data()
        
        if not self.validate_test_data(test_data):
            self.show_warning("Los datos de la prueba son incompletos")
            return
            
        # Detener timer
        self.timer_module.stop_countdown()
        
        # Agregar prueba completada al array
        completed_test = {
            **self.current_test,
            **test_data,
            "completed_at": time.time(),
            "test_duration": self.timer_module.get_elapsed_time()
        }
        
        self.completed_tests.append(completed_test)
        
        # Marcar prueba como completada en configuraciones
        self.mark_test_as_completed(self.current_test_index)
        
        # Limpiar estado
        self.is_testing = False
        self.current_test = None
        
        # Limpiar tabla
        self.test_table.clear()
        
        # Actualizar historial
        self.history_module.update_history(self.completed_tests)
        
        # Actualizar botones
        self.test_buttons.set_testing_state(False)
        self.test_buttons.update_available_tests(self.get_remaining_tests())
        
        print(f"[TEST_EXEC] ✅ Prueba finalizada. Total completadas: {len(self.completed_tests)}")
        
    def on_view_history(self):
        """Muestra el historial de pruebas"""
        self.history_module.show_history_dialog(self.page)
        
    def on_add_meter(self):
        """Agrega un nuevo medidor (función placeholder)"""
        self.show_info("🔄 Funcionalidad de agregar medidor en desarrollo")
        
    def on_end_session(self):
        """Termina la sesión de pruebas"""
        def confirm_end_session(e):
            if e.control.text == "Sí, terminar":
                # Si hay una prueba en curso, finalizarla automáticamente
                if self.is_testing:
                    self.on_finish_test()
                
                # Ir a vista de resumen
                self.show_results_summary()
                
            dialog.open = False
            self.page.update()
            
        dialog = ft.AlertDialog(
            title=ft.Text("Terminar Sesión de Pruebas"),
            content=ft.Text(
                f"¿Está seguro de terminar la sesión?\n\n"
                f"Pruebas completadas: {len(self.completed_tests)}\n"
                f"Pruebas restantes: {len(self.get_remaining_tests())}\n\n"
                f"Esta acción guardará todas las pruebas completadas."
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=confirm_end_session),
                ft.ElevatedButton(
                    "Sí, terminar", 
                    on_click=confirm_end_session,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.RED_600, color=ft.Colors.WHITE)
                ),
            ],
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
        
    def on_timer_finished(self):
        """Se ejecuta cuando termina el timer"""
        self.show_info("⏰ Tiempo de prueba completado")
        
    def on_table_data_changed(self, data):
        """Se ejecuta cuando cambian los datos de la tabla"""
        print(f"[TEST_EXEC] 📊 Datos de tabla actualizados: {data}")
        
    def find_next_test_of_type(self, test_type):
        """Encuentra la siguiente prueba pendiente del tipo especificado"""
        for i, config in enumerate(self.test_configurations):
            if (config["test_type"] == test_type and 
                not config.get("completed", False)):
                return {**config, "config_index": i}
        return None
        
    def mark_test_as_completed(self, index):
        """Marca una prueba como completada"""
        if index < len(self.test_configurations):
            self.test_configurations[index]["completed"] = True
            
    def get_remaining_tests(self):
        """Obtiene las pruebas restantes agrupadas por tipo"""
        remaining = {}
        for config in self.test_configurations:
            if not config.get("completed", False):
                test_type = config["test_type"]
                if test_type not in remaining:
                    remaining[test_type] = 0
                remaining[test_type] += 1
        return remaining
        
    def validate_test_data(self, data):
        """Valida que los datos de la prueba estén completos"""
        required_fields = ["initial_reading", "final_reading"]
        return all(field in data and data[field] is not None for field in required_fields)
        
    def show_results_summary(self):
        """Muestra la vista de resumen de resultados"""
        summary_data = {
            **self.test_data,
            "completed_tests": self.completed_tests,
            "total_tests": len(self.test_configurations),
            "completion_rate": len(self.completed_tests) / len(self.test_configurations) * 100
        }
        
        summary_view = get_results_summary_view(self.page, summary_data)
        self.page.controls.clear()
        self.page.controls.append(summary_view)
        self.page.update()
        
    def show_warning(self, message):
        """Muestra mensaje de advertencia"""
        self.page.snack_bar = ft.SnackBar(
            ft.Text(message), 
            bgcolor=ft.Colors.ORANGE_600
        )
        self.page.snack_bar.open = True
        self.page.update()
        
    def show_info(self, message):
        """Muestra mensaje informativo"""
        self.page.snack_bar = ft.SnackBar(
            ft.Text(message), 
            bgcolor=ft.Colors.BLUE_600
        )
        self.page.snack_bar.open = True
        self.page.update()

    def create_calculated_flows_display(self):
        """Crea el display responsivo de caudales calculados"""
        return ft.ResponsiveRow([
            ft.Container(
                content=ft.Column([
                    ft.Text("Caudales Calculados", size=16, weight="bold", color=ft.Colors.BLUE_700),
                    ft.ResponsiveRow([
                        ft.Container(
                            content=ft.Column([
                                ft.Text(f"Q1: {self.calculated_flows.get('Q1', 0):.2f} L/h", size=12, weight="bold", color=ft.Colors.BLUE_600),
                            ], horizontal_alignment="center"),
                            bgcolor=ft.Colors.BLUE_50,
                            padding=8,
                            border_radius=8,
                            col={"xs": 6, "sm": 3},  # 50% en móvil, 25% en escritorio
                        ),
                        ft.Container(
                            content=ft.Column([
                                ft.Text(f"Q2: {self.calculated_flows.get('Q2', 0):.2f} L/h", size=12, weight="bold", color=ft.Colors.GREEN_600),
                            ], horizontal_alignment="center"),
                            bgcolor=ft.Colors.GREEN_50,
                            padding=8,
                            border_radius=8,
                            col={"xs": 6, "sm": 3},
                        ),
                        ft.Container(
                            content=ft.Column([
                                ft.Text(f"Q3: {self.calculated_flows.get('Q3', 0):.2f} L/h", size=12, weight="bold", color=ft.Colors.ORANGE_600),
                            ], horizontal_alignment="center"),
                            bgcolor=ft.Colors.ORANGE_50,
                            padding=8,
                            border_radius=8,
                            col={"xs": 6, "sm": 3},
                        ),
                        ft.Container(
                            content=ft.Column([
                                ft.Text(f"Q4: {self.calculated_flows.get('Q4', 0):.2f} L/h", size=12, weight="bold", color=ft.Colors.PURPLE_600),
                            ], horizontal_alignment="center"),
                            bgcolor=ft.Colors.PURPLE_50,
                            padding=8,
                            border_radius=8,
                            col={"xs": 6, "sm": 3},
                        ),
                    ], spacing=10),
                ], spacing=10),
                padding=15,
                border_radius=12,
                border=ft.border.all(2, ft.Colors.BLUE_300),
                bgcolor=ft.Colors.BLUE_50,
                col=12,  # Ocupa toda la fila
            )
        ])

    def create_control_buttons(self):
        """Crea los botones de control responsivos"""
        return ft.ResponsiveRow([
            ft.Container(
                content=ft.ElevatedButton(
                    "📋 Ver Historial",
                    on_click=lambda e: self.on_view_history(),
                    height=40,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.BLUE_600,
                        color=ft.Colors.WHITE,
                    )
                ),
                col={"xs": 12, "sm": 6},  # 100% en móvil, 50% en escritorio
                padding=ft.padding.all(5),
            ),
            ft.Container(
                content=ft.ElevatedButton(
                    "➕ Agregar Medidor",
                    on_click=lambda e: self.on_add_meter(),
                    height=40,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.GREEN_600,
                        color=ft.Colors.WHITE,
                    )
                ),
                col={"xs": 12, "sm": 6},
                padding=ft.padding.all(5),
            ),
        ], spacing=10)
        
    def build(self):
        """Construye la vista completa con diseño completamente responsivo"""
        return ft.Container(
            content=ft.Column([
                # 🔥 TÍTULO CENTRADO RESPONSIVO
                ft.Container(
                    content=ft.Text(
                        "Ejecución de Pruebas",
                        size=28,
                        weight="bold",
                        text_align="center",
                        color=ft.Colors.BLUE_900
                    ),
                    alignment=ft.alignment.center,
                    padding=ft.padding.only(bottom=20),
                ),
                
                # 🔥 FILA 1: MODE SELECTION (RESPONSIVA)
                ft.ResponsiveRow([
                    ft.Container(
                        content=self.mode_selection,
                        bgcolor=ft.Colors.PURPLE_100,
                        border_radius=12,
                        padding=10,
                        margin=ft.margin.only(bottom=15),
                        col=12,  # Ocupa toda la fila en cualquier tamaño
                    )
                ]),
                
                # 🔥 FILA 2: BOTONES DE PRUEBAS (RESPONSIVA)
                ft.ResponsiveRow([
                    ft.Container(
                        content=self.test_buttons.build(),
                        margin=ft.margin.only(bottom=15),
                        col=12,  # Ocupa toda la fila
                    )
                ]),
                
                # 🔥 FILA 3: GRID PRINCIPAL RESPONSIVO
                ft.ResponsiveRow([
                    # 🔥 COLUMNA 1: VALORES INSTANTÁNEOS
                    ft.Container(
                        content=self.instant_values.build(),
                        col={"xs": 12, "md": 3},  # 100% en móvil, 25% en escritorio
                        padding=ft.padding.only(right=10),
                    ),
                    
                    # 🔥 COLUMNA 2: ÁREA PRINCIPAL
                    ft.Container(
                        content=ft.Column([
                            # 🔥 SUB-FILA 1: CAUDALES CALCULADOS
                            self.create_calculated_flows_display(),
                            
                            # 🔥 SUB-FILA 3: TABLA DE PRUEBAS
                            ft.Container(
                                content=self.test_table.build(),
                                margin=ft.margin.only(top=15),
                            ),
                            
                        ], spacing=15),
                        col={"xs": 12, "md": 9},  # 100% en móvil, 75% en escritorio
                    ),
                ], spacing=20),
                
            ], 
            spacing=0,
            scroll=ft.ScrollMode.AUTO,  # Scroll automático para contenido largo
            ),
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            alignment=ft.alignment.center,
            expand=True,
        )

def get_test_execution_view(page, test_data):
    """Función principal para obtener la vista de ejecución"""
    view = TestExecutionView(page, test_data)
    return view.build()