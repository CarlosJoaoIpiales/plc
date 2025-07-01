import flet as ft
from controllers.report_controller import get_report_for_serial

def get_report_view(page):
    serial_input = ft.TextField(label="Serial Number", width=250)
    table = ft.DataTable(
        columns=[ft.DataColumn(label=ft.Text("Test Type"))],  # Al menos una columna
        rows=[]
    )

    def search(e):
        serial = serial_input.value.strip()
        if not serial:
            return
        result = get_report_for_serial(serial)
        if not result:
            table.columns = [ft.DataColumn(label=ft.Text("No data found"))]
            table.rows = []
            page.snack_bar = ft.SnackBar(ft.Text("No tests found for this serial."), bgcolor="red")
            page.snack_bar.open = True
            page.update()
            return

        table.columns = [
            ft.DataColumn(label=ft.Text("Test Type")),
            ft.DataColumn(label=ft.Text("Test #")),
            ft.DataColumn(label=ft.Text("Initial")),
            ft.DataColumn(label=ft.Text("Final")),
            ft.DataColumn(label=ft.Text("Error %")),
            ft.DataColumn(label=ft.Text("Passed")),
            ft.DataColumn(label=ft.Text("Date")),
            ft.DataColumn(label=ft.Text("Brand")),
            ft.DataColumn(label=ft.Text("Model")),
            ft.DataColumn(label=ft.Text("Diameter")),
            ft.DataColumn(label=ft.Text("Batch")),
        ]
        table.rows = [
            ft.DataRow(cells=[
                ft.DataCell(ft.Text(r["test_type"])),
                ft.DataCell(ft.Text(str(r["test_number"]))),
                ft.DataCell(ft.Text(str(r["initial_reading"]))),
                ft.DataCell(ft.Text(str(r["final_reading"]))),
                ft.DataCell(ft.Text(f'{r["error"]:.2f}%')),
                ft.DataCell(ft.Text("✔" if r["passed"] else "❌", color="green" if r["passed"] else "red")),
                ft.DataCell(ft.Text(r["test_date"].strftime("%Y-%m-%d %H:%M"))),
                ft.DataCell(ft.Text(r["brand"])),
                ft.DataCell(ft.Text(r["model"])),
                ft.DataCell(ft.Text(str(r["diameter"]))),
                ft.DataCell(ft.Text(r["batch"])),
            ])
            for r in result
        ]
        page.update()

    return ft.Column([
        ft.Text("Search Test Report by Serial Number", size=24, weight="bold"),
        serial_input,
        ft.Row([
            ft.ElevatedButton("Search", on_click=search),
            ft.ElevatedButton("Export (Coming Soon)", disabled=True),
        ]),
        ft.Divider(),
        table,
    ])