import serial
import serial.tools.list_ports
import threading
import time
from utils.modbus_utils import build_modbus_ascii_command, parse_modbus_ascii_response
from utils.address_utils import get_address

BYTE_ORDER_FLOAT = 'little_word'

class ModbusService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ModbusService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.serial_port = None
        self.connected = False
        self.slave = 1
        self._reading = False
        self._read_thread = None
        self._lock = threading.Lock()
        self._initialized = True

    def detect_port(self):
        ports = list(serial.tools.list_ports.comports())
        return ports[0].device if ports else None

    def connect(self, port, baudrate=9600):
        try:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
            self.serial_port = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=serial.SEVENBITS,
                parity=serial.PARITY_EVEN,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )
            self.connected = True
            return True
        except Exception:
            self.connected = False
            return False

    def close(self):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            self.connected = False

    def send_command(self, command):
        if not self.connected or not self.serial_port:
            return None
        try:
            with self._lock:
                self.serial_port.reset_input_buffer()
                if isinstance(command, str):
                    print(f"[ModbusService] Sending command: {command.strip()}")
                    command_bytes = command.encode('ascii')
                else:
                    command_bytes = command
                    try:
                        print(f"[ModbusService] Sending command: {command_bytes.decode('ascii').strip()}")
                    except Exception:
                        print(f"[ModbusService] Sending command (bytes): {command_bytes}")
                self.serial_port.write(command_bytes)
                time.sleep(0.01)
                response = self.serial_port.read(100)
                return response
        except Exception as e:
            print(f"❌ Error sending command: {str(e)}")
            return

    def start_read_loop(self, slave, update_ui_callback):
        if self._read_thread and self._read_thread.is_alive():
            return
        self._reading = True
        self.slave = slave
        self._read_thread = threading.Thread(
            target=self._read_loop,
            args=(update_ui_callback,)
        )
        self._read_thread.daemon = True
        self._read_thread.start()

    def stop_read_loop(self):
        self._reading = False

    def _read_loop(self, update_ui_callback):
        while self._reading:
            try:
                # Read flow (caudal) values
                flow_info = get_address('D', 136)
                flow_cmd = build_modbus_ascii_command(
                    self.slave, 3,
                    int(flow_info['high_byte'], 16), int(flow_info['low_byte'], 16),
                    quantity=6
                )
                flow_response = self.send_command(flow_cmd)
                flow_data = []
                if flow_response:
                    parsed = parse_modbus_ascii_response(flow_response, float_byte_order=BYTE_ORDER_FLOAT)
                    flow_data = parsed.get('data', [])

                # Read volume values
                volume_info = get_address('D', 150)
                volume_cmd = build_modbus_ascii_command(
                    self.slave, 3,
                    int(volume_info['high_byte'], 16), int(volume_info['low_byte'], 16),
                    quantity=8
                )
                volume_response = self.send_command(volume_cmd)
                volume_data = []
                if volume_response:
                    parsed = parse_modbus_ascii_response(volume_response, float_byte_order=BYTE_ORDER_FLOAT)
                    volume_data = parsed.get('data', [])

                instant_data = flow_data + volume_data
                if len(instant_data) < 6:
                    instant_data += [0] * (6 - len(instant_data))

                update_ui_callback("instant", {"data": instant_data})

                time.sleep(0.5)
            except Exception as ex:
                update_ui_callback("log", {"log": f"Error in Modbus read: {ex}"})

    def send_boolean(self, name, value):
        """Envía un valor booleano a un registro M específico"""
        try:
            # 🔥 MAPEO CORRECTO DE NOMBRES A DIRECCIONES M
            button_mapping = {
                "Caudal Q1": "M264",
                "Caudal Q2": "M265", 
                "Caudal Q3": "M266",
                "Caudal Q4": "M267",
                "Hidrostática": "M268",
                "Iniciar Prueba": "M269",
                "Modo Automático": "M271",
                "Finalizar Prueba": "M270"
            }
            
            # 🔥 VERIFICAR QUE EL NOMBRE EXISTE EN EL MAPEO
            if name not in button_mapping:
                print(f"❌ Botón '{name}' no encontrado en mapeo. Disponibles: {list(button_mapping.keys())}")
                return False
                
            address_str = button_mapping[name]
            print(f"[MODBUS] Enviando {name} -> {address_str} = {value}")
            
            # Obtener información de dirección
            info = get_address('M', int(address_str[1:]))
            if not info:
                print(f"❌ No se pudo obtener información para {address_str}")
                return False
                
            # 🔥 FUNCIÓN AUXILIAR PARA ENVIAR COMANDO
            def send_single_command(val):
                command = build_modbus_ascii_command(
                    slave_address=self.slave,
                    function_code=5,  # Write Single Coil
                    address_high=int(info['high_byte'], 16),
                    address_low=int(info['low_byte'], 16),
                    quantity=1,
                    value=0xFF00 if val else 0x0000,
                    value_type="bool"
                )
                return self.send_command(command)
            
            # 🔥 ENVIAR EL VALOR SOLICITADO
            response = send_single_command(value)
            if not response:
                print(f"[MODBUS] ❌ Error enviando {name} = {value}")
                return False
                
            print(f"[MODBUS] ✅ {name} = {value} enviado correctamente")
            
            # 🔥 SI SE ENVIÓ TRUE, AUTOMÁTICAMENTE ENVIAR FALSE DESPUÉS
            if value:
                time.sleep(0.1)  # Pequeña pausa entre comandos
                response_false = send_single_command(False)
                if response_false:
                    print(f"[MODBUS] ✅ {name} = False enviado automáticamente (botón momentáneo)")
                else:
                    print(f"[MODBUS] ⚠️ Error enviando {name} = False automático")
            
            return True
            
        except Exception as ex:
            print(f"❌ Error en send_boolean para '{name}': {ex}")
            return False


    def send_values(self, field_map, field_widgets, changed_fields, log_callback):
        for name, (addr, value_type) in field_map.items():
            if not changed_fields[name]:
                continue
            widget = field_widgets[name]
            value_str = widget.get()
            try:
                value = int(float(value_str)) if value_type == "int" else float(value_str)
            except Exception as e:
                log_callback(f"⚠️ Invalid value in {name}: {value_str} ({e})")
                continue
            info = get_address('D', int(addr[1:]))
            if not isinstance(info, dict):
                log_callback(f"❌ Invalid address for {addr}")
                continue
            quantity = 1 if value_type == "int" else 2
            function = 6 if value_type == "int" else 16
            val_param = value if function == 6 else [value]
            cmd = build_modbus_ascii_command(
                self.slave, function,
                int(info['high_byte'], 16), int(info['low_byte'], 16),
                quantity=quantity,
                value=val_param,
                value_type=value_type,
                float_byte_order=BYTE_ORDER_FLOAT
            )
            self.send_command(cmd)
            log_callback(f"📤 Writing [{addr}]: {cmd.strip()}")


    def read_system_status(self):
        """Lee los estados FC0-FC25 (M277-M302) y retorna los mensajes activos"""
        if not self.connected or not self.serial_port:
            return []
        
        try:
            with self._lock:
                # Leer desde M277 hasta M302 (26 bits)
                info = get_address('M', 277)
                cmd = build_modbus_ascii_command(
                    self.slave, 1,  # Función 1 = Read Coils
                    int(info['high_byte'], 16), int(info['low_byte'], 16),
                    quantity=26
                )
                
                response = self.send_command(cmd)
                if not response:
                    return []
                    
                parsed = parse_modbus_ascii_response(response)
                if parsed.get('type') != 'read' or 'bits' not in parsed:
                    return []
                
                bits = parsed['bits']
                
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
                
                # Recopilar mensajes activos
                active_messages = []
                for i, bit_value in enumerate(bits[:26]):  # Solo los primeros 26 bits
                    if bit_value and i in fc_messages:
                        active_messages.append(fc_messages[i])
                
                return active_messages
                
        except Exception as e:
            print(f"❌ Error leyendo estados del sistema: {e}")
            return []
    