import flet as ft
import os
import time
import requests
from views.home import main

HEALTH_URL = "http://model:8000/health"
CHECK_INTERVAL = 5  

def wait_for_server():
    while True:
        try:
            resp = requests.get(HEALTH_URL, timeout=2)
            if resp.status_code == 200 and resp.json().get("status") == "ok":
                print("Servidor listo. Iniciando aplicación Flet...")
                return
            else:
                print(f"Servidor no listo ({resp.status_code}). Reintentando en {CHECK_INTERVAL}s...")
        except requests.RequestException as e:
            print(f"Esperando la conexión del servidor: {e}. Reintentando en {CHECK_INTERVAL}s...")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    start_time = time.time()
    wait_for_server()
    total_wait = time.time() - start_time

    print(f"Tiempo total de espera hasta que el servidor estuvo listo: {total_wait:.2f} segundos")

    port = int(os.getenv("PORT", "5555"))
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=port)