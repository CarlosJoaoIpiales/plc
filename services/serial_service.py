import serial
import serial.tools.list_ports

def detect_com_port():
    ports = list(serial.tools.list_ports.comports())
    return ports[0].device if ports else None

def create_serial_connection(port, baudrate=9600, timeout=1):
    try:
        ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.SEVENBITS,
            parity=serial.PARITY_EVEN,
            stopbits=serial.STOPBITS_ONE,
            timeout=timeout
        )
        return ser
    except Exception as e:
        return None
