import flet as ft
from controllers.client_controller import get_all_clients, add_client
from controllers.technician_controller import get_all_technicians, add_technician
from utils.validation_utils import is_valid_email, is_valid_phone, is_valid_name
from views.widgets.test_configuration_table import test_configuration_table
from utils.modbus_utils import build_modbus_ascii_command
from utils.address_utils import get_address
from services.modbus_service import ModbusService
import time
import threading

RATIO_OPTIONS = ["80", "100", "160", "250", "400"]
DIAMETER_OPTIONS = ["15", "20", "25", "32", "40", "50"]

def get_batch_registration_view(page, on_continue):
    clients = get_all_clients()
    technicians = get_all_technicians()

    calculated_flows = {"Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0}

    # 🔥 CREAR LA TABLA DE CONFIGURACIÓN DE PRUEBAS
    config_table = test_configuration_table()

    client_dropdown = ft.Dropdown(
        label="Cliente",
        options=[ft.dropdown.Option(c["name"]) for c in clients] + [ft.dropdown.Option("Agregar nuevo...")],
        expand=True
    )
    technician_dropdown = ft.Dropdown(
        label="Técnico",
        options=[ft.dropdown.Option(t["name"]) for t in technicians] + [ft.dropdown.Option("Agregar nuevo...")],
        expand=True
    )

    brand = ft.TextField(label="Marca", expand=True)
    model = ft.TextField(label="Modelo", expand=True)
    ratio = ft.Dropdown(
        label="Ratio",
        options=[ft.dropdown.Option(r) for r in RATIO_OPTIONS],
        expand=True
    )
    nominal_flow = ft.TextField(
        label="Caudal Nominal(L/h)",
        expand=True,
    )
    diameter = ft.Dropdown(
        label="Diametro",
        options=[ft.dropdown.Option(d) for d in DIAMETER_OPTIONS],
        expand=True
    )
    meter_type = ft.TextField(label="Tipo", expand=True)
    batch = ft.Dropdown(
        label="Estado",
        options=[ft.dropdown.Option("Nuevo"), ft.dropdown.Option("Usado")],
        expand=True
    )

    # 🔥 RADIOBUTTON PARA SELECCIÓN DE MODO
    operation_mode = ft.RadioGroup(
        content=ft.Row([
            ft.Radio(value="manual", label="Modo Manual"),
            ft.Radio(value="automatic", label="Modo Automático"),
        ]),
        value="automatic"  # 🔥 VALOR POR DEFECTO
    )

    # --- Popups para cliente/técnico ---
    client_name_field = ft.TextField(label="Nombre", expand=True)
    client_phone_field = ft.TextField(label="Teléfono", expand=True)
    client_address_field = ft.TextField(label="Dirección", expand=True)
    client_email_field = ft.TextField(label="Email", expand=True)
    client_error = ft.Text("", color="red")

    def calculate_flows():
        """Calcula los caudales Q1, Q2, Q3, Q4 basados en los datos ingresados"""
        try:
            if not all([ratio.value, nominal_flow.value]):
                return
                
            R = float(ratio.value)  # Ratio
            Q3 = float(nominal_flow.value)  # 🔥 YA ESTÁ EN L/H, NO CONVERTIR
            
            # 🔥 FÓRMULAS DE CÁLCULO
            Q1 = Q3 / R
            Q2 = Q1 * 1.6
            Q4 = Q3 * 1.25
            
            calculated_flows["Q1"] = round(Q1, 2)
            calculated_flows["Q2"] = round(Q2, 2)
            calculated_flows["Q3"] = round(Q3, 2)
            calculated_flows["Q4"] = round(Q4, 2)
            
            print(f"[BATCH_REG] 🧮 Caudales calculados: Q1={Q1:.2f}, Q2={Q2:.2f}, Q3={Q3:.2f}, Q4={Q4:.2f}")
            
            # 🔥 ACTUALIZAR LA TABLA CON LOS NUEVOS VALORES
            if hasattr(config_table, 'update_flow_values'):
                config_table.update_flow_values(Q1, Q2, Q3, Q4)
            
        except ValueError as e:
            print(f"[BATCH_REG] ❌ Error calculando caudales: {e}")
            calculated_flows.update({"Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0})

    def client_name_on_change(e):
        value = client_name_field.value.upper()
        value = ''.join([c for c in value if c.isalpha() or c == ' '])
        client_name_field.value = value
        page.update()

    def client_phone_on_change(e):
        value = ''.join([c for c in client_phone_field.value if c.isdigit()])
        client_phone_field.value = value
        page.update()

    client_name_field.on_change = client_name_on_change
    client_phone_field.on_change = client_phone_on_change

    def close_client_dialog(e=None):
        page.dialog.open = False
        page.update()

    def save_new_client(e):
        """Guarda un nuevo cliente usando solo el nombre"""
        name = client_name_field.value.strip().upper()
        phone = client_phone_field.value.strip()
        address = client_address_field.value.strip()
        email = client_email_field.value.strip()
        
        # 🔥 VALIDACIONES
        if not is_valid_name(name):
            client_error.value = "Nombre inválido (solo letras y espacios, mayúsculas, sin caracteres especiales)"
            page.update()
            return
        elif not is_valid_phone(phone):
            client_error.value = "Teléfono inválido (solo números, 7-20 dígitos)"
            page.update()
            return
        elif not is_valid_email(email):
            client_error.value = "Email inválido"
            page.update()
            return
        
        try:
            # 🔥 CORECCIÓN: PASAR SOLO EL NOMBRE, NO EL DICCIONARIO COMPLETO
            print(f"[CLIENT] 💾 Guardando cliente: {name}")
            add_client(name)  # 🔥 SOLO EL NOMBRE COMO STRING
            
            # 🔥 ACTUALIZAR DROPDOWN CON NUEVA LISTA
            updated_clients = get_all_clients()
            client_dropdown.options = [ft.dropdown.Option(c["name"]) for c in updated_clients] + [ft.dropdown.Option("Agregar nuevo...")]
            client_dropdown.value = name
            
            # 🔥 CERRAR DIÁLOGO
            page.dialog.open = False
            page.update()
            
            print(f"[CLIENT] ✅ Cliente '{name}' guardado exitosamente")
            
        except Exception as ex:
            print(f"[CLIENT] ❌ Error guardando cliente: {ex}")
            client_error.value = f"Error guardando cliente: {str(ex)}"
            page.update()

    client_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Row([
            ft.Text("Agregar Nuevo Cliente", expand=True),
            ft.IconButton(ft.Icons.CLOSE, on_click=close_client_dialog)
        ]),
        content=ft.Column([
            client_name_field,
            client_phone_field,
            client_address_field,
            client_email_field,
            client_error
        ], tight=True),
        actions=[
            ft.TextButton("Cancelar", on_click=close_client_dialog),
            ft.ElevatedButton("Guardar", on_click=save_new_client)
        ],
        actions_alignment="end"
    )

    technician_name_field = ft.TextField(label="Nombre", expand=True)
    technician_error = ft.Text("", color="red")

    def technician_name_on_change(e):
        value = technician_name_field.value.upper()
        value = ''.join([c for c in value if c.isalpha() or c == ' '])
        technician_name_field.value = value
        page.update()

    technician_name_field.on_change = technician_name_on_change

    def close_technician_dialog(e=None):
        page.dialog.open = False
        page.update()

    def save_new_technician(e):
        """Guarda un nuevo técnico usando solo el nombre"""
        name = technician_name_field.value.strip().upper()
        
        if not is_valid_name(name):
            technician_error.value = "Nombre inválido (solo letras y espacios, mayúsculas, sin caracteres especiales)"
            page.update()
            return
        
        try:
            # 🔥 CORECCIÓN: PASAR SOLO EL NOMBRE, NO EL DICCIONARIO COMPLETO
            print(f"[TECHNICIAN] 💾 Guardando técnico: {name}")
            add_technician(name)  # 🔥 SOLO EL NOMBRE COMO STRING
            
            # 🔥 ACTUALIZAR DROPDOWN CON NUEVA LISTA
            updated_technicians = get_all_technicians()
            technician_dropdown.options = [ft.dropdown.Option(t["name"]) for t in updated_technicians] + [ft.dropdown.Option("Agregar nuevo...")]
            technician_dropdown.value = name
            
            # 🔥 CERRAR DIÁLOGO
            page.dialog.open = False
            page.update()
            
            print(f"[TECHNICIAN] ✅ Técnico '{name}' guardado exitosamente")
            
        except Exception as ex:
            print(f"[TECHNICIAN] ❌ Error guardando técnico: {ex}")
            technician_error.value = f"Error guardando técnico: {str(ex)}"
            page.update()

    technician_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Row([
            ft.Text("Agregar Nuevo Técnico", expand=True),
            ft.IconButton(ft.Icons.CLOSE, on_click=close_technician_dialog)
        ]),
        content=ft.Column([
            technician_name_field,
            technician_error
        ], tight=True),
        actions=[
            ft.TextButton("Cancelar", on_click=close_technician_dialog),
            ft.ElevatedButton("Guardar", on_click=save_new_technician)
        ],
        actions_alignment="end"
    )

    def on_client_change(e):
        if client_dropdown.value == "Agregar nuevo...":
            client_name_field.value = ""
            client_phone_field.value = ""
            client_address_field.value = ""
            client_email_field.value = ""
            client_error.value = ""
            if client_dialog not in page.overlay:
                page.overlay.append(client_dialog)
            page.dialog = client_dialog
            page.dialog.open = True
            page.update()

    def on_technician_change(e):
        if technician_dropdown.value == "Agregar nuevo...":
            technician_name_field.value = ""
            technician_error.value = ""
            if technician_dialog not in page.overlay:
                page.overlay.append(technician_dialog)
            page.dialog = technician_dialog
            page.dialog.open = True
            page.update()
    
    def on_diameter_change(e):
        calculate_flows()

    def on_ratio_change(e):
        calculate_flows()
        
    def on_nominal_flow_change(e):
        value = nominal_flow.value
        # Permite solo números y un punto decimal
        if value and not value.replace('.', '', 1).isdigit():
            nominal_flow.value = ''.join([c for c in value if c.isdigit() or c == '.'])
            # Solo permite un punto
            if nominal_flow.value.count('.') > 1:
                parts = nominal_flow.value.split('.')
                nominal_flow.value = parts[0] + '.' + ''.join(parts[1:])
        calculate_flows()
        page.update()

    def send_bool_m(bit):
        """Envía comando boolean a dirección M específica"""
        try:
            info = get_address('M', bit)
            comand_on = build_modbus_ascii_command(
                1, 5, int(info['high_byte'], 16), int(info['low_byte'], 16), value=1)
            comand_off = build_modbus_ascii_command(
                1, 5, int(info['high_byte'], 16), int(info['low_byte'], 16), value=0)
            
            service = ModbusService()
            service.send_command(comand_on)
            time.sleep(0.1)  # 🔥 PAUSA ENTRE COMANDOS
            service.send_command(comand_off)
            print(f"[MODBUS] ✅ Bit M{bit} activado/desactivado correctamente")
            return True
            
        except Exception as ex:
            print(f"[MODBUS] ❌ Error al enviar a M{bit}: {ex}")
            return False

    def send_to_plc_register(address, value, value_type="int"):
        """Envía un valor al PLC en una dirección determinada"""
        try:
            # 🔥 EXTRAER NÚMERO DE DIRECCIÓN (D122 -> 122)
            if isinstance(address, str) and address.startswith('D'):
                address_num = int(address[1:])
            else:
                address_num = int(address)
                
            info = get_address('D', address_num)
            if not isinstance(info, dict):
                print(f"[MODBUS] ❌ Dirección inválida: D{address_num}")
                return False

            quantity = 1 if value_type == "int" else 2
            function = 6 if value_type == "int" else 16
            value_param = value if function == 6 else [value]

            command = build_modbus_ascii_command(
                slave_address=1,
                function_code=function,
                address_high=int(info['high_byte'], 16),
                address_low=int(info['low_byte'], 16),
                quantity=quantity,
                value=value_param,
                value_type=value_type
            )
            
            service = ModbusService()
            service.send_command(command)
            print(f"[MODBUS] ✅ Escribiendo D{address_num}: {value} ({command.strip()})")
            return True
            
        except Exception as ex:
            print(f"[MODBUS] ❌ Error al enviar D{address_num}: {ex}")
            return False

    ratio.on_change = on_ratio_change
    nominal_flow.on_change = on_nominal_flow_change
    diameter.on_change = on_diameter_change

    client_dropdown.on_change = on_client_change
    technician_dropdown.on_change = on_technician_change

    macro_error = ft.Text("", color="red")

    # 🔥 FUNCIÓN PARA ENVIAR DATOS AL PLC
    def send_data_to_plc_sync(mode, meter_data, calculated_flows, test_configs):
        """Envía datos al PLC según el modo seleccionado con logging detallado - VERSIÓN SÍNCRONA"""
        try:
            print(f"[PLC_COMM] 📡 Iniciando envío de datos al PLC en modo: {mode}")
            
            success_count = 0
            total_operations = 0
            operation_log = []  # 🔥 LOG DETALLADO DE OPERACIONES

            # 🔥 PASO 1: ENVIAR COMANDO DE MODO
            total_operations += 1
            operation_log.append(f"[{total_operations}] Enviando modo de operación...")
            
            if mode == "manual":
                print(f"[PLC_COMM] 🔧 Enviando comando: Modo Manual (bit M272)")
                if send_bool_m(272):
                    success_count += 1
                    operation_log.append(f"[{total_operations}] ✅ Modo Manual activado correctamente")
                else:
                    operation_log.append(f"[{total_operations}] ❌ Error activando Modo Manual")
            else:
                print(f"[PLC_COMM] 🤖 Enviando comando: Modo Automático (bit M271)")
                if send_bool_m(271):
                    success_count += 1
                    operation_log.append(f"[{total_operations}] ✅ Modo Automático activado correctamente")
                else:
                    operation_log.append(f"[{total_operations}] ❌ Error activando Modo Automático")

            # 🔥 PEQUEÑA PAUSA PARA QUE EL USUARIO VEA EL PROGRESO
            time.sleep(0.5)

            # 🔥 PASO 2: ENVIAR DATOS DE CONFIGURACIÓN
            ratio_value = int(meter_data["ratio"])
            q3_nominal = float(meter_data["nominal_flow"])

            print(f"[PLC_COMM] 📊 Enviando configuración del medidor:")
            print(f"  • Ratio: {ratio_value}")
            print(f"  • Q3 (Nominal): {q3_nominal} L/h")

            # Enviar ratio
            total_operations += 1
            operation_log.append(f"[{total_operations}] Enviando ratio: {ratio_value}")
            if send_to_plc_register("D122", ratio_value, "int"):
                success_count += 1
                operation_log.append(f"[{total_operations}] ✅ Ratio enviado a D122")
                print(f"[PLC_COMM] ✅ Ratio enviado a D122")
            else:
                operation_log.append(f"[{total_operations}] ❌ Error enviando ratio a D122")
                print(f"[PLC_COMM] ❌ Error enviando ratio")

            time.sleep(0.3)  # 🔥 PAUSA VISUAL

            # Enviar caudal nominal
            total_operations += 1
            operation_log.append(f"[{total_operations}] Enviando Q3 nominal: {q3_nominal} L/h")
            if send_to_plc_register("D144", q3_nominal, "float"):
                success_count += 1
                operation_log.append(f"[{total_operations}] ✅ Q3 nominal enviado a D144")
                print(f"[PLC_COMM] ✅ Q3 nominal enviado a D144")
            else:
                operation_log.append(f"[{total_operations}] ❌ Error enviando Q3 nominal a D144")
                print(f"[PLC_COMM] ❌ Error enviando Q3 nominal")

            time.sleep(0.3)  # 🔥 PAUSA VISUAL

            # 🔥 PASO 3: ENVIAR VOLÚMENES DE PRUEBAS
            test_address_map = {
                "Q1": "D118",
                "Q2": "D116", 
                "Q3": "D114",
                "Q4": "D112"
            }

            # Crear diccionario test_type -> volumen
            volume_map = {}
            for cfg in test_configs:
                test_type = cfg["test_type"]
                volume = int(cfg["volume"])
                if test_type not in volume_map:
                    volume_map[test_type] = []
                volume_map[test_type].append(volume)

            print(f"[PLC_COMM] 📦 Enviando volúmenes de prueba:")
            for test_type, address in test_address_map.items():
                total_operations += 1
                
                if test_type in volume_map:
                    # Si hay múltiples volúmenes, enviar el primero
                    volume = volume_map[test_type][0]
                    operation_log.append(f"[{total_operations}] Enviando volumen {test_type}: {volume}L → {address}")
                    print(f"[PLC_COMM] 📦 Enviando volumen para {test_type}: {volume} L a {address}")
                    if send_to_plc_register(address, volume, "int"):
                        success_count += 1
                        operation_log.append(f"[{total_operations}] ✅ Volumen {test_type} enviado correctamente")
                    else:
                        operation_log.append(f"[{total_operations}] ❌ Error enviando volumen {test_type}")
                else:
                    # Si no hay volumen definido, enviar 0
                    operation_log.append(f"[{total_operations}] Enviando volumen {test_type}: 0L → {address} (no configurado)")
                    print(f"[PLC_COMM] 📦 Enviando volumen para {test_type}: 0 L a {address} (no configurado)")
                    if send_to_plc_register(address, 0, "int"):
                        success_count += 1
                        operation_log.append(f"[{total_operations}] ✅ Volumen {test_type} (0L) enviado correctamente")
                    else:
                        operation_log.append(f"[{total_operations}] ❌ Error enviando volumen {test_type} (0L)")
                
                time.sleep(0.2)  # 🔥 PAUSA ENTRE COMANDOS

            # 🔥 MOSTRAR RESUMEN COMPLETO
            print(f"[PLC_COMM] 📊 Resumen de envío:")
            print(f"  • Operaciones exitosas: {success_count}/{total_operations}")
            print(f"  • Porcentaje de éxito: {(success_count/total_operations)*100:.1f}%")
            
            # 🔥 MOSTRAR LOG DETALLADO
            print(f"[PLC_COMM] 📋 Log detallado de operaciones:")
            for log_entry in operation_log:
                print(f"  {log_entry}")

            # Considerar éxito si al menos el 80% de operaciones fueron exitosas
            is_success = (success_count / total_operations) >= 0.8
            
            if is_success:
                print(f"[PLC_COMM] ✅ Envío completado exitosamente")
            else:
                print(f"[PLC_COMM] ⚠️ Envío completado con errores")
                
            return is_success

        except Exception as e:
            print(f"[PLC_COMM] ❌ Error crítico enviando datos al PLC: {e}")
            return False

    def validate_and_continue(e):
        """Valida ambos grupos y continúa al siguiente paso"""
        client_name = client_dropdown.value
        technician_name = technician_dropdown.value

        # 🔥 VALIDACIÓN GRUPO 1: DATOS DE MEDIDORES
        if not client_name or client_name == "Agregar nuevo...":
            macro_error.value = "Por favor selecciona o agrega un cliente."
            page.update()
            return
        if not technician_name or technician_name == "Agregar nuevo...":
            macro_error.value = "Por favor selecciona o agrega un técnico."
            page.update()
            return

        # Validación de campos obligatorios
        if not all([brand.value, model.value, ratio.value, nominal_flow.value, diameter.value, meter_type.value, batch.value]):
            macro_error.value = "Todos los campos de medidores son obligatorios."
            page.update()
            return

        # Validación de caudal nominal flotante
        try:
            float(nominal_flow.value)
        except Exception:
            macro_error.value = "El caudal nominal debe ser un número decimal."
            page.update()
            return

        # 🔥 VALIDACIÓN GRUPO 2: MODELO DE ENSAYO
        errors, valid_configs = config_table.validate_configurations()
        
        if errors:
            # Mostrar errores de configuración en diálogo
            error_text = "❌ Errores en la configuración de pruebas:\n\n" + "\n".join(errors)
            
            def close_error_dialog(e):
                error_dialog.open = False
                page.update()
            
            error_dialog = ft.AlertDialog(
                title=ft.Text("❌ Configuración de Pruebas Inválida"),
                content=ft.Text(error_text),
                actions=[ft.TextButton("Corregir", on_click=close_error_dialog)],
            )
            
            page.overlay.append(error_dialog)
            error_dialog.open = True
            page.update()
            return

        # 🔥 VALIDACIÓN GRUPO 3: MODO DE OPERACIÓN
        if not operation_mode.value:
            macro_error.value = "Por favor selecciona un modo de operación."
            page.update()
            return

        # 🔥 SI TODO ES VÁLIDO, OBTENER CONFIGURACIONES Y CONTINUAR
        test_configurations = config_table.get_test_configurations()
        selected_mode = operation_mode.value
        print(f"[BATCH_REG] ✅ Configuraciones válidas: {len(test_configurations)} pruebas")
        print(f"[BATCH_REG] 🎯 Modo seleccionado: {selected_mode}")
        
        # Guardar configuraciones en la sesión
        page.session.set("test_configurations", test_configurations)
        page.session.set("calculated_flows", calculated_flows)
        page.session.set("operation_mode", selected_mode)
        
        # Preparar datos del medidor
        meter_data = {
            "brand": brand.value,
            "model": model.value,
            "ratio": ratio.value,
            "nominal_flow": nominal_flow.value,
            "diameter": diameter.value,
            "type": meter_type.value,
            "batch": batch.value,
            "client_name": client_name,
            "technician_name": technician_name,
        }
        
        # Mostrar confirmación con el modo seleccionado
        config_summary = "📋 Resumen de configuración:\n\n"
        config_summary += f"🎯 Modo de operación: {selected_mode.upper()}\n\n"
        config_summary += f"🔧 Datos del medidor:\n"
        config_summary += f"  • Marca: {brand.value}\n"
        config_summary += f"  • Modelo: {model.value}\n"
        config_summary += f"  • Ratio: {ratio.value}\n"
        config_summary += f"  • Caudal Nominal (Q3): {nominal_flow.value} L/h\n"
        config_summary += f"  • Diámetro: {diameter.value} mm\n\n"
        config_summary += f"📊 Caudales calculados:\n"
        config_summary += f"  • Q1: {calculated_flows['Q1']:.2f} L/h\n"
        config_summary += f"  • Q2: {calculated_flows['Q2']:.2f} L/h\n"
        config_summary += f"  • Q3: {calculated_flows['Q3']:.2f} L/h\n"
        config_summary += f"  • Q4: {calculated_flows['Q4']:.2f} L/h\n\n"
        config_summary += f"📋 Total de pruebas: {len(test_configurations)}\n"
        config_summary += f"🔬 Tipos de prueba: {', '.join(set(c['test_type'] for c in test_configurations))}\n\n"
        config_summary += "Secuencia de pruebas:\n"
        for i, config in enumerate(test_configurations, 1):
            config_summary += f"{i}. {config['test_name']}"
            if config['total_repetitions'] > 1:
                config_summary += f" (Rep. {config['repetition']}/{config['total_repetitions']})"
            config_summary += f" - Vol: {config['volume']:.2f}L, Tiempo: {config['time_formatted']}\n"

        # 🔥 ELEMENTOS DEL DIÁLOGO DE PROGRESO
        progress_ring = ft.ProgressRing(width=50, height=50, stroke_width=4)
        progress_text = ft.Text("Enviando datos al PLC...", size=16, text_align="center")
        progress_details = ft.Text("Iniciando comunicación...", size=12, text_align="center", color=ft.Colors.GREY_600)

        def confirm_and_send_data(e):
            """Confirma y envía datos al PLC con indicador de progreso detallado - VERSIÓN CORREGIDA"""
            confirm_dialog.open = False
            page.update()
            
            # 🔥 GUARDAR TODOS LOS DATOS EN LA PÁGINA PARA ACCESO POSTERIOR
            page.client_name = client_name
            page.technician_name = technician_name
            page.brand = brand.value
            page.model = model.value
            page.ratio = ratio.value
            page.nominal_flow = nominal_flow.value
            page.diameter = diameter.value
            page.meter_type = meter_type.value
            page.batch = batch.value
            
            print(f"[BATCH_REG] 💾 Datos guardados en página:")
            print(f"  • Cliente: {client_name}")
            print(f"  • Técnico: {technician_name}")
            print(f"  • Marca: {brand.value}")
            print(f"  • Modelo: {model.value}")
            print(f"  • Ratio: {ratio.value}")
            print(f"  • Caudal Nominal: {nominal_flow.value}")
            print(f"  • Diámetro: {diameter.value}")
            print(f"  • Tipo: {meter_type.value}")
            print(f"  • Batch: {batch.value}")
            
            # 🔥 TAMBIÉN GUARDAR EN SESSION COMO RESPALDO
            try:
                page.session.set("client_name", client_name)
                page.session.set("technician_name", technician_name)
                page.session.set("brand", brand.value)
                page.session.set("model", model.value)
                page.session.set("ratio", ratio.value)
                page.session.set("nominal_flow", nominal_flow.value)
                page.session.set("diameter", diameter.value)
                page.session.set("meter_type", meter_type.value)
                page.session.set("batch", batch.value)
                print("[BATCH_REG] 💾 Datos también guardados en session")
            except Exception as session_error:
                print(f"[BATCH_REG] ⚠️ Error guardando en session: {session_error}")
            
            # 🔥 ELEMENTOS DEL DIÁLOGO DE PROGRESO MEJORADOS
            progress_ring = ft.ProgressRing(width=60, height=60, stroke_width=6, color=ft.Colors.BLUE_600)
            progress_text = ft.Text("Iniciando comunicación con PLC...", size=16, text_align="center", weight="bold")
            progress_details = ft.Text("Preparando datos...", size=12, text_align="center", color=ft.Colors.GREY_600)
            progress_percentage = ft.Text("0%", size=20, text_align="center", weight="bold", color=ft.Colors.BLUE_700)
            
            # 🔥 BARRA DE PROGRESO ADICIONAL
            progress_bar = ft.ProgressBar(width=280, height=8, bgcolor=ft.Colors.GREY_300, color=ft.Colors.BLUE_600, value=0)
            
            # 🔥 LISTA DE PASOS COMPLETADOS
            steps_column = ft.Column([], spacing=5, height=150, scroll=ft.ScrollMode.AUTO)
            
            def add_step_indicator(step_text, status="progress"):
                """Agrega un indicador de paso"""
                if status == "progress":
                    icon = ft.Icon(ft.Icons.HOURGLASS_EMPTY, color=ft.Colors.ORANGE_600, size=16)
                    color = ft.Colors.ORANGE_600
                elif status == "success":
                    icon = ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_600, size=16)
                    color = ft.Colors.GREEN_600
                elif status == "error":
                    icon = ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED_600, size=16)
                    color = ft.Colors.RED_600
                else:
                    icon = ft.Icon(ft.Icons.CIRCLE, color=ft.Colors.GREY_400, size=16)
                    color = ft.Colors.GREY_600
                
                step_row = ft.Row([
                    icon,
                    ft.Text(step_text, size=11, color=color, expand=True)
                ], spacing=8)
                
                steps_column.controls.append(step_row)
                page.update()  # 🔥 ACTUALIZAR INMEDIATAMENTE
            
            # 🔥 MOSTRAR DIÁLOGO DE PROGRESO MEJORADO
            progress_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Row([
                    ft.Icon(ft.Icons.SETTINGS_ETHERNET, color=ft.Colors.BLUE_600, size=24),
                    ft.Text("📡 Comunicación con PLC", size=18, weight="bold"),
                ]),
                content=ft.Container(
                    content=ft.Column([
                        # 🔥 PROGRESO VISUAL
                        ft.Container(
                            content=ft.Stack([
                                progress_ring,
                                ft.Container(
                                    progress_percentage,
                                    alignment=ft.alignment.center,
                                ),
                            ]),
                            alignment=ft.alignment.center,
                            height=80,
                        ),
                        
                        # 🔥 TEXTO DE ESTADO
                        progress_text,
                        progress_details,
                        
                        # 🔥 BARRA DE PROGRESO
                        progress_bar,
                        
                        ft.Divider(height=10),
                        
                        # 🔥 PASOS DETALLADOS
                        ft.Container(
                            content=ft.Column([
                                ft.Text("Progreso detallado:", size=12, weight="bold", color=ft.Colors.GREY_700),
                                steps_column,
                            ], spacing=5),
                            bgcolor=ft.Colors.GREY_50,
                            padding=10,
                            border_radius=8,
                            border=ft.border.all(1, ft.Colors.GREY_300),
                        ),
                    ], 
                    horizontal_alignment="center",
                    spacing=15,
                    ),
                    width=400,
                    height=500,
                ),
            )
            
            # 🔥 MOSTRAR EL DIÁLOGO INMEDIATAMENTE
            page.overlay.append(progress_dialog)
            progress_dialog.open = True
            page.update()
            
            # 🔥 FUNCIÓN PARA ACTUALIZAR PROGRESO CON FORZAR UPDATE
            def update_progress(step_text, detail_text="", percentage=0):
                # Actualizar elementos visuales
                progress_text.value = step_text
                progress_details.value = detail_text
                progress_percentage.value = f"{percentage}%"
                progress_bar.value = percentage / 100
                
                # Agregar paso a la lista
                add_step_indicator(f"{step_text}", "progress")
                
                # 🔥 FORZAR ACTUALIZACIÓN INMEDIATA
                page.update()
                
                # 🔥 SLEEP PARA QUE EL USUARIO VEA EL PROGRESO
                time.sleep(0.5)  # 🔥 INCREMENTADO A 0.5 SEGUNDOS
                
                # Marcar como completado
                if steps_column.controls:
                    last_step = steps_column.controls[-1]
                    last_step.controls[0] = ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_600, size=16)
                    last_step.controls[1].color = ft.Colors.GREEN_600
                
                # 🔥 ACTUALIZAR DE NUEVO
                page.update()
                time.sleep(0.3)  # 🔥 PAUSA ADICIONAL PARA VER EL COMPLETADO
                
            def retry_connection():
                """Función para reintentar la conexión"""
                progress_dialog.open = False
                page.update()
                # Llamar de nuevo a la función principal
                confirm_and_send_data(None)
                
            def close_progress_dialog():
                """Función para cerrar el diálogo de progreso"""
                progress_dialog.open = False
                page.update()
            
            try:
                # 🔥 EJECUTAR PASOS CON PROGRESO VISUAL Y FORZAR UPDATES
                update_progress("🔌 Estableciendo conexión con PLC...", "Verificando puerto COM y protocolo Modbus", 10)
                
                update_progress("🎯 Enviando modo de operación...", f"Configurando modo {selected_mode.upper()}", 25)
                
                update_progress("⚙️ Enviando ratio del medidor...", f"Ratio: {meter_data['ratio']}", 40)
                
                update_progress("📊 Enviando caudal nominal...", f"Q3: {meter_data['nominal_flow']} L/h", 55)
                
                update_progress("📦 Enviando volúmenes de prueba...", "Configurando volúmenes Q1, Q2, Q3, Q4", 70)
                
                update_progress("🔄 Procesando comandos...", "Ejecutando secuencia de comandos Modbus", 85)
                
                # 🔥 ENVIAR DATOS REALES AL PLC - CON LOGGING INTEGRADO
                print("[BATCH_REG] 🚀 Iniciando envío real de datos...")
                
                # 🔥 FUNCIÓN INTEGRADA PARA ENVIAR DATOS CON PROGRESO EN TIEMPO REAL
                def send_data_with_visual_progress():
                    try:
                        print(f"[PLC_COMM] 📡 Iniciando envío de datos al PLC en modo: {selected_mode}")
                        
                        success_count = 0
                        total_operations = 7  # Número fijo de operaciones
                        
                        # 🔥 OPERACIÓN 1: ENVIAR MODO
                        if selected_mode == "manual":
                            print(f"[PLC_COMM] 🔧 Enviando comando: Modo Manual (bit M272)")
                            if send_bool_m(272):
                                success_count += 1
                                print(f"[PLC_COMM] ✅ Modo Manual activado correctamente")
                            else:
                                print(f"[PLC_COMM] ❌ Error activando Modo Manual")
                        else:
                            print(f"[PLC_COMM] 🤖 Enviando comando: Modo Automático (bit M271)")
                            if send_bool_m(271):
                                success_count += 1
                                print(f"[PLC_COMM] ✅ Modo Automático activado correctamente")
                            else:
                                print(f"[PLC_COMM] ❌ Error activando Modo Automático")

                        # 🔥 PAUSA VISUAL
                        time.sleep(0.3)

                        # 🔥 OPERACIÓN 2: ENVIAR RATIO
                        ratio_value = int(meter_data["ratio"])
                        q3_nominal = float(meter_data["nominal_flow"])

                        print(f"[PLC_COMM] 📊 Enviando configuración del medidor:")
                        print(f"  • Ratio: {ratio_value}")
                        print(f"  • Q3 (Nominal): {q3_nominal} L/h")

                        if send_to_plc_register("D122", ratio_value, "int"):
                            success_count += 1
                            print(f"[PLC_COMM] ✅ Ratio enviado a D122")
                        else:
                            print(f"[PLC_COMM] ❌ Error enviando ratio")

                        time.sleep(0.3)

                        # 🔥 OPERACIÓN 3: ENVIAR CAUDAL NOMINAL
                        if send_to_plc_register("D144", q3_nominal, "float"):
                            success_count += 1
                            print(f"[PLC_COMM] ✅ Q3 nominal enviado a D144")
                        else:
                            print(f"[PLC_COMM] ❌ Error enviando Q3 nominal")

                        time.sleep(0.3)

                        # 🔥 OPERACIONES 4-7: ENVIAR VOLÚMENES
                        test_address_map = {
                            "Q1": "D118",
                            "Q2": "D116", 
                            "Q3": "D114",
                            "Q4": "D112"
                        }

                        # Crear diccionario test_type -> volumen
                        volume_map = {}
                        for cfg in test_configurations:
                            test_type = cfg["test_type"]
                            volume = int(cfg["volume"])
                            if test_type not in volume_map:
                                volume_map[test_type] = []
                            volume_map[test_type].append(volume)

                        print(f"[PLC_COMM] 📦 Enviando volúmenes de prueba:")
                        for test_type, address in test_address_map.items():
                            
                            if test_type in volume_map:
                                # Si hay múltiples volúmenes, enviar el primero
                                volume = volume_map[test_type][0]
                                print(f"[PLC_COMM] 📦 Enviando volumen para {test_type}: {volume} L a {address}")
                                if send_to_plc_register(address, volume, "int"):
                                    success_count += 1
                                else:
                                    print(f"[PLC_COMM] ❌ Error enviando volumen {test_type}")
                            else:
                                # Si no hay volumen definido, enviar 0
                                print(f"[PLC_COMM] 📦 Enviando volumen para {test_type}: 0 L a {address} (no configurado)")
                                if send_to_plc_register(address, 0, "int"):
                                    success_count += 1
                                else:
                                    print(f"[PLC_COMM] ❌ Error enviando volumen {test_type} (0L)")
                            
                            time.sleep(0.2)  # 🔥 PAUSA ENTRE COMANDOS

                        # 🔥 MOSTRAR RESUMEN COMPLETO
                        print(f"[PLC_COMM] 📊 Resumen de envío:")
                        print(f"  • Operaciones exitosas: {success_count}/{total_operations}")
                        print(f"  • Porcentaje de éxito: {(success_count/total_operations)*100:.1f}%")

                        # Considerar éxito si al menos el 80% de operaciones fueron exitosas
                        is_success = (success_count / total_operations) >= 0.8
                        
                        if is_success:
                            print(f"[PLC_COMM] ✅ Envío completado exitosamente")
                        else:
                            print(f"[PLC_COMM] ⚠️ Envío completado con errores")
                            
                        return is_success

                    except Exception as e:
                        print(f"[PLC_COMM] ❌ Error crítico enviando datos al PLC: {e}")
                        return False
                
                # 🔥 LLAMAR A LA FUNCIÓN INTEGRADA
                success = send_data_with_visual_progress()
                
                update_progress("✅ Verificando datos enviados...", "Confirmando recepción en PLC", 95)
                
                if success:
                    update_progress("🎉 ¡Comunicación exitosa!", "Todos los datos enviados correctamente", 100)
                    
                    # 🔥 FINALIZAR CON ÉXITO
                    progress_text.value = "✅ ¡Configuración completada!"
                    progress_details.value = "Preparando interfaz de operación..."
                    progress_ring.visible = False
                    
                    # 🔥 MOSTRAR ÍCONO DE ÉXITO
                    success_icon = ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_600, size=60)
                    progress_dialog.content.content.controls[0] = ft.Container(
                        success_icon,
                        alignment=ft.alignment.center,
                        height=80,
                    )
                    
                    page.update()
                    time.sleep(1.5)
                    
                    # Cerrar diálogo de progreso
                    progress_dialog.open = False
                    page.update()
                    
                    # 🔥 CONTINUAR A LA VISTA CORRESPONDIENTE
                    from views.test_execution_view import get_test_execution_view
            
                    complete_data = {
                        **meter_data,
                        "test_configurations": test_configurations,
                        "calculated_flows": calculated_flows,
                        "operation_mode": selected_mode
                    }
                    
                    # Cambiar a vista de ejecución
                    page.controls.clear()
                    page.controls.append(get_test_execution_view(page, complete_data))
                    page.update()
                    
                else:
                    # 🔥 ERROR EN EL ENVÍO
                    add_step_indicator("❌ Error en la comunicación", "error")
                    progress_text.value = "❌ Error en la comunicación"
                    progress_details.value = "No se pudieron enviar todos los datos al PLC"
                    progress_ring.visible = False
                    
                    # 🔥 MOSTRAR ÍCONO DE ERROR
                    error_icon = ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED_600, size=60)
                    progress_dialog.content.content.controls[0] = ft.Container(
                        error_icon,
                        alignment=ft.alignment.center,
                        height=80,
                    )
                    
                    # 🔥 AGREGAR BOTÓN DE REINTENTAR
                    retry_button = ft.ElevatedButton(
                        "🔄 Reintentar",
                        on_click=lambda e: retry_connection(),
                        bgcolor=ft.Colors.ORANGE_600,
                        color=ft.Colors.WHITE,
                    )
                    
                    close_button = ft.ElevatedButton(
                        "Cerrar",
                        on_click=lambda e: close_progress_dialog(),
                        bgcolor=ft.Colors.GREY_600,
                        color=ft.Colors.WHITE,
                    )
                    
                    progress_dialog.actions = [retry_button, close_button]
                    page.update()
                    
            except Exception as error:
                # 🔥 ERROR CRÍTICO
                add_step_indicator(f"💥 Error crítico: {str(error)}", "error")
                progress_text.value = "❌ Error inesperado"
                progress_details.value = f"Error: {str(error)[:50]}..."
                progress_ring.visible = False
                
                # 🔥 MOSTRAR ÍCONO DE ERROR CRÍTICO
                error_icon = ft.Icon(ft.Icons.WARNING, color=ft.Colors.RED_700, size=60)
                progress_dialog.content.content.controls[0] = ft.Container(
                    error_icon,
                    alignment=ft.alignment.center,
                    height=80,
                )
                
                # 🔥 BOTÓN PARA CERRAR
                close_button = ft.ElevatedButton(
                    "Cerrar",
                    on_click=lambda e: close_progress_dialog(),
                    bgcolor=ft.Colors.RED_600,
                    color=ft.Colors.WHITE,
                )
                
                progress_dialog.actions = [close_button]
                page.update()
                
                # 🔥 MOSTRAR ERROR EN LA VISTA PRINCIPAL TAMBIÉN
                macro_error.value = f"Error crítico: {str(error)}"

        def cancel_continue(e):
            confirm_dialog.open = False
            page.update()

        confirm_dialog = ft.AlertDialog(
            title=ft.Text("✅ Confirmar Configuración y Envío"),
            content=ft.Container(
                content=ft.Text(config_summary, selectable=True),
                width=500,
                height=400,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cancel_continue),
                ft.ElevatedButton(
                    "📡 Enviar al PLC y Continuar", 
                    on_click=confirm_and_send_data,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.GREEN_600,
                        color=ft.Colors.WHITE,
                    )
                ),
            ],
        )
        
        page.overlay.append(confirm_dialog)
        confirm_dialog.open = True
        page.update()

    # 🔥 GRUPO 1: DATOS DE MEDIDORES
    meter_data_group = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.SETTINGS, color=ft.Colors.BLUE_700, size=24),
                ft.Text("Datos de Medidores", size=20, weight="bold", color=ft.Colors.BLUE_700),
            ], alignment="start"),
            
            ft.ResponsiveRow([
                ft.Container(brand, col={"xs":12, "sm":6, "md":4}),
                ft.Container(model, col={"xs":12, "sm":6, "md":4}),
                ft.Container(ratio, col={"xs":12, "sm":6, "md":4}),
                ft.Container(nominal_flow, col={"xs":12, "sm":6, "md":4}),
                ft.Container(diameter, col={"xs":12, "sm":6, "md":4}),
                ft.Container(meter_type, col={"xs":12, "sm":6, "md":4}),
                ft.Container(batch, col={"xs":12, "sm":6, "md":4}),
            ], spacing=10, run_spacing=10),
            
            ft.ResponsiveRow([
                ft.Container(client_dropdown, col={"xs":12, "sm":6, "md":6}),
                ft.Container(technician_dropdown, col={"xs":12, "sm":6, "md":6}),
            ], spacing=10),
        ], spacing=15),
        padding=20,
        border_radius=12,
        border=ft.border.all(2, ft.Colors.BLUE_300),
        bgcolor=ft.Colors.BLUE_50,
        margin=ft.margin.only(bottom=20),
    )

    # 🔥 GRUPO 2: MODELO DE ENSAYO
    test_model_group = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.SCIENCE, color=ft.Colors.GREEN_700, size=24),
                ft.Text("Modelo de Ensayo", size=20, weight="bold", color=ft.Colors.GREEN_700),
            ], alignment="start"),
            config_table,  # 🔥 TABLA DE CONFIGURACIÓN DE PRUEBAS
        ], spacing=15),
        padding=20,
        border_radius=12,
        border=ft.border.all(2, ft.Colors.GREEN_300),
        bgcolor=ft.Colors.GREEN_50,
        margin=ft.margin.only(bottom=20),
    )

    # 🔥 GRUPO 3: MODO DE OPERACIÓN
    operation_mode_group = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.PLAY_ARROW, color=ft.Colors.PURPLE_700, size=24),
                ft.Text("Modo de Operación", size=20, weight="bold", color=ft.Colors.PURPLE_700),
            ], alignment="start"),
            ft.Container(
                content=ft.Column([
                    ft.Text("Seleccione el modo de operación para las pruebas:", size=14, color=ft.Colors.GREY_700),
                    operation_mode,
                ], spacing=10),
                padding=ft.padding.all(15),
            ),
        ], spacing=15),
        padding=20,
        border_radius=12,
        border=ft.border.all(2, ft.Colors.PURPLE_300),
        bgcolor=ft.Colors.PURPLE_50,
        margin=ft.margin.only(bottom=20),
    )

    # 🔥 BOTÓN DE CONTINUAR Y ERRORES
    action_section = ft.Container(
        content=ft.Column([
            macro_error,
            ft.ElevatedButton(
                "📡 Enviar Configuración y Continuar",
                on_click=validate_and_continue,
                width=350,
                height=50,
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.BLUE_600,
                    color=ft.Colors.WHITE,
                    text_style=ft.TextStyle(size=16, weight="bold"),
                )
            ),
        ], horizontal_alignment="center", spacing=10),
        padding=20,
        alignment=ft.alignment.center,
    )

    # 🔥 LAYOUT PRINCIPAL CON SCROLL
    return ft.Column([
        ft.Container(
            content=ft.Text(
                "Registro de Medidores",
                size=28,
                weight="bold",
                text_align="center",
                color=ft.Colors.BLUE_900
            ),
            padding=ft.padding.only(bottom=20),
            alignment=ft.alignment.center,
        ),
        
        meter_data_group,        # 🔥 GRUPO 1
        test_model_group,        # 🔥 GRUPO 2  
        operation_mode_group,    # 🔥 GRUPO 3
        action_section,          # 🔥 ACCIONES
        
    ], 
    scroll=ft.ScrollMode.AUTO,
    spacing=0,
    expand=True,
    )