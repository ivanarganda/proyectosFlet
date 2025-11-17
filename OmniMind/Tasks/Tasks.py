import os
import flet as ft
from helpers.utils import (
    getSession, addElementsPage, setGradient,
    setInputField, log_error
)
from Tasks.views.tasks import ListTasks
from Tasks.views.categories import loadTasksCategories
from middlewares.auth import middleware_auth
from footer_navegation.navegation import footer_navbar
from params import *

# --------------------------
# Campos globales
# --------------------------
input_search_field = setInputField("search", placeholder="Look for...")

current_path = {
    "path": os.path.abspath(__file__),
    "folder": os.path.dirname(os.path.abspath(__file__)).split("\\")[-1],
    "file": __file__.split("\\")[-1]
}

user_session = {}
token_session = None
# --------------------------
# UI: Lista de tareas
# --------------------------
def InitTasksCategories(page:ft.Page):
    global categories_container

    categories_container = ft.Column(controls=[])

    def refresh_categories():
        categories_container.controls.clear()
        categories_container.controls.append(
            loadTasksCategories(page, token_session, viewDetailsCategory, addTask, addCategory)
        )
        page.update()

    input_search = ft.Container(input_search_field)

    # Fondo superior degradado
    backwallpaper = ft.Container(
        expand=True,
        gradient=setGradient("black-blue"),
        alignment=ft.alignment.top_center
    )

    # Cabecera
    header = ft.Container(
        width=page.window_width,
        top=0,
        left=0,
        right=0,
        padding=ft.padding.only(left=10, right=10, top=10, bottom=10),
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text(
                                    "Hello 👋",
                                    size=24,
                                    color="white",
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Text(
                                    user_session.get("username", "Guest"),
                                    size=17,
                                    color="white70",
                                ),
                            ],
                            spacing=2,
                            alignment=ft.MainAxisAlignment.START,
                            expand=True,
                        ),
                        ft.CircleAvatar(
                            radius=26,
                            content=ft.Image(
                                src="https://raw.githubusercontent.com/ivanarganda/images_assets/main/avatar_man.png",
                                width=52,
                                height=52,
                                border_radius=100,
                                fit=ft.ImageFit.COVER,
                            ),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(
                    content=input_search_field,
                    border_radius=12,
                    bgcolor="white",
                    padding=ft.padding.only(left=10),
                    height=45,
                    alignment=ft.alignment.center_left,
                    shadow=ft.BoxShadow(blur_radius=12, color="#00000030"),
                ),
                ft.Divider(height=20, color="transparent"),
                categories_container
            ]
        ),
    )

    refresh_categories()

    content_area = ListTasks(page, session={ "username":user_session, "token": token_session }, callbacks={
        "load_categories": {
            "function": refresh_categories,
            "args": []
        }
    })  # List tasks

    background = [backwallpaper, content_area, header]
    return background
# --------------------------
# Navegación
# --------------------------
def viewDetailsCategory(page:ft.Page, t="AllTasks", category=None):
    try:
        page.go(f"/category/details/{category}")
    except Exception as e:
        log_error("viewDetailsCategory", e)
        loadSnackbar(page, "❌ Error navigating to category details.", "red")

def addTask(page:ft.Page, id_category):
    try:
        page.go(f"/tasks/create/{id_category}")
    except Exception as e:
        log_error("addTask", e)
        loadSnackbar(page, "❌ Error navigating to task creation.", "red")


def addCategory(page:ft.Page):
    try:
        page.go("/category/create")
    except Exception as e:
        log_error("addCategory", e)
        loadSnackbar(page, "❌ Error navigating to category creation.", "red")


# --------------------------
# Render principal
# --------------------------
def RenderTasks(page:ft.Page):
    global user_session, token_session

    try:
        session = middleware_auth(page)
        if not isinstance(session, dict):
            raise TypeError("middleware_auth no devolvió un dict válido.")

        user_session = session.get("session") or {}
        token_session = session.get("token") or None

        page.title = "Tasks"
        page.window_width = 500
        page.window_height = 900
        page.window_resizable = False
        page.bgcolor = "#000000"
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        page.vertical_alignment = ft.MainAxisAlignment.START

        background_layers = InitTasksCategories(page)

        dispatches = {"add_category": (addCategory, [page])}
        footer = footer_navbar(page=page, current_path=current_path, dispatches=dispatches)

        stack = ft.Stack([*background_layers, footer], expand=True)

        return addElementsPage(page, [stack])

    except Exception as e:
        log_error("RenderTasks", e)
        return addElementsPage(page, [
            ft.Text("❌ Error rendering tasks module.", color="red", size=18)
        ])
