import flet as ft
from datetime import datetime

def get_results_summary_view(page, summary_data):
    """Vista de resumen final de todas las pruebas"""
    
    completed_tests = summary_data.get("completed_tests", [])
    test_data = summary_data
    
    # Estadísticas generales
    total_planned = summary_data.get("total_tests", 0)
    total_completed = len(completed_tests)
    completion_rate = summary_data.get("completion_rate", 0)
    
    passed_tests = sum(1 for test in completed_tests if test.get("is_passed", False))
    success_rate = (passed_tests / total_completed * 100) if total_completed > 0 else 0
    
    def go_to_tests(e):
        """Volver a la vista de pruebas"""
        page.go("/tests")
        
    def export_results(e):
        """Exportar resultados (placeholder)"""
        page.snack_bar = ft.SnackBar(
            ft.Text("🚧 Función de exportación en desarrollo"), 
            bgcolor=ft.Colors.BLUE_600
        )
        page.snack_bar.open = True
        page.update()
    
    # Crear tabla de resultados
    result_rows = []
    for i, test in enumerate(completed_tests, 1):
        completed_time = datetime.fromtimestamp(test.get("completed_at", 0))
        result_color = ft.Colors.GREEN if test.get("is_passed", False) else ft.Colors.RED
        
        result_rows.append(
            ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(i), size=12)),
                ft.DataCell(ft.Text(test.get("test_name", "N/A"), size=12)),
                ft.DataCell(ft.Text(test.get("test_type", "N/A"), size=12)),
                ft.DataCell(ft.Text(f"{test.get('volume', 0)}L", size=12)),
                ft.DataCell(ft.Text(f"{test.get('initial_reading', 0):.2f}", size=12)),
                ft.DataCell(ft.Text(f"{test.get('final_reading', 0):.2f}", size=12)),
                ft.DataCell(ft.Text(f"{test.get('volume_difference', 0):.2f}L", size=12)),
                ft.DataCell(ft.Text(f"{test.get('error_percentage', 0):.2f}%", size=12)),
                ft.DataCell(
                    ft.Text(
                        "✅ APROBADO" if test.get("is_passed", False) else "❌ REPROBADO",
                        size=12,
                        color=result_color,
                        weight="bold"
                    )
                ),
                ft.DataCell(ft.Text(completed_time.strftime("%H:%M:%S"), size=11)),
            ])
        )
    
    results_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("#", size=12, weight="bold")),
            ft.DataColumn(ft.Text("Prueba", size=12, weight="bold")),
            ft.DataColumn(ft.Text("Tipo", size=12, weight="bold")),
            ft.DataColumn(ft.Text("Volumen", size=12, weight="bold")),
            ft.DataColumn(ft.Text("Lectura Inicial", size=12, weight="bold")),
            ft.DataColumn(ft.Text("Lectura Final", size=12, weight="bold")),
            ft.DataColumn(ft.Text("Diferencia", size=12, weight="bold")),
            ft.DataColumn(ft.Text("Error %", size=12, weight="bold")),
            ft.DataColumn(ft.Text("Resultado", size=12, weight="bold")),
            ft.DataColumn(ft.Text("Hora", size=12, weight="bold")),
        ],
        rows=result_rows,
        border=ft.border.all(1, ft.Colors.GREY_300),
        heading_row_color=ft.Colors.BLUE_100,
    )
    
    return ft.Column([
        # Título
        ft.Container(
            content=ft.Text(
                "📊 Resumen de Resultados",
                size=32,
                weight="bold",
                text_align="center",
                color=ft.Colors.BLUE_900
            ),
            padding=ft.padding.only(bottom=30),
            alignment=ft.alignment.center,
        ),
        
        # Información del medidor
        ft.Container(
            content=ft.Column([
                ft.Text("🔧 Información del Medidor", size=18, weight="bold", color=ft.Colors.BLUE_700),
                ft.Row([
                    ft.Text(f"Marca: {test_data.get('brand', 'N/A')}", size=14),
                    ft.Text(f"Modelo: {test_data.get('model', 'N/A')}", size=14),
                    ft.Text(f"Ratio: {test_data.get('ratio', 'N/A')}", size=14),
                    ft.Text(f"Q3 Nominal: {test_data.get('nominal_flow', 'N/A')} L/h", size=14),
                ], 
                alignment=ft.MainAxisAlignment.SPACE_AROUND
                ),
                ft.Row([
                    ft.Text(f"Cliente: {test_data.get('client_name', 'N/A')}", size=14),
                    ft.Text(f"Técnico: {test_data.get('technician_name', 'N/A')}", size=14),
                    ft.Text(f"Modo: {test_data.get('operation_mode', 'N/A').upper()}", size=14),
                ], 
                alignment=ft.MainAxisAlignment.SPACE_AROUND
                ),
            ], spacing=15),
            padding=20,
            border_radius=12,
            border=ft.border.all(2, ft.Colors.BLUE_300),
            bgcolor=ft.Colors.BLUE_50,
            margin=ft.margin.only(bottom=20),
        ),
        
        # Estadísticas
        ft.Row([
            ft.Container(
                content=ft.Column([
                    ft.Text("📋 Pruebas Planificadas", size=14, weight="bold", color=ft.Colors.GREY_700),
                    ft.Text(str(total_planned), size=24, weight="bold", color=ft.Colors.BLUE_600),
                ], horizontal_alignment="center"),
                padding=20,
                border_radius=12,
                bgcolor=ft.Colors.BLUE_50,
                expand=True,
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("✅ Pruebas Completadas", size=14, weight="bold", color=ft.Colors.GREY_700),
                    ft.Text(str(total_completed), size=24, weight="bold", color=ft.Colors.GREEN_600),
                ], horizontal_alignment="center"),
                padding=20,
                border_radius=12,
                bgcolor=ft.Colors.GREEN_50,
                expand=True,
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("📊 Tasa de Finalización", size=14, weight="bold", color=ft.Colors.GREY_700),
                    ft.Text(f"{completion_rate:.1f}%", size=24, weight="bold", color=ft.Colors.ORANGE_600),
                ], horizontal_alignment="center"),
                padding=20,
                border_radius=12,
                bgcolor=ft.Colors.ORANGE_50,
                expand=True,
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("🎯 Tasa de Éxito", size=14, weight="bold", color=ft.Colors.GREY_700),
                    ft.Text(f"{success_rate:.1f}%", size=24, weight="bold", color=ft.Colors.PURPLE_600),
                ], horizontal_alignment="center"),
                padding=20,
                border_radius=12,
                bgcolor=ft.Colors.PURPLE_50,
                expand=True,
            ),
        ], spacing=15),
        
        ft.Container(height=20),  # Spacer
        
        # Tabla de resultados
        ft.Container(
            content=ft.Column([
                ft.Text("📊 Detalle de Resultados", size=18, weight="bold", color=ft.Colors.GREEN_700),
                ft.Container(
                    content=ft.Row([results_table], scroll=ft.ScrollMode.AUTO),
                    height=400,
                    border_radius=8,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                ),
            ], spacing=15),
            padding=20,
            border_radius=12,
            border=ft.border.all(2, ft.Colors.GREEN_300),
            bgcolor=ft.Colors.GREEN_50,
        ),
        
        ft.Container(height=20),  # Spacer
        
        # Botones de acción
        ft.Row([
            ft.ElevatedButton(
                "🔄 Nueva Sesión",
                on_click=go_to_tests,
                width=200,
                height=50,
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.BLUE_600,
                    color=ft.Colors.WHITE,
                )
            ),
            ft.ElevatedButton(
                "📤 Exportar Resultados",
                on_click=export_results,
                width=200,
                height=50,
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.GREEN_600,
                    color=ft.Colors.WHITE,
                )
            ),
        ], 
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=20
        ),
        
    ], 
    scroll=ft.ScrollMode.AUTO,
    spacing=0,
    expand=True,
    )