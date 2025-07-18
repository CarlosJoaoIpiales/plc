import flet as ft
import time
import threading
from utils.modbus_utils import build_modbus_ascii_command
from utils.address_utils import get_address
from services.modbus_service import ModbusService
from views.automatic_mode_view import get_automatic_mode_view

def get_mode_selection_view(on_auto, on_manual):
    # Área donde se cargan los widgets del modo seleccionado
    content_area = ft.Column(
        expand=True,
        alignment="center",
        horizontal_alignment="center",
        scroll=ft.ScrollMode.AUTO
    )

    # Mostrar mensajes de estado (ahora como Column para múltiples mensajes)
    messages_column = ft.Column(
        controls=[ft.Text("📋 Estado del sistema listo", size=20, selectable=True)],
        spacing=5,
        scroll=ft.ScrollMode.AUTO,
        height=50  # Altura fija para el scroll
    )

    # Control de lectura de estados
    _reading_status = {"active": False}

    # Mapeo de FC a mensajes
    fc_messages = {
        0: "✅ Activación de FC0 para selección del modo de trabajo",
        1: "📝 Introducción de valores de ratio, Q3 y selección de la prueba",
        2: "🔧 Inicio de purga de la línea Q1",
        3: "⚙️ Inicio de calibración Q1",
        4: "✅ Fin de calibración Q1",
        5: "🧪 Inicio de prueba Q1",
        6: "✅ Fin de prueba Q1",
        7: "🔧 Inicio de purga de la línea Q2",
        8: "⚙️ Inicio de calibración Q2",
        9: "✅ Fin de calibración Q2",
        10: "🧪 Inicio de prueba Q2",
        11: "✅ Fin de prueba Q2",
        12: "⚙️ Inicio de calibración Q3",
        13: "✅ Fin de calibración Q3",
        14: "🧪 Inicio de prueba Q3",
        15: "✅ Fin de prueba Q3",
        16: "⚙️ Inicio de calibración Q4",
        17: "✅ Fin de calibración Q4",
        18: "🧪 Inicio de prueba Q4",
        19: "✅ Fin de prueba Q4",
        20: "💧 Inicio prueba hidrostática",
        21: "🔚 Fin de prueba, cierre de válvula de entrada de forma manual",
        22: "⚡ Apagado del variador, inicia la prueba",
        23: "⏳ Estado de espera, vuelta a inicio de la selección de la prueba",
        24: "🔧 Inicio modo mantenimiento en modo manual",
        25: "✅ Fin modo mantenimiento en modo manual"
    }

    # Función para leer estados FC
    def read_fc_states():
        """Lee los estados FC0-FC25 (M277-M302) y retorna los mensajes activos"""
        try:
            service = ModbusService()
            if not service.connected:
                return []

            # Leer desde M277 hasta M302 (26 bits)
            info = get_address('M', 277)
            cmd = build_modbus_ascii_command(
                1, 1,  # Función 1 = Read Coils
                int(info['high_byte'], 16), int(info['low_byte'], 16),
                quantity=26
            )
            
            response = service.send_command(cmd)
            if not response:
                return []

            # Parsear respuesta
            from utils.modbus_utils import parse_modbus_ascii_response
            parsed = parse_modbus_ascii_response(response)
            if parsed.get('type') != 'read' or 'bits' not in parsed:
                return []
            
            bits = parsed['bits']
            
            # Recopilar mensajes activos
            active_messages = []
            for i, bit_value in enumerate(bits[:26]):  # Solo los primeros 26 bits
                if bit_value and i in fc_messages:
                    active_messages.append(fc_messages[i])
            
            return active_messages
            
        except Exception as e:
            print(f"❌ Error leyendo estados FC: {e}")
            return []

    # Función para actualizar mensajes en la UI
    def update_messages_ui(active_messages=None):
        """Actualiza la UI con los mensajes activos"""
        try:
            # 🔥 SI NO SE PROPORCIONAN MENSAJES, LEER DEL PLC
            if active_messages is None:
                active_messages = read_fc_states()
            
            # Limpiar mensajes anteriores (excepto el mensaje inicial si no hay estados activos)
            messages_column.controls.clear()
            
            if active_messages:
                for msg in active_messages:
                    messages_column.controls.append(
                        ft.Text(msg, size=20, selectable=True, color=ft.Colors.GREEN)
                    )
                    
                    # 🔥 NUEVA FUNCIONALIDAD: ENVIAR MENSAJES A TRAVÉS DEL TABLE MANAGER
                    table_manager = get_table_manager()
                    table_manager.process_calibration_message(msg)
                    table_manager.process_test_completion_message(msg)
                    print(f"[MODE_SELECTION] 📡 Mensaje enviado a través del Table Manager: {msg}")
            else:
                messages_column.controls.append(
                    ft.Text("Sistema en espera", size=14, color=ft.Colors.GREY)
                )
            
            try:
                messages_column.update()
            except:
                pass  # Ignora errores de actualización UI
                
        except Exception as e:
            print(f"❌ Error actualizando UI de mensajes: {e}")

    # Hilo para monitoreo continuo de estados FC
    def status_monitoring_loop():
        """Loop principal para monitorear estados FC"""
        while _reading_status["active"]:
            try:
                active_messages = read_fc_states()
                
                # Usar timer para ejecutar en el hilo principal de Flet
                def update_ui():
                    update_messages_ui(active_messages)
                
                threading.Timer(0.1, update_ui).start()
                
                time.sleep(1.5)  # Verificar cada 1.5 segundos
                
            except Exception as e:
                print(f"❌ Error en loop de monitoreo: {e}")
                time.sleep(2)

    # Función para iniciar monitoreo de estados
    def start_status_monitoring():
        """Inicia el monitoreo de estados FC"""
        if not _reading_status["active"]:
            _reading_status["active"] = True
            monitor_thread = threading.Thread(target=status_monitoring_loop, daemon=True)
            monitor_thread.start()
            print("Monitoreo de estados FC iniciado")

    # Función para detener monitoreo (opcional)
    def stop_status_monitoring():
        """Detiene el monitoreo de estados FC"""
        _reading_status["active"] = False
        print("⏹️ Monitoreo de estados FC detenido")

    # Enviar booleanos a bits específicos
    def send_bool_m(bit):
        try:
            info = get_address('M', bit)
            comand_on = build_modbus_ascii_command(
                1, 5, int(info['high_byte'], 16), int(info['low_byte'], 16), value=1)
            comand_off = build_modbus_ascii_command(
                1, 5, int(info['high_byte'], 16), int(info['low_byte'], 16), value=0)
            service = ModbusService()
            service.send_command(comand_on)
            service.send_command(comand_off)
            print(f"[MODBUS] Bit M{bit} activado/desactivado")
            
            # Forzar una lectura inmediata después de enviar comando
            threading.Timer(0.2, lambda: threading.Timer(0.1, lambda: update_messages_ui(read_fc_states())).start()).start()
            
        except Exception as ex:
            print(f"❌ Error al enviar a M{bit}: {ex}")

    # Manejador para seleccionar modo
    def make_handler(modo):
        def handler(e):
            if modo == "auto":
                bit = 271
                widget = get_automatic_mode_view(page=e.page, meter_group_id=None, selected_batch=None)
            else:
                bit = 272
                widget = ft.Text("🔧 Aquí iría el widget del modo manual (pendiente)")

            send_bool_m(bit)
            content_area.controls.clear()
            content_area.controls.append(widget)
            
            # Agregar mensaje local también
            local_msg = ft.Text(f"✅ Modo {modo.upper()} activado correctamente.", 
                               size=12, color=ft.Colors.BLUE)
            messages_column.controls.insert(0, local_msg)
            
            try:
                e.page.update()
            except:
                pass
                
        return handler

    # Tamaño uniforme de botones
    button_width = 200

    # Botones de selección de modo
    modo_buttons_column = ft.Column(
        [
            ft.ElevatedButton("Modo Automático", width=button_width, on_click=make_handler("auto")),
            ft.ElevatedButton("Modo Manual", width=button_width, on_click=make_handler("manual")),
        ],
        alignment="center",
        horizontal_alignment="center",
        spacing=15
    )

    # Mensajes en el centro (con scroll)
    mensaje_column = ft.Column(
        [
            ft.Text("📝 Mensajes del sistema", weight="bold"),
            ft.Container(
                content=messages_column,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=8,
                padding=10,
                bgcolor=ft.Colors.GREY_50,
            )
        ],
        alignment="center",
        horizontal_alignment="center",
        spacing=10,
        expand=True
    )

    # Botones de seguridad (también activarán la lectura de estados)
    def emergency_stop(e):
        send_bool_m(262)
    
    def rearme(e):
        send_bool_m(263)

    seguridad_buttons_column = ft.Column(
        [
            ft.ElevatedButton("Parada de Emergencia", width=button_width, color="white", bgcolor="red",
                              on_click=emergency_stop),
            ft.ElevatedButton("Reiniciar", width=button_width, color="white", bgcolor="green",
                              on_click=rearme),
        ],
        alignment="center",
        horizontal_alignment="center",
        spacing=15
    )

    # Footer con tres columnas centradas y responsivas
    footer = ft.Container(
        bgcolor="lightgray",
        padding=20,
        content=ft.Row(
            controls=[
                ft.Container(content=modo_buttons_column, expand=1, alignment=ft.alignment.center),
                ft.Container(content=mensaje_column, expand=2, alignment=ft.alignment.center),
                ft.Container(content=seguridad_buttons_column, expand=1, alignment=ft.alignment.center),
            ],
            alignment="center",
            vertical_alignment="center",
            spacing=20,
            expand=True,
            wrap=False
        )
    )

    # ✅ INICIAR MONITOREO AL CARGAR LA VISTA
    start_status_monitoring()

    # Layout principal
    layout = ft.Column(
        [
            footer,
            content_area
        ],
        expand=True,
        alignment="center",
        horizontal_alignment="center"
    )

    # Agregar función de limpieza para detener monitoreo (opcional)
    layout.stop_monitoring = stop_status_monitoring

    return layout