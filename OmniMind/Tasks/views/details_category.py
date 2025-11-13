import os
import json
import flet as ft
from helpers.utils import log_error, addElementsPage
from Tasks.views.tasks import ListTasks
from middlewares.auth import middleware_auth
from footer_navegation.navegation import footer_navbar

current_path = {
    "path": os.path.abspath(__file__),
    "folder": os.path.dirname(os.path.abspath(__file__)).split("\\")[-1],
    "file": __file__.split("\\")[-1]
}

user_session = {}
token_session = None


def loadDetailsCategory(page: ft.Page, category):
    global user_session, token_session

    # ✅ Asegurar que category sea dict
    if isinstance(category, str):
        try:
            category = json.loads(category)
        except Exception:
            category = {"id": category, "name": str(category)}

    try:
        # --- Sesión ---
        session = middleware_auth(page)
        if not isinstance(session, dict):
            raise TypeError("middleware_auth no devolvió un dict válido.")

        user_session = session.get("session") or {}
        token_session = session.get("token") or None

        # --- Config página ---
        page.title = f"Category Details"
        page.window_width = 500
        page.window_height = 900
        page.window_resizable = False
        page.bgcolor = "#F6F7FB"
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        page.vertical_alignment = ft.MainAxisAlignment.START

        # --- Lista de tareas ---
        tasks_section = ListTasks(
            page=page,
            t="AllTasks",
            category=category,
            session={"username": user_session, "token": token_session},
            absolute=False,
        )

        # --- Footer fijo ---
        footer = footer_navbar(page=page, current_path=current_path, dispatches={})

        # --- Estructura final con scroll + footer fijo ---
        stack = ft.Stack(
            expand=True,
            controls=[
                ft.Container(
                    expand=True,
                    content=ft.Column(
                        [
                            ft.Container(
                                expand=True,
                                content=ft.ListView(
                                    controls=[tasks_section],
                                ),
                            ),
                        ],
                        spacing=0,
                    ),
                ),
                footer
            ],
        )

        return addElementsPage(page, [stack])

    except Exception as e:
        log_error("loadDetailsCategory", e)
        return addElementsPage(page, [
            ft.Text("❌ Error loading category details.", color="red", size=18)
        ])
