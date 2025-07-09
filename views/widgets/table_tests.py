import flet as ft

DROPDOWN_OPTIONS = ["Escoja una opción", "Q1", "Q2", "Q3", "Q4"]
INPUT_BG = "#f3f4f6"

def table_tests():
    # 🔥 ESTRUCTURA DE FILAS: [#, Serial, Tipo, Inicial, Final, Volumen_Patron, Error, Estado]
    rows = []
    completed_rows = set()  # Índices de filas que ya tienen prueba completada
    frozen_values = {}
    
    print(f"[TABLE_TESTS] 🚀 Inicializando tabla con {len(rows)} fila(s)")

    meter_status_dropdown = ft.Dropdown(
        label="Estado del medidor",
        options=[ft.dropdown.Option("Escoja una opción"), ft.dropdown.Option("Nuevo"), ft.dropdown.Option("Usado")],
        value="Escoja una opción",
        width=200,
        bgcolor=INPUT_BG,
        border_radius=12,
    )

    # 🔥 VALORES INSTANTÁNEOS ACTUALES (SE ACTUALIZAN EN TIEMPO REAL)
    instant_values = {
        "Q1": 1000.0,
        "Q2": 2000.0,
        "Q3": 3000.0,
        "Q4": 4000.0,
    }

    def update_ui(kind, data):
        if kind == "instant" and "data" in data:
            # 🔥 ACTUALIZAR VALORES GLOBALES
            instant_values["Q1"] = data['data'][3] if len(data['data']) > 3 else 0.0
            instant_values["Q2"] = data['data'][4] if len(data['data']) > 4 else 0.0
            instant_values["Q3"] = data['data'][5] if len(data['data']) > 5 else 0.0
            instant_values["Q4"] = data['data'][6] if len(data['data']) > 6 else 0.0
            
            print(f"[AUTO_MODE] 📊 Valores actualizados: Q1={instant_values['Q1']:.2f}, Q2={instant_values['Q2']:.2f}, Q3={instant_values['Q3']:.2f}, Q4={instant_values['Q4']:.2f}")
                        
            # 🔥 ENVIAR VALORES INSTANTÁNEOS A TABLA
            if hasattr(table_widget, 'actualizar_valores_instantaneos'):
                table_widget.actualizar_valores_instantaneos(
                    instant_values["Q1"], instant_values["Q2"], 
                    instant_values["Q3"], instant_values["Q4"]
                )
        
        elif kind == "log" and "log" in data:
            print(f"[MODBUS_LOG] {data['log']}")


    # 🔥 VALORES PATRÓN GUARDADOS (SE GUARDAN AL COMPLETAR PRUEBA)
    saved_pattern_values = {
        "Q1": [],  # Lista de valores guardados para Q1
        "Q2": [],  # Lista de valores guardados para Q2
        "Q3": [],  # Lista de valores guardados para Q3
        "Q4": [],  # Lista de valores guardados para Q4
    }

    # 🔥 ESTADO DE PRUEBAS ACTIVAS (PARA RESETEAR CUANDO INICIA NUEVA PRUEBA)
    active_test_type = None
    test_in_progress = False

    # 🔥 CONTADOR PARA DEBUG
    add_row_counter = 0

    data_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("#", text_align=ft.TextAlign.CENTER)),
            ft.DataColumn(ft.Text("Serial", text_align=ft.TextAlign.CENTER)),
            ft.DataColumn(ft.Text("Tipo de Prueba", text_align=ft.TextAlign.CENTER)),
            ft.DataColumn(ft.Text("Lectura Inicial", text_align=ft.TextAlign.CENTER)),
            ft.DataColumn(ft.Text("Lectura Final", text_align=ft.TextAlign.CENTER)),
            ft.DataColumn(ft.Text("Volumen Patrón", text_align=ft.TextAlign.CENTER)),
            ft.DataColumn(ft.Text("Error (%)", text_align=ft.TextAlign.CENTER)),
            ft.DataColumn(ft.Text("Estado", text_align=ft.TextAlign.CENTER)),
            ft.DataColumn(ft.Text("Acción", text_align=ft.TextAlign.CENTER)),
        ],
        rows=[],
        column_spacing=12,
        data_row_min_height=60,  # 🔥 AUMENTADO PARA ACOMODAR MÁRGENES
        border=ft.border.all(1, ft.Colors.GREY_300),
        divider_thickness=1,
        heading_row_color=ft.Colors.GREY_100,
        heading_row_height=45,
        horizontal_margin=8,
    )

    table_with_margin = ft.Container(
        content=data_table,
        margin=ft.margin.symmetric(vertical=5),  # 🔥 MARGEN VERTICAL DE 5PX
    )

    def get_test_count(serial, test_type, max_idx):
        """Cuenta cuántas pruebas del mismo tipo y serial hay hasta el índice dado"""
        count = 0
        for i in range(max_idx + 1):
            if i < len(rows) and rows[i][1] == serial and rows[i][2] == test_type:
                count += 1
        return count if serial else ""

    def get_pattern_volume_for_row(row_idx):
        """Obtiene el volumen patrón para una fila específica"""
        try:
            if row_idx >= len(rows):
                return 0.0
                
            test_type = rows[row_idx][2]
            if test_type == "Escoja una opción":
                return 0.0
            
            # 🔥 OBTENER EL SERIAL DE LA FILA ACTUAL
            current_serial = rows[row_idx][1]
            
            # 🔥 CONTAR CUÁNTAS PRUEBAS DEL MISMO TIPO Y MISMO SERIAL HAY ANTES DE ESTA FILA
            test_count = 0
            for i in range(row_idx + 1):  # Incluir la fila actual
                if i < len(rows) and rows[i][2] == test_type and rows[i][1] == current_serial:
                    test_count += 1
            
            # 🔥 OBTENER EL VALOR PATRÓN GUARDADO CORRESPONDIENTE
            saved_values = saved_pattern_values.get(test_type, [])
            
            print(f"[TABLE_TESTS] 🔍 Fila {row_idx}: tipo={test_type}, serial={current_serial}, test_count={test_count}")
            print(f"[TABLE_TESTS] 📚 Valores guardados para {test_type}: {saved_values}")
            
            # 🔥 USAR EL ÚLTIMO VALOR GUARDADO SI EXISTE
            if len(saved_values) > 0:
                volume_index = min(test_count - 1, len(saved_values) - 1)
                volume = saved_values[volume_index]
                print(f"[TABLE_TESTS] 📊 Usando volumen guardado [{volume_index}]: {volume}")
                return volume
            else:
                # Si no hay valor guardado, usar el instantáneo actual
                volume = instant_values.get(test_type, 0.0)
                print(f"[TABLE_TESTS] 📊 Usando volumen instantáneo: {volume}")
                return volume
                    
        except Exception as e:
            print(f"[TABLE_TESTS] ❌ Error obteniendo volumen patrón: {e}")
            return 0.0

    def calculate_error(start_str, end_str, pattern_volume):
        """Calcula el error porcentual y determina si pasa o no"""
        try:
            start = float(start_str) if start_str else 0
            end = float(end_str) if end_str else 0
            pattern = max(pattern_volume, 0.1)

            error = (((end - start) - pattern) / pattern) * 100
            status = meter_status_dropdown.value
            
            # 🔥 TOLERANCIAS SEGÚN ESTADO Y TIPO
            if status == "Nuevo":
                tolerance = 5.0
            elif status == "Usado":
                tolerance = 10.0
            else:
                tolerance = 4.0  # Default

            return round(error, 2), "PASA" if abs(error) <= tolerance else "NO PASA", \
                ft.Colors.GREEN if abs(error) <= tolerance else ft.Colors.RED
                
        except Exception as e:
            print(f"[TABLE_TESTS] ❌ Error calculando: {e}")
            return 0, "Error", ft.Colors.GREY

    def update_table():
        """Actualiza la tabla con los datos actuales"""
        try:
            print(f"[TABLE_TESTS] 🔄 Actualizando tabla con {len(rows)} filas")
            data_rows = []
            
            for idx, row in enumerate(rows):
                if idx >= len(rows):
                    continue
                    
                test_num = get_test_count(row[1], row[2], idx)
                pattern_volume = get_pattern_volume_for_row(idx)
                
                # 🔥 ACTUALIZAR EL VOLUMEN PATRÓN EN LA FILA
                rows[idx][5] = f"{pattern_volume:.2f}"
                
                error, status_text, status_color = calculate_error(row[3], row[4], pattern_volume)
                rows[idx][6] = str(error)
                rows[idx][7] = status_text
    
                data_rows.append(ft.DataRow(cells=[
                    # 🔥 CELDA DE NÚMERO - CENTRADA
                    ft.DataCell(ft.Container(
                        ft.Text(str(test_num)),
                        alignment=ft.alignment.center,  # 🔥 CENTRADO
                    )),
                    # 🔥 CELDA DE SERIAL - CENTRADA
                    ft.DataCell(ft.Container(
                        ft.TextField(
                            value=row[1],
                            on_change=lambda e, row_idx=idx: on_text_change(e, row_idx, 1),
                            on_submit=lambda e, row_idx=idx: recalculate_errors(None),  # 🔥 RECALCULAR CON ENTER
                            keyboard_type=ft.KeyboardType.NUMBER,
                            input_filter=ft.InputFilter(allow=True, regex_string=r"^\d*$"),
                            dense=True,
                            border=ft.InputBorder.UNDERLINE,
                            border_radius=12,
                            filled=True,
                            bgcolor=INPUT_BG,
                            text_align=ft.TextAlign.CENTER,  # 🔥 TEXTO CENTRADO
                        ),
                        width=120,
                        padding=0,
                        alignment=ft.alignment.center,  # 🔥 CONTAINER CENTRADO
                    )),
                    # 🔥 CELDA DE DROPDOWN - CENTRADA
                    ft.DataCell(ft.Container(
                        ft.Dropdown(
                            options=[ft.dropdown.Option(opt) for opt in DROPDOWN_OPTIONS],
                            value=row[2],
                            on_change=lambda e, row_idx=idx: on_dropdown_change(e, row_idx),
                            dense=True,
                            border_radius=12,
                            bgcolor=INPUT_BG,
                            border="none",
                            alignment=ft.alignment.center,  # 🔥 DROPDOWN CENTRADO
                        ),
                        width=100,
                        padding=0,
                        alignment=ft.alignment.center,  # 🔥 CONTAINER CENTRADO
                    )),
                    # 🔥 CELDA DE LECTURA INICIAL - CENTRADA
                    ft.DataCell(ft.Container(
                        ft.TextField(
                            value=row[3],
                            on_change=lambda e, row_idx=idx: on_text_change(e, row_idx, 3),
                            on_submit=lambda e, row_idx=idx: recalculate_errors(None),  # 🔥 RECALCULAR CON ENTER
                            keyboard_type=ft.KeyboardType.NUMBER,
                            input_filter=ft.InputFilter(allow=True, regex_string=r"^\d*\.?\d*$"),
                            dense=True,
                            border=ft.InputBorder.UNDERLINE,
                            border_radius=12,
                            filled=True,
                            bgcolor=INPUT_BG,
                            text_align=ft.TextAlign.CENTER,  # 🔥 TEXTO CENTRADO
                        ),
                        width=80,
                        padding=0,
                        alignment=ft.alignment.center,  # 🔥 CONTAINER CENTRADO
                    )),
                    # 🔥 CELDA DE LECTURA FINAL - CENTRADA
                    ft.DataCell(ft.Container(
                        ft.TextField(
                            value=row[4],
                            on_change=lambda e, row_idx=idx: on_text_change(e, row_idx, 4),
                            on_submit=lambda e, row_idx=idx: recalculate_errors(None),  # 🔥 RECALCULAR CON ENTER
                            keyboard_type=ft.KeyboardType.NUMBER,
                            input_filter=ft.InputFilter(allow=True, regex_string=r"^\d*\.?\d*$"),
                            dense=True,
                            border=ft.InputBorder.UNDERLINE,
                            border_radius=12,
                            filled=True,
                            bgcolor=INPUT_BG,
                            text_align=ft.TextAlign.CENTER,  # 🔥 TEXTO CENTRADO
                        ),
                        width=80,
                        padding=0,
                        alignment=ft.alignment.center,  # 🔥 CONTAINER CENTRADO
                    )),
                    # 🔥 COLUMNA DE VOLUMEN PATRÓN CON MARGEN - CENTRADA
                    ft.DataCell(ft.Container(
                        ft.Container(  # 🔥 CONTAINER INTERNO CON MARGEN
                            ft.Text(
                                f"{pattern_volume:.2f}",
                                weight="bold",
                                color=ft.Colors.BLUE_700,
                                text_align=ft.TextAlign.CENTER,  # 🔥 TEXTO CENTRADO
                            ),
                            width=75,  # 🔥 ANCHO FIJO MÁS PEQUEÑO
                            height=30,  # 🔥 ALTURA FIJA
                            padding=ft.padding.all(6),
                            bgcolor=ft.Colors.BLUE_50,
                            border_radius=8,
                            alignment=ft.alignment.center,  # 🔥 CONTENIDO CENTRADO
                            margin=ft.margin.symmetric(vertical=5),  # 🔥 MARGEN VERTICAL
                        ),
                        width=90,  # Container externo
                        alignment=ft.alignment.center,  # 🔥 CONTAINER CENTRADO
                    )),
                    # 🔥 CELDA DE ERROR - CENTRADA
                    ft.DataCell(ft.Container(
                        ft.Text(str(error), weight="bold", text_align=ft.TextAlign.CENTER),
                        alignment=ft.alignment.center,  # 🔥 CONTAINER CENTRADO
                        margin=ft.margin.symmetric(vertical=5),  # 🔥 MARGEN PARA ERROR
                    )),
                    # 🔥 COLUMNA DE ESTADO CON MARGEN Y TAMAÑO CONTROLADO - CENTRADA
                    ft.DataCell(ft.Container(
                        ft.Container(  # 🔥 CONTAINER INTERNO CON MARGEN
                            ft.Text(
                                status_text, 
                                color="white", 
                                weight="bold", 
                                size=12,
                                text_align=ft.TextAlign.CENTER  # 🔥 TEXTO CENTRADO
                            ),
                            bgcolor=status_color,
                            padding=ft.padding.symmetric(horizontal=8, vertical=6),
                            border_radius=8,
                            alignment=ft.alignment.center,  # 🔥 CONTENIDO CENTRADO
                            width=80,  # 🔥 ANCHO FIJO
                            height=28,  # 🔥 ALTURA FIJA PEQUEÑA
                            margin=ft.margin.symmetric(vertical=8),  # 🔥 MARGEN VERTICAL
                        ),
                        alignment=ft.alignment.center,  # 🔥 CONTAINER CENTRADO
                        width=100,  # Container externo
                    )),
                    # 🔥 CELDA DE BOTÓN - CENTRADA
                    ft.DataCell(ft.Container(
                        ft.IconButton(
                            icon=ft.Icons.DELETE,
                            tooltip="Eliminar fila",
                            icon_color=ft.Colors.RED_400,
                            on_click=lambda e, idx=idx: remove_row(idx),
                        ),
                        alignment=ft.alignment.center,  # 🔥 BOTÓN CENTRADO
                        margin=ft.margin.symmetric(vertical=3),  # 🔥 MARGEN PARA BOTÓN
                    )),
                ]))
            
            data_table.rows = data_rows
            print(f"[TABLE_TESTS] 🔄 DataTable actualizado con {len(data_rows)} filas")
            
            if hasattr(data_table, 'page') and data_table.page is not None:
                data_table.update()
            
        except Exception as e:
            print(f"❌ Error actualizando tabla: {e}")
            import traceback
            traceback.print_exc()

    def add_row(e):
        """Agrega una nueva fila a la tabla"""
        nonlocal add_row_counter
        add_row_counter += 1
        print(f"[TABLE_TESTS] 🔄 add_row llamado #{add_row_counter}")
        print(f"[TABLE_TESTS] 🔄 Agregando fila. Filas antes: {len(rows)}")
        
        rows.append(["", "", DROPDOWN_OPTIONS[0], "", "", "", "", ""])
        print(f"[TABLE_TESTS] 🔄 Filas después: {len(rows)}")
        update_table()

    def remove_row(idx):
        """Elimina una fila de la tabla"""
        if len(rows) > 1 and idx < len(rows):
            print(f"[TABLE_TESTS] 🗑️ Eliminando fila {idx}")
            rows.pop(idx)
            update_table()
        else:
            print(f"[TABLE_TESTS] ⚠️ No se puede eliminar fila {idx} (total: {len(rows)})")

    def on_text_change(e, row_idx, col_idx):
        """Maneja cambios en los campos de texto"""
        if row_idx < len(rows):
            rows[row_idx][col_idx] = e.control.value
            # 🔥 NO ACTUALIZAR TABLA AUTOMÁTICAMENTE PARA EVITAR PERDER FOCO

    def on_key_press(e, row_idx, col_idx):
        """Maneja teclas presionadas en los campos"""
        if e.key == "Enter":
            print(f"[TABLE_TESTS] ⏎ ENTER presionado en fila {row_idx}, columna {col_idx}")
            recalculate_errors(None)  # Recalcular cuando se presiona ENTER

    def on_dropdown_change(e, row_idx):
        """Maneja cambios en el dropdown de tipo de prueba"""
        if row_idx < len(rows):
            rows[row_idx][2] = e.control.value
            print(f"[TABLE_TESTS] 🔄 Tipo de prueba cambiado en fila {row_idx}: {e.control.value}")
            update_table()  # Solo actualizar cuando cambia el tipo

    def on_meter_status_change(e):
        """Maneja cambios en el estado del medidor"""
        print(f"[TABLE_TESTS] 🔄 Estado del medidor cambiado: {e.control.value}")
        update_table()

    meter_status_dropdown.on_change = on_meter_status_change

    # 🔥 FUNCIÓN PARA NOTIFICAR INICIO DE NUEVA PRUEBA
    def notify_test_start(test_type):
        nonlocal active_test_type, test_in_progress
        
        print(f"[TABLE_TESTS] 🚀 INICIO DE CONFIGURACIÓN: {test_type}")
        
        # Si es una nueva prueba del mismo tipo, es repetibilidad
        if active_test_type == test_type:
            print(f"[TABLE_TESTS] 🔄 Prueba de repetibilidad detectada para {test_type}")
        
        active_test_type = test_type
        test_in_progress = True
        
        print(f"[TABLE_TESTS] 📊 Prueba {test_type} marcada como activa")

    # 🔥 FUNCIÓN PARA CAPTURAR Y GUARDAR VOLUMEN AL COMPLETAR PRUEBA
    def capture_pattern_volume(test_type, final_volume):
        nonlocal test_in_progress, active_test_type
        
        print(f"[TABLE_TESTS] 🏁 PRUEBA COMPLETADA: {test_type}")
        print(f"[TABLE_TESTS] 💾 Guardando volumen patrón: {final_volume:.2f}")
        
        # 🔥 VALIDAR QUE EL VOLUMEN SEA VÁLIDO
        if final_volume < 1.0:
            print(f"[TABLE_TESTS] ⚠️ Volumen muy pequeño ({final_volume:.2f}), no guardando")
            return
        
        # 🔥 GUARDAR EL VOLUMEN PATRÓN FINAL
        if test_type in saved_pattern_values:
            saved_pattern_values[test_type].append(final_volume)
            print(f"[TABLE_TESTS] 📚 Histórico {test_type}: {saved_pattern_values[test_type]}")
            
            # 🔥 ACTUALIZAR INMEDIATAMENTE TODAS LAS FILAS
            print(f"[TABLE_TESTS] 🔄 Forzando actualización de tabla...")
            update_table()
            
            # 🔥 FORZAR UPDATE DE LA PÁGINA
            if hasattr(data_table, 'page') and data_table.page is not None:
                print(f"[TABLE_TESTS] 🔄 Forzando update de página...")
                data_table.page.update()
    
        test_in_progress = False
        active_test_type = None
    
    def update_instant_values(q1, q2, q3, q4):
        """Actualiza los valores instantáneos"""
        # 🔥 LOGS REDUCIDOS PARA EVITAR SPAM
        if test_in_progress and active_test_type:
            print(f"[TABLE_TESTS] 📊 Actualizando {active_test_type}: {locals()[active_test_type.lower()]:.2f}")
        
        # 🔥 SOLO ACTUALIZAR EL VALOR DE LA PRUEBA ACTIVA SI HAY PRUEBA EN CURSO
        if test_in_progress and active_test_type:
            if active_test_type == "Q1":
                instant_values["Q1"] = max(q1, 0.1)
            elif active_test_type == "Q2":
                instant_values["Q2"] = max(q2, 0.1)
            elif active_test_type == "Q3":
                instant_values["Q3"] = max(q3, 0.1)
            elif active_test_type == "Q4":
                instant_values["Q4"] = max(q4, 0.1)
        else:
            # Si no hay prueba activa, actualizar todos los valores normalmente
            instant_values["Q1"] = max(q1, 0.1)
            instant_values["Q2"] = max(q2, 0.1)
            instant_values["Q3"] = max(q3, 0.1)
            instant_values["Q4"] = max(q4, 0.1)

    # 🔥 AGREGAR BOTÓN PARA VER HISTÓRICO DE VOLÚMENES
    def show_volume_history(e):
        """Muestra el histórico de volúmenes patrón"""
        history_text = "📚 Histórico de Volúmenes Patrón:\n\n"
        for test_type, values in saved_pattern_values.items():
            if values:
                history_text += f"{test_type}: {', '.join([f'{v:.2f}' for v in values])}\n"
            else:
                history_text += f"{test_type}: Sin pruebas completadas\n"
        print(history_text)

    # 🔥 FUNCIÓN PARA RECALCULAR ERRORES MANUALMENTE
    def recalculate_errors(e):
        """Recalcula todos los errores y actualiza la tabla"""
        print(f"[TABLE_TESTS] 🔄 Recalculando errores manualmente...")
        print(f"[TABLE_TESTS] 📊 Valores instantáneos actuales: {instant_values}")
        print(f"[TABLE_TESTS] 📚 Volúmenes guardados: {saved_pattern_values}")
        update_table()
    
        # 🔥 FORZAR UPDATE COMPLETO
        if hasattr(data_table, 'page') and data_table.page is not None:
            data_table.page.update()

    def update_status_indicator():
        """Actualiza el indicador de estado en la UI"""
        status_text = (
            f"🔄 Prueba activa: {active_test_type if test_in_progress else 'Ninguna'} | "
            f"Volúmenes guardados: Q1({len(saved_pattern_values['Q1'])}), Q2({len(saved_pattern_values['Q2'])}), "
            f"Q3({len(saved_pattern_values['Q3'])}), Q4({len(saved_pattern_values['Q4'])})"
        )
        # Actualizar el texto del indicador si existe
        if hasattr(main_column, 'page') and main_column.page is not None:
            main_column.page.update()

    table_container = ft.Container(
        content=ft.Column(
            controls=[table_with_margin],  # 🔥 USAR EL TABLE CON MARGEN
            scroll=ft.ScrollMode.AUTO,
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        ),
        height=500,
        width=1200,
        border_radius=12,
        border=ft.border.all(1, ft.Colors.GREY_300),
        bgcolor=ft.Colors.GREY_50,
        padding=10,
        alignment=ft.alignment.top_center,
    )

    main_column = ft.Column([
        ft.Text("Medidores", size=24, weight="bold", text_align="center"),
        ft.Row([
            ft.ElevatedButton("Agregar fila", icon=ft.Icons.ADD, on_click=add_row, width=140),
            meter_status_dropdown,
            ft.ElevatedButton("Ver Histórico", icon=ft.Icons.HISTORY, on_click=show_volume_history, width=140),
            ft.Text("💡 Presiona ENTER para recalcular errores", size=12, color=ft.Colors.BLUE_700),
        ], alignment="start", spacing=15),
        # 🔥 AGREGAR INDICADOR DE ESTADO DE PRUEBA
        ft.Container(
            content=ft.Text(
                f"🔄 Prueba activa: {active_test_type if test_in_progress else 'Ninguna'} | "
                f"Volúmenes guardados: Q1({len(saved_pattern_values['Q1'])}), Q2({len(saved_pattern_values['Q2'])}), "
                f"Q3({len(saved_pattern_values['Q3'])}), Q4({len(saved_pattern_values['Q4'])})",
                size=11,
                color=ft.Colors.GREY_600
            ),
            padding=ft.padding.symmetric(vertical=5)
        ),
        table_container,
    ], 
    expand=True,
    alignment=ft.MainAxisAlignment.START,
    horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )

    def initialize_table():
        """Inicializa la tabla con los valores por defecto"""
        try:
            print(f"[TABLE_TESTS] 🔄 Inicializando tabla. Filas: {len(rows)}")
            update_table()
        except Exception as e:
            print(f"❌ Error inicializando tabla: {e}")

    # 🔥 EXPONER LAS FUNCIONES PÚBLICAS
    main_column.actualizar_valores_instantaneos = update_instant_values
    main_column.initialize_table = initialize_table
    main_column.notify_test_start = notify_test_start
    main_column.capture_pattern_volume = capture_pattern_volume

    return main_column