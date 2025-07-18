import flet as ft
from datetime import datetime

class TestHistoryModule:
    def __init__(self, completed_tests):
        self.completed_tests = completed_tests
        
    def update_history(self, new_completed_tests):
        """Actualiza la lista de pruebas completadas"""
        self.completed_tests = new_completed_tests
        
    def show_history_dialog(self, page):
        """Muestra el diálogo con el historial de pruebas"""
        
        def close_dialog(e):
            dialog.open = False
            page.update()
            
        if not self.completed_tests:
            content = ft.Text(
                "📭 No hay pruebas completadas aún",
                size=16,
                text_align="center",
                color=ft.Colors.GREY_600
            )
        else:
            # Crear tabla de historial
            rows = []
            for i, test in enumerate(self.completed_tests, 1):
                completed_time = datetime.fromtimestamp(test.get("completed_at", 0))
                
                # Determinar color según resultado
                result_color = ft.Colors.GREEN if test.get("is_passed", False) else ft.Colors.RED
                
                rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(i), size=12)),
                        ft.DataCell(ft.Text(test.get("test_name", "N/A"), size=12)),
                        ft.DataCell(ft.Text(f"{test.get('volume', 0)}L", size=12)),
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
                
            history_table = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("#", size=12, weight="bold")),
                    ft.DataColumn(ft.Text("Prueba", size=12, weight="bold")),
                    ft.DataColumn(ft.Text("Volumen", size=12, weight="bold")),
                    ft.DataColumn(ft.Text("Error %", size=12, weight="bold")),
                    ft.DataColumn(ft.Text("Resultado", size=12, weight="bold")),
                    ft.DataColumn(ft.Text("Hora", size=12, weight="bold")),
                ],
                rows=rows,
                border=ft.border.all(1, ft.Colors.GREY_300),
                heading_row_color=ft.Colors.BLUE_100,
            )
            
            # Estadísticas
            passed_tests = sum(1 for test in self.completed_tests if test.get("is_passed", False))
            total_tests = len(self.completed_tests)
            success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
            
            stats = ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text("📊 Estadísticas", size=14, weight="bold"),
                        ft.Text(f"Total: {total_tests}", size=12),
                        ft.Text(f"Aprobadas: {passed_tests}", size=12, color=ft.Colors.GREEN),
                        ft.Text(f"Reprobadas: {total_tests - passed_tests}", size=12, color=ft.Colors.RED),
                        ft.Text(f"Tasa de éxito: {success_rate:.1f}%", size=12, weight="bold"),
                    ], spacing=5),
                ], 
                alignment=ft.MainAxisAlignment.CENTER
                ),
                padding=15,
                border_radius=8,
                bgcolor=ft.Colors.GREY_100,
                margin=ft.margin.only(bottom=15),
            )
            
            content = ft.Column([
                stats,
                ft.Container(
                    content=ft.Row([history_table], scroll=ft.ScrollMode.AUTO),
                    height=300,
                ),
            ])
            
        dialog = ft.AlertDialog(
            title=ft.Text("📋 Historial de Pruebas"),
            content=ft.Container(
                content=content,
                width=700,
                height=400,
            ),
            actions=[
                ft.TextButton("Cerrar", on_click=close_dialog)
            ],
        )
        
        page.overlay.append(dialog)
        dialog.open = True
        page.update()

def create_test_history_module(completed_tests):
    """Función factory para crear el módulo de historial"""
    return TestHistoryModule(completed_tests)