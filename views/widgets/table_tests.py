import flet as ft

DROPDOWN_OPTIONS = ["Escoja una opción", "Q1", "Q2", "Q3", "Q4"]
INPUT_BG = "#f3f4f6"

def table_tests():
    rows = [["", "", DROPDOWN_OPTIONS[0], "", "", "", "", ""]]

    # Cambiar el valor predeterminado de 'value' a "Escoja una opción"
    meter_status_dropdown = ft.Dropdown(
        label="Estado del medidor",
        options=[ft.dropdown.Option("Escoja una opción"), ft.dropdown.Option("Nuevo"), ft.dropdown.Option("Usado")],
        value="Escoja una opción",
        width=200,
        bgcolor=INPUT_BG,
        border_radius=12,
    )

    instant_values = {
        "Q1": 1000.0,
        "Q2": 2000.0,
        "Q3": 3000.0,
        "Q4": 4000.0,
    }

    data_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("#")),
            ft.DataColumn(ft.Text("Serial")),
            ft.DataColumn(ft.Text("Tipo de Prueba")),
            ft.DataColumn(ft.Text("Lectura Inicial")),
            ft.DataColumn(ft.Text("Lectura Final")),
            ft.DataColumn(ft.Text("Error (%)")),
            ft.DataColumn(ft.Text("Estado")),
            ft.DataColumn(ft.Text("Acción")),
        ],
        rows=[],
        column_spacing=16,
        data_row_min_height=48,
    )

    def get_test_count(serial, test_type, max_idx):
        count = 0
        for i in range(max_idx + 1):
            if rows[i][1] == serial and rows[i][2] == test_type:
                count += 1
        return count if serial else ""

    def calculate_error(start_str, end_str, test_type):
        try:
            start = float(start_str) if start_str else 0
            end = float(end_str) if end_str else 0
            pattern = max(instant_values.get(test_type, 0), 0.1)

            error = (((end - start - pattern) / pattern) * 100)
            status = meter_status_dropdown.value
            tolerance = 5.0 if status == "Nuevo" else 10.0 if test_type == "Q1" else 4.0

            print(f"[CÁLCULO] Tipo: {test_type} | Start: {start} | End: {end} | Pattern: {pattern} | Error: {error:.2f}%")

            return round(error, 2), "PASA" if abs(error) <= tolerance else "NO PASA", \
                "green" if abs(error) <= tolerance else "red"
        except Exception as e:
            print(f"[ERROR] Calcular error: {e}")
            return 0, "Error", "gray"

    def update_table():
        # ✅ VERIFICAR SI LA TABLA ESTÁ EN LA PÁGINA ANTES DE ACTUALIZAR
        try:
            data_rows = []
            for idx, row in enumerate(rows):
                test_num = get_test_count(row[1], row[2], idx)
                error, status_text, status_color = calculate_error(row[3], row[4], row[2])
                rows[idx][5] = str(error)
                rows[idx][6] = status_text

                data_rows.append(ft.DataRow(cells=[
                    ft.DataCell(ft.Text(str(test_num))),
                    ft.DataCell(ft.Container(
                        ft.TextField(
                            value=row[1],
                            on_change=lambda e, row_idx=idx: on_text_change(e, row_idx, 1),
                            keyboard_type=ft.KeyboardType.NUMBER,
                            input_filter=ft.InputFilter(allow=True, regex_string=r"^\d*$"),
                            dense=True,
                            border=ft.InputBorder.UNDERLINE,
                            border_radius=12,
                            filled=True,
                            bgcolor=INPUT_BG,
                        ),
                        width=150,
                        padding=0
                    )),
                    ft.DataCell(ft.Container(
                        ft.Dropdown(
                            options=[ft.dropdown.Option(opt) for opt in DROPDOWN_OPTIONS],
                            value=row[2],
                            on_change=lambda e, row_idx=idx: on_dropdown_change(e, row_idx),
                            dense=True,
                            border_radius=12,
                            bgcolor=INPUT_BG,
                            border="none",
                        ),
                        width=200,
                        padding=0
                    )),
                    ft.DataCell(ft.Container(
                        ft.TextField(
                            value=row[3],
                            on_blur=lambda e, row_idx=idx: on_text_change(e, row_idx, 3),
                            keyboard_type=ft.KeyboardType.NUMBER,
                            input_filter=ft.InputFilter(allow=True, regex_string=r"^\d*\.?\d*$"),
                            dense=True,
                            border=ft.InputBorder.UNDERLINE,
                            border_radius=12,
                            filled=True,
                            bgcolor=INPUT_BG,
                        ),
                        width=120,
                        padding=0
                    )),
                    ft.DataCell(ft.Container(
                        ft.TextField(
                            value=row[4],
                            on_blur=lambda e, row_idx=idx: on_text_change(e, row_idx, 4),
                            keyboard_type=ft.KeyboardType.NUMBER,
                            input_filter=ft.InputFilter(allow=True, regex_string=r"^\d*\.?\d*$"),
                            dense=True,
                            border=ft.InputBorder.UNDERLINE,
                            border_radius=12,
                            filled=True,
                            bgcolor=INPUT_BG,
                        ),
                        width=120,
                        padding=0
                    )),
                    ft.DataCell(ft.Text(str(error), weight="bold")),
                    ft.DataCell(ft.Container(
                        ft.Text(status_text, color="white", weight="bold"),
                        bgcolor=status_color,
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                        border_radius=8,
                        alignment=ft.alignment.center,
                    )),
                    ft.DataCell(ft.IconButton(
                        icon=ft.Icons.DELETE,
                        tooltip="Eliminar fila",
                        icon_color=ft.Colors.RED_400,
                        on_click=lambda e, idx=idx: remove_row(idx),
                    )),
                ]))
            
            data_table.rows = data_rows
            
            # ✅ SOLO ACTUALIZAR SI LA TABLA TIENE UNA PÁGINA ASIGNADA
            if hasattr(data_table, 'page') and data_table.page is not None:
                data_table.update()
            
        except Exception as e:
            print(f"❌ Error actualizando tabla: {e}")

    def add_row(e):
        rows.append(["", "", DROPDOWN_OPTIONS[0], "", "", "", "", ""])
        update_table()

    def remove_row(idx):
        if len(rows) > 1:
            rows.pop(idx)
            update_table()

    def on_text_change(e, row_idx, col_idx):
        rows[row_idx][col_idx] = e.control.value
        if col_idx in [3, 4]:
            update_table()

    def on_dropdown_change(e, row_idx):
        rows[row_idx][2] = e.control.value
        update_table()

    def on_meter_status_change(e):
        update_table()

    meter_status_dropdown.on_change = on_meter_status_change

    def update_instant_values(q1, q2, q3, q4):
        instant_values["Q1"] = max(q1, 0.1)
        instant_values["Q2"] = max(q2, 0.1)
        instant_values["Q3"] = max(q3, 0.1)
        instant_values["Q4"] = max(q4, 0.1)
        update_table()

    data_table.actualizar_valores_instantaneos = update_instant_values

    # ✅ CREAR LA ESTRUCTURA PRIMERO, LUEGO ACTUALIZAR
    table_container = ft.Container(
        content=ft.Column(
            controls=[data_table], 
            scroll=ft.ScrollMode.AUTO,
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        ),
        height=500,
        border_radius=12,
        border=ft.border.all(1, ft.Colors.GREY_300),
        bgcolor=ft.Colors.GREY_50,
        padding=10,
        alignment=ft.alignment.top_center,
    )

    main_column = ft.Column([
        ft.Text("Medidores", size=24, weight="bold", text_align="center"),
        ft.Row([
            ft.ElevatedButton("Agregar fila", icon=ft.Icons.ADD, on_click=add_row, width=180),
            meter_status_dropdown,
        ], alignment="start", spacing=15),
        table_container,
    ], 
    expand=True,
    alignment=ft.MainAxisAlignment.START,
    horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )

    # ✅ FUNCIÓN PARA INICIALIZAR LA TABLA DESPUÉS DE AGREGARSE A LA PÁGINA
    def initialize_table():
        """Inicializa la tabla con datos después de que se agrega a la página"""
        try:
            update_table()
        except Exception as e:
            print(f"❌ Error inicializando tabla: {e}")

    # ✅ AGREGAR FUNCIÓN DE INICIALIZACIÓN AL COMPONENTE PRINCIPAL
    main_column.initialize_table = initialize_table

    return main_column