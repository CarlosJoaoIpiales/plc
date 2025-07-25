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

        # 🔥 ELIMINAR: saved_pattern_values (YA NO SE NECESITA)
        # 🔥 Los valores patrón ahora se obtienen directamente de instant_values en tiempo real

        # 🔥 ESTADO DE PRUEBAS ACTIVAS (PARA RESETEAR CUANDO INICIA NUEVA PRUEBA)
        self.active_test_type = None
        self.test_in_progress = False

        # 🔥 CONTADOR PARA DEBUG
        self.add_row_counter = 0

        # 🔥 TIMER MODULE
        self.timer_module = create_timer_module(self._on_timer_finished)

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
            disabled=True,
            on_click=self._on_finish_test
        )


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

    def calculate_estimated_time(self, test_type, volume=100):
        """🔥 NUEVA FUNCIÓN: Calcula tiempo estimado para una prueba"""
        try:
            # 🔥 OBTENER CAUDAL MÁXIMO PARA EL TIPO DE PRUEBA
            current_flow = self.instant_values.get(test_type, 0)
            
            if current_flow <= 0:
                print(f"[TEST_TABLE] ⚠️ Caudal para {test_type} es 0, usando default")
                return 5  # 5 minutos por defecto
            
            # 🔥 CALCULAR QMAX (10% SOBRE EL CAUDAL NOMINAL)
            qmax_lh = current_flow * 1.1  # L/h
            
            if qmax_lh <= 0:
                return 5
            
            # 🔥 CALCULAR TIEMPO: tiempo = volumen / caudal_max
            # Volumen en litros, caudal en L/h, resultado en horas -> convertir a minutos
            time_hours = volume / qmax_lh
            time_minutes = time_hours * 60
            
            # 🔥 MÍNIMO 1 MINUTO, MÁXIMO 30 MINUTOS
            time_minutes = max(1, min(30, time_minutes))
            
            print(f"[TEST_TABLE] ⏱️ Tiempo estimado para {test_type}: {volume}L / {qmax_lh:.2f}L/h = {time_minutes:.1f} min")
            
            return time_minutes
            
        except Exception as e:
            print(f"[TEST_TABLE] ❌ Error calculando tiempo estimado: {e}")
            return 5  # Default 5 minutos

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
        """🔥 CORREGIDA: Establece el tipo de prueba desde calibración del PLC"""
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
        
        # 🔥 CALCULAR Y CONFIGURAR TIEMPO ESTIMADO EN EL TIMER
        estimated_time = self.calculate_estimated_time(test_type)
        self.timer_module.set_time(estimated_time)
        
        # 🔥 FORZAR ACTUALIZACIÓN COMPLETA DE LA TABLA
        print(f"[TEST_TABLE] 🔄 Forzando actualización completa de tabla...")
        self.update_table()
        
        print(f"[TEST_TABLE] ✅ Tipo de prueba establecido: {test_type}")
        print(f"[TEST_TABLE] ⏱️ Tiempo estimado configurado: {estimated_time:.1f} minutos")

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
        """🔥 MEJORADA: Inicia la prueba con validaciones"""
        # 🔥 VALIDAR QUE HAYA UN TIPO DE PRUEBA SELECCIONADO
        if not self.current_test_type:
            print("[TEST_TABLE] ⚠️ No hay tipo de prueba seleccionado")
            # 🔥 MOSTRAR ALERTA DE TIPO DE PRUEBA NO SELECCIONADO
            def close_alert(e):
                alert.open = False
                if hasattr(alert, 'page') and alert.page is not None:
                    alert.page.update()
            
            alert = ft.AlertDialog(
                title=ft.Text("❌ Tipo de Prueba No Definido"),
                content=ft.Text("Por favor, espere a que el sistema detecte la calibración (Q1, Q2, Q3 o Q4) antes de iniciar la prueba.", size=14),
                actions=[ft.TextButton("Entendido", on_click=close_alert)],
            )
            
            if hasattr(self.data_table, 'page') and self.data_table.page is not None:
                self.data_table.page.overlay.append(alert)
                alert.open = True
                self.data_table.page.update()
            return
        
        # 🔥 VALIDAR LECTURAS INICIALES
        empty_rows = self._validate_initial_readings()
        if empty_rows:
            print(f"[TEST_TABLE] ❌ Faltan lecturas iniciales en filas: {empty_rows}")
            self._show_validation_alert(empty_rows)
            return
        
        print("[TEST_TABLE] ✅ Validaciones pasadas, iniciando prueba...")
        
        # 🔥 MARCAR PRUEBA COMO EN PROGRESO
        self.test_in_progress = True
        self.active_test_type = self.current_test_type
        
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
        
        # 🔥 INICIAR TIMER CON EL TIEMPO YA CONFIGURADO
        self.timer_module.start_countdown()
        
        if hasattr(self, 'on_test_control'):
            self.on_test_control("start")
            
        try:
            self.start_test_button.update()
            self.finish_test_button.update()
        except:
            pass
            
        print(f"[TEST_TABLE] ▶️ Prueba iniciada: {self.current_test_type}")

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
        self.finish_test_button.disabled = True
        
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
        """Inicializa la tabla con los valores por defecto"""
        try:
            print(f"[TEST_TABLE] 🔄 Inicializando tabla. Filas: {len(self.rows)}")
            if not self.rows:
                self.rows.append(["", "", "", "", "", "", "", ""])
            self.update_table()
        except Exception as e:
            print(f"❌ Error inicializando tabla: {e}")

    def build(self):
        """🔥 CONSTRUYE LA TABLA COMPLETA CON BOTONES EN UNA SOLA FILA"""
        table_container = ft.Container(
            content=ft.Column(
                controls=[self.table_with_margin],  # 🔥 USAR EL TABLE CON MARGEN
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

        main_column = ft.Column([
            
            # 🔥 FILA ÚNICA CON TODOS LOS BOTONES Y TIMER
            ft.Row([
                ft.ElevatedButton("Agregar fila", icon=ft.Icons.ADD, on_click=self.add_row, width=140),
                self.timer_module.build(),  # 🔥 TIMER INTEGRADO
                self.start_test_button,     # 🔥 BOTÓN INICIAR PRUEBA
                self.finish_test_button,    # 🔥 BOTÓN FINALIZAR PRUEBA
                ft.ElevatedButton("Ver Histórico", icon=ft.Icons.HISTORY, on_click=self.show_volume_history, width=140),
            ], alignment="start", spacing=15),
            
            table_container,
        ], 
        expand=True,
        alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )

        return main_column

    # 🔥 FUNCIONES PÚBLICAS PARA COMPATIBILIDAD
    def actualizar_valores_instantaneos(self, q1, q2, q3, q4):
        """Wrapper para compatibilidad"""
        return self.update_instant_values(q1, q2, q3, q4)

def create_test_table_module(on_data_changed):
    """Función factory para crear el módulo de tabla"""
    return TestTableModule(on_data_changed)