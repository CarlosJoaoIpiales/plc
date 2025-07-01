import flet as ft
from views.batch_registration_view import get_batch_registration_view
from views.mode_selection_view import get_mode_selection_view
from views.automatic_mode_view import get_automatic_mode_view
from views.manual_mode_view import get_manual_mode_view  # <-- Agrega esta línea
from controllers.test_controller import save_meter_group
from controllers.client_controller import get_all_clients
from controllers.technician_controller import get_all_technicians
from controllers.modbus_controller import ModbusController

def get_test_full_view(page: ft.Page):
    step = ft.Ref[int]()
    step.current = 1

    meter_group_id = ft.Ref[int]()
    selected_batch = ft.Ref[str]()
    macro_data = ft.Ref[dict]()
    macro_data.current = {}

    modbus_controller = ModbusController(lambda *a, **kw: None)  # Dummy update_ui

    def on_continue_macro(data):
        clients = get_all_clients()
        technicians = get_all_technicians()
        client_id = next((c["id"] for c in clients if c["name"] == data["client_name"]), None)
        technician_id = next((t["id"] for t in technicians if t["name"] == data["technician_name"]), None)
        if client_id is None or technician_id is None:
            page.snack_bar = ft.SnackBar(ft.Text("Cliente o técnico inválido."), bgcolor="red")
            page.snack_bar.open = True
            page.update()
            return
        result = save_meter_group(data, client_id, technician_id)
        if result["success"]:
            meter_group_id.current = result["meter_group_id"]
            selected_batch.current = data["batch"]
            macro_data.current = data
            step.current = 2
            refresh_view()
        else:
            page.snack_bar = ft.SnackBar(ft.Text("Error: " + result["error"]), bgcolor="red")
            page.snack_bar.open = True
            page.update()

    def on_auto(e):
        step.current = 3
        refresh_view()

    def on_manual(e):
        step.current = 4  # Nuevo paso para modo manual
        refresh_view()

    content = ft.Column([], expand=True)
    def refresh_view():
        if step.current == 1:
            # content.controls = [get_batch_registration_view(page, on_continue_macro)]
            content.controls = [get_mode_selection_view(on_auto, on_manual)]
        elif step.current == 2:
            # En test_view.py o donde corresponda:
            content.controls = [get_mode_selection_view(on_auto, on_manual)]
        elif step.current == 3:
            content.controls = [get_automatic_mode_view(page, meter_group_id.current, selected_batch.current)]
        elif step.current == 4:
            content.controls = [get_manual_mode_view(meter_group_id.current, selected_batch.current)]
        page.update()

    refresh_view()
    return content