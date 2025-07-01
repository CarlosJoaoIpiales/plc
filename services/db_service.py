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
