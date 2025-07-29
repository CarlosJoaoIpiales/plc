import flet as ft
import threading
import time
from datetime import datetime

class AutoFillBot:
    def __init__(self, page: ft.Page):
        self.page = page
        self.running = False
        self.progress = ft.Text("⚙️ Bot listo", color=ft.Colors.GREY_600)

    def start_bot(self, e):
        if not self.running:
            self.running = True
            self.progress.value = "🟢 Bot en ejecución..."
            self.page.update()
            
            thread = threading.Thread(target=self.run_automation, daemon=True)
            thread.start()
        else:
            self.progress.value = " El bot ya está en ejecución"
            self.page.update()

    def run_automation(self):
        """Lógica principal del bot"""
        try:
            # ---- 1. Rellenar datos del cliente ----
            self._update_status("Seleccionando cliente...")
            self._select_dropdown("client_dropdown", "Cliente Demo")
            
            # ---- 2. Datos del medidor ----
            self._update_status("Rellenando datos técnicos...")
            self._fill_text("brand_field", "Marca AutoBot")
            self._fill_text("model_field", "Modelo X-2023")
            self._select_dropdown("ratio_dropdown", "100")
            self._fill_text("flow_field", "150.50")
            
            # ---- 3. Configurar pruebas ----
            self._update_status("Configurando pruebas...")
            time.sleep(1)  # Simula tiempo de configuración
            
            # ---- 4. Seleccionar modo ----
            self._select_radio("operation_radio", "automatic")
            
            self._update_status(" Formulario completado!", ft.Colors.GREEN)
            time.sleep(2)
            
        except Exception as e:
            self._update_status(f" Error: {str(e)}", ft.Colors.RED)
        finally:
            self.running = False

    def _update_status(self, message, color=ft.Colors.BLUE):
        self.progress.value = message
        self.progress.color = color
        self.page.update()

    def _select_dropdown(self, control_id, value):
        control = self.page.get_control(control_id)
        control.value = value
        self.page.update()
        time.sleep(0.5)

    def _fill_text(self, control_id, value):
        control = self.page.get_control(control_id)
        control.value = value
        self.page.update()
        time.sleep(0.3)

    def _select_radio(self, control_id, value):
        control = self.page.get_control(control_id)
        control.value = value
        self.page.update()
        time.sleep(0.5)

    def get_controls(self):
        """Retorna los controles UI del bot"""
        return ft.Column([
            ft.ElevatedButton(
                "🤖 Iniciar Bot Automático",
                icon=ft.Icons.PLAY_ARROW,
                on_click=self.start_bot,
                bgcolor=ft.Colors.GREEN_700,
                color=ft.Colors.WHITE,
                width=250
            ),
            ft.Container(
                self.progress,
                padding=10,
                border_radius=8,
                bgcolor=ft.Colors.GREY_100,
                width=250
            )
        ], horizontal_alignment="center")