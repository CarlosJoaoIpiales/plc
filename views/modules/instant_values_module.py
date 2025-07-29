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
        
        #  NUEVA VARIABLE: TIPO DE PRUEBA ACTUAL
        self.current_test_type = None
        
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
        
        #  NUEVO: CAUDAL Q4 INSTANTÁNEO
        self.inst_flow_q4 = ft.TextField(
            label="Caudal Q4 (Inst.)",
            value="0.00",
            read_only=True,
            text_align="center",
            width=180,
            height=50,
            text_style=ft.TextStyle(size=12, weight="bold", color=ft.Colors.PURPLE_700)
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

        self.current_values = {
            "flow_q1": 0.0,
            "flow_q2": 0.0,
            "flow_q3": 0.0,
            "flow_q4": 0.0,  #  NUEVO: AGREGAR Q4 FLOW
            "vol_q1": 0.0,
            "vol_q2": 0.0,
            "vol_q3": 0.0,
            "vol_q4": 0.0,
        }
        
        #  INICIALIZAR CONTROLADOR MODBUS
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
                print("[INSTANT_VALUES]  Controlador Modbus inicializado")
            else:
                print("[INSTANT_VALUES]  No se pudo detectar puerto Modbus")
                
        except Exception as e:
            print(f"[INSTANT_VALUES]  Error configurando Modbus: {e}")
            self.controller = None

    #  NUEVA FUNCIÓN: ESTABLECER TIPO DE PRUEBA ACTUAL
    def set_current_test_type(self, test_type):
        """Establece el tipo de prueba actual para manejar la lógica Q3/Q4"""
        old_test_type = self.current_test_type
        self.current_test_type = test_type
        
        print(f"[INSTANT_VALUES]  Tipo de prueba cambiado: {old_test_type} → {test_type}")
        
        #  ACTUALIZAR INMEDIATAMENTE LA VISUALIZACIÓN SEGÚN EL TIPO
        self.update_flow_display_based_on_test_type()

    def update_flow_display_based_on_test_type(self):
        """ NUEVA FUNCIÓN: Actualiza la visualización de caudales según el tipo de prueba"""
        try:
            #  OBTENER EL VALOR ACTUAL DE Q3 (FÍSICO)
            current_q3_flow = self.current_values.get("flow_q3", 0.0)
            
            if self.current_test_type == "Q3":
                #  MODO Q3: MOSTRAR VALOR EN Q3, LIMPIAR Q4
                self.inst_flow_q3.value = f"{current_q3_flow:.2f}"
                self.inst_flow_q4.value = "0.00"
                
                #  DESTACAR Q3, ATENUAR Q4
                self.inst_flow_q3.text_style = ft.TextStyle(size=12, weight="bold", color=ft.Colors.ORANGE_700)
                self.inst_flow_q4.text_style = ft.TextStyle(size=12, weight="normal", color=ft.Colors.GREY_500)
                
                print(f"[INSTANT_VALUES] Modo Q3: Mostrando {current_q3_flow:.2f} en Q3, Q4 en 0.00")
                
            elif self.current_test_type == "Q4":
                #  MODO Q4: MOSTRAR VALOR EN Q4, LIMPIAR Q3
                self.inst_flow_q3.value = "0.00"
                self.inst_flow_q4.value = f"{current_q3_flow:.2f}"
                
                #  DESTACAR Q4, ATENUAR Q3
                self.inst_flow_q3.text_style = ft.TextStyle(size=12, weight="normal", color=ft.Colors.GREY_500)
                self.inst_flow_q4.text_style = ft.TextStyle(size=12, weight="bold", color=ft.Colors.PURPLE_700)
                
                print(f"[INSTANT_VALUES] Modo Q4: Mostrando {current_q3_flow:.2f} en Q4, Q3 en 0.00")
                
            else:
                #  MODO NEUTRAL: MOSTRAR Q3 EN SU LUGAR NORMAL, Q4 EN 0
                self.inst_flow_q3.value = f"{current_q3_flow:.2f}"
                self.inst_flow_q4.value = "0.00"
                
                #  COLORES NORMALES
                self.inst_flow_q3.text_style = ft.TextStyle(size=12, weight="bold", color=ft.Colors.ORANGE_700)
                self.inst_flow_q4.text_style = ft.TextStyle(size=12, weight="bold", color=ft.Colors.PURPLE_700)
                
                print(f"[INSTANT_VALUES]  Modo neutral: Q3={current_q3_flow:.2f}, Q4=0.00")
            
            #  ACTUALIZAR CONTROLES EN UI DE FORMA SEGURA
            self.safe_update_controls([self.inst_flow_q3, self.inst_flow_q4])
            
        except Exception as e:
            print(f"[INSTANT_VALUES]  Error actualizando visualización por tipo: {e}")

    def safe_update_controls(self, controls):
        """ NUEVA FUNCIÓN: Actualiza múltiples controles de forma segura"""
        for control in controls:
            try:
                if hasattr(control, 'page') and control.page is not None:
                    control.update()
            except Exception as e:
                print(f"[INSTANT_VALUES]  Error actualizando control: {e}")
    
    def update_ui(self, kind, data):
        """Callback para actualizar la UI con datos del Modbus - MEJORADO CON LÓGICA Q3/Q4"""
        if kind == "instant" and "data" in data:
            try:
                #  VALIDAR QUE TENEMOS SUFICIENTES DATOS
                if not data['data'] or len(data['data']) < 7:
                    print(f"[INSTANT_VALUES]  Datos insuficientes: {len(data['data']) if data['data'] else 0} elementos")
                    return
                
                #  VALIDAR QUE TODOS LOS DATOS SON NUMÉRICOS
                try:
                    values = [float(x) for x in data['data'][:7]]
                except (ValueError, TypeError) as e:
                    print(f"[INSTANT_VALUES]  Datos no numéricos: {data['data'][:7]} - Error: {e}")
                    return
                
                #  ACTUALIZAR VALORES NORMALES (Q1, Q2)
                self.inst_flow_q1.value = f"{values[0]:.2f}"
                self.inst_flow_q2.value = f"{values[1]:.2f}"
                
                #  ACTUALIZAR VOLÚMENES (SIN CAMBIOS)
                self.inst_vol_q1.value = f"{values[3]:.2f}"
                self.inst_vol_q2.value = f"{values[4]:.2f}"
                self.inst_vol_q3.value = f"{values[5]:.2f}"
                self.inst_vol_q4.value = f"{values[6]:.2f}"
                
                #  ACTUALIZAR VALORES ACTUALES PARA ACCESO DIRECTO
                self.current_values = {
                    "flow_q1": values[0],
                    "flow_q2": values[1],
                    "flow_q3": values[2],  #  VALOR FÍSICO DE Q3
                    "flow_q4": values[2],  #  Q4 USA EL MISMO VALOR QUE Q3
                    "vol_q1": values[3],
                    "vol_q2": values[4],
                    "vol_q3": values[5],
                    "vol_q4": values[6],
                }
                
                #  ACTUALIZAR Q3/Q4 SEGÚN EL TIPO DE PRUEBA ACTUAL
                self.update_flow_display_based_on_test_type()
                
                #  ENVIAR VALORES A LA TABLA EN TIEMPO REAL (INCLUIR Q4 FLOW)
                if self.value_callback:
                    try:
                        #  ENVIAR TODOS LOS VOLÚMENES + FLOWS
                        self.value_callback(values[3], values[4], values[5], values[6])  # Volúmenes Q1, Q2, Q3, Q4
                        
                        #  DEBUG OCASIONAL
                        if hasattr(self, '_update_counter'):
                            self._update_counter += 1
                        else:
                            self._update_counter = 1
                            
                        if self._update_counter % 50 == 0:  # Cada 50 actualizaciones
                            print(f"[INSTANT_VALUES]  Enviando a tabla: Vol Q1={values[3]:.2f}, Q2={values[4]:.2f}, Q3={values[5]:.2f}, Q4={values[6]:.2f}")
                            print(f"[INSTANT_VALUES]  Flows: Q1={values[0]:.2f}, Q2={values[1]:.2f}, Q3={values[2]:.2f} (compartido Q4)")
                    except Exception as callback_error:
                        print(f"[INSTANT_VALUES]  Error en callback: {callback_error}")
                
                #  ACTUALIZAR CONTROLES RESTANTES DE FORMA SEGURA
                remaining_controls = [self.inst_flow_q1, self.inst_flow_q2, self.inst_vol_q1, self.inst_vol_q2, self.inst_vol_q3, self.inst_vol_q4]
                self.safe_update_controls(remaining_controls)
                
                #  LOG OCASIONAL PARA VERIFICAR FUNCIONAMIENTO
                if hasattr(self, '_log_counter'):
                    self._log_counter += 1
                else:
                    self._log_counter = 1
                    
                if self._log_counter % 30 == 0:
                    print(f"[INSTANT_VALUES]  Valores OK - Tipo actual: {self.current_test_type}")
                    print(f"[INSTANT_VALUES]  Q3 físico: {values[2]:.2f}, mostrado en: {'Q4' if self.current_test_type == 'Q4' else 'Q3'}")
                
            except Exception as e:
                print(f"[INSTANT_VALUES]  Error actualizando UI: {e}")
                
        elif kind == "log" and "log" in data:
            #  MANEJAR LOGS NORMALES (filtrar spam)
            log_message = data['log']
            if not any(spam_text in log_message for spam_text in [
                "Valores leídos correctamente", 
                "Sending command", 
                "Reading values"
            ]):
                print(f"[INSTANT_VALUES_LOG] {log_message}")
        
        elif kind == "error" and "error" in data:
            #  MANEJAR ERRORES DE MODBUS
            error_message = data['error']
            if "Controlador no válido" not in error_message:  # Filtrar error común
                print(f"[INSTANT_VALUES_ERROR] {error_message}")
    
    #  NUEVA FUNCIÓN: CONFIGURAR CALLBACK
    def set_value_callback(self, callback):
        """Configura el callback para enviar valores a la tabla"""
        self.value_callback = callback
        print("[INSTANT_VALUES]  Callback configurado para envío de valores")
    
    def get_current_values(self):
        """Obtiene los valores actuales como diccionario - ACTUALIZADO CON Q4 FLOW"""
        try:
            return {
                "flow_q1": float(self.inst_flow_q1.value),
                "flow_q2": float(self.inst_flow_q2.value),
                "flow_q3": float(self.inst_flow_q3.value),
                "flow_q4": float(self.inst_flow_q4.value),  #  INCLUIR Q4 FLOW
                "vol_q1": float(self.inst_vol_q1.value),
                "vol_q2": float(self.inst_vol_q2.value),
                "vol_q3": float(self.inst_vol_q3.value),
                "vol_q4": float(self.inst_vol_q4.value),
            }
        except Exception as e:
            print(f"[INSTANT_VALUES]  Error obteniendo valores actuales: {e}")
            return {
                "flow_q1": 0.0, "flow_q2": 0.0, "flow_q3": 0.0, "flow_q4": 0.0,
                "vol_q1": 0.0, "vol_q2": 0.0, "vol_q3": 0.0, "vol_q4": 0.0
            }
        
    def get_current_instant_values(self):
        """ NUEVA FUNCIÓN: Obtiene valores en formato para tabla de pruebas"""
        current = self.get_current_values()
        return {
            "Q1": current.get("vol_q1", 0.0),
            "Q2": current.get("vol_q2", 0.0),
            "Q3": current.get("vol_q3", 0.0),
            "Q4": current.get("vol_q4", 0.0)
        }

    def get_pattern_value_for_test(self, test_type):
        """ MEJORADA: Obtiene el valor patrón específico con lógica Q3/Q4"""
        try:
            mapping = {
                "Q1": "vol_q1",
                "Q2": "vol_q2", 
                "Q3": "vol_q3",
                "Q4": "vol_q4"  #  Q4 USA SU PROPIO VOLUMEN
            }
            
            volume_key = mapping.get(test_type)
            if not volume_key:
                print(f"[INSTANT_VALUES]  Tipo de prueba no válido: {test_type}")
                return 0.0
            
            #  DEBUG: MOSTRAR ESTADO COMPLETO
            print(f"[INSTANT_VALUES]  === DEBUG PARA {test_type} ===")
            print(f"[INSTANT_VALUES]  Volume key: {volume_key}")
            print(f"[INSTANT_VALUES]  current_values completo: {self.current_values}")
            print(f"[INSTANT_VALUES]  Tipo de prueba actual: {self.current_test_type}")
            
            #  PRIORIDAD 1: current_values (más actualizado)
            pattern_value = self.current_values.get(volume_key, 0.0)
            print(f"[INSTANT_VALUES]  Valor desde current_values: {pattern_value:.2f}")
            
            #  PRIORIDAD 2: TextField como respaldo
            if pattern_value <= 0.0:
                text_field_mapping = {
                    "vol_q1": self.inst_vol_q1,
                    "vol_q2": self.inst_vol_q2,
                    "vol_q3": self.inst_vol_q3,
                    "vol_q4": self.inst_vol_q4
                }
                
                text_field = text_field_mapping.get(volume_key)
                if text_field:
                    try:
                        textfield_value = float(text_field.value)
                        print(f"[INSTANT_VALUES]  Valor desde TextField: {textfield_value:.2f}")
                        pattern_value = textfield_value
                    except (ValueError, TypeError) as e:
                        print(f"[INSTANT_VALUES]  Error convirtiendo TextField: {e}")
                        pattern_value = 0.0
            
            #  PRIORIDAD 3: Último recurso - intentar get_current_values()
            if pattern_value <= 0.0:
                try:
                    current_from_method = self.get_current_values()
                    method_value = current_from_method.get(volume_key, 0.0)
                    print(f"[INSTANT_VALUES]  Valor desde get_current_values(): {method_value:.2f}")
                    pattern_value = method_value
                except Exception as e:
                    print(f"[INSTANT_VALUES]  Error en get_current_values(): {e}")
            
            print(f"[INSTANT_VALUES]  === RESULTADO FINAL PARA {test_type}: {pattern_value:.2f} ===")
            return pattern_value
            
        except Exception as e:
            print(f"[INSTANT_VALUES]  Error obteniendo valor patrón para {test_type}: {e}")
            import traceback
            traceback.print_exc()
            return 0.0

    def force_update_current_values(self):
        """ NUEVA FUNCIÓN: Fuerza actualización de current_values desde TextFields"""
        try:
            self.current_values = {
                "flow_q1": float(self.inst_flow_q1.value),
                "flow_q2": float(self.inst_flow_q2.value),
                "flow_q3": float(self.inst_flow_q3.value),
                "flow_q4": float(self.inst_flow_q4.value),  #  INCLUIR Q4
                "vol_q1": float(self.inst_vol_q1.value),
                "vol_q2": float(self.inst_vol_q2.value),
                "vol_q3": float(self.inst_vol_q3.value),
                "vol_q4": float(self.inst_vol_q4.value),
            }
            print(f"[INSTANT_VALUES]  current_values actualizados forzadamente: {self.current_values}")
            return self.current_values
        except Exception as e:
            print(f"[INSTANT_VALUES]  Error forzando actualización: {e}")
            return self.current_values

    def debug_all_values(self):
        """ NUEVA FUNCIÓN: Debug completo de todos los valores"""
        print(f"[INSTANT_VALUES]  === DEBUG COMPLETO ===")
        print(f"[INSTANT_VALUES]  current_test_type: {self.current_test_type}")
        print(f"[INSTANT_VALUES]  current_values: {self.current_values}")
        
        textfield_values = {}
        try:
            textfield_values = {
                "flow_q1": self.inst_flow_q1.value,
                "flow_q2": self.inst_flow_q2.value,
                "flow_q3": self.inst_flow_q3.value,
                "flow_q4": self.inst_flow_q4.value,  #  INCLUIR Q4
                "vol_q1": self.inst_vol_q1.value,
                "vol_q2": self.inst_vol_q2.value,
                "vol_q3": self.inst_vol_q3.value,
                "vol_q4": self.inst_vol_q4.value,
            }
            print(f"[INSTANT_VALUES]  TextField values: {textfield_values}")
        except Exception as e:
            print(f"[INSTANT_VALUES]  Error leyendo TextFields: {e}")
        
        try:
            method_values = self.get_current_values()
            print(f"[INSTANT_VALUES]  get_current_values(): {method_values}")
        except Exception as e:
            print(f"[INSTANT_VALUES]  Error en get_current_values(): {e}")
        
        print(f"[INSTANT_VALUES]  === FIN DEBUG ===")
    
    def stop_monitoring(self):
        """Detiene el monitoreo"""
        try:
            if self.controller:
                self.controller.stop_reading()
                print("[INSTANT_VALUES] ⏹️ Monitoreo de valores instantáneos detenido")
        except Exception as e:
            print(f"[INSTANT_VALUES]  Error deteniendo monitoreo: {e}")
                
    def build(self):
        """Construye el módulo de valores instantáneos - ACTUALIZADO CON Q4 FLOW"""
        return ft.Column([
            ft.Text("Valores instantáneos", weight="bold", text_align="center"),
            
            #  SECCIÓN DE CAUDALES (INCLUYENDO Q4)
            ft.Container(
                content=ft.Column([
                    ft.Text("Caudales (L/h)", size=12, weight="bold", color=ft.Colors.BLUE_800, text_align="center"),
                    self.inst_flow_q1,
                    self.inst_flow_q2,
                    self.inst_flow_q3,
                    self.inst_flow_q4,  #  AGREGAR Q4 FLOW
                ], spacing=5),
                margin=ft.margin.only(bottom=15),
            ),
            
            #  SECCIÓN DE VOLÚMENES
            ft.Container(
                content=ft.Column([
                    ft.Text("Volúmenes (L)", size=12, weight="bold", color=ft.Colors.GREEN_800, text_align="center"),
                    self.inst_vol_q1,
                    self.inst_vol_q2,
                    self.inst_vol_q3,
                    self.inst_vol_q4,
                ], spacing=5),
            ),
            
        ], spacing=10, alignment="center", horizontal_alignment="center")

def create_instant_values_module():
    """Función factory para crear el módulo de valores instantáneos"""
    return InstantValuesModule()