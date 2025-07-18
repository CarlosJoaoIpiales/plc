import serial
import serial.tools.list_ports
import threading
import time
import queue
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

        # Cola FIFO y worker thread para comandos
        self.command_queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()

    def _process_queue(self):
        while True:
            func, args, kwargs, result_queue = self.command_queue.get()
            # print(f"[ModbusService] Ejecutando comando en la cola: {func.__name__}")
            try:
                result = func(*args, **kwargs)
                if result_queue:
                    result_queue.put(result)
            except Exception as ex:
                #print(f"[ModbusService] ❌ Error procesando comando: {ex}")
                if result_queue:
                    result_queue.put(None)
            #print(f"[ModbusService] Comando finalizado: {func.__name__}")
            self.command_queue.task_done()

    def enqueue_command(self, func, *args, wait_result=False, **kwargs):
        """Agrega un comando a la cola. Si wait_result=True, espera y retorna el resultado."""
        result_queue = queue.Queue() if wait_result else None
        self.command_queue.put((func, args, kwargs, result_queue))
        if wait_result:
            return result_queue.get()
        return None

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

    # --- Métodos Modbus adaptados para usar la cola ---

    def send_command(self, command):
        """Encola el comando y espera la respuesta."""
        return self.enqueue_command(self._send_command_internal, command, wait_result=True)

    def _send_command_internal(self, command):
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
                flow_response = self.enqueue_command(self._send_command_internal, flow_cmd, wait_result=True)
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
                volume_response = self.enqueue_command(self._send_command_internal, volume_cmd, wait_result=True)
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
        """Encola el envío de un valor booleano a un registro M específico"""
        return self.enqueue_command(self._send_boolean_internal, name, value, wait_result=True)

    def _send_boolean_internal(self, name, value):
        try:
            print(f"[send_boolean] INICIO: name={name}, value={value}")
            button_mapping = {
                "Caudal Q1": "M264",
                "Caudal Q2": "M265", 
                "Caudal Q3": "M266",
                "Caudal Q4": "M267",
                "Hidrostática": "M268",
                "Iniciar Prueba": "M269",
                "Modo Automático": "M271",
                "Finalizar Prueba": "M270",
                "Reiniciar": "M263"
            }
            if name not in button_mapping:
                print(f"[send_boolean] ❌ Botón '{name}' no encontrado en mapeo. Disponibles: {list(button_mapping.keys())}")
                return False
            address_str = button_mapping[name]
            print(f"[send_boolean] [MODBUS] Enviando {name} -> {address_str} = {value}")
            info = get_address('M', int(address_str[1:]))
            print(f"[send_boolean] Dirección obtenida: {info}")
            if not info:
                print(f"[send_boolean] ❌ No se pudo obtener información para {address_str}")
                return False
            def send_single_command(val):
                print(f"[send_boolean] Preparando comando para valor: {val}")
                command = build_modbus_ascii_command(
                    slave_address=self.slave,
                    function_code=5,
                    address_high=int(info['high_byte'], 16),
                    address_low=int(info['low_byte'], 16),
                    quantity=1,
                    value=0xFF00 if val else 0x0000,
                    value_type="bool"
                )
                print(f"[send_boolean] Comando generado: {command}")
                resp = self.send_command(command)
                print(f"[send_boolean] Respuesta de send_command: {resp}")
                return resp
            print(f"[send_boolean] Enviando valor principal: {value}")
            response = send_single_command(value)
            print(f"[send_boolean] Respuesta tras enviar valor principal: {response}")
            if not response:
                print(f"[send_boolean] [MODBUS] ❌ Error enviando {name} = {value}")
                return False
            print(f"[send_boolean] [MODBUS] ✅ {name} = {value} enviado correctamente")
            if value:
                print(f"[send_boolean] Esperando 0.1s antes de enviar FALSE automático...")
                time.sleep(0.1)
                print(f"[send_boolean] Enviando FALSE automático...")
                response_false = send_single_command(False)
                print(f"[send_boolean] Respuesta tras enviar FALSE automático: {response_false}")
                if response_false:
                    print(f"[send_boolean] [MODBUS] ✅ {name} = False enviado automáticamente (botón momentáneo)")
                else:
                    print(f"[send_boolean] [MODBUS] ⚠️ Error enviando {name} = False automático")
            print(f"[send_boolean] FIN OK")
            return True
        except Exception as ex:
            print(f"[send_boolean] ❌ Error en send_boolean para '{name}': {ex}")
            return False