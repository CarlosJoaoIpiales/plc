import flet as ft
import threading
from controllers.modbus_controller import ModbusController
from utils.modbus_utils import build_modbus_ascii_command, parse_modbus_ascii_response
from utils.address_utils import get_address
from .widgets.table_tests import table_tests
from services.modbus_service import ModbusService

def send_bool_m(bit, update_messages_ui, read_fc_states):
    try:
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
        
        # 🔥 LLAMADA SIMPLIFICADA Y DIRECTA
        threading.Timer(0.3, update_messages_ui).start()
        
    except Exception as ex:
        print(f"[MODBUS] ❌ Error en send_bool_m para M{bit}: {ex}")

def get_automatic_mode_view(page, meter_group_id, selected_batch):

    last_active_test = None

    def readonly_input(label):
        return ft.TextField(label=label, width=120, read_only=True, bgcolor="#f0f0f0")
    # Editable fields
    ratio_input = ft.TextField(label="Ratio", width=120)
    q1_flow = readonly_input("Caudal Q1")
    q2_flow = readonly_input("Caudal Q2")
    q3_flow_input = ft.TextField(label="Caudal Q3 (Prueba)", width=120)
    q4_flow = readonly_input("Caudal Q4")
    q1_volume_input = ft.TextField(label="Volumen Q1 (Prueba)", width=120)
    q2_volume_input = ft.TextField(label="Volumen Q2 (Prueba)", width=120)
    q3_volume_input = ft.TextField(label="Volumen Q3 (Prueba)", width=120)
    q4_volume = ft.TextField(label="Volumen Q4 (Prueba)", width=120)

    # Instant values
    inst_flow_q1 = readonly_input("Caudal Q1 (Inst.)")
    inst_flow_q2 = readonly_input("Caudal Q2 (Inst.)")
    inst_flow_q3 = readonly_input("Caudal Q3 (Inst.)")
    inst_vol_q1 = readonly_input("Volumen Q1 (Inst.)")
    inst_vol_q2 = readonly_input("Volumen Q2 (Inst.)")
    inst_vol_q3 = readonly_input("Volumen Q3 (Inst.)")
    inst_vol_q4 = readonly_input("Volumen Q4 (Inst.)")

    # ✅ CREAR LA REFERENCIA A LA TABLA AQUÍ (ANTES DE update_ui)
    table_widget = table_tests()
    
    # 🔥 DEBUG: Verificar inmediatamente después de crear
    print(f"[DEBUG] table_widget creado: {type(table_widget)}")
    print(f"[DEBUG] table_widget tiene método: {hasattr(table_widget, 'actualizar_valores_instantaneos')}")
    if hasattr(table_widget, 'actualizar_valores_instantaneos'):
        print(f"[DEBUG] Método es callable: {callable(table_widget.actualizar_valores_instantaneos)}")

    # FUNCIÓN PARA ACTUALIZAR ESTADOS DESDE AUTOMATIC MODE
    def update_system_status_from_automatic():
        """Lee y muestra los estados del sistema"""
        nonlocal last_active_test
        
        try:
            service = ModbusService()
            active_messages = service.read_system_status()
            
            if active_messages:
                status_text = "\n".join(active_messages)
                system_status_display.value = status_text
                
                # 🔥 DETECTAR QUÉ PRUEBA ESTÁ ACTIVA
                for message in active_messages:
                    if "🧪 Inicio de prueba Q1" in message:
                        last_active_test = "Q1"
                        print(f"[AUTO_MODE] 🧪 Prueba activa: Q1")
                    elif "🧪 Inicio de prueba Q2" in message:
                        last_active_test = "Q2"
                        print(f"[AUTO_MODE] 🧪 Prueba activa: Q2")
                    elif "🧪 Inicio de prueba Q3" in message:
                        last_active_test = "Q3"
                        print(f"[AUTO_MODE] 🧪 Prueba activa: Q3")
                    elif "🧪 Inicio de prueba Q4" in message:
                        last_active_test = "Q4"
                        print(f"[AUTO_MODE] 🧪 Prueba activa: Q4")
                    
                    # 🔥 DETECTAR TAMBIÉN FIN DE PRUEBA INDIVIDUAL COMO BACKUP
                    elif "✅ Fin de prueba Q1" in message:
                        if last_active_test == "Q1":
                            print(f"[AUTO_MODE] 🏁 FIN DE PRUEBA Q1 DETECTADO")
                            current_volume = float(inst_vol_q1.value) if inst_vol_q1.value else 0.0
                            if hasattr(table_widget, 'capture_pattern_volume') and current_volume > 1.0:
                                print(f"[AUTO_MODE] 🏁 Capturando volumen Q1: {current_volume:.2f}")
                                table_widget.capture_pattern_volume("Q1", current_volume)
                                last_active_test = None
                    
                    elif "✅ Fin de prueba Q2" in message:
                        if last_active_test == "Q2":
                            print(f"[AUTO_MODE] 🏁 FIN DE PRUEBA Q2 DETECTADO")
                            current_volume = float(inst_vol_q2.value) if inst_vol_q2.value else 0.0
                            if hasattr(table_widget, 'capture_pattern_volume') and current_volume > 1.0:
                                print(f"[AUTO_MODE] 🏁 Capturando volumen Q2: {current_volume:.2f}")
                                table_widget.capture_pattern_volume("Q2", current_volume)
                                last_active_test = None
                    
                    elif "✅ Fin de prueba Q3" in message:
                        if last_active_test == "Q3":
                            print(f"[AUTO_MODE] 🏁 FIN DE PRUEBA Q3 DETECTADO")
                            current_volume = float(inst_vol_q3.value) if inst_vol_q3.value else 0.0
                            if hasattr(table_widget, 'capture_pattern_volume') and current_volume > 1.0:
                                print(f"[AUTO_MODE] 🏁 Capturando volumen Q3: {current_volume:.2f}")
                                table_widget.capture_pattern_volume("Q3", current_volume)
                                last_active_test = None
                    
                    elif "✅ Fin de prueba Q4" in message:  # FC19
                        if last_active_test == "Q4":
                            print(f"[AUTO_MODE] 🏁 FIN DE PRUEBA Q4 DETECTADO")
                            current_volume = float(inst_vol_q4.value) if inst_vol_q4.value else 0.0
                            if hasattr(table_widget, 'capture_pattern_volume') and current_volume > 1.0:
                                print(f"[AUTO_MODE] 🏁 Capturando volumen Q4: {current_volume:.2f}")
                                table_widget.capture_pattern_volume("Q4", current_volume)
                                last_active_test = None
                    
                    # 🔥 BACKUP: DETECTAR FC23 COMO SEGUNDA OPCIÓN
                    elif "⏳ Estado de espera, vuelta a inicio de la selección de la prueba" in message:
                        print(f"[AUTO_MODE] 🔄 Detectado FC23 - VUELTA AL INICIO")
                        if last_active_test and hasattr(table_widget, 'capture_pattern_volume'):
                            if last_active_test == "Q1":
                                current_volume = float(inst_vol_q1.value) if inst_vol_q1.value else 0.0
                            elif last_active_test == "Q2":
                                current_volume = float(inst_vol_q2.value) if inst_vol_q2.value else 0.0
                            elif last_active_test == "Q3":
                                current_volume = float(inst_vol_q3.value) if inst_vol_q3.value else 0.0
                            elif last_active_test == "Q4":
                                current_volume = float(inst_vol_q4.value) if inst_vol_q4.value else 0.0
                            
                            if current_volume > 1.0:
                                print(f"[AUTO_MODE] 🏁 Capturando volumen {last_active_test} por FC23: {current_volume:.2f}")
                                table_widget.capture_pattern_volume(last_active_test, current_volume)
                            last_active_test = None
        except Exception as e:
            print(f"Error actualizando estado del sistema: {e}")
    

    # ✅ Controller update function (AHORA table_widget YA ESTÁ DEFINIDA)
    def update_ui(kind, data):
        if kind == "instant" and "data" in data:
            # ACTUALIZAR VALORES INSTANTÁNEOS EN UI
            inst_flow_q1.value = f"{data['data'][0]:.2f}"
            inst_flow_q2.value = f"{data['data'][1]:.2f}"
            inst_flow_q3.value = f"{data['data'][2]:.2f}"
            inst_vol_q1.value = f"{data['data'][3]:.2f}"
            inst_vol_q2.value = f"{data['data'][4]:.2f}"
            inst_vol_q3.value = f"{data['data'][5]:.2f}"
            inst_vol_q4.value = f"{data['data'][6]:.2f}"
            page.update()
            
            # 🔥 ENVIAR VALORES INSTANTÁNEOS A TABLA (SIN FORZAR UPDATE DE TABLA)
            if hasattr(table_widget, 'actualizar_valores_instantaneos'):
                table_widget.actualizar_valores_instantaneos(
                    data['data'][3], data['data'][4], data['data'][5], data['data'][6]
                )
        
        elif kind == "log" and "log" in data:
            # 🔥 MANEJAR LOGS NORMALES
            print(f"[MODBUS_LOG] {data['log']}")

    # Pulsador button generator usando el número de bit
    def create_test_button(name, bit):
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
                print(f"[AUTOMATIC_MODE] 🔧 Configurando prueba: {test_type}")
                
                # Notificar a la tabla que se inicia una nueva configuración
                if hasattr(table_widget, 'notify_test_start'):
                    table_widget.notify_test_start(test_type)
            
            # 🔥 MANTENER EL SISTEMA DE ENVÍO ORIGINAL
            send_bool_m(bit, update_system_status_from_automatic, controller.service.read_system_status)
            
        return ft.ElevatedButton(content=ft.Text(name), width=180, on_click=on_click)

    # Setup controller
    controller = ModbusController(update_ui)
    port = controller.service.detect_port()
    if port:
        controller.service.connect(port)
        controller.start_reading(1)

    # Read from Modbus
    def read_test_values():
        try:
            info_ratio = get_address('D', 122)
            cmd_ratio = build_modbus_ascii_command(1, 3, int(info_ratio['high_byte'], 16), int(info_ratio['low_byte'], 16), value=1)
            try:
                res_ratio = controller.service.send_command(cmd_ratio)
                ratio_input.value = str(parse_modbus_ascii_response(res_ratio)["data"][0])
            except Exception as ex:
                print(f"Error leyendo ratio: {ex}")

            info_flows = get_address('D', 142)
            cmd_flows = build_modbus_ascii_command(1, 3, int(info_flows['high_byte'], 16), int(info_flows['low_byte'], 16), quantity=8)
            try:
                res_flows = controller.service.send_command(cmd_flows)
                flow_data = parse_modbus_ascii_response(res_flows, float_byte_order='little_word')["data"]
                q1_flow.value = flow_data[3]
                q2_flow.value = flow_data[2]
                q3_flow_input.value = flow_data[1]
                q4_flow.value = flow_data[0]
            except Exception as ex:
                print(f"Error leyendo caudales de prueba: {ex}")

            try:
                # Q1 - D118
                info_q1 = get_address('D', 118)
                cmd_q1 = build_modbus_ascii_command(1, 3, int(info_q1['high_byte'], 16), int(info_q1['low_byte'], 16), quantity=1)
                res_q1 = controller.service.send_command(cmd_q1)
                q1_volume_input.value = int(parse_modbus_ascii_response(res_q1)["data"][0])
            
                # Q2 - D116
                info_q2 = get_address('D', 116)
                cmd_q2 = build_modbus_ascii_command(1, 3, int(info_q2['high_byte'], 16), int(info_q2['low_byte'], 16), quantity=1)
                res_q2 = controller.service.send_command(cmd_q2)
                q2_volume_input.value = int(parse_modbus_ascii_response(res_q2)["data"][0])
            
                # Q3 - D114
                info_q3 = get_address('D', 114)
                cmd_q3 = build_modbus_ascii_command(1, 3, int(info_q3['high_byte'], 16), int(info_q3['low_byte'], 16), quantity=1)
                res_q3 = controller.service.send_command(cmd_q3)
                q3_volume_input.value = int(parse_modbus_ascii_response(res_q3)["data"][0])
            
                # Q4 - D112
                info_q4 = get_address('D', 112)
                cmd_q4 = build_modbus_ascii_command(1, 3, int(info_q4['high_byte'], 16), int(info_q4['low_byte'], 16), quantity=1)
                res_q4 = controller.service.send_command(cmd_q4)
                q4_volume.value = int(parse_modbus_ascii_response(res_q4)["data"][0])
            except Exception as ex:
                print(f"Error leyendo volúmenes de prueba: {ex}")

            page.update()
        except Exception as e:
            print(f"Error leyendo pruebas volumétricas: {e}")

    # ---------- BOTÓN ENVIAR VALORES ----------
    def on_send_values(e):
        try:
            campos = [
                ("Ratio", ratio_input, "D122", "int"),
                ("Caudal Q3 (Prueba)", q3_flow_input, "D144", "float"),
                ("Volumen Q1 (Prueba)", q1_volume_input, "D118", "int"),
                ("Volumen Q2 (Prueba)", q2_volume_input, "D116", "int"),
                ("Volumen Q3 (Prueba)", q3_volume_input, "D114", "int"),
                ("Volumen Q4 (Prueba)", q4_volume, "D112", "int"),
            ]
            for name, widget, address, type_value in campos:
                value = widget.value
                if str(value).strip() == "":
                    continue
                try:
                    val = int(float(value)) if type_value == "int" else float(value)
                except Exception as ex:
                    print(f"Valor inválido en {name}: {value} ({ex})")
                    continue
                info = get_address('D', int(address[1:]))
                if not isinstance(info, dict):
                    print(f"Dirección inválida para {address}")
                    continue
                quantity = 1 if type_value == "int" else 2
                funtion = 6 if type_value == "int" else 16
                value_param = val if funtion == 6 else [val]
                comand = build_modbus_ascii_command(
                    slave_address=1,
                    function_code=funtion,
                    address_high=int(info['high_byte'], 16),
                    address_low=int(info['low_byte'], 16),
                    quantity=quantity,
                    value=value_param,
                    value_type=type_value
                )
                controller.service.send_command(comand)
                print(f"Escribiendo {name}: {comand.strip()}")
            read_test_values()
            update_system_status_from_automatic()
        except Exception as ex:
            print(f"Error al enviar valores: {ex}")
    
    # Buttons
    send_button = ft.ElevatedButton("Enviar valores", width=180, on_click=on_send_values)
    finish_button = ft.ElevatedButton("Finalizar Prueba", width=180)

    # Columns
    left_column = ft.Column([
        ft.Text("📦 Configuración y Lecturas", weight="bold", text_align="center"),
        ratio_input,
        q1_flow,
        q2_flow,
        q3_flow_input,
        q4_flow,
        q1_volume_input,
        q2_volume_input,
        q3_volume_input,
        q4_volume,
        
        ft.Divider(),
        send_button
    ], spacing=10, alignment="center", horizontal_alignment="center")

    # ✅ USAR LA VARIABLE table_widget YA DEFINIDA
    center_column = ft.Column([
        ft.Text("📋 Resultados de pruebas", weight="bold", text_align="center"),
        table_widget  # ✅ AQUÍ USAS LA VARIABLE YA CREADA
    ], spacing=15, alignment="center", horizontal_alignment="center")

    right_column = ft.Column([
        ft.Text("📊 Valores instantáneos", weight="bold", text_align="center"),
        inst_flow_q1,
        inst_flow_q2,
        inst_flow_q3,
        inst_vol_q1,
        inst_vol_q2,
        inst_vol_q3,
        inst_vol_q4,
    ], spacing=10, alignment="center", horizontal_alignment="center")

    # Footer buttons con número de bit/dispositivo
    footer = ft.Column([
        ft.Text("⚙️ Controles de prueba", weight="bold", text_align="center"),
        ft.Row([
            ft.Column([create_test_button("Caudal Q1", 264), create_test_button("Caudal Q2", 265)], spacing=10, expand=1),
            ft.Column([create_test_button("Caudal Q3", 266), create_test_button("Caudal Q4", 267)], spacing=10, expand=1),
            ft.Column([create_test_button("Hidrostática", 268), create_test_button("Iniciar Prueba", 269)], spacing=10, expand=1),
            ft.Column([finish_button], horizontal_alignment="end", expand=1),
        ], alignment="spaceBetween", spacing=20)
    ], spacing=10)

    layout = ft.Column(
        expand=True,
        spacing=10,
        controls=[
            ft.Container(content=footer, padding=10, border_radius=8),
            ft.Row([
                ft.Container(content=left_column, padding=10, border_radius=8, expand=1),
                ft.Container(content=center_column, padding=10, border_radius=8, expand=4),
                ft.Container(content=right_column, padding=10, border_radius=8, expand=1),
            ], expand=True, spacing=10),
        ]
    )

    read_test_values()
    return layout