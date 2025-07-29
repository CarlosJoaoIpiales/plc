-- Table: clients
CREATE TABLE IF NOT EXISTS clients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    address TEXT,
    email VARCHAR(100)
);

-- Table: technicians
CREATE TABLE IF NOT EXISTS technicians (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

-- Table: meter_groups
CREATE TABLE IF NOT EXISTS meter_groups (
    id SERIAL PRIMARY KEY,
    brand VARCHAR(50),
    model VARCHAR(50),
    ratio INTEGER,
    nominal_flow NUMERIC,
    diameter NUMERIC,
    type VARCHAR(50),
    batch VARCHAR(10) CHECK (batch IN ('new', 'used', 'nuevo', 'usado')), --  AGREGAR ESPAÑOL
    client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
    technician_id INTEGER REFERENCES technicians(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: meters
CREATE TABLE IF NOT EXISTS meters (
    id SERIAL PRIMARY KEY,
    serial_number VARCHAR(100) NOT NULL, --  QUITAR UNIQUE AQUÍ
    meter_group_id INTEGER REFERENCES meter_groups(id) ON DELETE CASCADE,
    UNIQUE(serial_number, meter_group_id) --  UNIQUE COMPUESTO PARA PERMITIR MISMO SERIAL EN DIFERENTES GRUPOS
);

-- Table: tests
CREATE TABLE IF NOT EXISTS tests (
    id SERIAL PRIMARY KEY,
    meter_id INTEGER REFERENCES meters(id) ON DELETE CASCADE,
    test_type VARCHAR(10),
    test_number INTEGER,
    initial_reading NUMERIC,
    final_reading NUMERIC,
    reference_value NUMERIC DEFAULT 100,
    error NUMERIC,
    passed BOOLEAN,
    test_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

--  ÍNDICES ADICIONALES PARA MEJOR RENDIMIENTO
CREATE INDEX IF NOT EXISTS idx_meters_serial ON meters(serial_number);
CREATE INDEX IF NOT EXISTS idx_meters_group ON meters(meter_group_id);
CREATE INDEX IF NOT EXISTS idx_tests_meter ON tests(meter_id);
CREATE INDEX IF NOT EXISTS idx_tests_type ON tests(test_type);
CREATE INDEX IF NOT EXISTS idx_tests_date ON tests(test_date);
CREATE INDEX IF NOT EXISTS idx_meter_groups_client ON meter_groups(client_id);
CREATE INDEX IF NOT EXISTS idx_meter_groups_technician ON meter_groups(technician_id);