import flet as ft
from controllers.modbus_controller import ModbusController
import threading
import time

class InstantValuesModule:
    def __init__(self):
        self.is_monitoring = False
        self.monitor_thread = None
        self.value_callback = None
        self.controller = None
        
        # Valores instantáneos - Caudales
        self.inst_flow_q1 = ft.TextField(
            label="Caudal Q1 (Inst.)",
            value="0.00",
            read_only=True,
            text_align="center",
            width=180,
            height=50,
            text_style=ft.TextStyle(size=12, weight="bold", color=ft.Colors.BLUE_700)
        )
        
        self.inst_flow_q2 = ft.TextField(
            label="Caudal Q2 (Inst.)",
            value="0.00",
            read_only=True,
            text_align="center",
            width=180,
            height=50,
            text_style=ft.TextStyle(size=12, weight="bold", color=ft.Colors.GREEN_700)
        )
        
        self.inst_flow_q3 = ft.TextField(
            label="Caudal Q3 (Inst.)",
            value="0.00",
            read_only=True,
            text_align="center",
            width=180,
            height=50,
            text_style=ft.TextStyle(size=12, weight="bold", color=ft.Colors.ORANGE_700)
        )
        
        # Valores instantáneos - Volúmenes
        self.inst_vol_q1 = ft.TextField(
            label="Volumen Q1 (Inst.)",
            value="0.00",
            read_only=True,
            text_align="center",
            width=180,
            height=50,
            text_style=ft.TextStyle(size=12, weight="bold", color=ft.Colors.BLUE_700)
        )
        
        self.inst_vol_q2 = ft.TextField(
            label="Volumen Q2 (Inst.)",
            value="0.00",
            read_only=True,
            text_align="center",
            width=180,
            height=50,
            text_style=ft.TextStyle(size=12, weight="bold", color=ft.Colors.GREEN_700)
        )
        
        self.inst_vol_q3 = ft.TextField(
            label="Volumen Q3 (Inst.)",
            value="0.00",
            read_only=True,
            text_align="center",
            width=180,
            height=50,
            text_style=ft.TextStyle(size=12, weight="bold", color=ft.Colors.ORANGE_700)
        )
        
        self.inst_vol_q4 = ft.TextField(
            label="Volumen Q4 (Inst.)",
            value="0.00",
            read_only=True,
            text_align="center",
            width=180,
            height=50,
            text_style=ft.TextStyle(size=12, weight="bold", color=ft.Colors.PURPLE_700)
        )
        
        # 🔥 INICIALIZAR CONTROLADOR MODBUS
        self.setup_modbus_controller()
        
    def setup_modbus_controller(self):
        """Configura el controlador Modbus para lectura de valores instantáneos"""
        try:
            # Crear controlador con callback para actualizar UI
            self.controller = ModbusController(self.update_ui)
            
            # Detectar y conectar puerto
            port = self.controller.service.detect_port()
            if port:
                self.controller.service.connect(port)
                # Iniciar lectura con ID 1
                self.controller.start_reading(1)
                print("[INSTANT_VALUES] ✅ Controlador Modbus inicializado")
            else:
                print("[INSTANT_VALUES] ⚠️ No se pudo detectar puerto Modbus")
                
        except Exception as e:
            print(f"[INSTANT_VALUES] ❌ Error configurando Modbus: {e}")
            self.controller = None
    
    def update_ui(self, kind, data):
        """Callback para actualizar la UI con datos del Modbus - CON VALIDACIONES ROBUSTAS"""
        if kind == "instant" and "data" in data:
            try:
                # 🔥 VALIDAR QUE TENEMOS SUFICIENTES DATOS
                if not data['data'] or len(data['data']) < 7:
                    print(f"[INSTANT_VALUES] ⚠️ Datos insuficientes: {len(data['data']) if data['data'] else 0} elementos")
                    return
                
                # 🔥 VALIDAR QUE TODOS LOS DATOS SON NUMÉRICOS
                try:
                    values = [float(x) for x in data['data'][:7]]
                except (ValueError, TypeError) as e:
                    print(f"[INSTANT_VALUES] ⚠️ Datos no numéricos: {data['data'][:7]} - Error: {e}")
                    return
                
                # ACTUALIZAR VALORES INSTANTÁNEOS EN UI
                self.inst_flow_q1.value = f"{values[0]:.2f}"
                self.inst_flow_q2.value = f"{values[1]:.2f}"
                self.inst_flow_q3.value = f"{values[2]:.2f}"
                self.inst_vol_q1.value = f"{values[3]:.2f}"
                self.inst_vol_q2.value = f"{values[4]:.2f}"
                self.inst_vol_q3.value = f"{values[5]:.2f}"
                self.inst_vol_q4.value = f"{values[6]:.2f}"
                
                # 🔥 NUEVO: ENVIAR VALORES A LA TABLA SI HAY CALLBACK
                if self.value_callback:
                    instant_values = {
                        "Q1": values[3],  # vol_q1
                        "Q2": values[4],  # vol_q2  
                        "Q3": values[5],  # vol_q3
                        "Q4": values[6]   # vol_q4
                    }
                    try:
                        self.value_callback(instant_values)
                    except Exception as callback_error:
                        print(f"[INSTANT_VALUES] ❌ Error en callback: {callback_error}")
                
                # Actualizar controles en UI de forma segura
                def safe_update():
                    try:
                        for control in [self.inst_flow_q1, self.inst_flow_q2, self.inst_flow_q3,
                                       self.inst_vol_q1, self.inst_vol_q2, self.inst_vol_q3, self.inst_vol_q4]:
                            if hasattr(control, 'update'):
                                control.update()
                    except Exception as update_error:
                        print(f"[INSTANT_VALUES] ⚠️ Error actualizando control: {update_error}")
                
                # 🔥 USAR THREADING TIMER PARA EVITAR PROBLEMAS DE CONCURRENCIA
                threading.Timer(0.1, safe_update).start()
                
                # 🔥 LOG OCASIONAL PARA VERIFICAR FUNCIONAMIENTO (cada 30 lecturas)
                if hasattr(self, '_log_counter'):
                    self._log_counter += 1
                else:
                    self._log_counter = 1
                    
                if self._log_counter % 30 == 0:
                    print(f"[INSTANT_VALUES] 📊 Valores OK: Q1={values[3]:.2f}, Q2={values[4]:.2f}, Q3={values[5]:.2f}, Q4={values[6]:.2f}")
                
            except Exception as e:
                print(f"[INSTANT_VALUES] ❌ Error actualizando UI: {e}")
                # 🔥 INFORMACIÓN ADICIONAL PARA DEBUG
                print(f"[INSTANT_VALUES] 🔍 Data recibida: {data}")
                
        elif kind == "log" and "log" in data:
            # 🔥 MANEJAR LOGS NORMALES (filtrar spam)
            log_message = data['log']
            if not any(spam_text in log_message for spam_text in [
                "Valores leídos correctamente", 
                "Sending command", 
                "Reading values"
            ]):
                print(f"[INSTANT_VALUES_LOG] {log_message}")
        
        elif kind == "error" and "error" in data:
            # 🔥 MANEJAR ERRORES DE MODBUS
            error_message = data['error']
            if "Controlador no válido" not in error_message:  # Filtrar error común
                print(f"[INSTANT_VALUES_ERROR] {error_message}")
    
    # 🔥 NUEVA FUNCIÓN: CONFIGURAR CALLBACK
    def set_value_callback(self, callback):
        """Configura el callback para enviar valores a la tabla"""
        self.value_callback = callback
        print("[INSTANT_VALUES] ✅ Callback configurado para envío de valores")
    
    def get_current_values(self):
        """Obtiene los valores actuales como diccionario"""
        try:
            return {
                "flow_q1": float(self.inst_flow_q1.value),
                "flow_q2": float(self.inst_flow_q2.value),
                "flow_q3": float(self.inst_flow_q3.value),
                "vol_q1": float(self.inst_vol_q1.value),
                "vol_q2": float(self.inst_vol_q2.value),
                "vol_q3": float(self.inst_vol_q3.value),
                "vol_q4": float(self.inst_vol_q4.value),
            }
        except Exception as e:
            print(f"[INSTANT_VALUES] ⚠️ Error obteniendo valores actuales: {e}")
            return {
                "flow_q1": 0.0, "flow_q2": 0.0, "flow_q3": 0.0,
                "vol_q1": 0.0, "vol_q2": 0.0, "vol_q3": 0.0, "vol_q4": 0.0
            }
    
    def stop_monitoring(self):
        """Detiene el monitoreo"""
        try:
            if self.controller:
                self.controller.stop_reading()
                print("[INSTANT_VALUES] ⏹️ Monitoreo de valores instantáneos detenido")
        except Exception as e:
            print(f"[INSTANT_VALUES] ⚠️ Error deteniendo monitoreo: {e}")
                
    def build(self):
        """Construye el módulo de valores instantáneos"""
        return ft.Column([
            ft.Text("Valores instantáneos", weight="bold", text_align="center"),
            self.inst_flow_q1,
            self.inst_flow_q2,
            self.inst_flow_q3,
            self.inst_vol_q1,
            self.inst_vol_q2,
            self.inst_vol_q3,
            self.inst_vol_q4,
        ], spacing=10, alignment="center", horizontal_alignment="center")

def create_instant_values_module():
    """Función factory para crear el módulo de valores instantáneos"""
    return InstantValuesModule()