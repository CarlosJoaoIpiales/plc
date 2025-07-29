import psycopg2

# --- Conexión base ---
def connect():
    return psycopg2.connect(
        dbname="test_bench",
        user="postgres",
        password="admin",
        host="localhost",
        port="5432"
    )


# --- CLIENTES ---
def insert_client(name):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO clients (name) VALUES (%s) RETURNING id", (name,))
        client_id = cur.fetchone()[0]
        conn.commit()
        return client_id
    finally:
        cur.close()
        conn.close()


def fetch_all_clients():
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM clients ORDER BY name")
        rows = cur.fetchall()
        return [{"id": row[0], "name": row[1]} for row in rows]
    finally:
        cur.close()
        conn.close()


# --- TÉCNICOS ---
def insert_technician(name):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO technicians (name) VALUES (%s) RETURNING id", (name,))
        technician_id = cur.fetchone()[0]
        conn.commit()
        return technician_id
    finally:
        cur.close()
        conn.close()


def fetch_all_technicians():
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM technicians ORDER BY name")
        rows = cur.fetchall()
        return [{"id": row[0], "name": row[1]} for row in rows]
    finally:
        cur.close()
        conn.close()


# --- LOTES DE MEDIDORES ---
def insert_meter_group(data, client_id, technician_id):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO meter_groups (
                brand, model, ratio, nominal_flow,
                diameter, type, batch, client_id, technician_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            data["brand"], data["model"], int(data["ratio"]),
            float(data["nominal_flow"]), float(data["diameter"]),
            data["type"], data["batch"], client_id, technician_id
        ))
        group_id = cur.fetchone()[0]
        conn.commit()
        return group_id
    finally:
        cur.close()
        conn.close()


# --- MEDIDORES ---
def save_meter_if_not_exists(serial_number, meter_group_id):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM meters WHERE serial_number = %s", (serial_number,))
        row = cur.fetchone()
        if row:
            return row[0]
        cur.execute("""
            INSERT INTO meters (serial_number, meter_group_id)
            VALUES (%s, %s) RETURNING id
        """, (serial_number, meter_group_id))
        meter_id = cur.fetchone()[0]
        conn.commit()
        return meter_id
    finally:
        cur.close()
        conn.close()


# --- PRUEBAS ---
def get_existing_test_count(serial_number, test_type):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM tests
            JOIN meters ON tests.meter_id = meters.id
            WHERE meters.serial_number = %s AND tests.test_type = %s
        """, (serial_number, test_type))
        return cur.fetchone()[0]
    finally:
        cur.close()
        conn.close()


def save_test_for_meter(meter_id, data):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO tests (
                meter_id, test_type, test_number,
                initial_reading, final_reading,
                reference_value, error, passed
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            meter_id, data["test_type"], data["test_number"],
            data["initial_reading"], data["final_reading"],
            data["reference_value"], data["error"], data["passed"]
        ))
        conn.commit()
    finally:
        cur.close()
        conn.close()


# --- REPORTES ---
def fetch_report_for_serial(serial_number):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                t.test_type, t.test_number, t.initial_reading, t.final_reading,
                t.error, t.passed, t.test_date,
                mg.brand, mg.model, mg.diameter, mg.batch
            FROM tests t
            JOIN meters m ON t.meter_id = m.id
            JOIN meter_groups mg ON m.meter_group_id = mg.id
            WHERE m.serial_number = %s
            ORDER BY t.test_date
        """, (serial_number,))
        rows = cur.fetchall()
        colnames = [desc[0] for desc in cur.description]
        return [dict(zip(colnames, row)) for row in rows]
    finally:
        cur.close()
        conn.close()

def _save_session_to_database(self):
    """ GUARDA TODA LA SESIÓN EN LA BASE DE DATOS USANDO TU ESQUEMA EXACTO"""
    try:
        print("[TEST_TABLE] 💾 Guardando sesión en base de datos PostgreSQL...")
        
        #  IMPORTAR TU SERVICIO DE BD
        from services.db_service import (
            insert_client, fetch_all_clients,
            insert_technician, fetch_all_technicians,
            insert_meter_group, save_meter_if_not_exists,
            save_test_for_meter, get_existing_test_count
        )
        
        #  OBTENER DATOS DE LA SESIÓN
        session_data = self._get_session_data()
        
        #  PASO 1: OBTENER/CREAR CLIENTE
        client_name = session_data.get("client_name", "Cliente Desconocido")
        print(f"[TEST_TABLE] 👤 Procesando cliente: {client_name}")
        
        # Buscar cliente existente por nombre
        existing_clients = fetch_all_clients()
        client_id = None
        for client in existing_clients:
            if client.get("name", "").lower().strip() == client_name.lower().strip():
                client_id = client["id"]
                break
        
        # Crear cliente si no existe
        if not client_id:
            client_id = insert_client(client_name)
            print(f"[TEST_TABLE]  Cliente creado: {client_name} (ID: {client_id})")
        else:
            print(f"[TEST_TABLE]  Cliente existente: {client_name} (ID: {client_id})")
        
        #  PASO 2: OBTENER/CREAR TÉCNICO
        technician_name = session_data.get("technician_name", "Técnico Desconocido")
        print(f"[TEST_TABLE] 🔧 Procesando técnico: {technician_name}")
        
        # Buscar técnico existente por nombre
        existing_technicians = fetch_all_technicians()
        technician_id = None
        for tech in existing_technicians:
            if tech.get("name", "").lower().strip() == technician_name.lower().strip():
                technician_id = tech["id"]
                break
        
        # Crear técnico si no existe
        if not technician_id:
            technician_id = insert_technician(technician_name)
            print(f"[TEST_TABLE]  Técnico creado: {technician_name} (ID: {technician_id})")
        else:
            print(f"[TEST_TABLE]  Técnico existente: {technician_name} (ID: {technician_id})")
        
        #  PASO 3: CREAR GRUPO DE MEDIDORES (SESIÓN) - USANDO TU ESQUEMA
        meter_group_data = {
            "brand": session_data.get("brand", "Marca Desconocida")[:50],  # Limitar a 50 chars
            "model": session_data.get("model", "Modelo Desconocido")[:50],
            "ratio": int(session_data.get("ratio", 100)),
            "nominal_flow": float(session_data.get("nominal_flow", 1000)),
            "diameter": float(session_data.get("diameter", 20)),
            "type": session_data.get("type", "Tipo Desconocido")[:50],
            "batch": self._normalize_batch_value(session_data.get("batch", "nuevo")),  #  NORMALIZAR
        }
        
        meter_group_id = insert_meter_group(meter_group_data, client_id, technician_id)
        print(f"[TEST_TABLE]  Grupo de medidores creado (ID: {meter_group_id})")
        
        #  PASO 4: GUARDAR MEDIDORES Y PRUEBAS
        saved_tests_count = 0
        saved_meters_count = 0
        processed_serials = set()
        
        for test_group in self.completed_tests:
            print(f"[TEST_TABLE] 📝 Procesando grupo: {test_group['test_name']}")
            
            for result in test_group["results"]:
                try:
                    serial_number = str(result["serial_number"]).strip()[:100]  # Limitar a 100 chars
                    
                    #  CREAR/OBTENER MEDIDOR (USANDO TU ESQUEMA)
                    meter_id = save_meter_if_not_exists(serial_number, meter_group_id)
                    if meter_id and serial_number not in processed_serials:
                        saved_meters_count += 1
                        processed_serials.add(serial_number)
                        print(f"[TEST_TABLE] 📏 Medidor procesado: {serial_number} (ID: {meter_id})")
                    
                    #  DETERMINAR NÚMERO DE PRUEBA AUTOMÁTICAMENTE
                    existing_count = get_existing_test_count(serial_number, test_group["test_type"])
                    test_number = existing_count + 1
                    
                    #  PREPARAR DATOS DE LA PRUEBA (USANDO TU ESQUEMA EXACTO)
                    test_data = {
                        "test_type": str(test_group["test_type"])[:10],  # Limitar a 10 chars
                        "test_number": int(test_number),
                        "initial_reading": float(result["initial_reading"]),
                        "final_reading": float(result["final_reading"]),
                        "reference_value": float(result.get("pattern_volume", 100.0)),  # Default 100 como en tu esquema
                        "error": float(result["error_percentage"]),
                        "passed": bool(result["is_passed"])
                    }
                    
                    #  GUARDAR PRUEBA EN BD
                    save_test_for_meter(meter_id, test_data)
                    saved_tests_count += 1
                    
                    print(f"[TEST_TABLE]  Prueba guardada: {serial_number} - {test_group['test_type']} #{test_number}")
                    
                except Exception as e:
                    print(f"[TEST_TABLE]  Error guardando resultado individual: {e}")
                    print(f"[TEST_TABLE]  Datos del resultado: {result}")
                    import traceback
                    traceback.print_exc()
        
        print(f"[TEST_TABLE]  Sesión guardada completamente en PostgreSQL")
        print(f"[TEST_TABLE]  Estadísticas finales:")
        print(f"  • Grupo ID: {meter_group_id}")
        print(f"  • Medidores únicos procesados: {saved_meters_count}")
        print(f"  • Pruebas guardadas: {saved_tests_count}")
        print(f"  • Cliente: {client_name} (ID: {client_id})")
        print(f"  • Técnico: {technician_name} (ID: {technician_id})")
        
        return meter_group_id  #  RETORNAR ID DE LA SESIÓN
        
    except Exception as e:
        print(f"[TEST_TABLE]  Error crítico guardando en PostgreSQL: {e}")
        import traceback
        traceback.print_exc()
        raise Exception(f"Error guardando en base de datos: {str(e)}")
def _normalize_batch_value(self, batch_value):
    """ NORMALIZA EL VALOR DE BATCH PARA QUE COINCIDA CON TU ESQUEMA"""
    if not batch_value:
        return "new"
    
    batch_lower = str(batch_value).lower().strip()
    
    # Mapear valores en español/inglés
    if batch_lower in ["nuevo", "new"]:
        return "new"
    elif batch_lower in ["usado", "used"]:
        return "used"
    else:
        print(f"[TEST_TABLE]  Valor de batch desconocido: {batch_value}, usando 'new'")
        return "new"
def _get_session_data(self):
    """ OBTIENE DATOS DE LA SESIÓN CON VALORES POR DEFECTO SEGUROS"""
    try:
        #  INTENTAR OBTENER DESDE PÁGINA
        if hasattr(self, 'page') and self.page and hasattr(self.page, 'session'):
            return {
                "client_name": getattr(self.page, 'client_name', 'Cliente Desconocido'),
                "technician_name": getattr(self.page, 'technician_name', 'Técnico Desconocido'),
                "brand": getattr(self.page, 'brand', 'Marca Desconocida'),
                "model": getattr(self.page, 'model', 'Modelo Desconocido'),
                "ratio": getattr(self.page, 'ratio', 100),
                "nominal_flow": getattr(self.page, 'nominal_flow', 1000.0),
                "diameter": getattr(self.page, 'diameter', 20.0),
                "type": getattr(self.page, 'meter_type', 'Tipo Desconocido'),
                "batch": getattr(self.page, 'batch', 'nuevo'),
            }
        
        #  DATOS POR DEFECTO SEGUROS
        return {
            "client_name": "Cliente Desconocido",
            "technician_name": "Técnico Desconocido", 
            "brand": "Marca Desconocida",
            "model": "Modelo Desconocido",
            "ratio": 100,
            "nominal_flow": 1000.0,
            "diameter": 20.0,
            "type": "Tipo Desconocido",
            "batch": "nuevo",
        }
        
    except Exception as e:
        print(f"[TEST_TABLE]  Error obteniendo datos de sesión: {e}")
        return {
            "client_name": "Cliente Desconocido",
            "technician_name": "Técnico Desconocido", 
            "brand": "Marca Desconocida",
            "model": "Modelo Desconocido",
            "ratio": 100,
            "nominal_flow": 1000.0,
            "diameter": 20.0,
            "type": "Tipo Desconocido",
            "batch": "nuevo",
        }