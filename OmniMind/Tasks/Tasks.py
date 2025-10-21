import os
import flet as ft
from helpers.utils import getSession, addElementsPage, setGradient, setInputField, setCarrousel
from middlewares.auth import middleware_auth
import asyncio
import requests_async as request
import json
from footer_navegation.navegation import footer_navbar
from params import *

input_search_field = setInputField("search", placeholder="Look for...")

current_path = {
    "path":os.path.abspath(__file__),
    "folder":os.path.dirname(os.path.abspath(__file__)).split("\\")[-1],
    "file":__file__.split("\\")[-1]
}

user_session = {}
token_session = None

def loadTasksCategories(page: ft.Page):
    global user_session, token_session

    async def load_data():
        headers = HEADERS
        headers["Authorization"] = f"Bearer {token_session}"

        response = await request.get(f"{REQUEST_URL_TEST}/tasks/categories", headers=headers)

        if response.status_code != 200:
            print(f"❌ Error HTTP: {response.status_code}")
            print(f"Response text: {response.json()}")
            return None

        try:
            data = response.json()
            return data
        except json.JSONDecodeError:
            print("❌ La respuesta no es JSON válido:")
            print(response.json()) 
            return None

    data = asyncio.run(load_data())
    if not data:
        print("⚠️ No se recibieron datos")
        return

    newData = []
    for id_category, content in enumerate(data["message"], start=1):
        # ⚠️ Aquí hacemos el json.loads
        try:
            parsed_content = json.loads(content["content"]) if isinstance(content["content"], str) else content["content"]
        except Exception as e:
            print(f"❌ Error al parsear content: {e}")
            parsed_content = {}

        newData.append({
            "id_category": {"id": id_category},
            "content": parsed_content
        })

    # Ya no hacemos json.dumps aquí
    sample_tasks = newData

    return setCarrousel(page, sample_tasks, addTask)

def ListTasks(page: ft.Page):
    # Fondo degradado azul

    input_search = ft.Container(
        input_search_field
    )

    backwallpaper = ft.Container(
        expand=True,
        gradient=setGradient("black-blue"),
        alignment=ft.alignment.top_center
    )

    # Header fijo arriba del todo
    header = ft.Container(
        width=page.window_width,
        top=0,  # lo fija en la parte superior
        left=0,
        right=0,
        padding=ft.padding.only(left=25, right=25, top=40, bottom=10),
        content= ft.Column(
            [
                ft.Row(
                    [
                        # Columna izquierda: saludo + nombre
                        ft.Column(
                            [
                                ft.Text("Hello", size=22, color="white", weight=ft.FontWeight.BOLD),
                                ft.Text(user_session.get("username","guest"), size=18, color="white")  # TODO sesión
                            ],
                            spacing=4,
                            alignment=ft.MainAxisAlignment.START,
                            horizontal_alignment=ft.CrossAxisAlignment.START,
                            expand=True
                        ),
                        # Avatar a la derecha
                        ft.CircleAvatar(
                            radius=25,  # circle size
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

    # Card blanca en la parte inferior
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

    # Stack general: degradado + card blanca + header arriba
    background = [
            backwallpaper,
            content_area,
            header
        ]

    return background

def addTask(page, id_category):
    page.go(f"/tasks/create/{id_category}")

def addCategory(page):
    page.go(f"/category/create")

def RenderTasks(page: ft.Page):

    global user_session, token_session

    session = middleware_auth(page)

    user_session = session.get("session")
    token_session = session.get("token")

    page.title = "Tasks"
    page.window_width = 500
    page.window_height = 900
    page.window_resizable = False
    page.bgcolor = "#000000"  # fondo base detrás del degradado
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.START

    background_layers = ListTasks(page)

    dispatches = {
        "add_category": ( addCategory , [ page ] )   # [ function , ( *Args ) ]
    }

    footer = footer_navbar(page = page, current_path = current_path, dispatches = dispatches )

    stack = ft.Stack(
        [*background_layers, footer],  # 👈 aquí el truco
        expand=True
    )

    return addElementsPage(page, [ stack ])
