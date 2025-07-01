import threading
import time
from services.serial_service import detect_com_port

def monitor_com_connection(on_ready_callback, update_ui_callback):
    def loop():
        while True:
            port = detect_com_port()
            if port:
                update_ui_callback(f"✅ COM Port Detected: {port}")
                time.sleep(1)
                on_ready_callback()
                break
            else:
                update_ui_callback("⚠️ No COM Port found. Waiting...")
                time.sleep(2)
    threading.Thread(target=loop, daemon=True).start()
