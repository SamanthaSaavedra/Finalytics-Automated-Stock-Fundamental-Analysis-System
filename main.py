import os
import flet as ft
from views.home import main as app_main

if __name__ == "__main__":

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))

    # Start process
    view = getattr(ft.AppView, "WEB_SERVER", None)
    if view is None:
        view = getattr(ft.AppView, "WEB_BROWSER")

    print(f"[Finalytics] starting at http://{host}:{port}  (view={view})")
    ft.app(
        target=app_main,
        view=view,
        host=host,
        port=port,
    )