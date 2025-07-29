import flet as ft

DROPDOWN_OPTIONS = ["Escoja una opción", "Q1", "Q2", "Q3", "Q4"]
INPUT_BG = "#f3f4f6"

def test_configuration_table(q1=0, q2=0, q3=0, q4=0):
    """Tabla para configurar las pruebas a realizar"""
    
    #  ESTRUCTURA DE FILAS: [#, Prueba, Repeticiones, Caudal_Max, Caudal_Min, Volumen, Tiempo_Aprox, Estado]
    rows = []
    
    #  GUARDAR VALORES DE CAUDALES CALCULADOS
    flow_values = {"Q1": q1, "Q2": q2, "Q3": q3, "Q4": q4}
    
    print(f"[TEST_CONFIG] 🚀 Inicializando tabla con caudales: Q1={q1}, Q2={q2}, Q3={q3}, Q4={q4}")

    #  CREAR ELEMENTOS DE TEXTO PARA LOS CAUDALES (CON REFERENCIAS)
    q1_text = ft.Text(f"{q1:.2f} L/h", size=14, weight="bold", color=ft.Colors.BLUE_800)
    q2_text = ft.Text(f"{q2:.2f} L/h", size=14, weight="bold", color=ft.Colors.GREEN_800)
    q3_text = ft.Text(f"{q3:.2f} L/h", size=14, weight="bold", color=ft.Colors.ORANGE_800)
    q4_text = ft.Text(f"{q4:.2f} L/h", size=14, weight="bold", color=ft.Colors.PURPLE_800)

    data_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("#", text_align=ft.TextAlign.CENTER, size=12)),  # Ancho automático
            ft.DataColumn(ft.Text("Tipo de Prueba", text_align=ft.TextAlign.CENTER, size=12)),
            ft.DataColumn(ft.Text("Repeticiones", text_align=ft.TextAlign.CENTER, size=12)),
            ft.DataColumn(ft.Text("Caudal Máx.", text_align=ft.TextAlign.CENTER, size=12)),
            ft.DataColumn(ft.Text("Caudal Mín.", text_align=ft.TextAlign.CENTER, size=12)),
            ft.DataColumn(ft.Text("Volumen", text_align=ft.TextAlign.CENTER, size=12)),
            ft.DataColumn(ft.Text("Tiempo", text_align=ft.TextAlign.CENTER, size=12)),
            ft.DataColumn(ft.Text("Acción", text_align=ft.TextAlign.CENTER, size=12)),
        ],
        rows=[],
        column_spacing=50,
        border=ft.border.all(1, ft.Colors.GREY_300),
        divider_thickness=1,
        heading_row_color=ft.Colors.BLUE_100,
        heading_row_height=70,
        data_row_max_height=70,
        height=None,
        horizontal_lines=None,
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
            
            #  USAR EL CAUDAL MÁXIMO PARA EL CÁLCULO
            qmax = round(base_flow * 1.1, 2)
            
            if qmax <= 0:
                print(f"[TEST_CONFIG] ⚠️ Caudal máximo calculado es 0 o inválido: {qmax}")
                return "0:00", 0
            
            #  REGLA DE 3: Si caudal_max = 60 minutos, entonces volumen = X minutos
            time_decimal = (volume_liters * 60) / qmax
            
            #  CONVERTIR DECIMALES A MINUTOS Y SEGUNDOS
            minutes = int(time_decimal)
            decimal_part = time_decimal - minutes
            seconds = int(decimal_part * 60)
            
            #  FORMATEAR COMO "MM:SS"
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
                #  CALCULAR MÍNIMOS Y MÁXIMOS SEGÚN LAS FÓRMULAS
                qmin = round(0.95 * base_flow, 2)
                qmax = round(base_flow * 1.1, 2)
                
                #  SOLO CALCULAR TIEMPO SI SE PROPORCIONA VOLUMEN
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
        
        #  ACTUALIZAR LOS TEXTOS DE LOS CAUDALES
        q1_text.value = f"{new_q1:.2f} L/h"
        q2_text.value = f"{new_q2:.2f} L/h"
        q3_text.value = f"{new_q3:.2f} L/h"
        q4_text.value = f"{new_q4:.2f} L/h"
        
        print(f"[TEST_CONFIG] 🔄 Actualizando caudales: Q1={new_q1}, Q2={new_q2}, Q3={new_q3}, Q4={new_q4}")
        
        #  RECALCULAR TIEMPOS PARA TODAS LAS FILAS QUE TENGAN VOLUMEN
        for idx, row in enumerate(rows):
            test_type = row[1]
            if test_type != "Escoja una opción" and row[5] and int(row[5]) > 0:
                volume = int(row[5])
                time_formatted, time_decimal = calculate_time_from_volume(test_type, volume)
                rows[idx][6] = time_formatted
                print(f"[TEST_CONFIG] 🔄 Recalculando tiempo para fila {idx}: {volume}L -> {time_formatted}")
        
        #  ACTUALIZAR LA TABLA Y LA UI
        update_table()
        
        #  FORZAR UPDATE DE LOS TEXTOS
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
                    
                    #  EXTRAER TIEMPO DECIMAL DEL FORMATO "MM:SS"
                    time_str = row[6]
                    try:
                        if ":" in time_str:
                            minutes, seconds = time_str.split(":")
                            time_decimal = int(minutes) + int(seconds) / 60
                        else:
                            time_decimal = float(time_str) if time_str.replace(".", "").isdigit() else 0
                    except Exception as e:
                        print(f"[TEST_CONFIG] ❌ Error procesando tiempo {time_str}: {e}")
                        time_decimal = 0
                    
                    configurations.append({
                        "test_name": test_name,
                        "test_type": test_type,
                        "repetition": rep + 1,
                        "total_repetitions": repetitions,
                        "config_row": idx,
                        "max_flow": float(row[3]) if row[3] else 0,
                        "min_flow": float(row[4]) if row[4] else 0,
                        "volume": int(row[5]) if row[5] else 0,
                        "estimated_time": time_decimal,
                        "time_formatted": time_str
                    })
        
        return configurations

    def on_volume_blur(e, row_idx):
        """Maneja cuando el campo de volumen pierde el foco - ACTUALIZA SOLO TIEMPO"""
        if row_idx < len(rows):
            try:
                #  MANEJAR CAMPO VACÍO
                volume_str = e.control.value.strip()
                if not volume_str:
                    rows[row_idx][5] = ""
                    rows[row_idx][6] = "0:00"
                    #  ACTUALIZAR SOLO EL TEXTO DE TIEMPO SIN REFRESCAR TABLA
                    update_time_for_row(row_idx, "0:00")
                    print(f"[TEST_CONFIG] 🔄 Volumen vacío en fila {row_idx}")
                    return
                
                #  CONVERTIR A ENTERO
                volume = int(volume_str)
                if volume <= 0:
                    print(f"[TEST_CONFIG] ⚠️ Volumen debe ser mayor a 0: {volume}")
                    e.control.error_text = "Debe ser mayor a 0"
                    #  VERIFICAR QUE EL CONTROL ESTÉ EN LA PÁGINA ANTES DE ACTUALIZAR
                    try:
                        if hasattr(e.control, 'page') and e.control.page is not None:
                            e.control.update()
                    except (AssertionError, AttributeError) as update_error:
                        print(f"[TEST_CONFIG] ⚠️ No se pudo actualizar control (ya no está en página): {update_error}")
                    return
                
                #  LIMPIAR ERROR
                e.control.error_text = None
                rows[row_idx][5] = str(volume)
                
                #  RECALCULAR EL TIEMPO BASADO EN EL NUEVO VOLUMEN
                test_type = rows[row_idx][1]
                if test_type != "Escoja una opción" and volume > 0:
                    time_formatted, time_decimal = calculate_time_from_volume(test_type, volume)
                    rows[row_idx][6] = time_formatted
                    #  ACTUALIZAR SOLO EL TIEMPO SIN REFRESCAR TABLA COMPLETA
                    update_time_for_row(row_idx, time_formatted)
                    print(f"[TEST_CONFIG]  Volumen confirmado en fila {row_idx}: {volume}L -> Tiempo: {time_formatted}")
                else:
                    rows[row_idx][6] = "0:00"
                    update_time_for_row(row_idx, "0:00")
                    print(f"[TEST_CONFIG] ⚠️ No se puede calcular tiempo: test_type='{test_type}', volume={volume}")
                
                #  ACTUALIZAR SOLO EL CONTROL ACTUAL CON VERIFICACIÓN SEGURA
                try:
                    if hasattr(e.control, 'page') and e.control.page is not None:
                        e.control.update()
                except (AssertionError, AttributeError) as update_error:
                    print(f"[TEST_CONFIG] ⚠️ No se pudo actualizar control (ya no está en página): {update_error}")
                
            except ValueError:
                print(f"[TEST_CONFIG] ❌ Valor de volumen inválido: {e.control.value}")
                e.control.error_text = "Solo números enteros"
                #  VERIFICACIÓN SEGURA PARA UPDATE
                try:
                    if hasattr(e.control, 'page') and e.control.page is not None:
                        e.control.update()
                except (AssertionError, AttributeError) as update_error:
                    print(f"[TEST_CONFIG] ⚠️ No se pudo actualizar control de error: {update_error}")
            except Exception as general_error:
                print(f"[TEST_CONFIG] ❌ Error general en on_volume_blur: {general_error}")

    def update_time_for_row(row_idx, new_time):
        """ MEJORADA: Actualiza solo el tiempo de una fila específica con verificación segura"""
        try:
            if row_idx < len(data_table.rows):
                #  BUSCAR LA CELDA DE TIEMPO (índice 6) Y ACTUALIZAR SU TEXTO
                time_cell = data_table.rows[row_idx].cells[6]  # Columna de tiempo
                if hasattr(time_cell, 'content') and hasattr(time_cell.content, 'content'):
                    #  ACTUALIZAR EL TEXTO DENTRO DEL CONTAINER
                    time_text = time_cell.content.content
                    if hasattr(time_text, 'value'):
                        time_text.value = new_time if new_time and new_time != "0:00" else "--:--"
                        time_text.color = ft.Colors.ORANGE_700 if new_time != "0:00" else ft.Colors.GREY_500
                        
                        #  ACTUALIZAR SOLO ESTE CONTROL CON VERIFICACIÓN SEGURA
                        try:
                            if hasattr(time_text, 'page') and time_text.page is not None:
                                time_text.update()
                                print(f"[TEST_CONFIG] ⏱️ Tiempo actualizado para fila {row_idx}: {new_time}")
                                return True
                            else:
                                print(f"[TEST_CONFIG] ⚠️ time_text no está en página para fila {row_idx}")
                        except (AssertionError, AttributeError) as update_error:
                            print(f"[TEST_CONFIG] ⚠️ No se pudo actualizar tiempo (control no en página): {update_error}")
                            return False
            
            print(f"[TEST_CONFIG] ⚠️ No se pudo actualizar tiempo para fila {row_idx}")
            return False
            
        except Exception as e:
            print(f"[TEST_CONFIG] ❌ Error actualizando tiempo para fila {row_idx}: {e}")
            return False
    
    def safe_control_update(control, operation_name="update"):
        """ NUEVA FUNCIÓN: Actualiza un control de forma segura"""
        try:
            if control and hasattr(control, 'page') and control.page is not None:
                control.update()
                return True
            else:
                print(f"[TEST_CONFIG] ⚠️ Control no disponible para {operation_name}")
                return False
        except (AssertionError, AttributeError) as e:
            print(f"[TEST_CONFIG] ⚠️ Error en {operation_name}: {e}")
            return False
        except Exception as e:
            print(f"[TEST_CONFIG] ❌ Error general en {operation_name}: {e}")
            return False

    def on_volume_submit(e, row_idx):
        """Maneja el envío del volumen al presionar Enter - IGUAL QUE BLUR"""
        #  LLAMAR A LA MISMA FUNCIÓN QUE BLUR PARA CONSISTENCIA
        on_volume_blur(e, row_idx)

    def update_table():
        """Actualiza la tabla con los datos actuales"""
        try:
            print(f"[TEST_CONFIG] 🔄 Actualizando tabla con {len(rows)} filas")
            data_rows = []
            
            for idx, row in enumerate(rows):
                repetitions = int(row[2]) if row[2].isdigit() else 0
                test_type = row[1]
                
                #  CALCULAR SOLO CAUDALES MÁXIMOS Y MÍNIMOS (NO VOLUMEN NI TIEMPO)
                if test_type != "Escoja una opción" and repetitions > 0:
                    #  PRESERVAR VOLUMEN EXISTENTE
                    current_volume = int(row[5]) if row[5] and row[5] != "0" else None
                    values = calculate_flow_values(test_type, repetitions, current_volume)
                    rows[idx][3] = str(values["max_flow"])
                    rows[idx][4] = str(values["min_flow"])
                    #  NO SOBRESCRIBIR VOLUMEN
                    #  NO SOBRESCRIBIR TIEMPO A MENOS QUE SE HAYA CALCULADO NUEVO
                    if values["time"] != "0:00":
                        rows[idx][6] = values["time"]
                

                data_rows.append(ft.DataRow(
                    cells=[
                        #  NÚMERO DE FILA
                        ft.DataCell(
                            ft.Container(
                                ft.Text(str(idx + 1), 
                                text_align=ft.TextAlign.CENTER, 
                                size=10
                            ),
                            padding=ft.padding.all(4),
                        )),
                        
                        #  DROPDOWN DE TIPO DE PRUEBA
                        ft.DataCell(
                            ft.Container(
                                ft.Dropdown(
                                    options=[ft.dropdown.Option(opt) for opt in DROPDOWN_OPTIONS],
                                    value=row[1],
                                    on_change=lambda e, row_idx=idx: on_test_type_change(e, row_idx),
                                    dense=True,
                                    border_radius=8,
                                    bgcolor=INPUT_BG,
                                    text_size=10,
                                    content_padding=ft.padding.symmetric(horizontal=8, vertical=4)
                                ),
                                alignment=ft.alignment.center,
                                margin=ft.margin.all(10)
                            )
                        ),
                        
                        #  CAMPO DE REPETICIONES
                        ft.DataCell(
                            ft.Container(
                                ft.TextField(
                                    value=row[2],
                                    on_blur=lambda e, row_idx=idx: on_repetitions_blur(e, row_idx),  #  SOLO AL PERDER FOCO
                                    keyboard_type=ft.KeyboardType.NUMBER,
                                    #  SIN input_filter - LIBERTAD TOTAL PARA ESCRIBIR
                                    dense=True,
                                    border=ft.InputBorder.UNDERLINE,
                                    border_radius=8,
                                    filled=True,
                                    bgcolor=INPUT_BG,
                                    text_align=ft.TextAlign.CENTER,
                                    text_size=15,
                                    content_padding=ft.padding.symmetric(horizontal=4, vertical=6),
                                    width=90
                                ),
                                padding=ft.padding.symmetric(horizontal=2),
                                alignment=ft.alignment.center,
                            )
                        ),
                        
                        #  CAUDAL MÁXIMO
                        ft.DataCell(
                            ft.Container(
                                ft.Text(
                                    row[3] if row[3] else "0",
                                    weight="bold",
                                    color=ft.Colors.BLUE_700,
                                    text_align=ft.TextAlign.CENTER,
                                    size=15,
                                ),
                                padding=ft.padding.all(4),
                                alignment=ft.alignment.center,
                                border_radius=6,
                                width=None
                            )
                        ),
                        
                        #  CAUDAL MÍNIMO
                        ft.DataCell(
                            ft.Container(
                                ft.Text(
                                    row[4] if row[4] else "0",
                                    weight="bold",
                                    color=ft.Colors.GREEN_700,
                                    text_align=ft.TextAlign.CENTER,
                                    size=15,
                                ),
                                padding=ft.padding.all(4),
                                alignment=ft.alignment.center,
                                border_radius=6,
                                width=None
                            )
                        ),
                        
                        #  VOLUMEN - AGREGADO on_blur
                        ft.DataCell(
                            ft.Container(
                                ft.TextField(
                                    value=row[5] if row[5] and row[5] != "0" else "",
                                    on_submit=lambda e, row_idx=idx: on_volume_submit(e, row_idx),
                                    on_blur=lambda e, row_idx=idx: on_volume_blur(e, row_idx),  #  NUEVO: AL PERDER FOCO
                                    keyboard_type=ft.KeyboardType.NUMBER,
                                    input_filter=ft.InputFilter(allow=True, regex_string=r"^[1-9]\d*$"),
                                    dense=True,
                                    border=ft.InputBorder.UNDERLINE,
                                    border_radius=6,
                                    filled=True,
                                    bgcolor=ft.Colors.PURPLE_50,
                                    text_align=ft.TextAlign.CENTER,
                                    hint_text="Litros",
                                    text_size=15,
                                    text_style=ft.TextStyle(weight="bold", color=ft.Colors.PURPLE_700),
                                    content_padding=ft.padding.symmetric(horizontal=4, vertical=2),
                                    width=100
                                ),
                                alignment=ft.alignment.center,
                            )
                        ),
                        
                        #  TIEMPO - CON REFERENCIAS PARA ACTUALIZACIÓN INDIVIDUAL
                        ft.DataCell(
                            ft.Container(
                                ft.Text(
                                    row[6] if row[6] and row[6] != "0:00" else "--:--",
                                    weight="bold",
                                    color=ft.Colors.ORANGE_700 if row[6] != "0:00" else ft.Colors.GREY_500,
                                    text_align=ft.TextAlign.CENTER,
                                    size=15,
                                ),
                                padding=ft.padding.all(4),
                                alignment=ft.alignment.center,
                                border_radius=6,
                                width=None
                            )
                        ),
                        
                        #  BOTÓN ELIMINAR
                        ft.DataCell(
                            ft.Container(
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINED,
                                    tooltip="Eliminar",
                                    icon_color=ft.Colors.RED_400,
                                    icon_size=16,
                                    on_click=lambda e, idx=idx: remove_configuration(idx),
                                ),
                                padding=ft.padding.all(2),
                                alignment=ft.alignment.center,
                            )
                        ),
                    ]
                ))
            
            data_table.rows = data_rows
            print(f"[TEST_CONFIG]  Tabla actualizada con {len(data_rows)} configuraciones")
            
            if hasattr(data_table, 'page') and data_table.page is not None:
                data_table.update()
            
        except Exception as e:
            print(f"[TEST_CONFIG] ❌ Error actualizando tabla: {e}")

    def add_configuration(e=None):
        """Agrega una nueva configuración de prueba"""
        print(f"[TEST_CONFIG] ➕ Agregando nueva configuración")
        #  SIN VOLUMEN INICIAL - COMPLETAMENTE VACÍO
        rows.append([str(len(rows) + 1), "Escoja una opción", "1", "0", "0", "", "0:00", "Pendiente"])
        update_table()

    def remove_configuration(idx):
        """Elimina una configuración de prueba"""
        if len(rows) > 1 and idx < len(rows):
            print(f"[TEST_CONFIG] ➖ Eliminando configuración {idx}")
            rows.pop(idx)
            # Renumerar las filas
            for i, row in enumerate(rows):
                row[0] = str(i + 1)
            update_table()
        else:
            print(f"[TEST_CONFIG] ⚠️ No se puede eliminar configuración {idx}")

    def on_test_type_change(e, row_idx):
        """MEJORADA: Maneja cambios en el tipo de prueba - ACTUALIZACIÓN INTELIGENTE"""
        if row_idx < len(rows):
            old_test_type = rows[row_idx][1]
            new_test_type = e.control.value
            rows[row_idx][1] = new_test_type
            
            print(f"[TEST_CONFIG] 🔄 Tipo de prueba cambiado en fila {row_idx}: {old_test_type} -> {new_test_type}")
            
            #  RECALCULAR TIEMPO SI YA HAY VOLUMEN
            if rows[row_idx][5] and int(rows[row_idx][5]) > 0:
                volume = int(rows[row_idx][5])
                if new_test_type != "Escoja una opción":
                    time_formatted, time_decimal = calculate_time_from_volume(new_test_type, volume)
                    rows[row_idx][6] = time_formatted
                    
                    #  ACTUALIZAR SOLO EL TIEMPO SIN REFRESCAR TABLA
                    update_time_for_row(row_idx, time_formatted)
                    print(f"[TEST_CONFIG] 🧮 Cálculo tiempo: {volume}L / {new_test_type} = {time_formatted}")
                else:
                    rows[row_idx][6] = "0:00"
                    update_time_for_row(row_idx, "0:00")
            
            #  SOLO ACTUALIZAR CAUDALES DE ESTA FILA
            if new_test_type != "Escoja una opción":
                current_volume = int(rows[row_idx][5]) if rows[row_idx][5] and rows[row_idx][5] != "0" else None
                values = calculate_flow_values(new_test_type, int(rows[row_idx][2]), current_volume)
                rows[row_idx][3] = str(values["max_flow"])
                rows[row_idx][4] = str(values["min_flow"])
                
                #  ACTUALIZAR SOLO LAS CELDAS DE CAUDAL DE ESTA FILA
                update_flow_cells_for_row(row_idx, values["max_flow"], values["min_flow"])
            else:
                rows[row_idx][3] = "0"
                rows[row_idx][4] = "0"
                update_flow_cells_for_row(row_idx, 0, 0)

    def update_flow_cells_for_row(row_idx, max_flow, min_flow):
        """ MEJORADA: Actualiza solo las celdas de caudal de una fila específica con verificación segura"""
        try:
            if row_idx < len(data_table.rows):
                #  CAUDAL MÁXIMO (columna 3)
                max_flow_cell = data_table.rows[row_idx].cells[3]
                if hasattr(max_flow_cell, 'content') and hasattr(max_flow_cell.content, 'content'):
                    max_text = max_flow_cell.content.content
                    if hasattr(max_text, 'value'):
                        max_text.value = str(max_flow)
                        safe_control_update(max_text, f"max_flow_fila_{row_idx}")
                
                #  CAUDAL MÍNIMO (columna 4)
                min_flow_cell = data_table.rows[row_idx].cells[4]
                if hasattr(min_flow_cell, 'content') and hasattr(min_flow_cell.content, 'content'):
                    min_text = min_flow_cell.content.content
                    if hasattr(min_text, 'value'):
                        min_text.value = str(min_flow)
                        safe_control_update(min_text, f"min_flow_fila_{row_idx}")
                
                print(f"[TEST_CONFIG] 🔄 Caudales actualizados para fila {row_idx}: Max={max_flow}, Min={min_flow}")
                return True
            
            return False
            
        except Exception as e:
            print(f"[TEST_CONFIG] ❌ Error actualizando caudales para fila {row_idx}: {e}")
            return False

    def on_repetitions_blur(e, row_idx):
        """MEJORADA: Maneja cuando el campo de repeticiones pierde el foco - SIN REFRESCAR TABLA"""
        if row_idx < len(rows):
            try:
                #  SI ESTÁ VACÍO, PONER VALOR POR DEFECTO
                if not e.control.value.strip():
                    e.control.value = "1"
                    rows[row_idx][2] = "1"
                    print(f"[TEST_CONFIG] 🔄 Campo vacío en fila {row_idx}, usando valor por defecto: 1")
                else:
                    #  CONVERTIR A ENTERO Y VALIDAR
                    repetitions = int(e.control.value.strip())
                    
                    #  VALIDAR RANGO 1-100
                    if repetitions < 1:
                        repetitions = 1
                        e.control.value = "1"
                        e.control.error_text = "Mínimo 1"
                    elif repetitions > 100:
                        repetitions = 100
                        e.control.value = "100"
                        e.control.error_text = "Máximo 100"
                    else:
                        e.control.error_text = None
                    
                    rows[row_idx][2] = str(repetitions)
                    print(f"[TEST_CONFIG]  Repeticiones validadas en fila {row_idx}: {repetitions}")
                
                #  ACTUALIZAR SOLO EL CONTROL ACTUAL CON VERIFICACIÓN SEGURA
                safe_control_update(e.control, "repeticiones_blur")
                
            except ValueError:
                #  SI NO ES UN NÚMERO VÁLIDO, RESTAURAR A 1
                e.control.value = "1"
                rows[row_idx][2] = "1"
                e.control.error_text = "Solo números 1-100"
                print(f"[TEST_CONFIG] ❌ Valor inválido en repeticiones fila {row_idx}, restaurado a: 1")
                
                safe_control_update(e.control, "repeticiones_error")
            except Exception as general_error:
                print(f"[TEST_CONFIG] ❌ Error general en repeticiones_blur: {general_error}")

    def validate_configurations():
        """Valida que las configuraciones sean correctas"""
        errors = []
        valid_configs = []
        
        for idx, row in enumerate(rows):
            if row[1] == "Escoja una opción":
                errors.append(f"Fila {idx + 1}: Debe seleccionar un tipo de prueba")
            elif not row[2].isdigit() or int(row[2]) < 1:
                errors.append(f"Fila {idx + 1}: Número de repeticiones inválido")
            elif not row[5] or int(row[5]) <= 0:
                errors.append(f"Fila {idx + 1}: Debe ingresar un volumen válido (mayor a 0)")
            else:
                valid_configs.append(row)
        
        return errors, valid_configs

    #  DIV DE CAUDALES CALCULADOS (ENCIMA DE LA TABLA)
    flow_display = ft.Container(
        content=ft.Column([
            ft.Text("Caudales Calculados", size=14, weight="bold", color=ft.Colors.BLUE_700),
            ft.ResponsiveRow([
                ft.Container(
                    ft.Column([
                        ft.Row([
                            ft.Text("Q1:", size=12, weight="bold", color=ft.Colors.BLUE_600),
                            q1_text
                        ], alignment=ft.MainAxisAlignment.CENTER)
                    ], horizontal_alignment="center"),
                    col={"xs": 6, "sm": 3},
                    padding=5,
                ),
                ft.Container(
                    ft.Column([
                        ft.Row([
                            ft.Text("Q2:", size=12, weight="bold", color=ft.Colors.GREEN_600),
                            q2_text
                        ], alignment=ft.MainAxisAlignment.CENTER)
                    ], horizontal_alignment="center"),
                    col={"xs": 6, "sm": 3},
                    padding=5,
                ),
                ft.Container(
                    ft.Column([
                        ft.Row([
                            ft.Text("Q3 (Nominal):", size=12, weight="bold", color=ft.Colors.ORANGE_600),
                            q3_text
                        ], alignment=ft.MainAxisAlignment.CENTER)
                    ], horizontal_alignment="center"),
                    col={"xs": 6, "sm": 3},
                    padding=5,
                ),
                ft.Container(
                    ft.Column([
                        ft.Row([
                            ft.Text("Q4:", size=12, weight="bold", color=ft.Colors.PURPLE_600),
                            q4_text
                        ], alignment=ft.MainAxisAlignment.CENTER)
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

    #  CONTAINER RESPONSIVO DE LA TABLA CON SCROLL HORIZONTAL
    table_container = ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=data_table,
                    alignment=ft.alignment.top_center,
                    expand=True,
                )
            ],
            scroll=ft.ScrollMode.AUTO,
        ),
        height=400,
        border_radius=12,
        border=ft.border.all(1, ft.Colors.GREY_300),
        bgcolor=ft.Colors.GREY_50,
        padding=10,
    )
    
    # Layout principal responsivo
    main_column = ft.Column(
        [
            flow_display,
            
            #  BOTONES DE ACCIÓN - SOLO "AGREGAR"
            ft.Container(
                content=ft.Row(
                    [
                        ft.ElevatedButton(
                            "Agregar",
                            icon=ft.Icons.ADD,
                            on_click=add_configuration,
                            style=ft.ButtonStyle(
                                padding=ft.padding.symmetric(horizontal=16, vertical=8),
                            )
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=20,
                ),
                padding=ft.padding.only(bottom=15),
            ),
            
            # Contenedor de tabla con scroll
            ft.Container(
                content=table_container,
                expand=True,
                alignment=ft.alignment.top_center,
            ),
        ],
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        spacing=10,
    )

    # Agregar una configuración inicial
    add_configuration()

    # Exponer funciones públicas
    main_column.get_test_configurations = get_test_configurations
    main_column.validate_configurations = validate_configurations
    main_column.add_configuration = add_configuration
    main_column.update_flow_values = update_flow_values

    return main_column