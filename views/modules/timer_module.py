import flet as ft
import threading
import time

class TimerModule:
    def __init__(self, on_timer_finished):
        self.on_timer_finished = on_timer_finished
        self.total_time = 0  # En segundos
        self.remaining_time = 0
        self.is_running = False
        self.start_time = 0
        self.timer_thread = None
        
        # 🔥 ELEMENTO UI COMPACTO - SOLO UNA LÍNEA
        self.time_display = ft.Text(
            "Tiempo restante: 00:00",
            size=14,
            weight="bold",
            color=ft.Colors.BLUE_700,
            text_align="center"
        )
        
    def set_time(self, minutes):
        """Establece el tiempo del timer en minutos"""
        self.total_time = int(minutes * 60)
        self.remaining_time = self.total_time
        self.update_display()
        
    def start_countdown(self):
        """Inicia la cuenta regresiva"""
        if self.is_running:
            return
            
        self.is_running = True
        self.start_time = time.time()
        
        # Iniciar thread del timer
        self.timer_thread = threading.Thread(target=self._countdown_loop)
        self.timer_thread.daemon = True
        self.timer_thread.start()
        
    def stop_countdown(self):
        """Detiene la cuenta regresiva"""
        self.is_running = False
        self.update_display()
        
    def _countdown_loop(self):
        """Loop principal del countdown"""
        while self.is_running and self.remaining_time > 0:
            elapsed = time.time() - self.start_time
            self.remaining_time = max(0, self.total_time - int(elapsed))
            
            # Actualizar UI en el hilo principal
            try:
                self.update_display()
                time.sleep(1)
            except:
                break
                
        if self.remaining_time <= 0 and self.is_running:
            self.is_running = False
            self.update_display()
            self.on_timer_finished()
            
    def update_display(self):
        """🔥 ACTUALIZA SOLO EL TEXTO COMPACTO"""
        minutes = self.remaining_time // 60
        seconds = self.remaining_time % 60
        
        # 🔥 FORMATO SIMPLE: "Tiempo restante: MM:SS"
        time_str = f"{minutes:02d}:{seconds:02d}"
        
        if self.is_running:
            self.time_display.value = f"Tiempo restante: {time_str}"
            # Cambiar color según tiempo restante
            if self.remaining_time > self.total_time * 0.5:
                self.time_display.color = ft.Colors.BLUE_700
            elif self.remaining_time > self.total_time * 0.2:
                self.time_display.color = ft.Colors.ORANGE_700
            else:
                self.time_display.color = ft.Colors.RED_700
        elif self.remaining_time <= 0:
            self.time_display.value = "⏰ ¡Tiempo completado!"
            self.time_display.color = ft.Colors.RED_600
        else:
            self.time_display.value = f"Tiempo restante: {time_str}"
            self.time_display.color = ft.Colors.GREY_600
        
        try:
            self.time_display.update()
        except:
            pass
            
    def get_elapsed_time(self):
        """Obtiene el tiempo transcurrido en minutos"""
        if self.start_time > 0:
            elapsed_seconds = time.time() - self.start_time
            return elapsed_seconds / 60
        return 0
        
    def build(self):
        """🔥 CONSTRUYE EL MÓDULO COMPACTO - SOLO UNA FILA"""
        return self.time_display

def create_timer_module(on_timer_finished):
    """Función factory para crear el módulo de timer"""
    return TimerModule(on_timer_finished)