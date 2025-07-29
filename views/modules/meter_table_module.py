import flet as ft

class MeterTableModule:
    def __init__(self):
        self.meters = []  # Lista de medidores: [{"serial": "123", "reading": ""}]
        
        # Botón para agregar fila
        self.add_button = ft.ElevatedButton(
            "Agregar Medidor",
            icon=ft.Icons.ADD,
            on_click=self.add_meter_row,
            bgcolor=ft.Colors.GREEN_600,
            color=ft.Colors.WHITE
        )
        
        # Tabla de medidores
        self.data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("#", text_align=ft.TextAlign.CENTER)),
                ft.DataColumn(ft.Text("Serial", text_align=ft.TextAlign.CENTER)),
                ft.DataColumn(ft.Text("Lectura de Ingreso", text_align=ft.TextAlign.CENTER)),
                ft.DataColumn(ft.Text("Acción", text_align=ft.TextAlign.CENTER)),
            ],
            rows=[],
            column_spacing=20,
            border=ft.border.all(1, ft.Colors.GREY_300),
            heading_row_color=ft.Colors.BLUE_100,
        )
        
        # Contenedor de la tabla con scroll
        self.table_container = ft.Container(
            content=self.data_table,
            height=300,
            width=None,
            border_radius=8,
            border=ft.border.all(1, ft.Colors.GREY_300),
            bgcolor=ft.Colors.GREY_50,
            padding=10,
        )

    def add_meter_row(self, e=None):
        """Agrega una nueva fila vacía a la tabla"""
        print(f"[METER_TABLE] Estado antes de agregar: {len(self.meters)} medidores")
        for i, meter in enumerate(self.meters):
            print(f"[METER_TABLE]   Fila {i}: Serial='{meter['serial']}', Reading='{meter['reading']}'")
        
        self.meters.append({
            "serial": "",
            "reading": ""
        })
        
        print(f"[METER_TABLE] Agregada nueva fila. Total: {len(self.meters)}")
        self.update_table()
        
        print(f"[METER_TABLE] Estado después de agregar:")
        for i, meter in enumerate(self.meters):
            print(f"[METER_TABLE]   Fila {i}: Serial='{meter['serial']}', Reading='{meter['reading']}'")

    def remove_meter(self, index):
        """Elimina un medidor de la lista"""
        if 0 <= index < len(self.meters):
            removed = self.meters.pop(index)
            print(f"[METER_TABLE] Eliminado medidor en índice {index}: {removed}")
            self.update_table()
        else:
            print(f"[METER_TABLE] Índice inválido para eliminar: {index}")

    def update_serial(self, index, new_serial):
        """Actualiza el serial de un medidor"""
        if 0 <= index < len(self.meters):
            old_serial = self.meters[index]["serial"]
            self.meters[index]["serial"] = new_serial.upper().strip()
            print(f"[METER_TABLE] Serial actualizado en fila {index}: '{old_serial}' -> '{new_serial}'")

    def update_reading(self, index, new_reading):
        """Actualiza la lectura de un medidor"""
        if 0 <= index < len(self.meters):
            old_reading = self.meters[index]["reading"]
            self.meters[index]["reading"] = new_reading.strip()
            print(f"[METER_TABLE] Lectura actualizada en fila {index}: '{old_reading}' -> '{new_reading}'")

    def update_table(self):
        """Actualiza la tabla con los datos actuales"""
        rows = []
        
        for i, meter in enumerate(self.meters):
            # Campo de serial
            serial_field = ft.TextField(
                value=meter["serial"],
                border=ft.InputBorder.UNDERLINE,
                filled=False,
                border_radius=0,
                border_color=ft.Colors.GREY_400,
                text_align=ft.TextAlign.CENTER,
                height=40,
                width=None,
                content_padding=10,
                text_style=ft.TextStyle(size=12),
                keyboard_type=ft.KeyboardType.TEXT,
                on_blur=lambda e, idx=i: self.update_serial(idx, e.control.value),
                hint_text="Serial del medidor"
            )
            
            # Campo de lectura
            reading_field = ft.TextField(
                value=meter["reading"],
                border=ft.InputBorder.UNDERLINE,
                filled=False,
                border_radius=0,
                text_align=ft.TextAlign.CENTER,
                width=None,
                height=40,
                keyboard_type=ft.KeyboardType.NUMBER,
                on_blur=lambda e, idx=i: self.update_reading(idx, e.control.value),
                text_style=ft.TextStyle(size=12),
                content_padding=10,
                hint_text="0.000"
            )
            
            # Botón eliminar
            delete_button = ft.IconButton(
                icon=ft.Icons.DELETE_OUTLINE,
                icon_color=ft.Colors.RED_400,
                icon_size=18,
                tooltip="Eliminar medidor",
                on_click=lambda e, idx=i: self.remove_meter(idx)
            )
            
            row = ft.DataRow(
                cells=[
                    ft.DataCell(ft.Container(ft.Text(str(i + 1), text_align=ft.TextAlign.CENTER), width=50)),
                    ft.DataCell(ft.Container(serial_field, width=130)),
                    ft.DataCell(ft.Container(reading_field, width=80)),
                    ft.DataCell(ft.Container(delete_button, width=80)),
                ]
            )
            rows.append(row)
        
        self.data_table.rows = rows
        
        # Actualizar UI
        try:
            if hasattr(self.data_table, 'page') and self.data_table.page is not None:
                self.data_table.update()
                self.table_container.update()
                print(f"[METER_TABLE] Tabla actualizada con {len(self.meters)} medidores")
        except Exception as e:
            print(f"[METER_TABLE] Error actualizando tabla: {e}")

    def get_meters_data(self):
        """Obtiene los datos de todos los medidores"""
        return [
            {
                "index": i + 1,
                "serial": meter["serial"],
                "reading": meter["reading"]
            }
            for i, meter in enumerate(self.meters)
            if meter["serial"].strip()  # Solo medidores con serial
        ]

    def validate_meters(self):
        """Valida que todos los medidores tengan datos completos"""
        errors = []
        valid_meters = []
        
        for i, meter in enumerate(self.meters):
            if not meter["serial"].strip():
                errors.append(f"Fila {i + 1}: Serial requerido")
            elif not meter["reading"].strip():
                errors.append(f"Fila {i + 1}: Lectura requerida")
            else:
                try:
                    float(meter["reading"])
                    valid_meters.append(meter)
                except ValueError:
                    errors.append(f"Fila {i + 1}: Lectura debe ser un número")
        
        return errors, valid_meters

    def debug_meters_state(self):
        """Función de debug para ver el estado completo"""
        print(f"[METER_TABLE] === DEBUG ESTADO COMPLETO ===")
        print(f"[METER_TABLE] Total medidores: {len(self.meters)}")
        for i, meter in enumerate(self.meters):
            print(f"[METER_TABLE] Fila {i}: Serial='{meter['serial']}', Reading='{meter['reading']}'")
        print(f"[METER_TABLE] === FIN DEBUG ===")

    def build(self):
        """Construye el módulo de tabla de medidores"""
        return ft.Column([
            # Título
            ft.Row([
                ft.Icon(ft.Icons.SPEED, color=ft.Colors.ORANGE_700, size=20),
                ft.Text("Medidores de Prueba", size=16, weight="bold", color=ft.Colors.ORANGE_700),
            ]),
            
            # Botón de agregar
            ft.Row([
                self.add_button,
            ], alignment=ft.MainAxisAlignment.START),
            
            # Información
            ft.Text(
                "Presione 'Agregar Medidor' para añadir una nueva fila a la tabla.",
                size=11,
                color=ft.Colors.GREY_600,
                italic=True
            ),
            
            # Tabla
            self.table_container,
            
            # Resumen
            ft.Container(
                content=ft.Text(
                    f"Total de medidores: {len(self.meters)}",
                    size=12,
                    weight="bold",
                    color=ft.Colors.BLUE_700
                ),
                padding=ft.padding.all(10),
                bgcolor=ft.Colors.BLUE_50,
                border_radius=6,
            )
        ], spacing=15)

def create_meter_table_module():
    """Factory function para crear el módulo de tabla de medidores"""
    return MeterTableModule()