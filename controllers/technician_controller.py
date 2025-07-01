from services.db_service import fetch_all_technicians, insert_technician

def get_all_technicians():
    return fetch_all_technicians()

def add_technician(data):
    return insert_technician(data)
