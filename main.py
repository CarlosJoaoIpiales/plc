import flet as ft
from views.connection_view import get_connection_view
from views.test_view import get_test_full_view
from views.report_view import get_report_view
from services.modbus_service import ModbusService

def main(page: ft.Page):
    page.title = "Test Bench App"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = "auto"
    page.window.resizable = True
    page.window.maximized = True  # Maximizar la ventana al inicio

    def on_connection_ready():
        page.go("/tests")

    def cerrar_puerto(e):
        service = ModbusService()
        service.close()
        print("[MAIN] Puerto COM cerrado")

    def top_bar():
        return ft.AppBar(
            title=ft.Text("Test Bench System", size=20, weight="bold"),
            actions=[
                ft.TextButton("Tests", on_click=lambda _: page.go("/tests")),
                ft.TextButton("Reports", on_click=lambda _: page.go("/reports")),
            ]
        )

    def route_change(route):
        page.controls.clear()
        if page.route == "/tests":
            page.controls.append(get_test_full_view(page))
        elif page.route == "/reports":
            page.controls.append(get_report_view(page))
        else:
            page.controls.append(get_connection_view(page, on_connection_ready))
        page.update()

    page.appbar = top_bar()
    page.on_route_change = route_change
    page.go("/connection")
    page.on_close = cerrar_puerto

ft.app(target=main)