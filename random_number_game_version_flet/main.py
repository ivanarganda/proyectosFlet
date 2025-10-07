import flet as ft
from helpers.utils import getSession
import json
from LoginRegisterForm.LoginRegisterForm import renderTemplate
from MainMenu.MainMenu import renderMainMenu
from Tasks.Tasks import RenderTasks

def main(page: ft.Page):
    # handle session here    
    page.on_route_change = route_change
    
    user_data = getSession(page.client_storage.get("user") or "{}")

    # Check if the user is logged in
    if not user_data or not user_data.get("is_logged_in"):
        page.go("/tasks")       # Go to login page
    else:
        page.go("/menu")   # Go to main menu

def route_change(e: ft.RouteChangeEvent):
    page = e.page
    page.views.clear()
    if page.route == "/":
        page.views.append(ft.View("/", [renderTemplate(page)]))
    elif page.route == "/menu":
        page.views.append(ft.View("/menu", [renderMainMenu(page)]))
    elif page.route == "/games":
        page.views.append(ft.View("/games", [renderGame(page)]))
    elif page.route == "/tasks":
        page.views.append(ft.View("/tasks", [RenderTasks(page)]))
    page.update()
    
ft.app(target=main)
