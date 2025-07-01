from services.modbus_service import ModbusService

class ModbusController:
    def __init__(self, update_ui_callback):
        self.service = ModbusService()
        self.update_ui_callback = update_ui_callback

    def start_reading(self, esclavo):
        self.service.start_read_loop(esclavo, self.update_ui_callback)

    def stop_reading(self):
        self.service.stop_read_loop()