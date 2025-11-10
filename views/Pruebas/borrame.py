import flet as ft
from flet import Page, View, Text, ElevatedButton

def main(page: Page):
    # Vista inicial
    def build_home_view():
        home_view = View("/home", [
            Text("Bienvenido a la aplicación"),
            ElevatedButton("Ir al Dashboard", on_click=go_to_dashboard)
        ])
        return home_view

    # Vista del Dashboard
    def build_dashboard_view():
        dashboard_view = View("/dashboard", [
            Text("Aquí está el Dashboard de la empresa"),
            ElevatedButton("Volver a la Página Principal", on_click=go_to_home)
        ])
        return dashboard_view

    # Función para navegar a la vista del dashboard
    def go_to_dashboard(e):
        page.views.append(build_dashboard_view())  # Añadir la vista del dashboard
        page.go("/dashboard")  # Navegar a la vista del dashboard

    # Función para navegar a la vista de inicio
    def go_to_home(e):
        page.views.append(build_home_view())  # Añadir la vista de inicio
        page.go("/home")  # Navegar a la vista de inicio

    # Mostrar la vista inicial al cargar la página
    page.views.append(build_home_view())
    page.go("/home")  # Navegar a la vista inicial

# Crear y ejecutar la aplicación Flet
ft.app(target=main)
