import flet as ft
from controllers.client_controller import get_all_clients, add_client
from controllers.technician_controller import get_all_technicians, add_technician
from utils.validation_utils import is_valid_email, is_valid_phone, is_valid_name

RATIO_OPTIONS = ["80", "100", "160", "250", "400"]
DIAMETER_OPTIONS = ["15", "20", "25", "32", "40", "50"]

def get_batch_registration_view(page, on_continue):
    clients = get_all_clients()
    technicians = get_all_technicians()

    client_dropdown = ft.Dropdown(
        label="Cliente",
        options=[ft.dropdown.Option(c["name"]) for c in clients] + [ft.dropdown.Option("Agregar nuevo...")],
        expand=True
    )
    technician_dropdown = ft.Dropdown(
        label="Técnico",
        options=[ft.dropdown.Option(t["name"]) for t in technicians] + [ft.dropdown.Option("Agregar nuevo...")],
        expand=True
    )

    brand = ft.TextField(label="Marca", expand=True)
    model = ft.TextField(label="Modelo", expand=True)
    ratio = ft.Dropdown(
        label="Ratio",
        options=[ft.dropdown.Option(r) for r in RATIO_OPTIONS],
        expand=True
    )
    nominal_flow = ft.TextField(
        label="Caudal Nominal(m³/h)",
        expand=True,
    )
    diameter = ft.Dropdown(
        label="Diametro",
        options=[ft.dropdown.Option(d) for d in DIAMETER_OPTIONS],
        expand=True
    )
    meter_type = ft.TextField(label="Tipo", expand=True)
    batch = ft.Dropdown(
        label="Estado",
        options=[ft.dropdown.Option("Nuevo"), ft.dropdown.Option("Usado")],
        expand=True
    )

    # --- Popups para cliente/técnico ---
    client_name_field = ft.TextField(label="Nombre", expand=True)
    client_phone_field = ft.TextField(label="Teléfono", expand=True)
    client_address_field = ft.TextField(label="Dirección", expand=True)
    client_email_field = ft.TextField(label="Email", expand=True)
    client_error = ft.Text("", color="red")

    def client_name_on_change(e):
        value = client_name_field.value.upper()
        value = ''.join([c for c in value if c.isalpha() or c == ' '])
        client_name_field.value = value
        page.update()

    def client_phone_on_change(e):
        value = ''.join([c for c in client_phone_field.value if c.isdigit()])
        client_phone_field.value = value
        page.update()

    client_name_field.on_change = client_name_on_change
    client_phone_field.on_change = client_phone_on_change

    def close_client_dialog(e=None):
        page.dialog.open = False
        page.update()

    def save_new_client(e):
        name = client_name_field.value.strip().upper()
        phone = client_phone_field.value.strip()
        address = client_address_field.value.strip()
        email = client_email_field.value.strip()
        if not is_valid_name(name):
            client_error.value = "Nombre inválido (solo letras y espacios, mayúsculas, sin caracteres especiales)"
        elif not is_valid_phone(phone):
            client_error.value = "Teléfono inválido (solo números, 7-20 dígitos)"
        elif not is_valid_email(email):
            client_error.value = "Email inválido"
        else:
            add_client({"name": name, "phone": phone, "address": address, "email": email})
            client_dropdown.options = [ft.dropdown.Option(c["name"]) for c in get_all_clients()] + [ft.dropdown.Option("Agregar nuevo...")]
            client_dropdown.value = name
            page.dialog.open = False
            page.update()
            return
        page.update()

    client_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Row([
            ft.Text("Agregar Nuevo Cliente", expand=True),
            ft.IconButton(ft.Icons.CLOSE, on_click=close_client_dialog)
        ]),
        content=ft.Column([
            client_name_field,
            client_phone_field,
            client_address_field,
            client_email_field,
            client_error
        ], tight=True),
        actions=[
            ft.TextButton("Cancelar", on_click=close_client_dialog),
            ft.ElevatedButton("Guardar", on_click=save_new_client)
        ],
        actions_alignment="end"
    )

    technician_name_field = ft.TextField(label="Nombre", expand=True)
    technician_error = ft.Text("", color="red")

    def technician_name_on_change(e):
        value = technician_name_field.value.upper()
        value = ''.join([c for c in value if c.isalpha() or c == ' '])
        technician_name_field.value = value
        page.update()

    technician_name_field.on_change = technician_name_on_change

    def close_technician_dialog(e=None):
        page.dialog.open = False
        page.update()

    def save_new_technician(e):
        name = technician_name_field.value.strip().upper()
        if not is_valid_name(name):
            technician_error.value = "Nombre inválido (solo letras y espacios, mayúsculas, sin caracteres especiales)"
        else:
            add_technician({"name": name})
            technician_dropdown.options = [ft.dropdown.Option(t["name"]) for t in get_all_technicians()] + [ft.dropdown.Option("Agregar nuevo...")]
            technician_dropdown.value = name
            page.dialog.open = False
            page.update()
            return
        page.update()

    technician_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Row([
            ft.Text("Agregar Nuevo Técnico", expand=True),
            ft.IconButton(ft.Icons.CLOSE, on_click=close_technician_dialog)
        ]),
        content=ft.Column([
            technician_name_field,
            technician_error
        ], tight=True),
        actions=[
            ft.TextButton("Cancelar", on_click=close_technician_dialog),
            ft.ElevatedButton("Guardar", on_click=save_new_technician)
        ],
        actions_alignment="end"
    )

    def on_client_change(e):
        if client_dropdown.value == "Agregar nuevo...":
            client_name_field.value = ""
            client_phone_field.value = ""
            client_address_field.value = ""
            client_email_field.value = ""
            client_error.value = ""
            if client_dialog not in page.overlay:
                page.overlay.append(client_dialog)
            page.dialog = client_dialog
            page.dialog.open = True
            page.update()

    def on_technician_change(e):
        if technician_dropdown.value == "Agregar nuevo...":
            technician_name_field.value = ""
            technician_error.value = ""
            if technician_dialog not in page.overlay:
                page.overlay.append(technician_dialog)
            page.dialog = technician_dialog
            page.dialog.open = True
            page.update()
    
    def on_nominal_flow_change(e):
        value = nominal_flow.value
        # Permite solo números y un punto decimal
        if value and not value.replace('.', '', 1).isdigit():
            nominal_flow.value = ''.join([c for c in value if c.isdigit() or c == '.'])
            # Solo permite un punto
            if nominal_flow.value.count('.') > 1:
                parts = nominal_flow.value.split('.')
                nominal_flow.value = parts[0] + '.' + ''.join(parts[1:])
            page.update()

    nominal_flow.on_change = on_nominal_flow_change

    client_dropdown.on_change = on_client_change
    technician_dropdown.on_change = on_technician_change

    macro_error = ft.Text("", color="red")

    def on_continue_click(e):
        client_name = client_dropdown.value
        technician_name = technician_dropdown.value

        if not client_name or client_name == "Agregar nuevo...":
            macro_error.value = "Por favor selecciona o agrega un cliente."
            page.update()
            return
        if not technician_name or technician_name == "Agregar nuevo...":
            macro_error.value = "Por favor selecciona o agrega un técnico."
            page.update()
            return

        # Validación de campos obligatorios
        if not all([brand.value, model.value, ratio.value, nominal_flow.value, diameter.value, meter_type.value, batch.value]):
            macro_error.value = "Todos los campos son obligatorios."
            page.update()
            return

        # Validación de caudal nominal flotante
        try:
            float(nominal_flow.value)
        except Exception:
            macro_error.value = "El caudal nominal debe ser un número decimal."
            page.update()
            return

        # Devuelve los datos al callback
        on_continue({
            "brand": brand.value,
            "model": model.value,
            "ratio": ratio.value,
            "nominal_flow": nominal_flow.value,
            "diameter": diameter.value,
            "type": meter_type.value,
            "batch": batch.value,
            "client_name": client_name,
            "technician_name": technician_name
        })

    return ft.Column([
        ft.Text("Registrar Lote de Medidores", size=24, weight="bold"),
        ft.ResponsiveRow([
            ft.Container(brand, col={"xs":12, "sm":6, "md":4}),
            ft.Container(model, col={"xs":12, "sm":6, "md":4}),
            ft.Container(ratio, col={"xs":12, "sm":6, "md":4}),
            ft.Container(nominal_flow, col={"xs":12, "sm":6, "md":4}),
            ft.Container(diameter, col={"xs":12, "sm":6, "md":4}),
            ft.Container(meter_type, col={"xs":12, "sm":6, "md":4}),
            ft.Container(batch, col={"xs":12, "sm":6, "md":4}),
        ], spacing=10, run_spacing=10),
        ft.ResponsiveRow([
            ft.Container(client_dropdown, col={"xs":12, "sm":6, "md":6}),
            ft.Container(technician_dropdown, col={"xs":12, "sm":6, "md":6}),
        ], spacing=10),
        macro_error,
        ft.ElevatedButton("Continuar", on_click=on_continue_click)
    ])