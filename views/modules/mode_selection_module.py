import flet as ft
import time
import threading
from utils.modbus_utils import build_modbus_ascii_command
from utils.address_utils import get_address
from services.modbus_service import ModbusService

def create_mode_selection_module(current_mode, on_mode_changed, table_widget=None):
    """Crea el módulo de selección de modo con monitoreo de estados FC"""

    # Mostrar mensajes de estado (ahora como Column para múltiples mensajes)
    messages_column = ft.Column(
        controls=[ft.Text("Estado del sistema listo", size=20, selectable=True)],
        spacing=5,
        scroll=ft.ScrollMode.AUTO,
        height=None
    )

    # Control de lectura de estados
    _reading_status = {"active": False}

    # Mapeo de FC a mensajes
    fc_messages = {
        # --- Mensajes FC0-FC25 (existente) ---
        0: " Activación de FC0 para selección del modo de trabajo",
        1: " Introducción de valores de ratio, Q3 y selección de la prueba",
        2: " Inicio de purga de la línea Q1",
        3: " Inicio de calibración Q1",
        4: " Fin de calibración Q1",
        5: " Inicio de prueba Q1",
        6: " Fin de prueba Q1",
        7: " Inicio de purga de la línea Q2",
        8: " Inicio de calibración Q2",
        9: " Fin de calibración Q2",
        10: " Inicio de prueba Q2",
        11: " Fin de prueba Q2",
        12: " Inicio de calibración Q3",
        13: " Fin de calibración Q3",
        14: " Inicio de prueba Q3",
        15: " Fin de prueba Q3",
        16: " Inicio de calibración Q4",
        17: " Fin de calibración Q4",
        18: " Inicio de prueba Q4",
        19: " Fin de prueba Q4",
        20: " Inicio prueba hidrostática",
        21: " Fin de prueba, cierre de válvula de entrada de forma manual",
        22: " Apagado del variador, inicia la prueba",
        23: " Estado de espera, vuelta a inicio de la selección de la prueba",
        24: " Inicio modo mantenimiento en modo manual",
        25: " Fin modo mantenimiento en modo manual",
        
        # --- Nuevos mensajes M320-M326 (basado en la imagen) ---
        26: " Valores para la línea Q1 ingresados correctamente",  # M320
        27: " Valores para la línea Q2 ingresados correctamente",  # M321
        28: " Valores para la línea Q3 ingresados correctamente",  # M322
        29: " Valores para la línea Q4 ingresados correctamente",  # M323
        30: " Selección de prueba habilitada",                     # M324
        31: " Modo manual activado (100L)",                        # M325
        32: " Valores ingresados - Listo para seleccionar prueba"  # M326
    }

    def read_fc_states():
        """Lee los estados FC0-FC25 (M277-M302) y M320-M326, retorna los mensajes activos"""
        try:
            service = ModbusService()
            if not service.connected:
                return []
    
            # --- Bloque 1: Leer FC0-FC25 (M277-M302) ---
            info_fc = get_address('M', 277)
            cmd_fc = build_modbus_ascii_command(
                1, 1,  # Función 1 = Read Coils
                int(info_fc['high_byte'], 16), int(info_fc['low_byte'], 16),
                quantity=26
            )
            
            response_fc = service.send_command(cmd_fc)
            if not response_fc:
                return []
    
            # Parsear respuesta FC
            from utils.modbus_utils import parse_modbus_ascii_response
            parsed_fc = parse_modbus_ascii_response(response_fc)
            if parsed_fc.get('type') != 'read' or 'bits' not in parsed_fc:
                return []
            
            bits_fc = parsed_fc['bits']
            
            # --- Bloque 2: Leer M320-M326 (7 bits) ---
            info_m = get_address('M', 320)
            cmd_m = build_modbus_ascii_command(
                1, 1,  # Función 1 = Read Coils
                int(info_m['high_byte'], 16), int(info_m['low_byte'], 16),
                quantity=7
            )
            
            response_m = service.send_command(cmd_m)
            bits_m = []
            if response_m:
                parsed_m = parse_modbus_ascii_response(response_m)
                if parsed_m.get('type') == 'read' and 'bits' in parsed_m:
                    bits_m = parsed_m['bits']
    
            # Combinar todos los bits en un solo array [FC0-FC25] + [M320-M326]
            all_bits = bits_fc[:26] + bits_m[:7]  # Aseguramos 26+7 bits
    
            # Recopilar mensajes activos (solo FC0-FC25 usando fc_messages)
            active_messages = []
            for i, bit_value in enumerate(all_bits[:26]):  # Procesar solo FC0-FC25
                if bit_value and i in fc_messages:
                    active_messages.append(fc_messages[i])
            
            # (Opcional) Si necesitas procesar M320-M326 después:
            # for j, bit_value in enumerate(all_bits[26:33]):  # M320-M326
            #     if bit_value:
            #         active_messages.append(f" Alerta M32{j} activa")
            
            return active_messages
            
        except Exception as e:
            print(f" Error leyendo estados FC/M320-M326: {e}")
            return []
        
    # Función para actualizar mensajes en la UI
    def update_messages_ui(active_messages=None):
        """Actualiza la UI con los mensajes activos"""
        try:
            #  SI NO SE PROPORCIONAN MENSAJES, LEER DEL PLC
            if active_messages is None:
                active_messages = read_fc_states()
            
            # Limpiar mensajes anteriores (excepto el mensaje inicial si no hay estados activos)
            messages_column.controls.clear()
            
            if active_messages:
                for msg in active_messages:
                    messages_column.controls.append(
                        ft.Text(msg, size=20, selectable=True, color=ft.Colors.GREEN)
                    )
                    
                    #  NUEVA FUNCIONALIDAD: ENVIAR MENSAJES A LA TABLA
                    if table_widget and hasattr(table_widget, 'process_calibration_message'):
                        try:
                            table_widget.process_calibration_message(msg)
                            print(f"[MODE_SELECTION]  Mensaje enviado a tabla: {msg}")
                        except Exception as e:
                            print(f"[MODE_SELECTION]  Error enviando mensaje a tabla: {e}")
            else:
                messages_column.controls.append(
                    ft.Text("Sistema en espera", size=14, color=ft.Colors.GREY)
                )
            
            try:
                messages_column.update()
            except:
                pass  # Ignora errores de actualización UI
                
        except Exception as e:
            print(f" Error actualizando UI de mensajes: {e}")

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
                print(f" Error en loop de monitoreo: {e}")
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
        print("Monitoreo de estados FC detenido")

    # Enviar booleanos a bits específicos
    def send_bool_m(bit, update_messages_ui=None, read_fc_states=None):
        try:
            service = ModbusService()
            if not service.connected:
                print(" Modbus no conectado en send_bool_m")
                return
    
            info = get_address('M', bit)
            cmd_on = build_modbus_ascii_command(
                1, 5, int(info['high_byte'], 16), int(info['low_byte'], 16), value=1)
            cmd_off = build_modbus_ascii_command(
                1, 5, int(info['high_byte'], 16), int(info['low_byte'], 16), value=0)
    
            # Intento con reintentos
            for attempt in range(3):
                try:
                    print(f"Enviando comando ON (intento {attempt+1})")
                    service.send_command(cmd_on)
                    time.sleep(0.1)  # Pequeña pausa
                    service.send_command(cmd_off)
                    print(f" Bit M{bit} activado/desactivado")
                    break
                except Exception as ex:
                    print(f"Intento {attempt+1} fallido: {str(ex)}")
                    if attempt == 2:
                        raise
    
            # Actualización diferida segura
            def safe_update():
                try:
                    #  USAR LA FUNCIÓN LOCAL update_messages_ui
                    update_messages_ui()
                except Exception as e:
                    print(f"Error en actualización UI: {str(e)}")
    
            threading.Timer(0.5, safe_update).start()
    
        except Exception as ex:
            print(f" Error crítico en send_bool_m: {str(ex)}")

    def send_calibration_message(self, test_type):
        """Envía mensaje de calibración y notifica cambio de tipo"""
        message = f" Fin de calibración {test_type}"
        
        #  ENVIAR A LA TABLA
        if self.table_widget and hasattr(self.table_widget, 'process_calibration_message'):
            self.table_widget.process_calibration_message(message)
        
        #  ENVIAR DIRECTAMENTE EL TIPO DE PRUEBA A LA TABLA
        if self.table_widget and hasattr(self.table_widget, 'set_test_type_from_calibration'):
            self.table_widget.set_test_type_from_calibration(test_type)
            print(f"[MODE_SELECTION]  Tipo {test_type} establecido en tabla")
        
        print(f"[MODE_SELECTION]  Mensaje enviado a tabla: {message}")
    
    # Tamaño uniforme de botones
    button_width = 200

    # Mensajes en el centro (con scroll)
    mensaje_column = ft.Column(
        [
            ft.Text("Mensajes del sistema", weight="bold", text_align="center"),
            ft.Container(
                content=messages_column,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=8,
                padding=10,
                bgcolor=ft.Colors.GREY_50,
                width=None,
                height=None,
            )
        ],
        alignment="center",
        horizontal_alignment="center",
        spacing=10,
        expand=True
    )

    # Botones de seguridad
    def emergency_stop(e):
        send_bool_m(262)
    
    def rearme(e):
        send_bool_m(263)

    # Botón para reiniciar
    restart_button_column = ft.Column(
        [
            ft.ElevatedButton(
                "Reiniciar", 
                width=button_width, 
                color="white", 
                bgcolor="green",
                on_click=rearme
            ),
        ],
        alignment="center",
        horizontal_alignment="center",
        spacing=15
    )

    seguridad_buttons_column = ft.Column(
        [
            ft.ElevatedButton(
                "Parada de Emergencia", 
                width=button_width, 
                color="white", 
                bgcolor="red",
                on_click=emergency_stop
            ),
        ],
        alignment="center",
        horizontal_alignment="center",
        spacing=15
    )

    # INICIAR MONITOREO AL CARGAR LA VISTA
    start_status_monitoring()

    # Layout responsivo con ResponsiveRow
    layout = ft.ResponsiveRow([
        # Columna 1: Control de modo
        ft.Container(
            content=restart_button_column,
            col={"xs": 12, "sm": 4, "md": 3},
            padding=10,
            alignment=ft.alignment.center,
        ),
        
        # Columna 2: Mensajes del sistema
        ft.Container(
            content=mensaje_column,
            col={"xs": 12, "sm": 4, "md": 6},
            padding=10,
            alignment=ft.alignment.center,
        ),
        
        # Columna 3: Botones de seguridad
        ft.Container(
            content=ft.Column([
                seguridad_buttons_column,
            ], 
            spacing=15,
            horizontal_alignment="center",
            alignment="center"
            ),
            col={"xs": 12, "sm": 4, "md": 3},
            padding=10,
            alignment=ft.alignment.center,
        ),
    ], spacing=10)

    # Contenedor principal con estilo
    main_container = ft.Container(
        content=layout,
        padding=20,
        border_radius=12,
        border=ft.border.all(2, ft.Colors.PURPLE_300),
        bgcolor=ft.Colors.PURPLE_50,
    )

    # Agregar función de limpieza para detener monitoreo
    main_container.stop_monitoring = stop_status_monitoring
    
    #  NUEVA FUNCIÓN: Configurar referencia a la tabla
    def set_table_widget(widget):
        """Configura la referencia al widget de tabla"""
        nonlocal table_widget
        table_widget = widget
        print("[MODE_SELECTION] 🔗 Widget de tabla configurado")
    
    #  AGREGAR FUNCIÓN AL CONTAINER
    main_container.set_table_widget = set_table_widget

    return main_container