import flet as ft
from .timer_module import create_timer_module
import time

DROPDOWN_OPTIONS = ["Escoja una opción", "Q1", "Q2", "Q3", "Q4"]
INPUT_BG = "#f3f4f6"

class TestTableModule:
    def __init__(self, on_data_changed):
        self.on_data_changed = on_data_changed
        self.current_test = None
        self.meter_status = "nuevo"  # 🔥 SE OBTIENE DE BATCH REGISTRATION

        self.test_configurations_direct = []
        
        # 🔥 ESTRUCTURA DE FILAS: [#, Serial, Tipo, Inicial, Final, Volumen_Patron, Error, Estado]
        self.rows = []
        self.completed_rows = set()  # Índices de filas que ya tienen prueba completada
        self.frozen_values = {}
        
        # 🔥 NUEVO: TIPO DE PRUEBA ACTUAL SELECCIONADO POR CALIBRACIÓN
        self.current_test_type = None
        self.test_counters = {"Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0}  # Contadores de repetibilidad
        
        # 🔥 NUEVO: ARRAY DE PRUEBAS COMPLETADAS
        self.completed_tests = []
        
        # 🔥 CALLBACK PARA ENVIAR COMANDOS MODBUS
        self.send_modbus_command = None

        # 🔥 REFERENCIA AL MÓDULO DE VALORES INSTANTÁNEOS
        self.instant_values_module = None

        # 🔥 ELIMINAR ESTA LÍNEA - EL TIMER SE ESTABLECE EXTERNAMENTE
        # self.timer_module = create_timer_module(self._on_timer_finished)
        self.timer_module = None  # 🔥 SE ESTABLECE EXTERNAMENTE
        
        # 🔥 MAPEO DE TIPOS DE PRUEBA A VALORES INSTANTÁNEOS
        self.test_to_instant_mapping = {
            "Q1": "vol_q1",  # Q1 usa volumen Q1
            "Q2": "vol_q2",  # Q2 usa volumen Q2  
            "Q3": "vol_q3",  # Q3 usa volumen Q3
            "Q4": "vol_q4"   # Q4 usa volumen Q4
        }
        
        # 🔥 MAPEO DE MENSAJES DE CALIBRACIÓN A TIPOS DE PRUEBA
        self.calibration_messages = {
            "✅ Fin de calibración Q1": "Q1",
            "✅ Fin de calibración Q2": "Q2", 
            "✅ Fin de calibración Q3": "Q3",
            "✅ Fin de calibración Q4": "Q4"
        }
        
        print(f"[TEST_TABLE] 🚀 Inicializando tabla con {len(self.rows)} fila(s)")

        # 🔥 VALORES INSTANTÁNEOS ACTUALES (SE ACTUALIZAN EN TIEMPO REAL)
        self.instant_values = {
            "Q1": 0.1,  # 🔥 CAMBIADO DE 1000.0 A 0.1
            "Q2": 0.1,  # 🔥 CAMBIADO DE 2000.0 A 0.1
            "Q3": 0.1,  # 🔥 CAMBIADO DE 3000.0 A 0.1
            "Q4": 0.1,  # 🔥 CAMBIADO DE 4000.0 A 0.1
        }

        # 🔥 ESTADO DE PRUEBAS ACTIVAS (PARA RESETEAR CUANDO INICIA NUEVA PRUEBA)
        self.active_test_type = None
        self.test_in_progress = False

        # 🔥 CONTADOR PARA DEBUG
        self.add_row_counter = 0

        # 🔥 NUEVA VARIABLE: REFERENCIAS A LAS CELDAS DE VOLUMEN PATRÓN
        self.pattern_volume_cells = {}  # {row_idx: Text_widget}
        
        # 🔥 NUEVA VARIABLE: REFERENCIAS A LAS CELDAS DE ERROR
        self.error_cells = {}  # {row_idx: Text_widget}
        
        # 🔥 NUEVA VARIABLE: REFERENCIAS A LAS CELDAS DE ESTADO
        self.status_cells = {}

        self.data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("#", text_align=ft.TextAlign.CENTER)),
                ft.DataColumn(ft.Text("Serial", text_align=ft.TextAlign.CENTER)),
                ft.DataColumn(ft.Text("Tipo de Prueba", text_align=ft.TextAlign.CENTER)),  # 🔥 SIN DROPDOWN
                ft.DataColumn(ft.Text("Lectura Inicial", text_align=ft.TextAlign.CENTER)),
                ft.DataColumn(ft.Text("Lectura Final", text_align=ft.TextAlign.CENTER)),
                ft.DataColumn(ft.Text("Volumen Patrón", text_align=ft.TextAlign.CENTER)),
                ft.DataColumn(ft.Text("Error (%)", text_align=ft.TextAlign.CENTER)),
                ft.DataColumn(ft.Text("Estado", text_align=ft.TextAlign.CENTER)),
                ft.DataColumn(ft.Text("Acción", text_align=ft.TextAlign.CENTER)),
            ],
            rows=[],
            column_spacing=12,
            data_row_min_height=60,  # 🔥 AUMENTADO PARA ACOMODAR MÁRGENES
            border=ft.border.all(1, ft.Colors.GREY_300),
            divider_thickness=1,
            heading_row_color=ft.Colors.GREY_100,
            heading_row_height=45,
            horizontal_margin=8,
        )

        self.table_with_margin = ft.Container(
            content=self.data_table,
            margin=ft.margin.symmetric(vertical=5),  # 🔥 MARGEN VERTICAL DE 5PX
        )

        # 🔥 BOTONES DE CONTROL DE PRUEBA
        self.start_test_button = self.create_test_button("Iniciar Prueba", 269)

        self.finish_test_button = ft.ElevatedButton(
            "Finalizar Prueba",
            width=140,
            bgcolor=ft.Colors.RED_600,
            color="white",
            on_click=self._on_finish_test
        )

        self.end_tests_button = ft.ElevatedButton(
            "Finalizar Pruebas",
            width=140,
            bgcolor=ft.Colors.DEEP_ORANGE_600,
            color="white",
            on_click=self._on_end_tests,
            icon=ft.Icons.ASSIGNMENT_TURNED_IN
        )

        # 🔥 INICIALIZAR TABLA CON UNA FILA POR DEFECTO
        self.initialize_table()


    def set_test_configurations_directly(self, configurations):
        """🔥 NUEVA FUNCIÓN: Establece configuraciones directamente sin usar session"""
        self.test_configurations_direct = configurations
        print(f"[TEST_TABLE] 📦 Configuraciones establecidas directamente: {len(configurations)}")


    def set_timer_module(self, timer_module):
        """🔥 NUEVA FUNCIÓN: Establece referencia al módulo de timer"""
        self.timer_module = timer_module
        print("[TEST_TABLE] 🔗 Timer module conectado")

    def create_test_button(self, name, bit):
        """🔥 NUEVA FUNCIÓN: Crea botón de prueba que envía comando Modbus"""
        def on_click(e):
            print(f"[BOTÓN] Presionado: {name} (M{bit})")
            
            # 🔥 MANTENER EL SISTEMA DE ENVÍO ORIGINAL
            self.send_bool_m(bit)
            
        return ft.ElevatedButton(
            content=ft.Text(name), 
            width=140,
            bgcolor=ft.Colors.GREEN_600,
            color="white",
            on_click=on_click
        )

    def send_bool_m(self, bit):
        try:
            from utils.address_utils import get_address
            from utils.modbus_utils import build_modbus_ascii_command
            from services.modbus_service import ModbusService
            import threading
            
            info = get_address('M', bit)
            comand_on = build_modbus_ascii_command(
                1, 5, int(info['high_byte'], 16), int(info['low_byte'], 16), value=1)
            comand_off = build_modbus_ascii_command(
                1, 5, int(info['high_byte'], 16), int(info['low_byte'], 16), value=0)
            service = ModbusService()
            print(f"[MODBUS] Enviando ON a M{bit}: {comand_on.strip()}")
            service.send_command(comand_on)
            print(f"[MODBUS] Enviando OFF a M{bit}: {comand_off.strip()}")
            service.send_command(comand_off)
            print(f"[MODBUS] Bit M{bit} activado/desactivado")
            
            # 🔥 CORRECCIÓN: Timer necesita una función
            def dummy_callback():
                pass
            threading.Timer(0.3, dummy_callback).start()
            
        except Exception as ex:
            print(f"[MODBUS] ❌ Error en send_bool_m para M{bit}: {ex}")

    def set_instant_values_module(self, instant_values_module):
        """🔥 NUEVA FUNCIÓN: Establece referencia al módulo de valores instantáneos"""
        self.instant_values_module = instant_values_module
        print("[TEST_TABLE] 🔗 Referencia al módulo de valores instantáneos establecida")

    def set_modbus_callback(self, callback):
        """🔥 NUEVA FUNCIÓN: Establece el callback para enviar comandos Modbus"""
        self.send_modbus_command = callback
        print("[TEST_TABLE] 🔗 Callback Modbus configurado")

    def update_meter_status_from_batch(self, meter_status):
        """🔥 NUEVA FUNCIÓN: Actualiza el estado del medidor desde batch registration"""
        status_lower = str(meter_status).lower().strip()
        
        if status_lower in ["nuevo", "new"]:
            self.meter_status = "nuevo"
        elif status_lower in ["usado", "used"]:
            self.meter_status = "usado"
        else:
            self.meter_status = "nuevo"
            
        print(f"[TEST_TABLE] 🔄 Estado del medidor actualizado desde batch: {self.meter_status}")
        
        # Recalcular errores con el nuevo estado
        self.update_table()

    

    def process_calibration_message(self, message):
        """🔥 MEJORADA: Procesa mensajes de calibración Y establecimiento automático"""
        if not message:
            return
            
        message_str = str(message).strip()
        print(f"[TEST_TABLE] 📨 Procesando mensaje: '{message_str}'")
        
        # 🔥 BUSCAR SI EL MENSAJE CORRESPONDE A FIN DE CALIBRACIÓN
        for calib_msg, test_type in self.calibration_messages.items():
            if calib_msg in message_str:
                print(f"[TEST_TABLE] 🎯 Calibración detectada: {calib_msg} -> {test_type}")
                self.set_test_type_from_calibration(test_type)
                return
        
        # 🔥 VERIFICACIÓN POR CÓDIGOS NUMÉRICOS SOLO PARA CALIBRACIÓN
        calibration_codes = {
            4: "Q1",   # Fin de calibración Q1
            9: "Q2",   # Fin de calibración Q2
            13: "Q3",  # Fin de calibración Q3
            17: "Q4"   # Fin de calibración Q4
        }
        
        # Si el mensaje es un número, verificar si es código de calibración
        try:
            message_code = int(message_str)
            
            if message_code in calibration_codes:
                test_type = calibration_codes[message_code]
                print(f"[TEST_TABLE] 🎯 Código de calibración detectado: {message_code} -> {test_type}")
                self.set_test_type_from_calibration(test_type)
                
        except ValueError:
            # No es un número, continuar
            pass
        
        # 🔥 DETECTAR INICIO Y FIN DE PRUEBA SOLO PARA LOGS
        if "🧪 Inicio de prueba" in message_str:
            print(f"[TEST_TABLE] 🚀 Inicio de prueba detectado en mensaje")
            
            # 🔥 SI NO HAY TIPO DE PRUEBA ESTABLECIDO, INTENTAR EXTRAERLO DEL MENSAJE
            if not self.current_test_type:
                if "Q1" in message_str:
                    auto_type = "Q1"
                elif "Q2" in message_str:
                    auto_type = "Q2"
                elif "Q3" in message_str:
                    auto_type = "Q3"
                elif "Q4" in message_str:
                    auto_type = "Q4"
                else:
                    auto_type = None
                
                if auto_type:
                    print(f"[TEST_TABLE] 🎯 Auto-estableciendo tipo desde mensaje de inicio: {auto_type}")
                    self.set_test_type_from_calibration(auto_type)
                    
        elif "⏳ Estado de espera" in message_str:
            print(f"[TEST_TABLE] 🏁 Fin de prueba detectado en mensaje")

    
    def force_set_test_type_q4(self):
        """🔥 FUNCIÓN DE EMERGENCIA: Fuerza Q4 como tipo de prueba"""
        print(f"[TEST_TABLE] 🚨 FORZANDO tipo de prueba Q4")
        self.set_test_type_from_calibration("Q4")        

    def set_test_type_from_calibration(self, test_type):
        """🔥 MEJORADA: Establece el tipo de prueba y obtiene tiempo desde configuración"""
        print(f"[TEST_TABLE] 🎯 Estableciendo tipo de prueba por calibración: {test_type}")
        
        self.current_test_type = test_type
        
        # 🔥 CREAR AL MENOS UNA FILA SI NO HAY NINGUNA
        if not self.rows:
            self.rows.append(["", "", "", "", "", "", "", ""])
            print(f"[TEST_TABLE] 📝 Creada fila inicial")
        
        # 🔥 RELLENAR TODAS LAS FILAS CON EL TIPO DE PRUEBA SELECCIONADO
        for idx, row in enumerate(self.rows):
            old_type = row[2]
            row[2] = test_type  # Columna de tipo de prueba
            print(f"[TEST_TABLE] 🔄 Fila {idx}: '{old_type}' → '{test_type}'")
        
        # 🔥 OBTENER TIEMPO DESDE CONFIGURACIÓN DE PRUEBAS
        estimated_time_minutes = self.get_configured_time_for_test_type(test_type)
        
        # 🔥 CONFIGURAR TIEMPO EN EL TIMER SI ESTÁ DISPONIBLE
        if self.timer_module:
            self.timer_module.set_time(estimated_time_minutes)
            print(f"[TEST_TABLE] ⏰ Timer configurado con {estimated_time_minutes:.1f} minutos")
        else:
            print(f"[TEST_TABLE] ⚠️ Timer module no disponible")
        
        # 🔥 FORZAR ACTUALIZACIÓN COMPLETA DE LA TABLA
        print(f"[TEST_TABLE] 🔄 Forzando actualización completa de tabla...")
        self.update_table()
        
        print(f"[TEST_TABLE] ✅ Tipo de prueba establecido: {test_type}")
        print(f"[TEST_TABLE] ⏱️ Tiempo configurado: {estimated_time_minutes:.1f} minutos")

    def get_configured_time_for_test_type(self, test_type):
        """🔥 MEJORADA: Obtiene el tiempo configurado desde múltiples fuentes"""
        try:
            # 🔥 MÉTODO 1: INTENTAR OBTENER DESDE LA SESIÓN DE LA PÁGINA
            if hasattr(self, 'page') and self.page and hasattr(self.page, 'session'):
                try:
                    # 🔥 INTENTAR MÉTODO GET DE SESSIONSTORAGE
                    if hasattr(self.page.session, 'get'):
                        test_configurations = self.page.session.get("test_configurations") or []
                    else:
                        test_configurations = []
                    
                    print(f"[TEST_TABLE] 🔍 Configuraciones desde sesión: {len(test_configurations)}")
                    
                    # 🔥 BUSCAR CONFIGURACIÓN DEL TIPO ESPECIFICADO
                    for config in test_configurations:
                        config_type = config.get("test_type")
                        estimated_time = config.get("estimated_time", 0)
                        
                        if config_type == test_type:
                            print(f"[TEST_TABLE] 📊 ✅ Tiempo encontrado en sesión para {test_type}: {estimated_time:.2f} min")
                            return estimated_time
                            
                except Exception as e:
                    print(f"[TEST_TABLE] ⚠️ Error accediendo a sesión: {e}")
            
            # 🔥 MÉTODO 2: USAR CONFIGURACIONES DIRECTAS
            if hasattr(self, 'test_configurations_direct') and self.test_configurations_direct:
                print(f"[TEST_TABLE] 🔍 Configuraciones directas disponibles: {len(self.test_configurations_direct)}")
                
                for config in self.test_configurations_direct:
                    config_type = config.get("test_type")
                    estimated_time = config.get("estimated_time", 0)
                    
                    print(f"[TEST_TABLE] 🔍 Revisando config directa: tipo={config_type}, tiempo={estimated_time}")
                    
                    if config_type == test_type:
                        print(f"[TEST_TABLE] 📊 ✅ Tiempo encontrado en configuraciones directas para {test_type}: {estimated_time:.2f} min")
                        return estimated_time
            
            # 🔥 MÉTODO 3: USAR VALORES FIJOS PARA CADA TIPO
            default_times = {
                "Q1": 3.0,  # 3 minutos para Q1
                "Q2": 4.0,  # 4 minutos para Q2  
                "Q3": 5.0,  # 5 minutos para Q3
                "Q4": 5.0   # 5 minutos para Q4
            }
            
            if test_type in default_times:
                default_time = default_times[test_type]
                print(f"[TEST_TABLE] 🔄 Usando tiempo por defecto para {test_type}: {default_time} minutos")
                return default_time
            
            # 🔥 MÉTODO 4: CALCULAR DESDE FLUJO
            print(f"[TEST_TABLE] ⚠️ Calculando tiempo para {test_type}...")
            return self.calculate_estimated_time_from_flow(test_type)
            
        except Exception as e:
            print(f"[TEST_TABLE] ❌ Error obteniendo tiempo configurado: {e}")
            return 5.0  # Valor por defecto
        
    def calculate_estimated_time_from_flow(self, test_type, default_volume=100):
        """🔥 FUNCIÓN DE RESPALDO: Calcula tiempo usando la misma fórmula que test_configuration"""
        try:
            # 🔥 OBTENER CAUDAL BASE PARA EL TIPO DE PRUEBA
            base_flow = self.instant_values.get(test_type, 0)
            
            if base_flow <= 0:
                print(f"[TEST_TABLE] ⚠️ Caudal para {test_type} es 0, usando default")
                return 5.0  # 5 minutos por defecto
            
            # 🔥 CALCULAR QMAX (10% SOBRE EL CAUDAL NOMINAL) - MISMA FÓRMULA QUE TEST_CONFIG
            qmax = round(base_flow * 1.1, 2)
            
            if qmax <= 0:
                return 5.0
            
            # 🔥 CALCULAR TIEMPO: (volumen * 60) / qmax - MISMA FÓRMULA QUE TEST_CONFIG
            time_decimal = (default_volume * 60) / qmax
            
            # 🔥 MÍNIMO 1 MINUTO, MÁXIMO 30 MINUTOS
            time_minutes = max(1.0, min(30.0, time_decimal))
            
            print(f"[TEST_TABLE] ⏱️ Tiempo calculado para {test_type}: {default_volume}L / {qmax:.2f}L/h = {time_minutes:.1f} min")
            
            return time_minutes
            
        except Exception as e:
            print(f"[TEST_TABLE] ❌ Error calculando tiempo estimado: {e}")
            return 5.0  # Default 5 minutos
        
    def set_page_reference(self, page):
        """🔥 NUEVA FUNCIÓN: Establece referencia a la página para acceder a sesión"""
        self.page = page
        print("[TEST_TABLE] 🔗 Referencia a página establecida para acceso a configuraciones")


    def debug_set_test_type(self, test_type):
        """🔥 FUNCIÓN DEBUG: Fuerza el establecimiento de un tipo de prueba"""
        print(f"[TEST_TABLE] 🔧 DEBUG: Forzando tipo de prueba a {test_type}")
        self.set_test_type_from_calibration(test_type)

    def set_test_type_from_button(self, test_type):
        """🔥 FUNCIÓN EXISTENTE: Establece el tipo de prueba desde el botón presionado"""
        self.current_test_type = test_type
        
        # 🔥 CREAR AL MENOS UNA FILA SI NO HAY NINGUNA
        if not self.rows:
            self.rows.append(["", "", "", "", "", "", "", ""])
        
        # 🔥 RELLENAR TODAS LAS FILAS CON EL TIPO DE PRUEBA SELECCIONADO
        for row in self.rows:
            row[2] = test_type  # Columna de tipo de prueba
        
        # 🔥 CALCULAR TIEMPO ESTIMADO TAMBIÉN PARA BOTONES
        estimated_time = self.calculate_estimated_time(test_type)
        self.timer_module.set_time(estimated_time)
        
        self.update_table()
        print(f"[TEST_TABLE] 🎯 Tipo de prueba establecido: {test_type}")
        print(f"[TEST_TABLE] ⏱️ Tiempo estimado configurado: {estimated_time:.1f} minutos")

    def _on_timer_finished(self):
        """Callback cuando el timer termina"""
        print("[TEST_TABLE] ⏰ Timer terminado")
        if hasattr(self, 'on_timer_finished'):
            self.on_timer_finished()

    def get_test_count(self, serial, test_type, max_idx):
        """Cuenta cuántas pruebas del mismo tipo y serial hay hasta el índice dado"""
        count = 0
        for i in range(max_idx + 1):
            if i < len(self.rows) and self.rows[i][1] == serial and self.rows[i][2] == test_type:
                count += 1
        return count if serial else ""

    def get_pattern_volume_for_row(self, row_idx):
        """🔥 CORREGIDA: Obtiene el volumen patrón directamente de valores instantáneos"""
        try:
            if row_idx >= len(self.rows):
                return 0.1
                
            test_type = self.rows[row_idx][2]
            if not test_type or test_type == "Escoja una opción":
                return 0.1
            
            # 🔥 SIMPLIFICADO: OBTENER DIRECTAMENTE EL VALOR INSTANTÁNEO ACTUAL
            instant_volume = self.instant_values.get(test_type, 0.1)
            
            # 🔥 SI HAY MÓDULO DE VALORES INSTANTÁNEOS, USAR ESE VALOR
            if self.instant_values_module:
                try:
                    module_value = self.instant_values_module.get_pattern_value_for_test(test_type)
                    if module_value > 0.1:
                        instant_volume = module_value
                        print(f"[TEST_TABLE] 📊 Valor del módulo para {test_type}: {module_value:.2f}")
                except Exception as e:
                    print(f"[TEST_TABLE] ⚠️ Error obteniendo valor del módulo: {e}")
            
            # 🔥 ASEGURAR VALOR MÍNIMO
            instant_volume = max(instant_volume, 0.1)
            
            print(f"[TEST_TABLE] 📊 Volumen patrón para fila {row_idx} ({test_type}): {instant_volume:.2f}")
            return instant_volume
                    
        except Exception as e:
            print(f"[TEST_TABLE] ❌ Error obteniendo volumen patrón: {e}")
            return 0.1

    def calculate_error(self, start_str, end_str, pattern_volume, test_type):
        """Calcula el error porcentual y determina si pasa o no"""
        try:
            start = float(start_str) if start_str else 0
            end = float(end_str) if end_str else 0
            pattern = max(pattern_volume, 0.1)

            error = (((end - start) - pattern) / pattern) * 100
            
            # 🔥 USAR self.meter_status EN LUGAR DEL DROPDOWN
            status = self.meter_status
            
            # 🔥 TOLERANCIAS DINÁMICAS SEGÚN ESTADO Y TIPO DE PRUEBA
            base_tolerances = {
                "Q1": 5.0,  # Q1: ±5% para nuevo
                "Q2": 2.0,  # Q2: ±2% para nuevo  
                "Q3": 2.0,  # Q3: ±2% para nuevo
                "Q4": 2.0   # Q4: ±2% para nuevo
            }
            
            base_tolerance = base_tolerances.get(test_type, 2.0)
            
            if status == "nuevo":
                tolerance = base_tolerance
            elif status == "usado":
                tolerance = base_tolerance * 2  # Doble tolerancia para usados
            else:
                tolerance = base_tolerance  # Default

            return round(error, 2), "PASA" if abs(error) <= tolerance else "NO PASA", \
                ft.Colors.GREEN if abs(error) <= tolerance else ft.Colors.RED
                
        except Exception as e:
            print(f"[TEST_TABLE] ❌ Error calculando: {e}")
            return 0, "Error", ft.Colors.GREY

    def _validate_initial_readings(self):
        """🔥 NUEVA FUNCIÓN: Valida que todas las lecturas iniciales estén llenas"""
        empty_rows = []
        
        for idx, row in enumerate(self.rows):
            serial = row[1].strip()
            initial_reading = row[3].strip()
            
            # Solo validar filas que tienen serial
            if serial and not initial_reading:
                empty_rows.append(idx + 1)
        
        return empty_rows

    def _show_validation_alert(self, empty_rows):
        """🔥 NUEVA FUNCIÓN: Muestra alerta de validación"""
        def close_alert(e):
            alert.open = False
            if hasattr(alert, 'page') and alert.page is not None:
                alert.page.update()
        
        rows_text = ", ".join([f"#{row}" for row in empty_rows])
        message = f"⚠️ Las siguientes filas tienen seriales pero no lecturas iniciales:\n\n{rows_text}\n\nPor favor, complete las lecturas iniciales antes de iniciar la prueba."
        
        alert = ft.AlertDialog(
            title=ft.Text("❌ Lecturas Iniciales Faltantes"),
            content=ft.Text(message, size=14),
            actions=[
                ft.TextButton("Entendido", on_click=close_alert)
            ],
        )
        
        if hasattr(self.data_table, 'page') and self.data_table.page is not None:
            self.data_table.page.overlay.append(alert)
            alert.open = True
            self.data_table.page.update()

    def on_text_change_with_pattern_update(self, e, row_idx, col_idx):
        """🔥 NUEVA FUNCIÓN: Maneja cambios de texto Y actualiza valores patrón"""
        # 🔥 ACTUALIZAR EL VALOR EN EL ARRAY
        if row_idx < len(self.rows):
            self.rows[row_idx][col_idx] = e.control.value
        
        # 🔥 ACTUALIZAR SOLO LOS VALORES PATRÓN/ERROR DE ESTA FILA
        self.update_single_row_pattern(row_idx)

    def update_single_row_pattern(self, row_idx):
        """🔥 NUEVA FUNCIÓN: Actualiza el valor patrón y error de UNA SOLA fila"""
        try:
            if row_idx >= len(self.rows):
                return
            
            # 🔥 OBTENER NUEVO VALOR PATRÓN
            pattern_volume = self.get_pattern_volume_for_row(row_idx)
            
            # 🔥 ACTUALIZAR EL VALOR EN EL ARRAY
            self.rows[row_idx][5] = f"{pattern_volume:.2f}"
            
            # 🔥 ACTUALIZAR WIDGET DE VOLUMEN PATRÓN SI EXISTE
            if row_idx in self.pattern_volume_cells:
                pattern_cell = self.pattern_volume_cells[row_idx]
                if hasattr(pattern_cell, 'value'):
                    pattern_cell.value = f"{pattern_volume:.2f}"
                    try:
                        pattern_cell.update()
                    except:
                        pass
            
            # 🔥 RECALCULAR ERROR
            row = self.rows[row_idx]
            error, status_text, status_color = self.calculate_error(row[3], row[4], pattern_volume, row[2])
            
            # 🔥 ACTUALIZAR ERROR EN EL ARRAY
            self.rows[row_idx][6] = str(error)
            self.rows[row_idx][7] = status_text
            
            # 🔥 ACTUALIZAR WIDGET DE ERROR SI EXISTE
            if row_idx in self.error_cells:
                error_cell = self.error_cells[row_idx]
                if hasattr(error_cell, 'value'):
                    error_cell.value = str(error)
                    try:
                        error_cell.update()
                    except:
                        pass
            
            # 🔥 ACTUALIZAR WIDGET DE ESTADO SI EXISTE
            if row_idx in self.status_cells:
                status_container = self.status_cells[row_idx]
                if hasattr(status_container, 'content') and hasattr(status_container.content, 'value'):
                    status_container.content.value = status_text
                    status_container.content.color = "white"
                    status_container.bgcolor = status_color
                    try:
                        status_container.update()
                    except:
                        pass
            
        except Exception as e:
            print(f"[TEST_TABLE] ❌ Error actualizando fila {row_idx}: {e}")


    def update_table(self):
        """🔥 MEJORADA: Actualiza la tabla y guarda referencias a las celdas importantes"""
        try:
            print(f"[TEST_TABLE] 🔄 Actualizando tabla con {len(self.rows)} filas")
            data_rows = []
            
            # 🔥 LIMPIAR REFERENCIAS ANTERIORES
            self.pattern_volume_cells.clear()
            self.error_cells.clear()
            self.status_cells.clear()
            
            for idx, row in enumerate(self.rows):
                if idx >= len(self.rows):
                    continue
                    
                test_num = self.get_test_count(row[1], row[2], idx)
                pattern_volume = self.get_pattern_volume_for_row(idx)
                
                # 🔥 ACTUALIZAR EL VOLUMEN PATRÓN EN LA FILA
                self.rows[idx][5] = f"{pattern_volume:.2f}"
                
                error, status_text, status_color = self.calculate_error(row[3], row[4], pattern_volume, row[2])
                self.rows[idx][6] = str(error)
                self.rows[idx][7] = status_text

                # 🔥 CREAR WIDGETS CON REFERENCIAS GUARDADAS
                
                # 🔥 WIDGET DE VOLUMEN PATRÓN CON REFERENCIA
                pattern_text = ft.Text(
                    f"{pattern_volume:.2f}",
                    weight="bold",
                    color=ft.Colors.BLUE_700,
                    text_align=ft.TextAlign.CENTER,
                )
                self.pattern_volume_cells[idx] = pattern_text  # 🔥 GUARDAR REFERENCIA
                
                pattern_container = ft.Container(
                    content=pattern_text,
                    width=75,
                    height=30,
                    padding=ft.padding.all(6),
                    bgcolor=ft.Colors.BLUE_50,
                    border_radius=8,
                    alignment=ft.alignment.center,
                    margin=ft.margin.symmetric(vertical=5),
                )
                
                # 🔥 WIDGET DE ERROR CON REFERENCIA
                error_text = ft.Text(str(error), weight="bold", text_align=ft.TextAlign.CENTER)
                self.error_cells[idx] = error_text  # 🔥 GUARDAR REFERENCIA
                
                # 🔥 WIDGET DE ESTADO CON REFERENCIA
                status_text_widget = ft.Text(
                    status_text, 
                    color="white", 
                    weight="bold", 
                    size=12,
                    text_align=ft.TextAlign.CENTER
                )
                
                status_container = ft.Container(
                    content=status_text_widget,
                    bgcolor=status_color,
                    padding=ft.padding.symmetric(horizontal=8, vertical=6),
                    border_radius=8,
                    alignment=ft.alignment.center,
                    width=80,
                    height=28,
                    margin=ft.margin.symmetric(vertical=8),
                )
                self.status_cells[idx] = status_container  # 🔥 GUARDAR REFERENCIA
    
                data_rows.append(ft.DataRow(cells=[
                    # 🔥 CELDA DE NÚMERO - CENTRADA
                    ft.DataCell(ft.Container(
                        ft.Text(str(test_num)),
                        alignment=ft.alignment.center,
                    )),
                    # 🔥 CELDA DE SERIAL - CENTRADA
                    ft.DataCell(ft.Container(
                        ft.TextField(
                            value=row[1],
                            on_change=lambda e, row_idx=idx: self.on_text_change(e, row_idx, 1),
                            on_submit=lambda e, row_idx=idx: self.recalculate_errors(None),
                            keyboard_type=ft.KeyboardType.NUMBER,
                            input_filter=ft.InputFilter(allow=True, regex_string=r"^\d*$"),
                            dense=True,
                            border=ft.InputBorder.UNDERLINE,
                            border_radius=12,
                            filled=True,
                            bgcolor=INPUT_BG,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        width=120,
                        padding=0,
                        alignment=ft.alignment.center,
                    )),
                    # 🔥 CELDA DE TIPO DE PRUEBA - AHORA SOLO TEXTO (NO DROPDOWN)
                    ft.DataCell(ft.Container(
                        ft.Container(
                            ft.Text(
                                row[2] if row[2] and row[2] != "Escoja una opción" else "Sin definir",
                                weight="bold",
                                color=ft.Colors.PURPLE_700,
                                text_align=ft.TextAlign.CENTER,
                                size=12,
                            ),
                            width=80,
                            height=28,
                            padding=ft.padding.all(6),
                            bgcolor=ft.Colors.PURPLE_50,
                            border_radius=8,
                            alignment=ft.alignment.center,
                            margin=ft.margin.symmetric(vertical=5),
                        ),
                        width=90,
                        alignment=ft.alignment.center,
                    )),
                    # 🔥 CELDA DE LECTURA INICIAL - CENTRADA
                    ft.DataCell(ft.Container(
                        ft.TextField(
                            value=row[3],
                            on_change=lambda e, row_idx=idx: self.on_text_change_with_pattern_update(e, row_idx, 3),  # 🔥 NUEVA FUNCIÓN
                            on_submit=lambda e, row_idx=idx: self.recalculate_errors(None),
                            keyboard_type=ft.KeyboardType.NUMBER,
                            input_filter=ft.InputFilter(allow=True, regex_string=r"^\d*\.?\d*$"),
                            dense=True,
                            border=ft.InputBorder.UNDERLINE,
                            border_radius=12,
                            filled=True,
                            bgcolor=INPUT_BG,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        width=80,
                        padding=0,
                        alignment=ft.alignment.center,
                    )),
                    # 🔥 CELDA DE LECTURA FINAL - CENTRADA
                    ft.DataCell(ft.Container(
                        ft.TextField(
                            value=row[4],
                            on_change=lambda e, row_idx=idx: self.on_text_change_with_pattern_update(e, row_idx, 4),  # 🔥 NUEVA FUNCIÓN
                            on_submit=lambda e, row_idx=idx: self.recalculate_errors(None),
                            keyboard_type=ft.KeyboardType.NUMBER,
                            input_filter=ft.InputFilter(allow=True, regex_string=r"^\d*\.?\d*$"),
                            dense=True,
                            border=ft.InputBorder.UNDERLINE,
                            border_radius=12,
                            filled=True,
                            bgcolor=INPUT_BG,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        width=80,
                        padding=0,
                        alignment=ft.alignment.center,
                    )),
                    # 🔥 COLUMNA DE VOLUMEN PATRÓN CON REFERENCIA GUARDADA
                    ft.DataCell(ft.Container(
                        pattern_container,
                        width=90,
                        alignment=ft.alignment.center,
                    )),
                    # 🔥 CELDA DE ERROR CON REFERENCIA GUARDADA
                    ft.DataCell(ft.Container(
                        error_text,
                        alignment=ft.alignment.center,
                        margin=ft.margin.symmetric(vertical=5),
                    )),
                    # 🔥 COLUMNA DE ESTADO CON REFERENCIA GUARDADA
                    ft.DataCell(ft.Container(
                        status_container,
                        alignment=ft.alignment.center,
                        width=100,
                    )),
                    # 🔥 CELDA DE BOTÓN - CENTRADA
                    ft.DataCell(ft.Container(
                        ft.IconButton(
                            icon=ft.Icons.DELETE,
                            tooltip="Eliminar fila",
                            icon_color=ft.Colors.RED_400,
                            on_click=lambda e, idx=idx: self.remove_row(idx),
                        ),
                        alignment=ft.alignment.center,
                        margin=ft.margin.symmetric(vertical=3),
                    )),
                ]))
            
            self.data_table.rows = data_rows
            print(f"[TEST_TABLE] 🔄 DataTable actualizado con {len(data_rows)} filas")
            print(f"[TEST_TABLE] 🔗 Referencias guardadas: {len(self.pattern_volume_cells)} vol_patrón, {len(self.error_cells)} errores, {len(self.status_cells)} estados")
            
            if hasattr(self.data_table, 'page') and self.data_table.page is not None:
                self.data_table.update()
            
        except Exception as e:
            print(f"❌ Error actualizando tabla: {e}")
            import traceback
            traceback.print_exc()

    def add_row(self, e):
        """Agrega una nueva fila a la tabla"""
        self.add_row_counter += 1
        print(f"[TEST_TABLE] 🔄 add_row llamado #{self.add_row_counter}")
        print(f"[TEST_TABLE] 🔄 Agregando fila. Filas antes: {len(self.rows)}")
        
        # 🔥 AGREGAR FILA CON TIPO DE PRUEBA ACTUAL (SI HAY UNO SELECCIONADO)
        test_type = self.current_test_type if self.current_test_type else ""
        self.rows.append(["", "", test_type, "", "", "", "", ""])
        print(f"[TEST_TABLE] 🔄 Filas después: {len(self.rows)}")
        self.update_table()

    def remove_row(self, idx):
        """Elimina una fila de la tabla"""
        if len(self.rows) > 1 and idx < len(self.rows):
            print(f"[TEST_TABLE] 🗑️ Eliminando fila {idx}")
            self.rows.pop(idx)
            self.update_table()
        else:
            print(f"[TEST_TABLE] ⚠️ No se puede eliminar fila {idx} (total: {len(self.rows)})")

    def on_text_change(self, e, row_idx, col_idx):
        """Maneja cambios en los campos de texto"""
        if row_idx < len(self.rows):
            self.rows[row_idx][col_idx] = e.control.value
            # 🔥 NO ACTUALIZAR TABLA AUTOMÁTICAMENTE PARA EVITAR PERDER FOCO

    def _on_start_test(self, e):
        """🔥 MEJORADA: Inicia la prueba con timer de cuenta regresiva"""
        # 🔥 VALIDAR QUE HAYA UN TIPO DE PRUEBA SELECCIONADO
        if not self.current_test_type:
            print("[TEST_TABLE] ⚠️ No hay tipo de prueba seleccionado")
            self._show_error_alert(
                "❌ Tipo de Prueba No Definido",
                "Por favor, espere a que el sistema detecte la calibración (Q1, Q2, Q3 o Q4) antes de iniciar la prueba."
            )
            return
        
        # 🔥 VALIDAR QUE HAY AL MENOS UNA FILA CON SERIAL
        has_serial = any(row[1].strip() for row in self.rows)
        if not has_serial:
            print("[TEST_TABLE] ⚠️ No hay seriales ingresados")
            self._show_error_alert(
                "❌ Seriales Requeridos",
                "Por favor, ingrese al menos un número de serie antes de iniciar la prueba."
            )
            return
        
        # 🔥 VALIDAR LECTURAS INICIALES COMPLETAS
        empty_rows = self._validate_initial_readings()
        if empty_rows:
            print(f"[TEST_TABLE] ❌ Faltan lecturas iniciales en filas: {empty_rows}")
            self._show_validation_alert(empty_rows)
            return
        
        print("[TEST_TABLE] ✅ Todas las validaciones pasadas, iniciando prueba...")
        
        # 🔥 MARCAR PRUEBA COMO EN PROGRESO
        self.test_in_progress = True
        self.active_test_type = self.current_test_type
        
        # 🔥 VALIDAR QUE TENEMOS TIMER MODULE
        if not self.timer_module:
            print("[TEST_TABLE] ❌ Timer module no disponible")
            self._show_error_alert(
                "❌ Error del Sistema",
                "El módulo de timer no está disponible. Contacte al administrador."
            )
            return
        
        # 🔥 OBTENER TIEMPO CONFIGURADO PARA EL TIPO DE PRUEBA ACTUAL
        configured_time = self.get_configured_time_for_test_type(self.current_test_type)
        
        # 🔥 ASEGURAR QUE EL TIMER TENGA EL TIEMPO CORRECTO ANTES DE INICIAR
        self.timer_module.set_time(configured_time)
        print(f"[TEST_TABLE] ⏱️ Timer configurado con {configured_time:.1f} minutos para {self.current_test_type}")
        
        # 🔥 ENVIAR COMANDO M269 (INICIAR PRUEBA)
        if self.send_modbus_command:
            print("[TEST_TABLE] 📡 Enviando comando M269 (Iniciar Prueba)")
            try:
                self.send_modbus_command(269)
            except Exception as ex:
                print(f"[TEST_TABLE] ❌ Error enviando comando M269: {ex}")
        
        # 🔥 ACTUALIZAR ESTADO DE BOTONES
        self.start_test_button.disabled = True
        self.finish_test_button.disabled = False
        
        # 🔥 INICIAR CUENTA REGRESIVA CON EL TIEMPO CONFIGURADO
        print(f"[TEST_TABLE] 🚀 Iniciando cuenta regresiva de {configured_time:.1f} minutos...")
        self.timer_module.start_countdown()
        print(f"[TEST_TABLE] ⏰ Cuenta regresiva iniciada: {configured_time:.1f} minutos")
        
        if hasattr(self, 'on_test_control'):
            self.on_test_control("start")
            
        try:
            self.start_test_button.update()
            self.finish_test_button.update()
        except:
            pass
            
        print(f"[TEST_TABLE] ▶️ Prueba iniciada: {self.current_test_type} - Tiempo: {configured_time:.1f} min")

    def debug_show_configurations(self):
        """🔥 FUNCIÓN DEBUG MEJORADA: Muestra las configuraciones desde todas las fuentes"""
        try:
            print(f"[TEST_TABLE] 🔍 === DEBUG CONFIGURACIONES ===")
            
            # 🔥 DEBUG 1: CONFIGURACIONES DIRECTAS
            if hasattr(self, 'test_configurations_direct') and self.test_configurations_direct:
                print(f"[TEST_TABLE] 📦 Configuraciones directas: {len(self.test_configurations_direct)}")
                for i, config in enumerate(self.test_configurations_direct):
                    print(f"[TEST_TABLE] {i+1}. {config.get('test_name', 'Sin nombre')}")
                    print(f"    • Tipo: {config.get('test_type', 'N/A')}")
                    print(f"    • Volumen: {config.get('volume', 0)} L")
                    print(f"    • Tiempo: {config.get('estimated_time', 0):.2f} min")
            else:
                print(f"[TEST_TABLE] ⚠️ No hay configuraciones directas")
            
            # 🔥 DEBUG 2: CONFIGURACIONES DE SESIÓN
            if hasattr(self, 'page') and self.page and hasattr(self.page, 'session'):
                try:
                    if hasattr(self.page.session, 'get'):
                        test_configurations = self.page.session.get("test_configurations") or []
                        print(f"[TEST_TABLE] 📊 Configuraciones de sesión: {len(test_configurations)}")
                        
                        for i, config in enumerate(test_configurations):
                            print(f"[TEST_TABLE] S{i+1}. {config.get('test_name', 'Sin nombre')}")
                            print(f"    • Tipo: {config.get('test_type', 'N/A')}")
                            print(f"    • Tiempo: {config.get('estimated_time', 0):.2f} min")
                    else:
                        print(f"[TEST_TABLE] ⚠️ Sesión no tiene método get")
                except Exception as e:
                    print(f"[TEST_TABLE] ❌ Error accediendo sesión: {e}")
            else:
                print(f"[TEST_TABLE] ⚠️ No hay acceso a sesión")
            
            print(f"[TEST_TABLE] 🔍 === FIN DEBUG ===")
            
        except Exception as e:
            print(f"[TEST_TABLE] ❌ Error en debug configuraciones: {e}")

    # 🔥 FUNCIÓN DE PRUEBA PARA VERIFICAR CONFIGURACIONES
    def test_all_configurations(self):
        """🔥 FUNCIÓN DE PRUEBA: Verifica todas las configuraciones disponibles"""
        print("[TEST_TABLE] 🧪 === PRUEBA DE CONFIGURACIONES ===")
        
        test_types = ["Q1", "Q2", "Q3", "Q4"]
        
        for test_type in test_types:
            time_result = self.get_configured_time_for_test_type(test_type)
            print(f"[TEST_TABLE] 🧪 {test_type}: {time_result:.2f} minutos")
        
        print("[TEST_TABLE] 🧪 === FIN PRUEBA ===")

    def _validate_initial_readings(self):
        """🔥 MEJORADA: Valida que todas las lecturas iniciales estén llenas para filas con serial"""
        empty_rows = []
        
        for idx, row in enumerate(self.rows):
            serial = row[1].strip()
            initial_reading = row[3].strip()
            
            # Solo validar filas que tienen serial
            if serial and not initial_reading:
                empty_rows.append(idx + 1)  # +1 para numeración humana
        
        return empty_rows

    def _show_validation_alert(self, empty_rows):
        """🔥 MEJORADA: Muestra alerta de validación más clara"""
        rows_text = ", ".join([f"#{row}" for row in empty_rows])
        message = f"⚠️ Las siguientes filas tienen números de serie pero no tienen lecturas iniciales:\n\n🔢 Filas: {rows_text}\n\n📝 Por favor, complete las lecturas iniciales antes de iniciar la prueba."
        
        self._show_error_alert("❌ Lecturas Iniciales Faltantes", message)

    def _show_error_alert(self, title, message):
        """🔥 NUEVA FUNCIÓN: Muestra alertas de error de forma centralizada"""
        def close_alert(e):
            alert.open = False
            if hasattr(alert, 'page') and alert.page is not None:
                alert.page.update()
        
        alert = ft.AlertDialog(
            title=ft.Text(title, size=16, weight="bold"),
            content=ft.Text(message, size=14),
            actions=[
                ft.TextButton("Entendido", on_click=close_alert, style=ft.ButtonStyle(color=ft.Colors.BLUE))
            ],
        )
        
        if hasattr(self.data_table, 'page') and self.data_table.page is not None:
            self.data_table.page.overlay.append(alert)
            alert.open = True
            self.data_table.page.update()

    def _show_completion_alert(self, test_name, summary):
        """🔥 NUEVA FUNCIÓN: Muestra alerta de prueba completada"""
        def close_alert(e):
            alert.open = False
            if hasattr(alert, 'page') and alert.page is not None:
                alert.page.update()
        
        success_rate = summary['success_rate']
        status_emoji = "🎉" if success_rate >= 80 else "⚠️" if success_rate >= 50 else "❌"
        
        message = f"""🧪 {test_name} completada exitosamente
        
📊 Resumen de Resultados:
• Total de medidores: {summary['total']}
• ✅ Aprobados: {summary['passed']}
• ❌ Reprobados: {summary['failed']}
• 📈 Tasa de éxito: {success_rate:.1f}%

Los datos han sido guardados y la tabla está lista para la siguiente prueba."""
        
        alert = ft.AlertDialog(
            title=ft.Text(f"{status_emoji} Prueba Completada", size=16, weight="bold"),
            content=ft.Text(message, size=14),
            actions=[
                ft.TextButton("Continuar", on_click=close_alert, style=ft.ButtonStyle(color=ft.Colors.GREEN))
            ],
        )
        
        if hasattr(self.data_table, 'page') and self.data_table.page is not None:
            self.data_table.page.overlay.append(alert)
            alert.open = True
            self.data_table.page.update()

    def clear_data_preserve_serials(self, serials_to_preserve):
        """🔥 MEJORADA: Limpia datos pero preserva seriales para la siguiente prueba"""
        try:
            print(f"[TEST_TABLE] 🧹 Limpiando datos de {len(self.rows)} filas...")
            
            # 🔥 LIMPIAR FILAS EXISTENTES
            self.rows.clear()
            
            # 🔥 RECREAR FILAS SOLO CON SERIALES Y TIPO DE PRUEBA ACTUAL
            for serial in serials_to_preserve:
                test_type = self.current_test_type if self.current_test_type else ""
                # [#, Serial, Tipo, Inicial, Final, Volumen_Patron, Error, Estado]
                self.rows.append(["", serial, test_type, "", "", "", "", ""])
                print(f"[TEST_TABLE] 📝 Preservado serial: {serial} para tipo: {test_type}")
            
            # 🔥 SI NO HAY SERIALES, CREAR AL MENOS UNA FILA VACÍA
            if not self.rows:
                test_type = self.current_test_type if self.current_test_type else ""
                self.rows.append(["", "", test_type, "", "", "", "", ""])
                print(f"[TEST_TABLE] 📝 Creada fila vacía para tipo: {test_type}")
            
            # 🔥 ACTUALIZAR TABLA PARA MOSTRAR LOS CAMBIOS
            self.update_table()
            
            print(f"[TEST_TABLE] ✅ Datos limpiados, {len(serials_to_preserve)} seriales preservados")
            
        except Exception as e:
            print(f"[TEST_TABLE] ❌ Error limpiando datos: {e}")

    # 🔥 FUNCIÓN ADICIONAL: Obtener resumen de todas las pruebas por tipo
    def get_tests_summary_by_type(self):
        """🔥 NUEVA FUNCIÓN: Obtiene resumen organizado por tipo de prueba"""
        summary_by_type = {}
        
        for test_group in self.completed_tests:
            test_type = test_group["test_type"]
            
            if test_type not in summary_by_type:
                summary_by_type[test_type] = {
                    "test_count": 0,
                    "total_meters": 0,
                    "passed_meters": 0,
                    "failed_meters": 0,
                    "success_rate": 0.0,
                    "tests": []
                }
            
            type_summary = summary_by_type[test_type]
            type_summary["test_count"] += 1
            type_summary["total_meters"] += test_group["summary"]["total"]
            type_summary["passed_meters"] += test_group["summary"]["passed"]
            type_summary["failed_meters"] += test_group["summary"]["failed"]
            type_summary["tests"].append(test_group)
        
        # 🔥 CALCULAR TASAS DE ÉXITO
        for test_type, summary in summary_by_type.items():
            if summary["total_meters"] > 0:
                summary["success_rate"] = (summary["passed_meters"] / summary["total_meters"]) * 100
        
        return summary_by_type

    # 🔥 FUNCIÓN ADICIONAL: Limpiar completamente el historial
    def clear_all_tests(self):
        """🔥 NUEVA FUNCIÓN: Limpia todo el historial de pruebas"""
        self.completed_tests.clear()
        self.test_counters = {"Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0}
        print("[TEST_TABLE] 🗑️ Historial de pruebas limpiado completamente")

    def _on_finish_test(self, e):
        """🔥 NUEVA FUNCIÓN: Finaliza la prueba y guarda resultados"""
        if not self.current_test_type:
            print("[TEST_TABLE] ⚠️ No hay tipo de prueba para finalizar")
            return
            
        # 🔥 INCREMENTAR CONTADOR DE REPETIBILIDAD
        self.test_counters[self.current_test_type] += 1
        current_repetition = self.test_counters[self.current_test_type]
        
        # 🔥 CREAR NOMBRE DE PRUEBA CON REPETIBILIDAD
        if current_repetition == 1:
            test_name = f"Prueba {self.current_test_type}"
        else:
            test_name = f"Prueba {self.current_test_type}.{current_repetition}"
        
        print(f"[TEST_TABLE] 🏁 Finalizando: {test_name}")
        
        # 🔥 RECOPILAR DATOS DE TODAS LAS FILAS VÁLIDAS
        test_results = []
        serials_to_preserve = []
        
        for idx, row in enumerate(self.rows):
            serial = row[1].strip()
            test_type = row[2]
            initial_reading = row[3].strip()
            final_reading = row[4].strip()
            pattern_volume = row[5]
            error = row[6]
            status = row[7]
            
            # 🔥 SOLO PROCESAR FILAS CON DATOS COMPLETOS
            if serial and test_type and initial_reading and final_reading:
                test_data = {
                    "serial": serial,
                    "test_type": test_type,
                    "test_name": test_name,
                    "repetition": current_repetition,
                    "initial_reading": float(initial_reading),
                    "final_reading": float(final_reading),
                    "pattern_volume": float(pattern_volume) if pattern_volume else 0.0,
                    "volume_difference": float(final_reading) - float(initial_reading),
                    "error_percentage": float(error) if error else 0.0,
                    "status": status,
                    "is_passed": status == "PASA",
                    "meter_status": self.meter_status,
                    "completed_at": time.time(),
                }
                
                test_results.append(test_data)
                serials_to_preserve.append(serial)
                
        # 🔥 GUARDAR EN EL ARRAY DE PRUEBAS COMPLETADAS
        if test_results:
            # Crear grupo de prueba
            test_group = {
                "test_name": test_name,
                "test_type": self.current_test_type,
                "repetition": current_repetition,
                "completed_at": time.time(),
                "results": test_results,
                "summary": {
                    "total": len(test_results),
                    "passed": sum(1 for r in test_results if r["is_passed"]),
                    "failed": sum(1 for r in test_results if not r["is_passed"]),
                    "success_rate": (sum(1 for r in test_results if r["is_passed"]) / len(test_results)) * 100
                }
            }
            
            self.completed_tests.append(test_group)
            print(f"[TEST_TABLE] 💾 Guardados {len(test_results)} resultados para {test_name}")
            print(f"[TEST_TABLE] 📊 Total grupos de pruebas: {len(self.completed_tests)}")
        
        # 🔥 LIMPIAR DATOS PERO PRESERVAR SERIALES
        self.clear_data_preserve_serials(serials_to_preserve)
        
        # 🔥 DETENER TIMER Y ACTUALIZAR BOTONES
        self.timer_module.stop_countdown()
        self.start_test_button.disabled = False
        self.finish_test_button.disabled = False
        
        # 🔥 MARCAR PRUEBA COMO NO EN PROGRESO
        self.test_in_progress = False
        
        if hasattr(self, 'on_test_control'):
            self.on_test_control("finish")
            
        try:
            self.start_test_button.update()
            self.finish_test_button.update()
        except:
            pass
            
        print(f"[TEST_TABLE] ✅ Prueba finalizada: {test_name}")

    def clear_data_preserve_serials(self, serials_to_preserve):
        """🔥 NUEVA FUNCIÓN: Limpia datos pero preserva seriales"""
        try:
            # 🔥 LIMPIAR FILAS EXISTENTES
            self.rows.clear()
            
            # 🔥 RECREAR FILAS SOLO CON SERIALES
            for serial in serials_to_preserve:
                test_type = self.current_test_type if self.current_test_type else ""
                self.rows.append(["", serial, test_type, "", "", "", "", ""])
            
            # 🔥 SI NO HAY SERIALES, CREAR AL MENOS UNA FILA VACÍA
            if not self.rows:
                test_type = self.current_test_type if self.current_test_type else ""
                self.rows.append(["", "", test_type, "", "", "", "", ""])
            
            self.update_table()
            print(f"[TEST_TABLE] 🧹 Datos limpiados, {len(serials_to_preserve)} seriales preservados")
            
        except Exception as e:
            print(f"[TEST_TABLE] ❌ Error limpiando datos: {e}")

    def show_volume_history(self, e):
        """🔥 MEJORADO: Muestra historial con tablas separadas por tipo de prueba"""
        if not self.completed_tests:
            # Si no hay pruebas, mostrar mensaje
            def close_dialog(e):
                dialog.open = False
                dialog.page.update()
                
            dialog = ft.AlertDialog(
                title=ft.Text("📋 Historial de Pruebas"),
                content=ft.Text("📭 No hay pruebas completadas aún", size=16, text_align="center"),
                actions=[ft.TextButton("Cerrar", on_click=close_dialog)],
            )
            
            if hasattr(self.data_table, 'page') and self.data_table.page is not None:
                self.data_table.page.overlay.append(dialog)
                dialog.open = True
                self.data_table.page.update()
            return
        
        # 🔥 CREAR CONTENIDO CON TABLAS SEPARADAS
        content_column = ft.Column([], spacing=20, scroll=ft.ScrollMode.AUTO)
        
        # 🔥 ESTADÍSTICAS GENERALES
        total_tests = len(self.completed_tests)
        total_results = sum(len(test["results"]) for test in self.completed_tests)
        total_passed = sum(test["summary"]["passed"] for test in self.completed_tests)
        
        stats_container = ft.Container(
            content=ft.Column([
                ft.Text("📊 Estadísticas Generales", size=16, weight="bold", color=ft.Colors.BLUE_700),
                ft.Row([
                    ft.Text(f"Grupos de pruebas: {total_tests}", size=12),
                    ft.Text(f"Total medidores: {total_results}", size=12),
                    ft.Text(f"Aprobados: {total_passed}", size=12, color=ft.Colors.GREEN),
                    ft.Text(f"Reprobados: {total_results - total_passed}", size=12, color=ft.Colors.RED),
                ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
            ], spacing=10),
            padding=15,
            border_radius=8,
            bgcolor=ft.Colors.GREY_100,
        )
        content_column.controls.append(stats_container)
        
        # 🔥 CREAR TABLA PARA CADA GRUPO DE PRUEBA
        for test_group in self.completed_tests:
            test_name = test_group["test_name"]
            results = test_group["results"]
            summary = test_group["summary"]
            
            # 🔥 HEADER DE LA TABLA
            header = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text(f"🧪 {test_name}", size=14, weight="bold", color=ft.Colors.PURPLE_700),
                        ft.Text(f"✅ {summary['passed']}/{summary['total']} ({summary['success_rate']:.1f}%)", 
                                size=12, color=ft.Colors.GREEN if summary['success_rate'] >= 80 else ft.Colors.ORANGE),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ], spacing=5),
                padding=10,
                border_radius=8,
                bgcolor=ft.Colors.PURPLE_50,
                border=ft.border.all(1, ft.Colors.PURPLE_300),
            )
            content_column.controls.append(header)
            
            # 🔥 CREAR TABLA DE RESULTADOS
            table_rows = []
            for i, result in enumerate(results, 1):
                result_color = ft.Colors.GREEN if result["is_passed"] else ft.Colors.RED
                
                table_rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(i), size=12)),
                        ft.DataCell(ft.Text(result["serial"], size=12)),
                        ft.DataCell(ft.Text(f"{result['initial_reading']:.2f}", size=12)),
                        ft.DataCell(ft.Text(f"{result['final_reading']:.2f}", size=12)),
                        ft.DataCell(ft.Text(f"{result['volume_difference']:.2f}L", size=12)),
                        ft.DataCell(ft.Text(f"{result['error_percentage']:.2f}%", size=12)),
                        ft.DataCell(
                            ft.Text(
                                "✅ PASA" if result["is_passed"] else "❌ NO PASA",
                                size=12,
                                color=result_color,
                                weight="bold"
                            )
                        ),
                    ])
                )
            
            results_table = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("#", size=12, weight="bold")),
                    ft.DataColumn(ft.Text("Serial", size=12, weight="bold")),
                    ft.DataColumn(ft.Text("Inicial", size=12, weight="bold")),
                    ft.DataColumn(ft.Text("Final", size=12, weight="bold")),
                    ft.DataColumn(ft.Text("Diferencia", size=12, weight="bold")),
                    ft.DataColumn(ft.Text("Error %", size=12, weight="bold")),
                    ft.DataColumn(ft.Text("Estado", size=12, weight="bold")),
                ],
                rows=table_rows,
                border=ft.border.all(1, ft.Colors.GREY_300),
                heading_row_color=ft.Colors.GREY_100,
            )
            
            # 🔥 CONTAINER DE LA TABLA CON SCROLL
            table_container = ft.Container(
                content=ft.Row([results_table], scroll=ft.ScrollMode.AUTO),
                height=min(200, len(table_rows) * 50 + 50),  # Altura dinámica
                border_radius=8,
                border=ft.border.all(1, ft.Colors.GREY_300),
                padding=5,
            )
            content_column.controls.append(table_container)
        
        # 🔥 CREAR DIÁLOGO
        def close_dialog(e):
            dialog.open = False
            if hasattr(dialog, 'page') and dialog.page is not None:
                dialog.page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("📋 Historial de Pruebas"),
            content=ft.Container(
                content=content_column,
                width=800,
                height=600,
            ),
            actions=[ft.TextButton("Cerrar", on_click=close_dialog)],
        )
        
        if hasattr(self.data_table, 'page') and self.data_table.page is not None:
            self.data_table.page.overlay.append(dialog)
            dialog.open = True
            self.data_table.page.update()


    def update_instant_values(self, q1, q2, q3, q4):
        """🔥 MEJORADA: Actualiza los valores instantáneos Y fuerza actualización de tabla"""
        # 🔥 ASEGURAR QUE TODOS LOS VALORES SEAN AL MENOS 0.1
        q1 = max(q1, 0.1)
        q2 = max(q2, 0.1)
        q3 = max(q3, 0.1)
        q4 = max(q4, 0.1)
        
        # 🔥 ACTUALIZAR TODOS LOS VALORES
        old_values = self.instant_values.copy()
        self.instant_values["Q1"] = q1
        self.instant_values["Q2"] = q2
        self.instant_values["Q3"] = q3
        self.instant_values["Q4"] = q4
        
        # 🔥 DEBUG: MOSTRAR CAMBIOS SIGNIFICATIVOS
        for test_type in ["Q1", "Q2", "Q3", "Q4"]:
            old_val = old_values.get(test_type, 0.1)
            new_val = self.instant_values[test_type]
            if abs(new_val - old_val) > 1.0:
                print(f"[TEST_TABLE] 📊 {test_type}: {old_val:.2f} → {new_val:.2f}")
        
        # 🔥 FORZAR ACTUALIZACIÓN DE VALORES PATRÓN EN TIEMPO REAL
        self.update_pattern_values_only()
        
        # 🔥 SI HAY FILAS Y NO HAY TIPO DE PRUEBA, INTENTAR DETECTAR AUTOMÁTICAMENTE
        if self.rows and not self.current_test_type:
            # Detectar el tipo con mayor valor
            max_value = max(q1, q2, q3, q4)
            if max_value > 5.0:  # Solo si hay un valor significativo
                if max_value == q1:
                    auto_type = "Q1"
                elif max_value == q2:
                    auto_type = "Q2"
                elif max_value == q3:
                    auto_type = "Q3"
                elif max_value == q4:
                    auto_type = "Q4"
                
                print(f"[TEST_TABLE] 🤖 Auto-detectando tipo de prueba: {auto_type} (valor: {max_value:.2f})")
                # 🔥 ESTABLECER AUTOMÁTICAMENTE EL TIPO SI ES MUY CLARO
                if max_value > 10.0:  # Solo si el valor es muy claro
                    print(f"[TEST_TABLE] 🎯 Auto-estableciendo tipo de prueba: {auto_type}")
                    self.set_test_type_from_calibration(auto_type)


    def update_pattern_values_only(self):
        """🔥 MEJORADA: Actualiza SOLO los valores patrón y errores sin recrear toda la tabla"""
        try:
            for row_idx in range(len(self.rows)):
                # 🔥 OBTENER NUEVO VALOR PATRÓN
                pattern_volume = self.get_pattern_volume_for_row(row_idx)
                
                # 🔥 ACTUALIZAR EL VALOR EN EL ARRAY
                if row_idx < len(self.rows):
                    old_pattern = self.rows[row_idx][5]
                    new_pattern = f"{pattern_volume:.2f}"
                    
                    # Solo actualizar si cambió significativamente
                    try:
                        if abs(float(new_pattern) - float(old_pattern)) > 0.1:
                            self.rows[row_idx][5] = new_pattern
                            print(f"[TEST_TABLE] 🔄 Fila {row_idx} patrón: {old_pattern} → {new_pattern}")
                    except:
                        self.rows[row_idx][5] = new_pattern
                
                # 🔥 ACTUALIZAR WIDGET DE VOLUMEN PATRÓN SI EXISTE
                if row_idx in self.pattern_volume_cells:
                    pattern_cell = self.pattern_volume_cells[row_idx]
                    if hasattr(pattern_cell, 'value'):
                        pattern_cell.value = f"{pattern_volume:.2f}"
                        try:
                            pattern_cell.update()
                        except:
                            pass
                
                # 🔥 RECALCULAR ERROR
                row = self.rows[row_idx]
                error, status_text, status_color = self.calculate_error(row[3], row[4], pattern_volume, row[2])
                
                # 🔥 ACTUALIZAR ERROR EN EL ARRAY
                self.rows[row_idx][6] = str(error)
                self.rows[row_idx][7] = status_text
                
                # 🔥 ACTUALIZAR WIDGET DE ERROR SI EXISTE
                if row_idx in self.error_cells:
                    error_cell = self.error_cells[row_idx]
                    if hasattr(error_cell, 'value'):
                        error_cell.value = str(error)
                        try:
                            error_cell.update()
                        except:
                            pass
                
                # 🔥 ACTUALIZAR WIDGET DE ESTADO SI EXISTE
                if row_idx in self.status_cells:
                    status_container = self.status_cells[row_idx]
                    if hasattr(status_container, 'content') and hasattr(status_container.content, 'value'):
                        status_container.content.value = status_text
                        status_container.content.color = "white"
                        status_container.bgcolor = status_color
                        try:
                            status_container.update()
                        except:
                            pass
            
        except Exception as e:
            print(f"[TEST_TABLE] ❌ Error actualizando valores patrón: {e}")

    def get_pattern_volume_for_row(self, row_idx):
        """🔥 MEJORADA: Obtiene el volumen patrón con mejor manejo de valores"""
        try:
            if row_idx >= len(self.rows):
                return 0.1
                
            test_type = self.rows[row_idx][2]
            if not test_type or test_type == "Escoja una opción":
                return 0.1
            
            # 🔥 PRIORIDAD 1: MÓDULO DE VALORES INSTANTÁNEOS
            if self.instant_values_module:
                try:
                    module_value = self.instant_values_module.get_pattern_value_for_test(test_type)
                    if module_value > 0.1:
                        return module_value
                except Exception as e:
                    print(f"[TEST_TABLE] ⚠️ Error obteniendo valor del módulo: {e}")
            
            # 🔥 PRIORIDAD 2: VALORES LOCALES
            instant_volume = self.instant_values.get(test_type, 0.1)
            if instant_volume > 0.1:
                return instant_volume
            
            # 🔥 ÚLTIMO RECURSO
            return 0.1
                    
        except Exception as e:
            print(f"[TEST_TABLE] ❌ Error obteniendo volumen patrón: {e}")
            return 0.1

    def recalculate_errors(self, e):
        """🔥 FUNCIÓN PARA RECALCULAR ERRORES MANUALMENTE"""
        print(f"[TEST_TABLE] 🔄 Recalculando errores manualmente...")
        print(f"[TEST_TABLE] 📊 Valores instantáneos actuales: {self.instant_values}")
        self.update_table()
    
        # 🔥 FORZAR UPDATE COMPLETO
        if hasattr(self.data_table, 'page') and self.data_table.page is not None:
            self.data_table.page.update()

    def update_for_test(self, test_config):
        """Actualiza la tabla para una prueba específica"""
        self.current_test = test_config
        print(f"[TEST_TABLE] 🔄 Tabla actualizada para: {test_config.get('test_name', 'Prueba')}")

    def clear(self):
        """Limpia todos los campos"""
        self.rows.clear()
        self.rows.append(["", "", "", "", "", "", "", ""])
        self.update_table()

    def initialize_table(self):
        """🔥 MEJORADA: Inicializa la tabla con los valores por defecto"""
        try:
            print(f"[TEST_TABLE] 🔄 Inicializando tabla. Filas actuales: {len(self.rows)}")
            if not self.rows:
                self.rows.append(["", "", "", "", "", "", "", ""])
                print(f"[TEST_TABLE] 📝 Fila inicial creada")
            self.update_table()
            print(f"[TEST_TABLE] ✅ Tabla inicializada correctamente con {len(self.rows)} fila(s)")
        except Exception as e:
            print(f"[TEST_TABLE] ❌ Error inicializando tabla: {e}")

    def build(self):
        """🔥 CONSTRUYE LA TABLA COMPLETA CON TODOS LOS BOTONES"""
        table_container = ft.Container(
            content=ft.Column(
                controls=[self.table_with_margin],
                scroll=ft.ScrollMode.AUTO,
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            height=500,
            width=1200,
            border_radius=12,
            border=ft.border.all(1, ft.Colors.GREY_300),
            bgcolor=ft.Colors.GREY_50,
            padding=10,
            alignment=ft.alignment.top_center,
        )

        # 🔥 CREAR BOTONES DE CONTROL
        control_buttons = []
        
        # 🔥 BOTÓN AGREGAR FILA SIEMPRE DISPONIBLE
        control_buttons.append(
            ft.ElevatedButton("Agregar fila", icon=ft.Icons.ADD, on_click=self.add_row, width=140)
        )
        
        # 🔥 TIMER
        if self.timer_module:
            control_buttons.append(self.timer_module.build())
        else:
            control_buttons.append(
                ft.Container(
                    ft.Text("⏱️ Timer: No disponible", color=ft.Colors.GREY),
                    width=140,
                    height=40,
                    alignment=ft.alignment.center,
                    border_radius=8,
                    bgcolor=ft.Colors.GREY_100,
                )
            )
        
        # 🔥 BOTONES DE CONTROL DE PRUEBA
        control_buttons.extend([
            self.start_test_button,      # 🔥 INICIAR PRUEBA INDIVIDUAL
            self.finish_test_button,     # 🔥 FINALIZAR PRUEBA INDIVIDUAL
            ft.ElevatedButton("Ver Histórico", icon=ft.Icons.HISTORY, on_click=self.show_volume_history, width=140),
            self.end_tests_button,       # 🔥 NUEVO: FINALIZAR TODAS LAS PRUEBAS
        ])

        main_column = ft.Column([
            # 🔥 FILA ÚNICA CON TODOS LOS BOTONES Y TIMER
            ft.Row(
                control_buttons,
                alignment="start", 
                spacing=15
            ),
            table_container,
        ], 
        expand=True,
        alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )

        return main_column
    
    def _on_end_tests(self, e):
        """🔥 NUEVA FUNCIÓN: Finaliza toda la sesión de pruebas y guarda en BD"""
        print("[TEST_TABLE] 🏁 Iniciando finalización de todas las pruebas...")
        
        # 🔥 VALIDAR QUE HAY PRUEBAS COMPLETADAS
        if not self.completed_tests:
            self._show_error_alert(
                "❌ No hay pruebas para finalizar",
                "No se han completado pruebas aún. Complete al menos una prueba antes de finalizar la sesión."
            )
            return
        
        # 🔥 MOSTRAR DIÁLOGO DE CONFIRMACIÓN
        def confirm_end_tests(e):
            if e.control.text == "Sí, finalizar":
                # Cerrar diálogo de confirmación
                confirm_dialog.open = False
                if hasattr(confirm_dialog, 'page') and confirm_dialog.page is not None:
                    confirm_dialog.page.update()
                
                # 🔥 EJECUTAR FINALIZACIÓN
                self._execute_end_tests()
            else:
                # Cancelar
                confirm_dialog.open = False
                if hasattr(confirm_dialog, 'page') and confirm_dialog.page is not None:
                    confirm_dialog.page.update()
        
        # 🔥 CALCULAR ESTADÍSTICAS PARA EL DIÁLOGO
        total_tests = len(self.completed_tests)
        total_meters = sum(len(test["results"]) for test in self.completed_tests)
        total_passed = sum(sum(1 for r in test["results"] if r["is_passed"]) for test in self.completed_tests)
        
        summary_text = f"""📊 Resumen de la sesión:

🧪 Grupos de pruebas realizados: {total_tests}
📏 Total de medidores probados: {total_meters}
✅ Medidores aprobados: {total_passed}
❌ Medidores reprobados: {total_meters - total_passed}
📈 Tasa de éxito general: {(total_passed/total_meters*100):.1f}%

Esta acción guardará todos los datos en la base de datos y generará los informes finales.

¿Está seguro de finalizar la sesión de pruebas?"""
        
        confirm_dialog = ft.AlertDialog(
            title=ft.Text("🏁 Finalizar Sesión de Pruebas", size=18, weight="bold"),
            content=ft.Container(
                content=ft.Text(summary_text, size=14),
                width=400,
                height=300,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=confirm_end_tests),
                ft.ElevatedButton(
                    "Sí, finalizar",
                    on_click=confirm_end_tests,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.DEEP_ORANGE_600,
                        color=ft.Colors.WHITE
                    )
                ),
            ],
        )
        
        if hasattr(self.data_table, 'page') and self.data_table.page is not None:
            self.data_table.page.overlay.append(confirm_dialog)
            confirm_dialog.open = True
            self.data_table.page.update()

    def _execute_end_tests(self):
        """🔥 EJECUTA LA FINALIZACIÓN DE PRUEBAS"""
        try:
            print("[TEST_TABLE] 🔄 Ejecutando finalización de pruebas...")
            
            # 🔥 MOSTRAR DIÁLOGO DE PROGRESO
            progress_ring = ft.ProgressRing(width=50, height=50, stroke_width=4)
            progress_text = ft.Text("Finalizando sesión de pruebas...", size=16, text_align="center")
            progress_details = ft.Text("Preparando datos...", size=12, text_align="center", color=ft.Colors.GREY_600)

            progress_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("🏁 Finalizando Sesión"),
                content=ft.Container(
                    content=ft.Column([
                        ft.Container(
                            progress_ring,
                            alignment=ft.alignment.center,
                            padding=ft.padding.all(20),
                        ),
                        progress_text,
                        progress_details,
                    ], 
                    horizontal_alignment="center",
                    spacing=15,
                    ),
                    width=300,
                    height=200,
                ),
            )
            
            if hasattr(self.data_table, 'page') and self.data_table.page is not None:
                self.data_table.page.overlay.append(progress_dialog)
                progress_dialog.open = True
                self.data_table.page.update()

            # 🔥 SIMULAR PASOS DE FINALIZACIÓN
            steps = [
                ("Enviando comando de finalización al PLC...", 1.0),
                ("Recopilando datos de la sesión...", 0.8),
                ("Guardando en base de datos...", 1.5),
                ("Generando informes...", 1.2),
                ("Preparando vista de resultados...", 0.5),
            ]
            
            for step_text, duration in steps:
                progress_details.value = step_text
                if hasattr(self.data_table, 'page') and self.data_table.page is not None:
                    self.data_table.page.update()
                time.sleep(duration)
            
            # 🔥 ENVIAR COMANDO MODBUS DE FINALIZACIÓN (PARA FUTURO USO)
            self._send_end_tests_command()
            
            # 🔥 GUARDAR DATOS EN BASE DE DATOS
            session_id = self._save_session_to_database()
            
            # 🔥 FINALIZAR PROGRESO
            progress_text.value = "✅ Sesión finalizada exitosamente"
            progress_details.value = "Redirigiendo a informes..."
            progress_ring.visible = False
            if hasattr(self.data_table, 'page') and self.data_table.page is not None:
                self.data_table.page.update()
            
            time.sleep(1.5)
            
            # 🔥 CERRAR DIÁLOGO DE PROGRESO
            progress_dialog.open = False
            if hasattr(self.data_table, 'page') and self.data_table.page is not None:
                self.data_table.page.update()
            
            # 🔥 IR A VISTA DE INFORMES
            self._navigate_to_reports(session_id)
            
        except Exception as error:
            print(f"[TEST_TABLE] ❌ Error finalizando pruebas: {error}")
            
            # 🔥 MOSTRAR ERROR
            if hasattr(self.data_table, 'page') and self.data_table.page is not None:
                progress_dialog.open = False
                self.data_table.page.update()
                
                self._show_error_alert(
                    "❌ Error al Finalizar",
                    f"Ocurrió un error al finalizar la sesión:\n\n{str(error)}\n\nPor favor, contacte al administrador."
                )

    def _send_end_tests_command(self):
        """🔥 ENVÍA COMANDO MODBUS PARA FINALIZAR PRUEBAS (PARA FUTURO USO)"""
        try:
            # 🔥 COMANDO FICTICIO PARA FUTURO USO - CAMBIAR SEGÚN ESPECIFICACIONES
            end_tests_bit = 270  # 🔥 DEFINIR EL BIT CORRECTO CUANDO SE CONOZCA
            
            print(f"[TEST_TABLE] 📡 Enviando comando de finalización M{end_tests_bit}")
            
            if self.send_modbus_command:
                self.send_modbus_command(end_tests_bit)
                print(f"[TEST_TABLE] ✅ Comando de finalización enviado")
            else:
                print(f"[TEST_TABLE] ⚠️ Callback Modbus no disponible")
                
        except Exception as e:
            print(f"[TEST_TABLE] ❌ Error enviando comando de finalización: {e}")

    def _save_session_to_database(self):
        """🔥 GUARDA TODA LA SESIÓN EN LA BASE DE DATOS"""
        try:
            print("[TEST_TABLE] 💾 Guardando sesión en base de datos...")
            
            # 🔥 POR AHORA RETORNAR ID SIMULADO HASTA QUE SE IMPLEMENTEN LOS CONTROLADORES
            session_id = int(time.time())  # Usar timestamp como ID temporal
            
            print(f"[TEST_TABLE] ✅ Sesión guardada con ID: {session_id}")
            return session_id
            
            # 🔥 TODO: IMPLEMENTAR GUARDADO REAL EN BD CUANDO ESTÉN LISTOS LOS CONTROLADORES
            # from controllers.client_controller import get_client_by_name, add_client
            # from controllers.technician_controller import get_technician_by_name, add_technician
            # from controllers.meter_controller import add_meter_group, add_meter, add_test
            
        except Exception as e:
            print(f"[TEST_TABLE] ❌ Error guardando en base de datos: {e}")
            # 🔥 RETORNAR ID TEMPORAL AUNQUE HAYA ERROR
            return int(time.time())

    def _get_session_data(self):
        """🔥 OBTIENE DATOS COMPLETOS DE LA SESIÓN DESDE LA PÁGINA"""
        try:
            # 🔥 INTENTAR OBTENER DESDE PÁGINA (PRIORIDAD 1)
            if hasattr(self, 'page') and self.page:
                # Buscar datos en atributos de la página directamente
                page_data = {
                    "client_name": getattr(self.page, 'client_name', None),
                    "technician_name": getattr(self.page, 'technician_name', None),
                    "brand": getattr(self.page, 'brand', None),
                    "model": getattr(self.page, 'model', None),
                    "ratio": getattr(self.page, 'ratio', None),
                    "nominal_flow": getattr(self.page, 'nominal_flow', None),
                    "diameter": getattr(self.page, 'diameter', None),
                    "type": getattr(self.page, 'meter_type', None),
                    "batch": getattr(self.page, 'batch', None),
                }
                
                # Si encontramos al menos algunos datos, usar estos
                if any(value is not None for value in page_data.values()):
                    print(f"[TEST_TABLE] 📊 Datos obtenidos desde atributos de página: {page_data}")
                    # Rellenar valores faltantes con defaults
                    return {
                        "client_name": page_data["client_name"] or "Cliente Desconocido",
                        "technician_name": page_data["technician_name"] or "Técnico Desconocido",
                        "brand": page_data["brand"] or "Marca Desconocida",
                        "model": page_data["model"] or "Modelo Desconocido",
                        "ratio": int(page_data["ratio"]) if page_data["ratio"] else 100,
                        "nominal_flow": float(page_data["nominal_flow"]) if page_data["nominal_flow"] else 1000.0,
                        "diameter": float(page_data["diameter"]) if page_data["diameter"] else 20.0,
                        "type": page_data["type"] or "Tipo Desconocido",
                        "batch": page_data["batch"] or "nuevo",
                    }
            
            # 🔥 INTENTAR OBTENER DESDE SESSION (PRIORIDAD 2)
            if hasattr(self, 'page') and self.page and hasattr(self.page, 'session'):
                try:
                    session_data = {
                        "client_name": self.page.session.get("client_name"),
                        "technician_name": self.page.session.get("technician_name"),
                        "brand": self.page.session.get("brand"),
                        "model": self.page.session.get("model"),
                        "ratio": self.page.session.get("ratio"),
                        "nominal_flow": self.page.session.get("nominal_flow"),
                        "diameter": self.page.session.get("diameter"),
                        "type": self.page.session.get("meter_type"),
                        "batch": self.page.session.get("batch"),
                    }
                    
                    if any(value is not None for value in session_data.values()):
                        print(f"[TEST_TABLE] 📊 Datos obtenidos desde session: {session_data}")
                        return {
                            "client_name": session_data["client_name"] or "Cliente Desconocido",
                            "technician_name": session_data["technician_name"] or "Técnico Desconocido",
                            "brand": session_data["brand"] or "Marca Desconocida",
                            "model": session_data["model"] or "Modelo Desconocido",
                            "ratio": int(session_data["ratio"]) if session_data["ratio"] else 100,
                            "nominal_flow": float(session_data["nominal_flow"]) if session_data["nominal_flow"] else 1000.0,
                            "diameter": float(session_data["diameter"]) if session_data["diameter"] else 20.0,
                            "type": session_data["type"] or "Tipo Desconocido",
                            "batch": session_data["batch"] or "nuevo",
                        }
                except Exception as e:
                    print(f"[TEST_TABLE] ⚠️ Error accediendo a session: {e}")
            
            # 🔥 DATOS POR DEFECTO COMO ÚLTIMA OPCIÓN
            print("[TEST_TABLE] ⚠️ Usando datos por defecto - no se encontraron datos de sesión")
            return {
                "client_name": "Cliente Desconocido",
                "technician_name": "Técnico Desconocido", 
                "brand": "Marca Desconocida",
                "model": "Modelo Desconocido",
                "ratio": 100,
                "nominal_flow": 1000.0,
                "diameter": 20.0,
                "type": "Tipo Desconocido",
                "batch": "nuevo",
            }
            
        except Exception as e:
            print(f"[TEST_TABLE] ❌ Error obteniendo datos de sesión: {e}")
            return {
                "client_name": "Cliente Desconocido",
                "technician_name": "Técnico Desconocido", 
                "brand": "Marca Desconocida",
                "model": "Modelo Desconocido",
                "ratio": 100,
                "nominal_flow": 1000.0,
                "diameter": 20.0,
                "type": "Tipo Desconocido",
                "batch": "nuevo",
            }

    def force_q4_test_setup(self):
        """🔥 FUNCIÓN DESHABILITADA: Ya no se ejecuta automáticamente"""
        print("[TEST_TABLE] 🔇 force_q4_test_setup() deshabilitada - usar calibración manual")
        return

    def test_timer_functionality(self):
        """🔥 FUNCIÓN DESHABILITADA: Ya no se ejecuta automáticamente"""
        print("[TEST_TABLE] 🔇 test_timer_functionality() deshabilitada - timer funciona bajo demanda")
        return True

    def debug_force_test_type(self, test_type):
        """🔥 FUNCIÓN DEBUG: Fuerza un tipo de prueba manualmente (solo para debug)"""
        print(f"[TEST_TABLE] 🔧 DEBUG: Forzando manualmente tipo de prueba: {test_type}")
        self.set_test_type_from_calibration(test_type)

    def initialize_empty_table(self):
        """🔥 NUEVA FUNCIÓN: Inicializa la tabla completamente vacía"""
        try:
            print(f"[TEST_TABLE] 🔄 Inicializando tabla vacía...")
            if not self.rows:
                # 🔥 CREAR FILA VACÍA SIN TIPO DE PRUEBA NI DATOS
                self.rows.append(["", "", "", "", "", "", "", ""])
                print(f"[TEST_TABLE] 📝 Fila vacía creada")
            self.update_table()
            print(f"[TEST_TABLE] ✅ Tabla vacía inicializada correctamente")
        except Exception as e:
            print(f"[TEST_TABLE] ❌ Error inicializando tabla vacía: {e}")

    def set_test_type_from_calibration(self, test_type):
        """🔥 MEJORADA: Establece el tipo de prueba SOLO cuando hay calibración real"""
        print(f"[TEST_TABLE] 🎯 Estableciendo tipo de prueba por calibración: {test_type}")
        
        self.current_test_type = test_type
        
        # 🔥 CREAR AL MENOS UNA FILA SI NO HAY NINGUNA
        if not self.rows:
            self.rows.append(["", "", "", "", "", "", "", ""])
            print(f"[TEST_TABLE] 📝 Creada fila inicial")
        
        # 🔥 RELLENAR TODAS LAS FILAS CON EL TIPO DE PRUEBA SELECCIONADO
        for idx, row in enumerate(self.rows):
            old_type = row[2]
            row[2] = test_type  # Columna de tipo de prueba
            print(f"[TEST_TABLE] 🔄 Fila {idx}: '{old_type}' → '{test_type}'")
        
        # 🔥 OBTENER TIEMPO DESDE CONFIGURACIÓN DE PRUEBAS
        estimated_time_minutes = self.get_configured_time_for_test_type(test_type)
        
        # 🔥 CONFIGURAR TIEMPO EN EL TIMER PERO NO INICIARLO
        if self.timer_module:
            self.timer_module.set_time(estimated_time_minutes)
            print(f"[TEST_TABLE] ⏰ Timer configurado con {estimated_time_minutes:.1f} minutos (sin iniciar)")
        else:
            print(f"[TEST_TABLE] ⚠️ Timer module no disponible")
        
        # 🔥 HABILITAR BOTÓN DE INICIO SOLO CUANDO HAY TIPO DE PRUEBA
        self.start_test_button.disabled = False
        print(f"[TEST_TABLE] 🔓 Botón 'Iniciar Prueba' habilitado")
        
        # 🔥 FORZAR ACTUALIZACIÓN COMPLETA DE LA TABLA
        self.update_table()
        
        try:
            self.start_test_button.update()
        except:
            pass
        
        print(f"[TEST_TABLE] ✅ Tipo de prueba establecido: {test_type}")
        print(f"[TEST_TABLE] ⏱️ Tiempo configurado: {estimated_time_minutes:.1f} minutos")

    def _on_finish_test(self, e):
        """🔥 MEJORADA: Finaliza la prueba y resetea el sistema"""
        if not self.current_test_type:
            print("[TEST_TABLE] ⚠️ No hay tipo de prueba para finalizar")
            return
        
        # 🔥 INCREMENTAR CONTADOR DE REPETIBILIDAD
        self.test_counters[self.current_test_type] += 1
        current_repetition = self.test_counters[self.current_test_type]
        
        # 🔥 CREAR NOMBRE DE PRUEBA CON REPETIBILIDAD
        if current_repetition == 1:
            test_name = f"Prueba {self.current_test_type}"
        else:
            test_name = f"Prueba {self.current_test_type}.{current_repetition}"
        
        print(f"[TEST_TABLE] 🏁 Finalizando: {test_name}")
        
        # 🔥 RECOPILAR DATOS DE TODAS LAS FILAS VÁLIDAS
        test_results = []
        serials_to_preserve = []
        
        for idx, row in enumerate(self.rows):
            serial = row[1].strip()
            test_type = row[2]
            initial_reading = row[3].strip()
            final_reading = row[4].strip()
            pattern_volume = row[5]
            error = row[6]
            status = row[7]
            
            # 🔥 SOLO PROCESAR FILAS CON DATOS COMPLETOS
            if serial and test_type and initial_reading and final_reading:
                test_data = {
                    "serial_number": serial,
                    "test_type": test_type,
                    "test_name": test_name,
                    "repetition": current_repetition,
                    "initial_reading": float(initial_reading),
                    "final_reading": float(final_reading),
                    "pattern_volume": float(pattern_volume) if pattern_volume else 0.0,
                    "volume_difference": float(final_reading) - float(initial_reading),
                    "error_percentage": float(error) if error else 0.0,
                    "status": status,
                    "is_passed": status == "PASA",
                    "meter_status": self.meter_status,
                    "completed_at": time.time(),
                }
                
                test_results.append(test_data)
                serials_to_preserve.append(serial)
                
        # 🔥 GUARDAR EN EL ARRAY DE PRUEBAS COMPLETADAS
        if test_results:
            # Crear grupo de prueba
            test_group = {
                "test_name": test_name,
                "test_type": self.current_test_type,
                "repetition": current_repetition,
                "completed_at": time.time(),
                "results": test_results,
                "summary": {
                    "total": len(test_results),
                    "passed": sum(1 for r in test_results if r["is_passed"]),
                    "failed": sum(1 for r in test_results if not r["is_passed"]),
                    "success_rate": (sum(1 for r in test_results if r["is_passed"]) / len(test_results)) * 100
                }
            }
            
            self.completed_tests.append(test_group)
            print(f"[TEST_TABLE] 💾 Guardados {len(test_results)} resultados para {test_name}")
            print(f"[TEST_TABLE] 📊 Total grupos de pruebas: {len(self.completed_tests)}")
        
        # 🔥 LIMPIAR DATOS PERO PRESERVAR SERIALES
        self.clear_data_preserve_serials(serials_to_preserve)
        
        # 🔥 DETENER TIMER Y ACTUALIZAR BOTONES
        if self.timer_module:
            self.timer_module.stop_countdown()
        
        self.start_test_button.disabled = False
        self.finish_test_button.disabled = True
        
        # 🔥 MARCAR PRUEBA COMO NO EN PROGRESO
        self.test_in_progress = False
        self.active_test_type = None
        
        if hasattr(self, 'on_test_control'):
            self.on_test_control("finish")
            
        try:
            self.start_test_button.update()
            self.finish_test_button.update()
        except:
            pass
            
        print(f"[TEST_TABLE] ✅ Prueba finalizada: {test_name}")
        print(f"[TEST_TABLE] 🔄 Sistema listo para nueva prueba")

    def _navigate_to_reports(self, session_id):
        """🔥 NAVEGA A LA NUEVA VISTA DE RESUMEN CON DATOS COMPLETOS"""
        try:
            print(f"[TEST_TABLE] 🔄 Navegando a results_summary_view para sesión {session_id}")
            
            # 🔥 PREPARAR DATOS COMPLETOS PARA LA VISTA DE RESUMEN
            session_data = self._get_session_data()
            
            summary_data = {
                "session_id": session_id,
                "completed_tests": self.completed_tests,
                "session_data": session_data,  # 🔥 DATOS COMPLETOS DE BATCH REGISTRATION
                "operation_mode": getattr(self, 'operation_mode', 'automatic'),
                "total_groups": len(self.completed_tests),
                "total_meters": sum(len(test["results"]) for test in self.completed_tests),
                "total_passed": sum(sum(1 for r in test["results"] if r["is_passed"]) for test in self.completed_tests),
                # 🔥 AGREGAR DATOS ADICIONALES PARA EL REPORTE
                "test_summary": self._generate_test_summary(),
                "meter_details": self._generate_meter_details(),
                # 🔥 NUEVOS CAMPOS PARA MOSTRAR EN EL REPORTE
                "batch_info": {
                    "client": session_data["client_name"],
                    "technician": session_data["technician_name"],
                    "meter_brand": session_data["brand"],
                    "meter_model": session_data["model"],
                    "meter_type": session_data["type"],
                    "ratio": session_data["ratio"],
                    "nominal_flow": session_data["nominal_flow"],
                    "diameter": session_data["diameter"],
                    "batch_status": session_data["batch"],
                },
            }
            
            print(f"[TEST_TABLE] 📊 Datos de sesión preparados: {session_data}")
            
            # 🔥 VERIFICAR SI LA VISTA DE RESUMEN EXISTE
            try:
                from views.results_summary_view import get_results_summary_view
                print("[TEST_TABLE] ✅ Módulo results_summary_view encontrado")
            except ImportError as ie:
                print(f"[TEST_TABLE] ❌ No se pudo importar results_summary_view: {ie}")
                print("[TEST_TABLE] 🔄 Creando vista de resumen temporal...")
                self._show_temporary_summary(summary_data)
                return
            
            # 🔥 CAMBIAR A VISTA DE RESUMEN DE RESULTADOS
            if hasattr(self.data_table, 'page') and self.data_table.page is not None:
                page = self.data_table.page
                page.controls.clear()
                
                results_view = get_results_summary_view(page, summary_data)
                page.controls.append(results_view)
                page.update()
                
                print("[TEST_TABLE] ✅ Navegación a results_summary_view exitosa")
            
        except Exception as e:
            print(f"[TEST_TABLE] ❌ Error navegando a results_summary_view: {e}")
            import traceback
            traceback.print_exc()
            self._show_error_alert(
                "❌ Error de Navegación",
                f"No se pudo abrir la vista de resumen de resultados.\n\nSe guardaron los datos correctamente en la base de datos (Sesión ID: {session_id})\n\nError: {str(e)}"
            )
    

    def _generate_test_summary(self):
        """🔥 GENERA RESUMEN DETALLADO DE PRUEBAS"""
        try:
            summary = {}
            
            for test_group in self.completed_tests:
                test_type = test_group["test_type"]
                
                if test_type not in summary:
                    summary[test_type] = {
                        "groups": 0,
                        "total_meters": 0,
                        "passed_meters": 0,
                        "failed_meters": 0,
                        "success_rate": 0.0,
                        "avg_error": 0.0,
                        "test_names": []
                    }
                
                # Actualizar estadísticas
                summary[test_type]["groups"] += 1
                summary[test_type]["total_meters"] += len(test_group["results"])
                summary[test_type]["test_names"].append(test_group["test_name"])
                
                # Calcular estadísticas por medidor
                total_error = 0
                for result in test_group["results"]:
                    if result["is_passed"]:
                        summary[test_type]["passed_meters"] += 1
                    else:
                        summary[test_type]["failed_meters"] += 1
                    total_error += abs(result["error_percentage"])
                
                # Calcular promedios
                if summary[test_type]["total_meters"] > 0:
                    summary[test_type]["success_rate"] = (summary[test_type]["passed_meters"] / summary[test_type]["total_meters"]) * 100
                    summary[test_type]["avg_error"] = total_error / summary[test_type]["total_meters"]
            
            print(f"[TEST_TABLE] 📊 Resumen de pruebas generado: {len(summary)} tipos de prueba")
            return summary
            
        except Exception as e:
            print(f"[TEST_TABLE] ❌ Error generando resumen de pruebas: {e}")
            return {}

    def _generate_meter_details(self):
        """🔥 GENERA DETALLES POR MEDIDOR INDIVIDUAL"""
        try:
            meters = {}
            
            for test_group in self.completed_tests:
                for result in test_group["results"]:
                    serial = result["serial_number"]
                    
                    if serial not in meters:
                        meters[serial] = {
                            "serial_number": serial,
                            "tests": [],
                            "total_tests": 0,
                            "passed_tests": 0,
                            "failed_tests": 0,
                            "overall_passed": True,
                            "avg_error": 0.0
                        }
                    
                    # Agregar test al medidor
                    meters[serial]["tests"].append({
                        "test_name": test_group["test_name"],
                        "test_type": test_group["test_type"],
                        "repetition": test_group["repetition"],
                        "initial_reading": result["initial_reading"],
                        "final_reading": result["final_reading"],
                        "error_percentage": result["error_percentage"],
                        "is_passed": result["is_passed"],
                        "status": result["status"]
                    })
                    
                    # Actualizar estadísticas
                    meters[serial]["total_tests"] += 1
                    if result["is_passed"]:
                        meters[serial]["passed_tests"] += 1
                    else:
                        meters[serial]["failed_tests"] += 1
                        meters[serial]["overall_passed"] = False
            
            # Calcular error promedio para cada medidor
            for serial, meter_data in meters.items():
                if meter_data["total_tests"] > 0:
                    total_error = sum(abs(test["error_percentage"]) for test in meter_data["tests"])
                    meter_data["avg_error"] = total_error / meter_data["total_tests"]
            
            print(f"[TEST_TABLE] 📏 Detalles de medidores generados: {len(meters)} medidores")
            return meters
            
        except Exception as e:
            print(f"[TEST_TABLE] ❌ Error generando detalles de medidores: {e}")
            return {}

    def _show_temporary_summary(self, summary_data):
        """🔥 MUESTRA RESUMEN TEMPORAL SI NO EXISTE LA VISTA"""
        try:
            # 🔥 CREAR VISTA TEMPORAL SIMPLE
            total_meters = summary_data.get("total_meters", 0)
            total_passed = summary_data.get("total_passed", 0)
            success_rate = (total_passed / total_meters * 100) if total_meters > 0 else 0
            
            # 🔥 CONTENIDO DEL RESUMEN
            summary_content = ft.Column([
                ft.Text("📋 Resumen de la Sesión Finalizada", size=24, weight="bold", color=ft.Colors.BLUE_900),
                ft.Divider(),
                
                ft.Text(f"✅ Sesión guardada exitosamente en la base de datos", size=16, color=ft.Colors.GREEN, weight="bold"),
                ft.Text(f"🆔 ID de Sesión: {summary_data['session_id']}", size=14, color=ft.Colors.GREY_700),
                
                ft.Divider(),
                
                ft.Text("📊 Estadísticas Generales:", size=18, weight="bold", color=ft.Colors.PURPLE_700),
                ft.Text(f"🧪 Grupos de pruebas realizados: {summary_data['total_groups']}", size=14),
                ft.Text(f"📏 Total de medidores probados: {total_meters}", size=14),
                ft.Text(f"✅ Medidores aprobados: {total_passed}", size=14, color=ft.Colors.GREEN),
                ft.Text(f"❌ Medidores reprobados: {total_meters - total_passed}", size=14, color=ft.Colors.RED),
                ft.Text(f"📈 Tasa de éxito: {success_rate:.1f}%", size=16, weight="bold", 
                       color=ft.Colors.GREEN if success_rate >= 80 else ft.Colors.ORANGE),
                
                ft.Divider(),
                
                ft.Text("🔍 Detalles de Grupos de Pruebas:", size=18, weight="bold", color=ft.Colors.PURPLE_700),
                *[ft.Text(f"• {test['test_name']}: {len(test['results'])} medidores, "
                         f"{test['summary']['success_rate']:.1f}% éxito", size=14) 
                  for test in summary_data['completed_tests']],
                
                ft.Divider(),
                
                ft.Row([
                    ft.ElevatedButton(
                        "🏠 Volver al Inicio",
                        on_click=lambda e: self._go_to_home(),
                        bgcolor=ft.Colors.BLUE_600,
                        color="white",
                        width=200,
                    ),
                    ft.ElevatedButton(
                        "🔄 Nueva Sesión",
                        on_click=lambda e: self._start_new_session(),
                        bgcolor=ft.Colors.GREEN_600,
                        color="white",
                        width=200,
                    ),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
                
            ], spacing=15, scroll=ft.ScrollMode.AUTO)
            
            # 🔥 MOSTRAR EN LA PÁGINA
            if hasattr(self.data_table, 'page') and self.data_table.page is not None:
                page = self.data_table.page
                page.controls.clear()
                
                main_container = ft.Container(
                    content=summary_content,
                    padding=40,
                    alignment=ft.alignment.top_center,
                    expand=True,
                )
                
                page.controls.append(main_container)
                page.update()
                
                print("[TEST_TABLE] ✅ Resumen temporal mostrado")
            
        except Exception as e:
            print(f"[TEST_TABLE] ❌ Error mostrando resumen temporal: {e}")


    def _go_to_home(self):
        """🔥 NAVEGA AL MENÚ PRINCIPAL"""
        try:
            print("[TEST_TABLE] 🏠 Navegando al menú principal...")
            
            # 🔥 INTENTAR IMPORTAR MAIN
            try:
                from main import create_main_menu
                main_view = create_main_menu(self.data_table.page)
            except ImportError:
                try:
                    from main import main_menu
                    main_view = main_menu(self.data_table.page)
                except ImportError:
                    print("[TEST_TABLE] ❌ No se pudo importar función de menú principal")
                    self._show_error_alert("Error", "No se pudo volver al menú principal")
                    return
            
            # 🔥 CAMBIAR VISTA
            if hasattr(self.data_table, 'page') and self.data_table.page is not None:
                page = self.data_table.page
                page.controls.clear()
                page.controls.append(main_view)
                page.update()
                print("[TEST_TABLE] ✅ Navegación al inicio exitosa")
                
        except Exception as e:
            print(f"[TEST_TABLE] ❌ Error navegando al inicio: {e}")


    def test_timer_functionality(self):
        """🔥 FUNCIÓN DE PRUEBA: Verifica que el timer funcione"""
        if not self.timer_module:
            print("[TEST_TABLE] ❌ Timer module no disponible para prueba")
            return False
        
        print("[TEST_TABLE] 🧪 PRUEBA: Configurando timer de 2 minutos...")
        
        try:
            # Configurar 2 minutos
            self.timer_module.set_time(2.0)
            print("[TEST_TABLE] ✅ Timer configurado exitosamente")
            
            # Probar inicio de cuenta regresiva
            self.timer_module.start_countdown()
            print("[TEST_TABLE] ✅ Cuenta regresiva iniciada exitosamente")
            
            return True
            
        except Exception as e:
            print(f"[TEST_TABLE] ❌ Error en prueba de timer: {e}")
            return False
        
    def _start_new_session(self):
        """🔥 INICIA NUEVA SESIÓN DE PRUEBAS"""
        try:
            print("[TEST_TABLE] 🔄 Iniciando nueva sesión...")
            
            from views.batch_registration_view import get_batch_registration_view
            
            if hasattr(self.data_table, 'page') and self.data_table.page is not None:
                page = self.data_table.page
                page.controls.clear()
                
                # 🔥 CREAR NUEVA VISTA SIN PARÁMETROS ADICIONALES
                new_view = get_batch_registration_view(page, None)
                page.controls.append(new_view)
                page.update()
                
                print("[TEST_TABLE] ✅ Nueva sesión iniciada")
                
        except Exception as e:
            print(f"[TEST_TABLE] ❌ Error iniciando nueva sesión: {e}")

    def _normalize_batch_value(self, batch_value):
        """🔥 NORMALIZA EL VALOR DE BATCH PARA QUE COINCIDA CON TU ESQUEMA"""
        if not batch_value:
            return "new"
        
        batch_lower = str(batch_value).lower().strip()
        
        # Mapear valores en español/inglés
        if batch_lower in ["nuevo", "new"]:
            return "new"
        elif batch_lower in ["usado", "used"]:
            return "used"
        else:
            print(f"[TEST_TABLE] ⚠️ Valor de batch desconocido: {batch_value}, usando 'new'")
            return "new"


    def _get_session_data(self):
        """🔥 OBTIENE DATOS COMPLETOS DE LA SESIÓN DESDE LA PÁGINA"""
        try:
            # 🔥 INTENTAR OBTENER DESDE PÁGINA (PRIORIDAD 1)
            if hasattr(self, 'page') and self.page:
                # Buscar datos en atributos de la página directamente
                page_data = {
                    "client_name": getattr(self.page, 'client_name', None),
                    "technician_name": getattr(self.page, 'technician_name', None),
                    "brand": getattr(self.page, 'brand', None),
                    "model": getattr(self.page, 'model', None),
                    "ratio": getattr(self.page, 'ratio', None),
                    "nominal_flow": getattr(self.page, 'nominal_flow', None),
                    "diameter": getattr(self.page, 'diameter', None),
                    "type": getattr(self.page, 'meter_type', None),
                    "batch": getattr(self.page, 'batch', None),
                }
                
                # Si encontramos al menos algunos datos, usar estos
                if any(value is not None for value in page_data.values()):
                    print(f"[TEST_TABLE] 📊 Datos obtenidos desde atributos de página: {page_data}")
                    # Rellenar valores faltantes con defaults
                    return {
                        "client_name": page_data["client_name"] or "Cliente Desconocido",
                        "technician_name": page_data["technician_name"] or "Técnico Desconocido",
                        "brand": page_data["brand"] or "Marca Desconocida",
                        "model": page_data["model"] or "Modelo Desconocido",
                        "ratio": int(page_data["ratio"]) if page_data["ratio"] else 100,
                        "nominal_flow": float(page_data["nominal_flow"]) if page_data["nominal_flow"] else 1000.0,
                        "diameter": float(page_data["diameter"]) if page_data["diameter"] else 20.0,
                        "type": page_data["type"] or "Tipo Desconocido",
                        "batch": page_data["batch"] or "nuevo",
                    }
            
            # 🔥 INTENTAR OBTENER DESDE SESSION (PRIORIDAD 2)
            if hasattr(self, 'page') and self.page and hasattr(self.page, 'session'):
                try:
                    session_data = {
                        "client_name": self.page.session.get("client_name"),
                        "technician_name": self.page.session.get("technician_name"),
                        "brand": self.page.session.get("brand"),
                        "model": self.page.session.get("model"),
                        "ratio": self.page.session.get("ratio"),
                        "nominal_flow": self.page.session.get("nominal_flow"),
                        "diameter": self.page.session.get("diameter"),
                        "type": self.page.session.get("meter_type"),
                        "batch": self.page.session.get("batch"),
                    }
                    
                    if any(value is not None for value in session_data.values()):
                        print(f"[TEST_TABLE] 📊 Datos obtenidos desde session: {session_data}")
                        return {
                            "client_name": session_data["client_name"] or "Cliente Desconocido",
                            "technician_name": session_data["technician_name"] or "Técnico Desconocido",
                            "brand": session_data["brand"] or "Marca Desconocida",
                            "model": session_data["model"] or "Modelo Desconocido",
                            "ratio": int(session_data["ratio"]) if session_data["ratio"] else 100,
                            "nominal_flow": float(session_data["nominal_flow"]) if session_data["nominal_flow"] else 1000.0,
                            "diameter": float(session_data["diameter"]) if session_data["diameter"] else 20.0,
                            "type": session_data["type"] or "Tipo Desconocido",
                            "batch": session_data["batch"] or "nuevo",
                        }
                except Exception as e:
                    print(f"[TEST_TABLE] ⚠️ Error accediendo a session: {e}")
            
            # 🔥 DATOS POR DEFECTO COMO ÚLTIMA OPCIÓN
            print("[TEST_TABLE] ⚠️ Usando datos por defecto - no se encontraron datos de sesión")
            return {
                "client_name": "Cliente Desconocido",
                "technician_name": "Técnico Desconocido", 
                "brand": "Marca Desconocida",
                "model": "Modelo Desconocido",
                "ratio": 100,
                "nominal_flow": 1000.0,
                "diameter": 20.0,
                "type": "Tipo Desconocido",
                "batch": "nuevo",
            }
            
        except Exception as e:
            print(f"[TEST_TABLE] ❌ Error obteniendo datos de sesión: {e}")
            return {
                "client_name": "Cliente Desconocido",
                "technician_name": "Técnico Desconocido", 
                "brand": "Marca Desconocida",
                "model": "Modelo Desconocido",
                "ratio": 100,
                "nominal_flow": 1000.0,
                "diameter": 20.0,
                "type": "Tipo Desconocido",
                "batch": "nuevo",
            }

    def _save_session_to_database(self):
        """🔥 GUARDA TODA LA SESIÓN EN LA BASE DE DATOS USANDO TU SERVICIO DB"""
        try:
            print("[TEST_TABLE] 💾 Guardando sesión en base de datos PostgreSQL...")
            
            # 🔥 IMPORTAR TU SERVICIO DE BD
            from services.db_service import (
                insert_client, fetch_all_clients,
                insert_technician, fetch_all_technicians,
                insert_meter_group, save_meter_if_not_exists,
                save_test_for_meter, get_existing_test_count
            )
            
            # 🔥 OBTENER DATOS DE LA SESIÓN
            session_data = self._get_session_data()
            
            # 🔥 PASO 1: OBTENER/CREAR CLIENTE
            client_name = session_data.get("client_name", "Cliente Desconocido")
            print(f"[TEST_TABLE] 👤 Procesando cliente: {client_name}")
            
            # Buscar cliente existente por nombre
            existing_clients = fetch_all_clients()
            client_id = None
            for client in existing_clients:
                if client.get("name", "").lower().strip() == client_name.lower().strip():
                    client_id = client["id"]
                    break
            
            # Crear cliente si no existe
            if not client_id:
                client_id = insert_client(client_name)
                print(f"[TEST_TABLE] ✅ Cliente creado: {client_name} (ID: {client_id})")
            else:
                print(f"[TEST_TABLE] ✅ Cliente existente: {client_name} (ID: {client_id})")
            
            # 🔥 PASO 2: OBTENER/CREAR TÉCNICO
            technician_name = session_data.get("technician_name", "Técnico Desconocido")
            print(f"[TEST_TABLE] 🔧 Procesando técnico: {technician_name}")
            
            # Buscar técnico existente por nombre
            existing_technicians = fetch_all_technicians()
            technician_id = None
            for tech in existing_technicians:
                if tech.get("name", "").lower().strip() == technician_name.lower().strip():
                    technician_id = tech["id"]
                    break
            
            # Crear técnico si no existe
            if not technician_id:
                technician_id = insert_technician(technician_name)
                print(f"[TEST_TABLE] ✅ Técnico creado: {technician_name} (ID: {technician_id})")
            else:
                print(f"[TEST_TABLE] ✅ Técnico existente: {technician_name} (ID: {technician_id})")
            
            # 🔥 PASO 3: CREAR GRUPO DE MEDIDORES (SESIÓN) - USANDO TU ESQUEMA
            meter_group_data = {
                "brand": session_data.get("brand", "Marca Desconocida")[:50],  # Limitar a 50 chars
                "model": session_data.get("model", "Modelo Desconocido")[:50],
                "ratio": int(session_data.get("ratio", 100)),
                "nominal_flow": float(session_data.get("nominal_flow", 1000)),
                "diameter": float(session_data.get("diameter", 20)),
                "type": session_data.get("type", "Tipo Desconocido")[:50],
                "batch": self._normalize_batch_value(session_data.get("batch", "nuevo")),  # 🔥 NORMALIZAR
            }
            
            meter_group_id = insert_meter_group(meter_group_data, client_id, technician_id)
            print(f"[TEST_TABLE] ✅ Grupo de medidores creado (ID: {meter_group_id})")
            
            # 🔥 PASO 4: GUARDAR MEDIDORES Y PRUEBAS
            saved_tests_count = 0
            saved_meters_count = 0
            processed_serials = set()
            
            for test_group in self.completed_tests:
                print(f"[TEST_TABLE] 📝 Procesando grupo: {test_group['test_name']}")
                
                for result in test_group["results"]:
                    try:
                        serial_number = str(result["serial_number"]).strip()[:100]  # Limitar a 100 chars
                        
                        # 🔥 CREAR/OBTENER MEDIDOR (USANDO TU ESQUEMA)
                        meter_id = save_meter_if_not_exists(serial_number, meter_group_id)
                        if meter_id and serial_number not in processed_serials:
                            saved_meters_count += 1
                            processed_serials.add(serial_number)
                            print(f"[TEST_TABLE] 📏 Medidor procesado: {serial_number} (ID: {meter_id})")
                        
                        # 🔥 DETERMINAR NÚMERO DE PRUEBA AUTOMÁTICAMENTE
                        existing_count = get_existing_test_count(serial_number, test_group["test_type"])
                        test_number = existing_count + 1
                        
                        # 🔥 PREPARAR DATOS DE LA PRUEBA (USANDO TU ESQUEMA EXACTO)
                        test_data = {
                            "test_type": str(test_group["test_type"])[:10],  # Limitar a 10 chars
                            "test_number": int(test_number),
                            "initial_reading": float(result["initial_reading"]),
                            "final_reading": float(result["final_reading"]),
                            "reference_value": float(result.get("pattern_volume", 100.0)),  # Default 100 como en tu esquema
                            "error": float(result["error_percentage"]),
                            "passed": bool(result["is_passed"])
                        }
                        
                        # 🔥 GUARDAR PRUEBA EN BD
                        save_test_for_meter(meter_id, test_data)
                        saved_tests_count += 1
                        
                        print(f"[TEST_TABLE] ✅ Prueba guardada: {serial_number} - {test_group['test_type']} #{test_number}")
                        
                    except Exception as e:
                        print(f"[TEST_TABLE] ❌ Error guardando resultado individual: {e}")
                        print(f"[TEST_TABLE] 📋 Datos del resultado: {result}")
                        import traceback
                        traceback.print_exc()
            
            print(f"[TEST_TABLE] ✅ Sesión guardada completamente en PostgreSQL")
            print(f"[TEST_TABLE] 📊 Estadísticas finales:")
            print(f"  • Grupo ID: {meter_group_id}")
            print(f"  • Medidores únicos procesados: {saved_meters_count}")
            print(f"  • Pruebas guardadas: {saved_tests_count}")
            print(f"  • Cliente: {client_name} (ID: {client_id})")
            print(f"  • Técnico: {technician_name} (ID: {technician_id})")
            
            return meter_group_id  # 🔥 RETORNAR ID DE LA SESIÓN
            
        except Exception as e:
            print(f"[TEST_TABLE] ❌ Error crítico guardando en PostgreSQL: {e}")
            import traceback
            traceback.print_exc()
            raise Exception(f"Error guardando en base de datos: {str(e)}")
    
    
    # 🔥 FUNCIONES PÚBLICAS PARA COMPATIBILIDAD
    def actualizar_valores_instantaneos(self, q1, q2, q3, q4):
        """Wrapper para compatibilidad"""
        return self.update_instant_values(q1, q2, q3, q4)

def create_test_table_module(on_data_changed):
    """Función factory para crear el módulo de tabla"""
    return TestTableModule(on_data_changed)