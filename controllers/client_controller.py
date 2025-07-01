# controllers/client_controller.py

from services.db_service import fetch_all_clients, insert_client

def get_all_clients():
    return fetch_all_clients()  # ✅ retorna [{ "id": 1, "name": "CARLOS" }, ...]

def add_client(data):
    return insert_client(data)
