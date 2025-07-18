import flet as ft

DROPDOWN_OPTIONS = ["Escoja una opción", "Q1", "Q2", "Q3", "Q4"]
INPUT_BG = "#f3f4f6"

def test_configuration_table(q1=0, q2=0, q3=0, q4=0):
    """Tabla para configurar las pruebas a realizar"""
    
    # 🔥 ESTRUCTURA DE FILAS: [#, Prueba, Repeticiones, Caudal_Max, Caudal_Min, Volumen, Tiempo_Aprox, Estado]
    rows = []
    
    # 🔥 GUARDAR VALORES DE CAUDALES CALCULADOS
    flow_values = {"Q1": q1, "Q2": q2, "Q3": q3, "Q4": q4}
    
    print(f"[TEST_CONFIG] 🚀 Inicializando tabla con caudales: Q1={q1}, Q2={q2}, Q3={q3}, Q4={q4}")

    # 🔥 CREAR ELEMENTOS DE TEXTO PARA LOS CAUDALES (CON REFERENCIAS)
    q1_text = ft.Text(f"{q1:.2f} L/h", size=14, weight="bold", color=ft.Colors.BLUE_800)
    q2_text = ft.Text(f"{q2:.2f} L/h", size=14, weight="bold", color=ft.Colors.GREEN_800)
    q3_text = ft.Text(f"{q3:.2f} L/h", size=14, weight="bold", color=ft.Colors.ORANGE_800)
    q4_text = ft.Text(f"{q4:.2f} L/h", size=14, weight="bold", color=ft.Colors.PURPLE_800)

    data_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("#", text_align=ft.TextAlign.CENTER, size=12)),
            ft.DataColumn(ft.Text("Tipo de Prueba", text_align=ft.TextAlign.CENTER, size=12)),
            ft.DataColumn(ft.Text("Repeticiones", text_align=ft.TextAlign.CENTER, size=12)),
            ft.DataColumn(ft.Text("Caudal Máx.\n(L/h)", text_align=ft.TextAlign.CENTER, size=11)),
            ft.DataColumn(ft.Text("Caudal Mín.\n(L/h)", text_align=ft.TextAlign.CENTER, size=11)),
            ft.DataColumn(ft.Text("Volumen\n(L)", text_align=ft.TextAlign.CENTER, size=11)),
            ft.DataColumn(ft.Text("Tiempo\n(min:seg)", text_align=ft.TextAlign.CENTER, size=11)),
            ft.DataColumn(ft.Text("Estado", text_align=ft.TextAlign.CENTER, size=12)),
            ft.DataColumn(ft.Text("Acción", text_align=ft.TextAlign.CENTER, size=12)),
        ],
        rows=[],
        column_spacing=5,
        data_row_min_height=55,
        border=ft.border.all(1, ft.Colors.GREY_300),
        divider_thickness=1,
        heading_row_color=ft.Colors.BLUE_100,
        heading_row_height=45,
        horizontal_margin=2,
        height=None
    )

    def calculate_time_from_volume(test_type, volume_liters):
        """Calcula el tiempo usando regla de 3 y convierte decimales a minutos:segundos"""
        try:
            base_flow = flow_values.get(test_type, 0)
            
            if base_flow <= 0:
                print(f"[TEST_CONFIG] ⚠️ Caudal base para {test_type} es 0 o inválido: {base_flow}")
                return "0:00", 0
            
            if volume_liters <= 0:
                print(f"[TEST_CONFIG] ⚠️ Volumen inválido: {volume_liters}")
                return "0:00", 0
            
            # 🔥 USAR EL CAUDAL MÁXIMO PARA EL CÁLCULO
            qmax = round(base_flow * 1.1, 2)
            
            if qmax <= 0:
                print(f"[TEST_CONFIG] ⚠️ Caudal máximo calculado es 0 o inválido: {qmax}")
                return "0:00", 0
            
            # 🔥 REGLA DE 3: Si caudal_max = 60 minutos, entonces volumen = X minutos
            time_decimal = (volume_liters * 60) / qmax
            
            # 🔥 CONVERTIR DECIMALES A MINUTOS Y SEGUNDOS
            minutes = int(time_decimal)
            decimal_part = time_decimal - minutes
            seconds = int(decimal_part * 60)
            
            # 🔥 FORMATEAR COMO "MM:SS"
            time_formatted = f"{minutes}:{seconds:02d}"
            
            print(f"[TEST_CONFIG] 🧮 Cálculo tiempo: {volume_liters}L / {qmax}L/h = {time_decimal:.3f} min = {time_formatted}")
            
            return time_formatted, time_decimal
            
        except Exception as e:
            print(f"[TEST_CONFIG] ❌ Error calculando tiempo: {e}")
            return "0:00", 0

    def calculate_flow_values(test_type, repetitions, volume=None):
        """Calcula valores de caudal según el tipo de prueba - NO CALCULA VOLUMEN POR DEFECTO"""
        try:
            base_flow = flow_values.get(test_type, 0)
            
            if base_flow > 0:
                # 🔥 CALCULAR MÍNIMOS Y MÁXIMOS SEGÚN LAS FÓRMULAS
                qmin = round(0.95 * base_flow, 2)
                qmax = round(base_flow * 1.1, 2)
                
                # 🔥 SOLO CALCULAR TIEMPO SI SE PROPORCIONA VOLUMEN
                if volume is not None and volume > 0:
                    time_formatted, time_decimal = calculate_time_from_volume(test_type, volume)
                    calculated_volume = volume
                else:
                    time_formatted = "0:00"
                    time_decimal = 0
                    calculated_volume = 0
                
                return {
                    "max_flow": qmax,
                    "min_flow": qmin,
                    "volume": calculated_volume,
                    "time": time_formatted,
                    "time_decimal": time_decimal
                }
            else:
                return {"max_flow": 0, "min_flow": 0, "volume": 0, "time": "0:00", "time_decimal": 0}
                
        except Exception as e:
            print(f"[TEST_CONFIG] ❌ Error calculando valores de flujo: {e}")
            return {"max_flow": 0, "min_flow": 0, "volume": 0, "time": "0:00", "time_decimal": 0}

    def update_flow_values(new_q1, new_q2, new_q3, new_q4):
        """Actualiza los valores de caudales y recalcula la tabla"""
        flow_values["Q1"] = new_q1
        flow_values["Q2"] = new_q2
        flow_values["Q3"] = new_q3
        flow_values["Q4"] = new_q4
        
        # 🔥 ACTUALIZAR LOS TEXTOS DE LOS CAUDALES
        q1_text.value = f"{new_q1:.2f} L/h"
        q2_text.value = f"{new_q2:.2f} L/h"
        q3_text.value = f"{new_q3:.2f} L/h"
        q4_text.value = f"{new_q4:.2f} L/h"
        
        print(f"[TEST_CONFIG] 🔄 Actualizando caudales: Q1={new_q1}, Q2={new_q2}, Q3={new_q3}, Q4={new_q4}")
        
        # 🔥 RECALCULAR TIEMPOS PARA TODAS LAS FILAS QUE TENGAN VOLUMEN
        for idx, row in enumerate(rows):
            test_type = row[1]
            if test_type != "Escoja una opción" and row[5] and int(row[5]) > 0:
                volume = int(row[5])
                time_formatted, time_decimal = calculate_time_from_volume(test_type, volume)
                rows[idx][6] = time_formatted
                print(f"[TEST_CONFIG] 🔄 Recalculando tiempo para fila {idx}: {volume}L -> {time_formatted}")
        
        # 🔥 ACTUALIZAR LA TABLA Y LA UI
        update_table()
        
        # 🔥 FORZAR UPDATE DE LOS TEXTOS
        if hasattr(q1_text, 'page') and q1_text.page is not None:
            q1_text.update()
            q2_text.update()
            q3_text.update()
            q4_text.update()

    def get_test_configurations():
        """Obtiene las configuraciones de prueba como lista"""
        configurations = []
        for idx, row in enumerate(rows):
            if row[1] != "Escoja una opción" and int(row[2]) > 0:
                test_type = row[1]
                repetitions = int(row[2])
                
                # Crear lista de pruebas individuales
                for rep in range(repetitions):
                    if repetitions == 1:
                        test_name = test_type
                    else:
                        test_name = f"{test_type}.{rep + 1}"
                    
                    # 🔥 EXTRAER TIEMPO DECIMAL DEL FORMATO "MM:SS"
                    time_str = row[6]
                    try:
                        if ":" in time_str:
                            minutes, seconds = time_str.split(":")
                            time_decimal = int(minutes) + int(seconds) / 60
                        else:
                            time_decimal = float(time_str) if time_str.replace(".", "").isdigit() else 0
                    except Exception as e:
                        print(f"[TEST_CONFIG] ⚠️ Error procesando tiempo {time_str}: {e}")
                        time_decimal = 0
                    
                    configurations.append({
                        "test_name": test_name,
                        "test_type": test_type,
                        "repetition": rep + 1,
                        "total_repetitions": repetitions,
                        "config_row": idx,
                        "max_flow": float(row[3]) if row[3] else 0,
                        "min_flow": float(row[4]) if row[4] else 0,
                        "volume": int(row[5]) if row[5] else 0,  # 🔥 CONVERTIR A ENTERO
                        "estimated_time": time_decimal,
                        "time_formatted": time_str
                    })
        
        return configurations

    def update_table():
        """Actualiza la tabla con los datos actuales"""
        try:
            print(f"[TEST_CONFIG] 🔄 Actualizando tabla con {len(rows)} filas")
            data_rows = []
            
            for idx, row in enumerate(rows):
                repetitions = int(row[2]) if row[2].isdigit() else 0
                test_type = row[1]
                
                # 🔥 CALCULAR SOLO CAUDALES MÁXIMOS Y MÍNIMOS (NO VOLUMEN NI TIEMPO)
                if test_type != "Escoja una opción" and repetitions > 0:
                    # 🔥 PRESERVAR VOLUMEN EXISTENTE
                    current_volume = int(row[5]) if row[5] and row[5] != "0" else None
                    values = calculate_flow_values(test_type, repetitions, current_volume)
                    rows[idx][3] = str(values["max_flow"])
                    rows[idx][4] = str(values["min_flow"])
                    # 🔥 NO SOBRESCRIBIR VOLUMEN
                    # 🔥 NO SOBRESCRIBIR TIEMPO A MENOS QUE SE HAYA CALCULADO NUEVO
                    if values["time"] != "0:00":
                        rows[idx][6] = values["time"]
                
                # Determinar estado
                if test_type == "Escoja una opción":
                    status_text = "Pendiente"
                    status_color = ft.Colors.GREY
                elif repetitions == 0:
                    status_text = "Sin rep."
                    status_color = ft.Colors.ORANGE
                elif repetitions == 1:
                    status_text = "Única"
                    status_color = ft.Colors.GREEN
                else:
                    status_text = f"x{repetitions}"
                    status_color = ft.Colors.BLUE
                
                rows[idx][7] = status_text

                data_rows.append(ft.DataRow(cells=[
                    # 🔥 NÚMERO DE FILA
                    ft.DataCell(
                        ft.Text(str(idx + 1), text_align=ft.TextAlign.CENTER, size=12),
                    ),
                    
                    # 🔥 DROPDOWN DE TIPO DE PRUEBA
                    ft.DataCell(
                        ft.Dropdown(
                            options=[ft.dropdown.Option(opt) for opt in DROPDOWN_OPTIONS],
                            value=row[1],
                            on_change=lambda e, row_idx=idx: on_test_type_change(e, row_idx),
                            dense=True,
                            border_radius=8,
                            bgcolor=INPUT_BG,
                            text_size=10,
                            width=None
                        ),
                    ),
                    
                    # 🔥 CAMPO DE REPETICIONES
                    ft.DataCell(
                        ft.TextField(
                            value=row[2],
                            on_change=lambda e, row_idx=idx: on_repetitions_change(e, row_idx),
                            keyboard_type=ft.KeyboardType.NUMBER,
                            input_filter=ft.InputFilter(allow=True, regex_string=r"^[1-9]\d*$"),
                            dense=True,
                            border=ft.InputBorder.UNDERLINE,
                            border_radius=8,
                            filled=True,
                            bgcolor=INPUT_BG,
                            text_align=ft.TextAlign.CENTER,
                            hint_text="1-10",
                            text_size=10,
                            content_padding=ft.padding.symmetric(horizontal=4, vertical=2),
                        ),
                    ),
                    
                    # 🔥 CAUDAL MÁXIMO
                    ft.DataCell(
                        ft.Container(
                            ft.Text(
                                row[3] if row[3] else "0",
                                weight="bold",
                                color=ft.Colors.BLUE_700,
                                text_align=ft.TextAlign.CENTER,
                                size=10,
                            ),
                            alignment=ft.alignment.center,
                            padding=ft.padding.all(2),
                            bgcolor=ft.Colors.BLUE_50,
                            border_radius=6,
                            height=None
                        ),
                    ),
                    
                    # 🔥 CAUDAL MÍNIMO
                    ft.DataCell(
                        ft.Container(
                            ft.Text(
                                row[4] if row[4] else "0",
                                weight="bold",
                                color=ft.Colors.GREEN_700,
                                text_align=ft.TextAlign.CENTER,
                                size=10,
                            ),
                            alignment=ft.alignment.center,
                            padding=ft.padding.all(2),
                            bgcolor=ft.Colors.GREEN_50,
                            border_radius=6,
                        ),
                    ),
                    
                    # 🔥 VOLUMEN - SOLO NÚMEROS ENTEROS Y CÁLCULO AL PRESIONAR ENTER
                    ft.DataCell(
                        ft.TextField(
                            value=row[5] if row[5] and row[5] != "0" else "",
                            on_submit=lambda e, row_idx=idx: on_volume_submit(e, row_idx),  # 🔥 CAMBIO: on_submit EN VEZ DE on_change
                            keyboard_type=ft.KeyboardType.NUMBER,
                            input_filter=ft.InputFilter(allow=True, regex_string=r"^[1-9]\d*$"),  # 🔥 SOLO NÚMEROS ENTEROS POSITIVOS
                            dense=True,
                            border=ft.InputBorder.UNDERLINE,
                            border_radius=6,
                            filled=True,
                            bgcolor=ft.Colors.PURPLE_50,
                            text_align=ft.TextAlign.CENTER,
                            hint_text="L (presiona Enter)",  # 🔥 INDICAR QUE PRESIONE ENTER
                            text_size=10,
                            text_style=ft.TextStyle(weight="bold", color=ft.Colors.PURPLE_700),
                            content_padding=ft.padding.symmetric(horizontal=4, vertical=2),
                        ),
                    ),
                    
                    # 🔥 TIEMPO
                    ft.DataCell(
                        ft.Container(
                            ft.Text(
                                row[6] if row[6] and row[6] != "0:00" else "--:--",
                                weight="bold",
                                color=ft.Colors.ORANGE_700,
                                text_align=ft.TextAlign.CENTER,
                                size=10,
                            ),
                            alignment=ft.alignment.center,
                            padding=ft.padding.all(2),
                            bgcolor=ft.Colors.ORANGE_50,
                            border_radius=6,
                        ),
                    ),
                    
                    # 🔥 ESTADO
                    ft.DataCell(
                        ft.Container(
                            ft.Text(
                                status_text,
                                color=ft.Colors.WHITE,
                                weight="bold",
                                size=9,
                                text_align=ft.TextAlign.CENTER
                            ),
                            bgcolor=status_color,
                            padding=ft.padding.symmetric(horizontal=6, vertical=2),
                            border_radius=6,
                            alignment=ft.alignment.center,
                        ),
                    ),
                    
                    # 🔥 BOTÓN ELIMINAR
                    ft.DataCell(
                        ft.IconButton(
                            icon=ft.Icons.DELETE,
                            tooltip="Eliminar configuración",
                            icon_color=ft.Colors.RED_400,
                            icon_size=16,
                            on_click=lambda e, idx=idx: remove_configuration(idx),
                        ),
                    ),
                ]))
            
            data_table.rows = data_rows
            print(f"[TEST_CONFIG] 🔄 Tabla actualizada con {len(data_rows)} configuraciones")
            
            if hasattr(data_table, 'page') and data_table.page is not None:
                data_table.update()
            
        except Exception as e:
            print(f"[TEST_CONFIG] ❌ Error actualizando tabla: {e}")

    def add_configuration(e=None):
        """Agrega una nueva configuración de prueba"""
        print(f"[TEST_CONFIG] ➕ Agregando nueva configuración")
        # 🔥 SIN VOLUMEN INICIAL - COMPLETAMENTE VACÍO
        rows.append([str(len(rows) + 1), "Escoja una opción", "1", "0", "0", "", "0:00", "Pendiente"])
        update_table()

    def remove_configuration(idx):
        """Elimina una configuración de prueba"""
        if len(rows) > 1 and idx < len(rows):
            print(f"[TEST_CONFIG] 🗑️ Eliminando configuración {idx}")
            rows.pop(idx)
            # Renumerar las filas
            for i, row in enumerate(rows):
                row[0] = str(i + 1)
            update_table()
        else:
            print(f"[TEST_CONFIG] ⚠️ No se puede eliminar configuración {idx}")

    def on_test_type_change(e, row_idx):
        """Maneja cambios en el tipo de prueba"""
        if row_idx < len(rows):
            rows[row_idx][1] = e.control.value
            print(f"[TEST_CONFIG] 🔄 Tipo de prueba cambiado en fila {row_idx}: {e.control.value}")
            
            # 🔥 RECALCULAR TIEMPO SI YA HAY VOLUMEN
            if rows[row_idx][5] and int(rows[row_idx][5]) > 0:
                volume = int(rows[row_idx][5])
                time_formatted, time_decimal = calculate_time_from_volume(e.control.value, volume)
                rows[row_idx][6] = time_formatted
                
            update_table()

    def on_repetitions_change(e, row_idx):
        """Maneja cambios en el número de repeticiones"""
        if row_idx < len(rows):
            try:
                repetitions = int(e.control.value) if e.control.value else 1
                repetitions = max(1, min(10, repetitions))
                rows[row_idx][2] = str(repetitions)
                print(f"[TEST_CONFIG] 🔄 Repeticiones cambiadas en fila {row_idx}: {repetitions}")
                update_table()
            except ValueError:
                rows[row_idx][2] = "1"
                e.control.value = "1"

    def on_volume_submit(e, row_idx):
        """Maneja el envío del volumen al presionar Enter y recalcula el tiempo"""
        if row_idx < len(rows):
            try:
                # 🔥 MANEJAR CAMPO VACÍO
                volume_str = e.control.value.strip()
                if not volume_str:
                    rows[row_idx][5] = ""
                    rows[row_idx][6] = "0:00"
                    update_table()
                    print(f"[TEST_CONFIG] 🔄 Volumen vacío en fila {row_idx}")
                    return
                
                # 🔥 CONVERTIR A ENTERO
                volume = int(volume_str)
                if volume <= 0:
                    print(f"[TEST_CONFIG] ⚠️ Volumen debe ser mayor a 0: {volume}")
                    e.control.error_text = "Debe ser mayor a 0"
                    e.control.update()
                    return
                
                # 🔥 LIMPIAR ERROR
                e.control.error_text = None
                rows[row_idx][5] = str(volume)
                
                # 🔥 RECALCULAR EL TIEMPO BASADO EN EL NUEVO VOLUMEN
                test_type = rows[row_idx][1]
                if test_type != "Escoja una opción" and volume > 0:
                    time_formatted, time_decimal = calculate_time_from_volume(test_type, volume)
                    rows[row_idx][6] = time_formatted
                    print(f"[TEST_CONFIG] ✅ Volumen confirmado en fila {row_idx}: {volume}L -> Tiempo: {time_formatted}")
                else:
                    rows[row_idx][6] = "0:00"
                    print(f"[TEST_CONFIG] ⚠️ No se puede calcular tiempo: test_type='{test_type}', volume={volume}")
                
                update_table()
                
            except ValueError:
                print(f"[TEST_CONFIG] ❌ Valor de volumen inválido: {e.control.value}")
                e.control.error_text = "Solo números enteros"
                e.control.update()

    def show_test_sequence(e):
        """Muestra la secuencia de pruebas que se realizará"""
        configurations = get_test_configurations()
        
        if not configurations:
            sequence_text = "⚠️ No hay pruebas configuradas"
        else:
            sequence_text = "📋 Secuencia de Pruebas:\n\n"
            total_time_decimal = 0
            for i, config in enumerate(configurations, 1):
                sequence_text += f"{i}. {config['test_name']} "
                if config['total_repetitions'] > 1:
                    sequence_text += f"(Rep. {config['repetition']}/{config['total_repetitions']})"
                sequence_text += f" - Vol: {config['volume']}L - {config['time_formatted']}\n"
                total_time_decimal += config['estimated_time']
            
            # 🔥 CONVERTIR TIEMPO TOTAL A FORMATO LEGIBLE
            total_minutes = int(total_time_decimal)
            total_seconds = int((total_time_decimal - total_minutes) * 60)
            total_time_formatted = f"{total_minutes}:{total_seconds:02d}"
            
            sequence_text += f"\n📊 Total: {len(configurations)} pruebas"
            sequence_text += f"\n📦 Volumen total: {sum(c['volume'] for c in configurations)} litros"  # 🔥 SIN DECIMALES
            sequence_text += f"\n⏱️ Tiempo estimado total: {total_time_formatted} ({total_time_decimal:.1f} min)"

        print(f"[TEST_CONFIG] 📋 Secuencia generada:")
        for config in configurations:
            print(f"  - {config['test_name']} ({config['volume']}L, {config['time_formatted']})")

        # Mostrar en diálogo
        def close_dialog(e):
            dialog.open = False
            if hasattr(dialog, 'page') and dialog.page is not None:
                dialog.page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("📋 Secuencia de Pruebas"),
            content=ft.Text(sequence_text, selectable=True),
            actions=[ft.TextButton("Cerrar", on_click=close_dialog)],
        )
        
        if hasattr(main_column, 'page') and main_column.page is not None:
            main_column.page.overlay.append(dialog)
            dialog.open = True
            main_column.page.update()

    def validate_configurations():
        """Valida que las configuraciones sean correctas"""
        errors = []
        valid_configs = []
        
        for idx, row in enumerate(rows):
            if row[1] == "Escoja una opción":
                errors.append(f"Fila {idx + 1}: Debe seleccionar un tipo de prueba")
            elif not row[2].isdigit() or int(row[2]) < 1:
                errors.append(f"Fila {idx + 1}: Número de repeticiones inválido")
            elif not row[5] or int(row[5]) <= 0:  # 🔥 VALIDAR COMO ENTERO
                errors.append(f"Fila {idx + 1}: Debe ingresar un volumen válido (mayor a 0)")
            else:
                valid_configs.append(row)
        
        return errors, valid_configs

    # 🔥 DIV DE CAUDALES CALCULADOS (ENCIMA DE LA TABLA)
    flow_display = ft.Container(
        content=ft.Column([
            ft.Text("📊 Caudales Calculados", size=14, weight="bold", color=ft.Colors.BLUE_700),
            ft.ResponsiveRow([
                ft.Container(
                    ft.Column([
                        ft.Text("Q1", size=12, weight="bold", color=ft.Colors.BLUE_600),
                        q1_text,
                    ], horizontal_alignment="center"),
                    col={"xs": 6, "sm": 3},
                    padding=5,
                ),
                ft.Container(
                    ft.Column([
                        ft.Text("Q2", size=12, weight="bold", color=ft.Colors.GREEN_600),
                        q2_text,
                    ], horizontal_alignment="center"),
                    col={"xs": 6, "sm": 3},
                    padding=5,
                ),
                ft.Container(
                    ft.Column([
                        ft.Text("Q3 (Nominal)", size=12, weight="bold", color=ft.Colors.ORANGE_600),
                        q3_text,
                    ], horizontal_alignment="center"),
                    col={"xs": 6, "sm": 3},
                    padding=5,
                ),
                ft.Container(
                    ft.Column([
                        ft.Text("Q4", size=12, weight="bold", color=ft.Colors.PURPLE_600),
                        q4_text,
                    ], horizontal_alignment="center"),
                    col={"xs": 6, "sm": 3},
                    padding=5,
                ),
            ], spacing=5),
        ], spacing=10),
        padding=15,
        border_radius=8,
        bgcolor=ft.Colors.GREY_50,
        border=ft.border.all(1, ft.Colors.GREY_300),
        margin=ft.margin.only(bottom=15),
    )

    # 🔥 CONTAINER RESPONSIVO DE LA TABLA CON SCROLL HORIZONTAL
    table_container = ft.Container(
        content=ft.Row([
            ft.Container(
                content=data_table,
                alignment=ft.alignment.center,
                expand=True,
            )
        ], 
        scroll=ft.ScrollMode.AUTO,
        ),
        height=None,
        border_radius=12,
        border=ft.border.all(1, ft.Colors.GREY_300),
        bgcolor=ft.Colors.GREY_50,
        padding=10,
        alignment=ft.alignment.center,
    )

    # 🔥 LAYOUT PRINCIPAL RESPONSIVO
    main_column = ft.Column([
        ft.Container(
            content=ft.Text("Configuración de Pruebas", size=18, weight="bold", text_align="center"),
            alignment=ft.alignment.center,
        ),
        
        ft.Container(
            content=ft.Row([
                ft.ElevatedButton(
                    "Agregar", 
                    icon=ft.Icons.ADD, 
                    on_click=add_configuration, 
                    width=120,
                    height=35,
                ),
                ft.ElevatedButton(
                    "Ver Secuencia", 
                    icon=ft.Icons.LIST, 
                    on_click=show_test_sequence, 
                    width=140,
                    height=35,
                ),
            ], 
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
            ),
            alignment=ft.alignment.center,
        ),
        
        flow_display,
        
        ft.Container(
            content=table_container,
            alignment=ft.alignment.center,
            expand=True,
        ),
        
    ], 
    expand=True,
    alignment=ft.MainAxisAlignment.START,
    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    spacing=15,
    )

    # Agregar una configuración inicial
    add_configuration()

    # Exponer funciones públicas
    main_column.get_test_configurations = get_test_configurations
    main_column.validate_configurations = validate_configurations
    main_column.add_configuration = add_configuration
    main_column.update_flow_values = update_flow_values

    return main_column