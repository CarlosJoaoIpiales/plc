# controllers/client_controller.py

from services.db_service import fetch_all_clients, insert_client

def get_all_clients():
    return fetch_all_clients()  #  retorna [{ "id": 1, "name": "CARLOS" }, ...]

def add_client(client_data):
    """Agrega un nuevo cliente - acepta string (compatibilidad) o dict (completo)"""
    try:
        from services.db_service import connect
        
        conn = connect()
        cursor = conn.cursor()
        
        #  MANEJAR AMBOS FORMATOS PARA COMPATIBILIDAD
        if isinstance(client_data, str):
            # Formato viejo: solo nombre
            cursor.execute(
                "INSERT INTO clients (name) VALUES (%s) RETURNING id",
                (client_data,)
            )
            print(f"[CLIENT_CTRL]  Cliente guardado (solo nombre): {client_data}")
        
        elif isinstance(client_data, dict):
            # Formato nuevo: diccionario completo
            cursor.execute(
                "INSERT INTO clients (name, phone, address, email) VALUES (%s, %s, %s, %s) RETURNING id",
                (
                    client_data.get("name", ""), 
                    client_data.get("phone", ""), 
                    client_data.get("address", ""), 
                    client_data.get("email", "")
                )
            )
            print(f"[CLIENT_CTRL]  Cliente completo guardado: {client_data['name']}")
            print(f"[CLIENT_CTRL] 📞 Teléfono: {client_data.get('phone', 'N/A')}")
            print(f"[CLIENT_CTRL] 📍 Dirección: {client_data.get('address', 'N/A')}")
            print(f"[CLIENT_CTRL] 📧 Email: {client_data.get('email', 'N/A')}")
        
        else:
            raise ValueError("client_data debe ser string o diccionario")
        
        client_id = cursor.fetchone()[0]
        conn.commit()
        
        print(f"[CLIENT_CTRL] 🆔 Cliente guardado con ID: {client_id}")
        return client_id
        
    except Exception as e:
        print(f"[CLIENT_CTRL]  Error agregando cliente: {e}")
        if conn:
            conn.rollback()
        raise e
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
