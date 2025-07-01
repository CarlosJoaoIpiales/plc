import flet as ft
from controllers.modbus_controller import ModbusController
from utils.modbus_utils import build_modbus_ascii_command, parse_modbus_ascii_response
from utils.address_utils import get_address
from .widgets.table_tests import table_tests

def get_automatic_mode_view(page, meter_group_id, selected_batch):
    # Editable fields
    ratio_input = ft.TextField(label="Ratio", width=120)
    q3_flow_input = ft.TextField(label="Caudal Q3 (Prueba)", width=120)
    q1_volume_input = ft.TextField(label="Volumen Q1 (Prueba)", width=120)
    q2_volume_input = ft.TextField(label="Volumen Q2 (Prueba)", width=120)
    q3_volume_input = ft.TextField(label="Volumen Q3 (Prueba)", width=120)

    def readonly_input(label):
        return ft.TextField(label=label, width=120, read_only=True, bgcolor="#f0f0f0")

    q1_flow = readonly_input("Caudal Q1")
    q2_flow = readonly_input("Caudal Q2")
    q4_flow = readonly_input("Caudal Q4")
    q4_volume = readonly_input("Volumen Q4")

    # Instant values
    inst_flow_q1 = readonly_input("Caudal Q1 (Inst.)")
    inst_flow_q2 = readonly_input("Caudal Q2 (Inst.)")
    inst_flow_q3 = readonly_input("Caudal Q3 (Inst.)")
    inst_vol_q1 = readonly_input("Volumen Q1 (Inst.)")
    inst_vol_q2 = readonly_input("Volumen Q2 (Inst.)")
    inst_vol_q3 = readonly_input("Volumen Q3 (Inst.)")
    inst_vol_q4 = readonly_input("Volumen Q4 (Inst.)")

    # Pulsador button generator
    def create_test_button(name):
        def on_click(e):
            controller.service.send_boolean(name, True)
            print(f"{name} ON")
            
            # ✅ ACTUALIZAR ESTADOS DESPUÉS DE PRESIONAR CUALQUIER BOTÓN
            update_system_status_from_automatic()
            
        return ft.ElevatedButton(content=ft.Text(name), width=180, on_click=on_click)
    

    # FUNCIÓN PARA ACTUALIZAR ESTADOS DESDE AUTOMATIC MODE
    def update_system_status_from_automatic():
        try:
            active_messages = controller.service.read_system_status()
            if active_messages:
                for msg in active_messages:
                    print(f"[STATUS] {msg}")
        except Exception as ex:
            print(f"❌ Error actualizando estados desde automatic mode: {ex}")

    # Controller update function
    def update_ui(kind, data):
        if kind == "instant" and "data" in data:
            inst_flow_q1.value = f"{data['data'][0]:.2f}"
            inst_flow_q2.value = f"{data['data'][1]:.2f}"
            inst_flow_q3.value = f"{data['data'][2]:.2f}"
            inst_vol_q1.value = f"{data['data'][3]:.2f}"
            inst_vol_q2.value = f"{data['data'][4]:.2f}"
            inst_vol_q3.value = f"{data['data'][5]:.2f}"
            inst_vol_q4.value = f"{data['data'][6]:.2f}"
            page.update()
            if hasattr(table_widget, 'actualizar_valores_instantaneos'):
                table_widget.actualizar_valores_instantaneos(
                    data['data'][3], data['data'][4], data['data'][5], data['data'][6]
                )

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
                q1_flow.value = f"{flow_data[3]:.2f}"
                q2_flow.value = f"{flow_data[2]:.2f}"
                q3_flow_input.value = f"{flow_data[1]:.2f}"
                q4_flow.value = f"{flow_data[0]:.2f}"
            except Exception as ex:
                print(f"Error leyendo caudales de prueba: {ex}")

            info_vols = get_address('D', 112)
            cmd_vols = build_modbus_ascii_command(1, 3, int(info_vols['high_byte'], 16), int(info_vols['low_byte'], 16), quantity=8)
            try:
                res_vols = controller.service.send_command(cmd_vols)
                vol_data = parse_modbus_ascii_response(res_vols)["data"]
                q1_volume_input.value = str(vol_data[3])
                q2_volume_input.value = str(vol_data[2])
                q3_volume_input.value = str(vol_data[1])
                q4_volume.value = str(vol_data[0])
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
            ]
            for name, widget, address, type_value in campos:
                value = widget.value
                if value.strip() == "":
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
        q3_flow_input,
        q1_volume_input,
        q2_volume_input,
        q3_volume_input,
        q1_flow,
        q2_flow,
        q4_flow,
        q4_volume,
        ft.Divider(),
        send_button
    ], spacing=10, alignment="center", horizontal_alignment="center")

    center_column = ft.Column([
        ft.Text("📋 Resultados de pruebas", weight="bold", text_align="center"),
        table_tests()
    ], spacing=15, alignment="center", horizontal_alignment="center")

    right_column = ft.Column([
        ft.Text("📊 Valores instantáneos", weight="bold", text_align="center"),
        inst_flow_q1,
        inst_vol_q1,
        inst_flow_q2,
        inst_vol_q2,
        inst_flow_q3,
        inst_vol_q3,
        inst_vol_q4,
    ], spacing=10, alignment="center", horizontal_alignment="center")

    # Footer buttons
    footer = ft.Column([
        ft.Text("⚙️ Controles de prueba", weight="bold", text_align="center"),
        ft.Row([
            ft.Column([create_test_button("Caudal Q1"), create_test_button("Caudal Q2")], spacing=10, expand=1),
            ft.Column([create_test_button("Caudal Q3"), create_test_button("Caudal Q4")], spacing=10, expand=1),
            ft.Column([create_test_button("Hidrostática"), create_test_button("Iniciar Prueba")], spacing=10, expand=1),
            ft.Column([finish_button], horizontal_alignment="end", expand=1),
        ], alignment="spaceBetween", spacing=20)
    ], spacing=10)

    layout = ft.Column(
        expand=True,
        spacing=10,
        controls=[
            ft.Container(height=60, border_radius=8),  # Header
            ft.Row([
                ft.Container(content=left_column, padding=10, border_radius=8, expand=1),
                ft.Container(content=center_column, padding=10, border_radius=8, expand=4),
                ft.Container(content=right_column, padding=10, border_radius=8, expand=1),
            ], expand=True, spacing=10),
            ft.Container(content=footer, padding=10, border_radius=8),
        ]
    )

    read_test_values()
    return layout