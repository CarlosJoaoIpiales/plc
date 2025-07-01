import struct

def calculate_lrc(data_bytes):
    checksum = sum(data_bytes) % 256
    complement = (0xFF - checksum) + 1
    return complement & 0xFF

def pack_float(value: float, byte_order: str = 'big') -> bytes:
    if byte_order == 'big':
        return struct.pack('>f', value)
    elif byte_order == 'little':
        return struct.pack('<f', value)
    elif byte_order == 'big_word':
        return struct.pack('>f', value)
    elif byte_order == 'little_word':
        packed = struct.pack('>f', value)
        return packed[2:4] + packed[0:2]
    elif byte_order == 'little_word_byte':
        packed = struct.pack('>f', value)
        return bytes([packed[1], packed[0], packed[3], packed[2]])
    else:
        raise ValueError("Unsupported byte order")

def build_modbus_ascii_command(
    slave_address, function_code, address_high, address_low,
    quantity=1, value=None, value_type=None,
    custom_bytes=None, float_byte_order='little_word'
):
    data_bytes = [slave_address, function_code, address_high, address_low]

    if function_code == 3:  # Read holding registers
        data_bytes += [0x00, quantity]

    elif function_code == 6:  # Write single register
        if value_type == "int":
            high = (value >> 8) & 0xFF
            low = value & 0xFF
            data_bytes += [high, low]

    elif function_code == 16:  # Write multiple registers
        if value is None and custom_bytes is None:
            raise ValueError("Value or custom_bytes required")
        data_field = []
        if custom_bytes:
            data_field = custom_bytes
        elif value_type == 'float':
            for f in value:
                packed = pack_float(f, float_byte_order)
                data_field += list(packed)
        data_bytes += [(quantity >> 8) & 0xFF, quantity & 0xFF]
        data_bytes.append(len(data_field))
        data_bytes += data_field

    elif function_code == 5:  # Write single coil
        data_bytes += [0xFF, 0x00] if value else [0x00, 0x00]

    elif function_code == 1:  # Read coils
        data_bytes += [(quantity >> 8) & 0xFF, quantity & 0xFF]

    else:
        raise NotImplementedError("Function code not supported")

    lrc = calculate_lrc(data_bytes)
    command = ':' + ''.join(f'{b:02X}' for b in data_bytes) + f'{lrc:02X}\r\n'
    return command

def parse_float_modbus(data_bytes, byte_order='big'):
    if len(data_bytes) != 4:
        raise ValueError("Exactly 4 bytes are required")
    if byte_order == 'big':
        return struct.unpack('>f', data_bytes)[0]
    elif byte_order == 'little':
        return struct.unpack('<f', data_bytes)[0]
    elif byte_order == 'big_word':
        return struct.unpack('>f', data_bytes)[0]
    elif byte_order == 'little_word':
        reordered = bytes([data_bytes[2], data_bytes[3], data_bytes[0], data_bytes[1]])
        return struct.unpack('>f', reordered)[0]
    elif byte_order == 'little_word_byte':
        reordered = bytes([data_bytes[1], data_bytes[0], data_bytes[3], data_bytes[2]])
        return struct.unpack('>f', reordered)[0]
    else:
        raise ValueError("Unsupported byte order")

def parse_modbus_ascii_response(response_bytes, float_byte_order='little_word'):
    try:
        text = response_bytes.decode('ascii').strip()
    except Exception:
        return {"type": "error", "message": "Invalid ASCII response"}

    if not text.startswith(':'):
        return {"type": "error", "message": "Invalid Modbus format"}

    content = text[1:-2]
    try:
        data = bytes.fromhex(content)
    except ValueError:
        return {"type": "error", "message": "Invalid HEX content"}

    slave_address = data[0]
    function_code = data[1]

    if function_code & 0x80:
        return {"type": "error", "code": data[2], "message": f"Modbus error code {data[2]}"}

    if function_code == 3:
        byte_count = data[2]
        raw_data = data[3:3 + byte_count]

        if byte_count % 4 == 0:
            floats = []
            for i in range(0, byte_count, 4):
                chunk = raw_data[i:i+4]
                try:
                    val = parse_float_modbus(chunk, float_byte_order)
                    floats.append(val)
                except:
                    floats.append(None)
            return {"type": "read", "subtype": "float", "data": floats}

        elif byte_count % 2 == 0:
            integers = []
            for i in range(0, byte_count, 2):
                val = (raw_data[i] << 8) + raw_data[i+1]
                integers.append(val)
            return {"type": "read", "subtype": "int", "data": integers}

        else:
            return {"type": "read", "raw_bytes": raw_data}

    elif function_code == 1:
        byte_count = data[2]
        bit_data = data[3:3 + byte_count]
        bits = []
        for byte in bit_data:
            for i in range(8):
                bits.append((byte >> i) & 0x01)
        return {"type": "read", "subtype": "bits", "bits": bits}

    elif function_code in [5, 6, 15, 16]:
        return {"type": "write", "message": "Command executed successfully"}

    return {"type": "error", "message": f"Function code {function_code} not supported"}
