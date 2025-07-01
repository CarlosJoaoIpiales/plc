import flet as ft

def get_manual_mode_view(meter_group_id, selected_batch):
    return ft.Column([
        ft.Text("Modo Manual (en desarrollo)", size=22, weight="bold"),
        ft.Text("Aquí irá el formulario y lógica para el modo manual.")
    ])