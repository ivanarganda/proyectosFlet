import os
import json
import asyncio
import flet as ft
import requests_async as request
from helpers.utils import (
    getSession, addElementsPage, setGradient,
    setInputField, setCarrousel
)
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
# Función auxiliar para logs
# --------------------------
def log_error(context: str, error: Exception):
    print(f"❌ Error en {context}: {type(error).__name__} -> {error}")


# --------------------------
# Función principal: carga categorías
# --------------------------
def loadTasksCategories(page: ft.Page):
    """Carga las categorías de tareas desde la API."""
    global user_session, token_session

    async def load_data():
        try:
            headers = HEADERS.copy()
            headers["Authorization"] = f"Bearer {token_session}"

            response = await request.get(
                f"{REQUEST_URL}/tasks/categories",
                headers=headers,
                timeout=10
            )

            if response.status_code != 200:
                print(f"⚠️ HTTP Error: {response.status_code}")
                try:
                    print("Response:", response.json())
                except Exception:
                    print("Response not JSON decodable.")
                return None

            try:
                data = response.json()
                if not isinstance(data, dict):
                    raise ValueError("Response JSON is not a dictionary.")
                return data
            except Exception as e:
                log_error("load_data.json", e)
                return None

        except (asyncio.TimeoutError, OSError, ConnectionError):
            loadSnackbar(page, "⚠️ Connection error or timeout while loading categories.", "red")
            return None

        except Exception as e:
            log_error("load_data", e)
            return None

    # Ejecutar la corrutina de forma segura
    try:
        data = asyncio.run(load_data())
    except RuntimeError:
        # Si ya hay un loop en ejecución (posible en Flet)
        data = asyncio.get_event_loop().run_until_complete(load_data())
    except Exception as e:
        log_error("loadTasksCategories.asyncio_run", e)
        data = None

    # Validar data
    if not data or "message" not in data or not data["message"]:
        print("⚠️ No se recibieron categorías o datos vacíos.")
        return ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.icons.CATEGORY_OUTLINED, size=80, color="#B0B0B0"),
                    ft.Text(
                        "No categories yet",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color="#555",
                    ),
                    ft.Text(
                        "Create your first category to organize your tasks.",
                        size=14,
                        color="#777",
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Divider(height=10, color="transparent"),
                    ft.ElevatedButton(
                        "Create Category",
                        icon=ft.icons.ADD_CIRCLE_OUTLINE,
                        bgcolor="#4e73df",
                        color="white",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                        height=45,
                        width=220,
                        on_click=lambda _: addCategory(page)
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            padding=40,
            border_radius=20,
            bgcolor="#FFFFFF",
            shadow=ft.BoxShadow(blur_radius=25, color="#E0E0E0"),
            height=page.window_height - 400,
            expand=True
        )

    # Procesar datos recibidos
    newData = []
    for id_category, content in enumerate(data.get("message", []), start=1):
        try:
            parsed_content = (
                json.loads(content["content"])
                if isinstance(content["content"], str)
                else content["content"]
            )
            if not isinstance(parsed_content, dict):
                raise ValueError("Parsed content is not a dict.")
        except Exception as e:
            log_error(f"parse_content id={id_category}", e)
            parsed_content = {}

        newData.append({
            "id_category": {"id": id_category},
            "content": parsed_content
        })

    return setCarrousel(page, newData, addTask)


# --------------------------
# UI: Lista de tareas
# --------------------------
def ListTasks(page: ft.Page):
    input_search = ft.Container(input_search_field)

    backwallpaper = ft.Container(
        expand=True,
        gradient=setGradient("black-blue"),
        alignment=ft.alignment.top_center
    )

    header = ft.Container(
        width=page.window_width,
        top=0,
        left=0,
        right=0,
        padding=ft.padding.only(left=25, right=25, top=40, bottom=10),
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text("Hello", size=22, color="white", weight=ft.FontWeight.BOLD),
                                ft.Text(user_session.get("username", "guest"), size=18, color="white")
                            ],
                            spacing=4,
                            alignment=ft.MainAxisAlignment.START,
                            horizontal_alignment=ft.CrossAxisAlignment.START,
                            expand=True
                        ),
                        ft.CircleAvatar(
                            radius=25,
                            content=ft.Image(
                                src="https://raw.githubusercontent.com/ivanarganda/images_assets/main/avatar_man.png",
                                width=50,
                                height=50,
                                border_radius=100,
                                fit=ft.ImageFit.COVER
                            )
                        )
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                ),
                input_search,
                loadTasksCategories(page)
            ]
        )
    )

    content_area = ft.Container(
        bgcolor="#F6F4FB",
        border_radius=ft.border_radius.only(top_left=30, top_right=30),
        height=400,
        bottom=0,
        left=0,
        right=0,
        alignment=ft.alignment.top_center,
        shadow=ft.BoxShadow(
            spread_radius=-10,
            blur_radius=25,
            color=ft.colors.with_opacity(0.3, "#000000")
        ),
    )

    background = [backwallpaper, content_area, header]
    return background


# --------------------------
# Navegación
# --------------------------
def addTask(page, id_category):
    try:
        page.go(f"/tasks/create/{id_category}")
    except Exception as e:
        log_error("addTask", e)
        loadSnackbar(page, "❌ Error navigating to task creation.", "red")


def addCategory(page):
    try:
        page.go("/category/create")
    except Exception as e:
        log_error("addCategory", e)
        loadSnackbar(page, "❌ Error navigating to category creation.", "red")


# --------------------------
# Render principal
# --------------------------
def RenderTasks(page: ft.Page):
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

        background_layers = ListTasks(page)

        dispatches = {"add_category": (addCategory, [page])}
        footer = footer_navbar(page=page, current_path=current_path, dispatches=dispatches)

        stack = ft.Stack([*background_layers, footer], expand=True)

        return addElementsPage(page, [stack])

    except Exception as e:
        log_error("RenderTasks", e)
        return addElementsPage(page, [
            ft.Text("❌ Error rendering tasks module.", color="red", size=18)
        ])
