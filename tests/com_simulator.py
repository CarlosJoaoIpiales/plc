import serial
import time
import struct
import random

# Cambia esto al COM que esté emparejado con el de tu app
SIMULATED_PORT = 'COM2'
BAUDRATE = 9600

class ModbusSimulator:
    def __init__(self):
        # Estados simulados de los registros
        self.holding_registers = {}  # D registers
        self.coil_states = {}       # M registers (bits)
        
        # Buffer para comandos parciales
        self.command_buffer = ""
        
        # Inicializar valores por defecto
        self.init_default_values()
        
    def init_default_values(self):
        # Valores instantáneos (D136-D141) - Caudales Q1, Q2, Q3
        self.holding_registers[136] = self.float_to_registers(125.5)  # Q1 flow
        self.holding_registers[138] = self.float_to_registers(250.0)  # Q2 flow  
        self.holding_registers[140] = self.float_to_registers(375.2)  # Q3 flow
        
        # Volúmenes instantáneos (D150-D157) - Q1, Q2, Q3, Q4
        self.holding_registers[150] = self.float_to_registers(1000.0)  # Q1 volume
        self.holding_registers[152] = self.float_to_registers(2000.0)  # Q2 volume
        self.holding_registers[154] = self.float_to_registers(3000.0)  # Q3 volume
        self.holding_registers[156] = self.float_to_registers(4000.0)  # Q4 volume
        
        # Valores de prueba (D112-D119) - Volúmenes de prueba
        self.holding_registers[112] = 4500  # Q4 volume test
        self.holding_registers[114] = 3200  # Q3 volume test
        self.holding_registers[116] = 2100  # Q2 volume test
        self.holding_registers[118] = 1050  # Q1 volume test
        
        # Valores de configuración
        self.holding_registers[122] = 100   # Ratio
        self.holding_registers[144] = self.float_to_registers(375.0)  # Q3 flow test
        
        # Caudales de prueba (D142-D149)
        self.holding_registers[142] = self.float_to_registers(400.0)  # Q4 flow test
        self.holding_registers[143] = self.float_to_registers(300.0)  # Q3 flow test  
        self.holding_registers[144] = self.float_to_registers(200.0)  # Q2 flow test
        self.holding_registers[145] = self.float_to_registers(100.0)  # Q1 flow test
        
        # Estados FC (M277-M302) - Todos inician en False
        for i in range(277, 303):
            self.coil_states[i] = False
            
        # Estados de botones de prueba (M262-M269)
        for i in range(262, 270):
            self.coil_states[i] = False
            
        print("✅ Valores por defecto inicializados")

    def float_to_registers(self, value):
        """Convierte float a 2 registros (little_word format)"""
        packed = struct.pack('>f', value)
        # little_word: intercambiar palabras
        return [
            (packed[2] << 8) | packed[3],  # Low word first
            (packed[0] << 8) | packed[1]   # High word second
        ]

    def registers_to_bytes(self, registers):
        """Convierte lista de registros a bytes para respuesta Modbus"""
        bytes_data = []
        for reg in registers:
            if isinstance(reg, list):  # Float (2 registros)
                for r in reg:
                    bytes_data.extend([(r >> 8) & 0xFF, r & 0xFF])
            else:  # Int (1 registro)
                bytes_data.extend([(reg >> 8) & 0xFF, reg & 0xFF])
        return bytes_data

    def simulate_dynamic_values(self):
        """Simula cambios dinámicos en valores instantáneos"""
        # Agregar pequeñas variaciones aleatorias a caudales
        base_flows = [125.5, 250.0, 375.2]
        for i, base in enumerate(base_flows):
            variation = random.uniform(-5, 5)
            new_value = base + variation
            reg_addr = 136 + (i * 2)
            self.holding_registers[reg_addr] = self.float_to_registers(new_value)
        
        # Incrementar volúmenes gradualmente
        base_volumes = [1000.0, 2000.0, 3000.0, 4000.0]
        for i, base in enumerate(base_volumes):
            increment = random.uniform(0.1, 2.0)
            reg_addr = 150 + (i * 2)
            if reg_addr in self.holding_registers:
                current = self.holding_registers[reg_addr]
                if isinstance(current, list):
                    # Convertir de vuelta a float, incrementar, y volver a convertir
                    old_val = struct.unpack('>f', struct.pack('>HH', current[1], current[0]))[0]
                    new_val = old_val + increment
                    self.holding_registers[reg_addr] = self.float_to_registers(new_val)
                    
                    # 🔥 LOG para debugging
                    print(f"[SIMULATOR] 📊 Volumen Q{i+1}: {old_val:.2f} → {new_val:.2f}")

    def handle_read_holding_registers(self, start_addr, quantity):
        """Función 3: Leer registros de retención"""
        data = []
        for addr in range(start_addr, start_addr + quantity):
            if addr in self.holding_registers:
                reg_value = self.holding_registers[addr]
                if isinstance(reg_value, list):  # Float
                    data.extend(reg_value)
                else:  # Int
                    data.append(reg_value)
            else:
                data.append(0)  # Valor por defecto
        return data

    def handle_read_coils(self, start_addr, quantity):
        """Función 1: Leer bobinas"""
        bits = []
        for addr in range(start_addr, start_addr + quantity):
            if addr in self.coil_states:
                bits.append(1 if self.coil_states[addr] else 0)
            else:
                bits.append(0)
        
        # Convertir bits a bytes
        bytes_data = []
        for i in range(0, len(bits), 8):
            byte_val = 0
            for j in range(8):
                if i + j < len(bits):
                    byte_val |= (bits[i + j] << j)
            bytes_data.append(byte_val)
        
        return bytes_data

    def handle_write_single_coil(self, addr, value):
        """Función 5: Escribir bobina simple"""
        self.coil_states[addr] = (value == 0xFF00)
        print(f"🔧 M{addr} = {self.coil_states[addr]}")
        
        # Simular activación de estados FC según los botones presionados
        self.simulate_fc_states(addr)
        
        return True

    def handle_write_single_register(self, addr, value):
        """Función 6: Escribir registro simple"""
        self.holding_registers[addr] = value
        print(f"📝 D{addr} = {value}")
        return True

    def handle_write_multiple_registers(self, addr, values):
        """Función 16: Escribir múltiples registros"""
        for i, value in enumerate(values):
            self.holding_registers[addr + i] = value
            print(f"📝 D{addr + i} = {value}")
        return True

    def simulate_fc_states(self, button_addr):
        """Simula activación de estados FC según botones presionados"""
        fc_mapping = {
            271: [0],      # Modo automático -> FC0
            264: [2, 3, 4, 5, 6],    # Caudal Q1 -> FC2-FC6 (secuencia Q1)
            265: [7, 8, 9, 10, 11],  # Caudal Q2 -> FC7-FC11 (secuencia Q2)
            266: [12, 13, 14, 15],   # Caudal Q3 -> FC12-FC15 (secuencia Q3)
            267: [16, 17, 18, 19],   # Caudal Q4 -> FC16-FC19 (secuencia Q4)
            268: [20, 21],           # Hidrostática -> FC20-FC21
            269: [1, 22, 23],        # Iniciar prueba -> FC1, FC22, FC23
        }
        
        if button_addr in fc_mapping:
            # Activar secuencialmente los FC correspondientes
            def activate_sequence():
                for fc_num in fc_mapping[button_addr]:
                    fc_addr = 277 + fc_num
                    self.coil_states[fc_addr] = True
                    print(f"✅ FC{fc_num} (M{fc_addr}) activado")
                    time.sleep(0.5)  # Simular tiempo entre activaciones
                    
                    # Desactivar después de un tiempo
                    time.sleep(1.0)
                    self.coil_states[fc_addr] = False
                    print(f"⏹️ FC{fc_num} (M{fc_addr}) desactivado")
            
            # Ejecutar secuencia en hilo separado para no bloquear
            import threading
            threading.Thread(target=activate_sequence, daemon=True).start()

    def calculate_lrc(self, data_bytes):
        """Calcula LRC para respuesta Modbus ASCII"""
        checksum = sum(data_bytes) % 256
        complement = (0xFF - checksum) + 1
        return complement & 0xFF

    def create_response(self, slave_addr, function_code, data_bytes):
        """Crea respuesta Modbus ASCII completa"""
        response_data = [slave_addr, function_code] + data_bytes
        lrc = self.calculate_lrc(response_data)
        
        hex_string = ''.join(f'{b:02X}' for b in response_data) + f'{lrc:02X}'
        return f":{hex_string}\r\n"

    # 🔥 NUEVA FUNCIÓN PARA SEPARAR COMANDOS MÚLTIPLES
    def extract_commands(self, raw_data):
        """Extrae comandos individuales de datos concatenados"""
        self.command_buffer += raw_data
        commands = []
        
        while ':' in self.command_buffer:
            start_pos = self.command_buffer.find(':')
            if start_pos == -1:
                break
                
            # Buscar el final del comando (siguiente ':' o fin de buffer)
            next_start = self.command_buffer.find(':', start_pos + 1)
            
            if next_start == -1:
                # No hay siguiente comando, usar todo el buffer restante
                if len(self.command_buffer) >= start_pos + 17:  # Comando mínimo completo
                    command = self.command_buffer[start_pos:start_pos + 17]
                    commands.append(command)
                    self.command_buffer = self.command_buffer[start_pos + 17:]
                else:
                    # Comando incompleto, esperar más datos
                    break
            else:
                # Hay siguiente comando
                command = self.command_buffer[start_pos:next_start]
                if len(command) >= 17:  # Comando completo
                    commands.append(command)
                self.command_buffer = self.command_buffer[next_start:]
        
        return commands

    def parse_command(self, command):
        """Parsea comando Modbus ASCII recibido"""
        try:
            if not command.startswith(':'):
                return None
            
            # Limpiar comando (quitar espacios, \r, \n)
            clean_command = command.strip().replace('\r', '').replace('\n', '')
            
            if len(clean_command) < 9:  # Comando muy corto
                return None
                
            hex_data = clean_command[1:-2]  # Quitar ':' y LRC (últimos 2 chars)
            
            # 🔥 VERIFICAR QUE SOLO CONTIENE CARACTERES HEX VÁLIDOS
            if not all(c in '0123456789ABCDEFabcdef' for c in hex_data):
                print(f"❌ Comando contiene caracteres no hexadecimales: {hex_data}")
                return None
                
            data_bytes = bytes.fromhex(hex_data)
            
            if len(data_bytes) < 2:
                return None
                
            slave_addr = data_bytes[0]
            function_code = data_bytes[1]
            
            if function_code == 3:  # Read Holding Registers
                if len(data_bytes) >= 6:
                    start_addr = (data_bytes[2] << 8) | data_bytes[3]
                    quantity = (data_bytes[4] << 8) | data_bytes[5]
                    return {
                        'slave': slave_addr,
                        'function': function_code,
                        'start_addr': start_addr,
                        'quantity': quantity
                    }
                    
            elif function_code == 1:  # Read Coils
                if len(data_bytes) >= 6:
                    start_addr = (data_bytes[2] << 8) | data_bytes[3]
                    quantity = (data_bytes[4] << 8) | data_bytes[5]
                    return {
                        'slave': slave_addr,
                        'function': function_code,
                        'start_addr': start_addr,
                        'quantity': quantity
                    }
                    
            elif function_code == 5:  # Write Single Coil
                if len(data_bytes) >= 6:
                    addr = (data_bytes[2] << 8) | data_bytes[3]
                    value = (data_bytes[4] << 8) | data_bytes[5]
                    return {
                        'slave': slave_addr,
                        'function': function_code,
                        'addr': addr,
                        'value': value
                    }
                    
            elif function_code == 6:  # Write Single Register
                if len(data_bytes) >= 6:
                    addr = (data_bytes[2] << 8) | data_bytes[3]
                    value = (data_bytes[4] << 8) | data_bytes[5]
                    return {
                        'slave': slave_addr,
                        'function': function_code,
                        'addr': addr,
                        'value': value
                    }
                    
            elif function_code == 16:  # Write Multiple Registers
                if len(data_bytes) >= 7:
                    addr = (data_bytes[2] << 8) | data_bytes[3]
                    quantity = (data_bytes[4] << 8) | data_bytes[5]
                    byte_count = data_bytes[6]
                    values = []
                    for i in range(0, byte_count, 2):
                        if 7 + i + 1 < len(data_bytes):
                            val = (data_bytes[7 + i] << 8) | data_bytes[7 + i + 1]
                            values.append(val)
                    return {
                        'slave': slave_addr,
                        'function': function_code,
                        'addr': addr,
                        'quantity': quantity,
                        'values': values
                    }
                    
        except Exception as e:
            print(f"❌ Error parseando comando '{command}': {e}")
            return None

    def process_command(self, parsed_cmd):
        """Procesa comando parseado y genera respuesta"""
        if not parsed_cmd:
            return ":010182B6\r\n"  # Error response
            
        slave = parsed_cmd['slave']
        function = parsed_cmd['function']
        
        try:
            if function == 3:  # Read Holding Registers
                data = self.handle_read_holding_registers(
                    parsed_cmd['start_addr'], 
                    parsed_cmd['quantity']
                )
                byte_count = len(data) * 2
                data_bytes = [byte_count] + self.registers_to_bytes(data)
                
                # 🔥 LOG ESPECIAL PARA VOLÚMENES INSTANTÁNEOS
                if parsed_cmd['start_addr'] == 150 and parsed_cmd['quantity'] == 4:
                    print(f"[SIMULATOR] 📊 Enviando volúmenes instantáneos:")
                    for i in range(4):
                        addr = 150 + (i * 2)
                        if addr in self.holding_registers:
                            vol_data = self.holding_registers[addr]
                            if isinstance(vol_data, list):
                                val = struct.unpack('>f', struct.pack('>HH', vol_data[1], vol_data[0]))[0]
                                print(f"  📊 Q{i+1} Volume: {val:.2f}")
                
                return self.create_response(slave, function, data_bytes)
                
            elif function == 1:  # Read Coils
                data = self.handle_read_coils(
                    parsed_cmd['start_addr'],
                    parsed_cmd['quantity']
                )
                byte_count = len(data)
                data_bytes = [byte_count] + data
                return self.create_response(slave, function, data_bytes)
                
            elif function == 5:  # Write Single Coil
                success = self.handle_write_single_coil(
                    parsed_cmd['addr'],
                    parsed_cmd['value']
                )
                if success:
                    # Echo back the command for write confirmation
                    data_bytes = [
                        (parsed_cmd['addr'] >> 8) & 0xFF,
                        parsed_cmd['addr'] & 0xFF,
                        (parsed_cmd['value'] >> 8) & 0xFF,
                        parsed_cmd['value'] & 0xFF
                    ]
                    return self.create_response(slave, function, data_bytes)
                    
            elif function == 6:  # Write Single Register
                success = self.handle_write_single_register(
                    parsed_cmd['addr'],
                    parsed_cmd['value']
                )
                if success:
                    data_bytes = [
                        (parsed_cmd['addr'] >> 8) & 0xFF,
                        parsed_cmd['addr'] & 0xFF,
                        (parsed_cmd['value'] >> 8) & 0xFF,
                        parsed_cmd['value'] & 0xFF
                    ]
                    return self.create_response(slave, function, data_bytes)
                    
            elif function == 16:  # Write Multiple Registers
                success = self.handle_write_multiple_registers(
                    parsed_cmd['addr'],
                    parsed_cmd['values']
                )
                if success:
                    data_bytes = [
                        (parsed_cmd['addr'] >> 8) & 0xFF,
                        parsed_cmd['addr'] & 0xFF,
                        (parsed_cmd['quantity'] >> 8) & 0xFF,
                        parsed_cmd['quantity'] & 0xFF
                    ]
                    return self.create_response(slave, function, data_bytes)
                    
        except Exception as e:
            print(f"❌ Error procesando comando: {e}")
            
        return ":010182B6\r\n"  # Error response por defecto

def run_simulator():
    simulator = ModbusSimulator()
    
    try:
        ser = serial.Serial(
            port=SIMULATED_PORT,
            baudrate=BAUDRATE,
            bytesize=serial.SEVENBITS,
            parity=serial.PARITY_EVEN,
            stopbits=serial.STOPBITS_ONE,
            timeout=1
        )
        print(f"✅ COM Simulator activo en {SIMULATED_PORT}")
        print("📊 Simulando datos en tiempo real...")
        
        last_dynamic_update = time.time()
        
        while True:
            # Actualizar valores dinámicos cada 2 segundos
            if time.time() - last_dynamic_update > 2:
                simulator.simulate_dynamic_values()
                last_dynamic_update = time.time()
            
            # Procesar comandos recibidos
            if ser.in_waiting:
                raw_data = ser.read(500).decode(errors='ignore')
                if not raw_data:
                    continue

                print(f"📥 Datos brutos recibidos: {repr(raw_data)}")
                
                # 🔥 EXTRAER COMANDOS INDIVIDUALES
                commands = simulator.extract_commands(raw_data)
                
                for command in commands:
                    print(f"📥 Procesando comando: {command}")
                    
                    # Parsear y procesar comando
                    parsed_cmd = simulator.parse_command(command)
                    response = simulator.process_command(parsed_cmd)
                    
                    print(f"📤 Enviando: {response.strip()}")
                    ser.write(response.encode('ascii'))
                    time.sleep(0.01)  # Pequeña pausa entre respuestas

            time.sleep(0.05)

    except Exception as e:
        print(f"❌ Error en simulador: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando simulador COM mejorado...")
    print("📋 Funciones simuladas:")
    print("   - Lectura de caudales instantáneos (D136-D141)")
    print("   - Lectura de volúmenes instantáneos (D150-D157)")
    print("   - Lectura/escritura de valores de prueba")
    print("   - Estados FC (M277-M302)")
    print("   - Botones de control (M262-M269)")
    print("   - Valores dinámicos con variaciones aleatorias")
    print("   - Manejo de comandos concatenados")
    print()
    run_simulator()