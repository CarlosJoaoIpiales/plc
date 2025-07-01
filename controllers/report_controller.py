from services.db_service import fetch_report_for_serial
from services.export_service import export_report_to_csv

def get_report_for_serial(serial_number):
    return fetch_report_for_serial(serial_number)

def export_serial_report_csv(serial_number):
    data = fetch_report_for_serial(serial_number)
    if not data:
        return {"success": False, "error": "No data found"}
    filepath = export_report_to_csv(serial_number, data)
    return {"success": True, "file": filepath}
