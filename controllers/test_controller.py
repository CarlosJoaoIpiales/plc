from services.db_service import (
    get_existing_test_count,
    save_meter_if_not_exists,
    save_test_for_meter,
    insert_client,
    insert_technician,
    insert_meter_group
)

# Devuelve el número de prueba siguiente para un medidor y tipo de prueba
def get_test_number_for_serial(serial_number, test_type):
    return get_existing_test_count(serial_number, test_type) + 1

# Guarda una prueba individual
def save_test_entry(data):
    try:
        # Validación de campos requeridos
        required_keys = [
            "serial_number",
            "meter_group_id",
            "test_type",
            "test_number",
            "initial_reading",
            "final_reading",
            "reference_value",
            "batch"  # <- importante para calcular tolerancia
        ]
        for key in required_keys:
            if key not in data:
                return {"success": False, "error": f"Missing field: {key}"}

        # Crea o encuentra el medidor (por serial)
        meter_id = save_meter_if_not_exists(data["serial_number"], data["meter_group_id"])

        # Calcular error y resultado según batch
        error = ((data["final_reading"] - data["initial_reading"] - data["reference_value"]) / data["reference_value"]) * 100
        tolerance = 2 if data["batch"] == "new" else 5
        passed = abs(error) <= tolerance

        # Guardar prueba
        save_test_for_meter(meter_id, {
            "test_type": data["test_type"],
            "test_number": data["test_number"],
            "initial_reading": data["initial_reading"],
            "final_reading": data["final_reading"],
            "reference_value": data["reference_value"],
            "error": error,
            "passed": passed
        })

        return {"success": True}

    except Exception as e:
        return {"success": False, "error": str(e)}

# Guarda un grupo de medidores con cliente y técnico
def save_meter_group(data, client_id, technician_id):
    try:
        required_fields = ["brand", "model", "ratio", "nominal_flow", "diameter", "type", "batch"]
        for field in required_fields:
            if field not in data or not data[field]:
                return {"success": False, "error": f"{field.replace('_', ' ').capitalize()} is required"}

        if not client_id:
            return {"success": False, "error": "Client ID is required"}
        if not technician_id:
            return {"success": False, "error": "Technician ID is required"}

        meter_group_id = insert_meter_group(data, client_id, technician_id)
        return {"success": True, "meter_group_id": meter_group_id}

    except Exception as e:
        return {"success": False, "error": str(e)}
