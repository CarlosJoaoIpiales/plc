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
    batch VARCHAR(10) CHECK (batch IN ('new', 'used')),
    client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
    technician_id INTEGER REFERENCES technicians(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: meters
CREATE TABLE IF NOT EXISTS meters (
    id SERIAL PRIMARY KEY,
    serial_number VARCHAR(100) UNIQUE NOT NULL,
    meter_group_id INTEGER REFERENCES meter_groups(id) ON DELETE CASCADE
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
