import flet as ft
from controllers.connection_controller import monitor_com_connection
from services.modbus_service import ModbusService

def get_connection_view(page, on_connection_ready):
    status_text = ft.Text("Checking COM port...", size=20)

    def update_status(msg):
        status_text.value = msg
        page.update()

    def on_ready():
        # Abrir el puerto COM aquí
        service = ModbusService()
        port = service.detect_port()
        if port and service.connect(port):
            print(f"[CONNECTION_VIEW] Puerto COM abierto: {port}")
            on_connection_ready()
        else:
            update_status("❌ No se pudo abrir el puerto COM")
            print("[CONNECTION_VIEW] No se pudo abrir el puerto COM")

    monitor_com_connection(on_ready, update_status)

    return ft.Column([
        ft.Text("Test Bench App", size=32, weight="bold"),
        ft.Divider(),
        status_text
    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)