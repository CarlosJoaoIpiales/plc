import flet as ft
from controllers.test_controller import save_test_entry, get_test_number_for_serial

def get_test_entry_form(meter_group_id: int, batch: str):
    rows = []

    def add_row(e=None):
        serial = ft.TextField(label="Serial Number", width=150)
        test_type = ft.Dropdown(
            label="Test Type",
            width=100,
            options=[ft.dropdown.Option(t) for t in ["Q1", "Q2", "Q3", "Q4"]],
            on_change=lambda ev: update_test_number()
        )
        initial = ft.TextField(label="Initial", width=100)
        final = ft.TextField(label="Final", width=100)
        test_number = ft.Text(value="1", width=50)
        error_text = ft.Text(value="0.00%", width=80)
        result_text = ft.Text(value="Pending", color=ft.colors.GREY, width=80)

        def update_test_number():
            if serial.value and test_type.value:
                n = get_test_number_for_serial(serial.value, test_type.value)
                test_number.value = str(n)
                page.update()

        def calculate(ev=None):
            try:
                i = float(initial.value)
                f = float(final.value)
                ref = 100
                error = ((f - i - ref) / ref) * 100
                tol = 2 if batch == "new" else 5
                passed = abs(error) <= tol
                error_text.value = f"{error:.2f}%"
                result_text.value = "PASS" if passed else "FAIL"
                result_text.color = ft.colors.GREEN if passed else ft.colors.RED
                page.update()
            except:
                error_text.value = "ERR"
                result_text.value = "Invalid"
                result_text.color = ft.colors.ORANGE
                page.update()

        def save_row(e=None):
            data = {
                "serial_number": serial.value,
                "test_type": test_type.value,
                "test_number": int(test_number.value),
                "initial_reading": float(initial.value),
                "final_reading": float(final.value),
                "reference_value": 100,
                "meter_group_id": meter_group_id,
                "batch": batch
            }
            res = save_test_entry(data)
            if res["success"]:
                result_text.value = "SAVED"
                result_text.color = ft.colors.GREEN
            else:
                result_text.value = "ERROR"
                result_text.color = ft.colors.RED
            page.update()

        save_btn = ft.IconButton(icon=ft.icons.SAVE, on_click=save_row)
        calc_btn = ft.IconButton(icon=ft.icons.CALCULATE, on_click=calculate)

        row = ft.Row([
            serial, test_type, test_number,
            initial, final, error_text, result_text,
            calc_btn, save_btn
        ])
        rows.append(row)
        page.controls.insert(-1, row)
        page.update()

    page = ft.Column([
        ft.Text("Register individual tests", size=20, weight="bold"),
        ft.ElevatedButton("Add Row", on_click=add_row)
    ])
    return page
