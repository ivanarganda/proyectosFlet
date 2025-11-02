import flet as ft
from helpers.utils import getSession
import json
from MainMenu.MainMenu import renderMainMenu
from MainMenu.views.dashboard import render_dashboard
from MainMenu.views.prediccion_ventas import prediccion_ventas
from MainMenu.views.historial_ventas import historial_ventas

def main(page: ft.Page):
    # handle session here    
    page.on_route_change = route_change

    page.go("/menu")   # Go to main menu

def route_change(e: ft.RouteChangeEvent):
    page = e.page
    page.views.clear()
    if page.route == "/menu":
        page.views.append(ft.View("/menu", [renderMainMenu(page)]))
    elif page.route == "/dashboard":
        layout, actualizar_dashboard = render_dashboard(page)
        page.views.append(ft.View("/dashboard", [layout]))
        page.update()
        actualizar_dashboard()

    elif page.route == "/historial_ventas":
        page.views.append(ft.View("/historial_ventas", [historial_ventas(page)]))
    elif page.route == "/prediccion_ventas":
        page.views.append(ft.View("/prediccion_ventas", [prediccion_ventas(page)]))
    page.update()
    
ft.app(target=main)
