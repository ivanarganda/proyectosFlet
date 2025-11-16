import os
import flet as ft
from datetime import datetime
from helpers.utils import (
    getSession, addElementsPage, setGradient,
    setInputField, loadLoader, loadSnackbar, clearInputsForm, handle_logout, log_error
)
from middlewares.auth import middleware_auth
from footer_navegation.navegation import footer_navbar

import asyncio
import requests_async as request
import json
from params import *


current_path = {
    "path": os.path.abspath(__file__),
    "folder": os.path.dirname(os.path.abspath(__file__)).split("\\")[-1],
    "file": __file__.split("\\")[-1]
}

user_session = {}
token_session = None
# --------------------------------------------------------------------------
def AddTaskForm(page: ft.Page, id_category=None):

    global user_session, token_session

    session = middleware_auth(page) # check session

    user_session = session.get("session")
    token_session = session.get("token")

    page.title = "New Task"
    page.window_width = 420
    page.window_height = 820
    page.window_resizable = False
    page.bgcolor = "#F6F4FB"

    # Loader
    loader = loadLoader()
    page.overlay.append(loader)

    # --- CAMPOS -------------------------------------------------------------
    txt_title = setInputField("text", label="Task title")

    txt_description = MarkdownEditor(
        on_change=lambda value: set_description(value)
    )

    # --- PREVIEW ------------------------------------------------------------
    preview_title = ft.Text(
        "Your task title will appear here...",
        size=22,
        weight=ft.FontWeight.BOLD,
        color="#2C3E50",
        text_align=ft.TextAlign.CENTER,
    )

    preview_date = ft.Text(
        f"Created on {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        size=12,
        color="#808080",
        italic=True,
        text_align=ft.TextAlign.CENTER,
    )

    preview_desc = ft.Column(
        [
            ft.Text(
                "Start writing your task description to see a live preview here...",
                size=15,
                color="#444",
                text_align=ft.TextAlign.JUSTIFY,
                selectable=True,
            )
        ],
        height=100,
        scroll=ft.ScrollMode.AUTO,
        expand=False
    ) 

    preview_card = ft.Container(
        content=ft.Column(
            [
                ft.Text("Live Preview", size=18, weight=ft.FontWeight.BOLD, color="#4e73df"),
                # ft.Divider(height=8, color="#4e73df"),
                preview_title,
                preview_date,
                # ft.Divider(height=8, color="transparent"),
                preview_desc,
            ],
            spacing=10,
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=20,
        margin=ft.margin.only(top=20, bottom=10),
        bgcolor="#FFFFFF",
        border_radius=16,
        shadow=ft.BoxShadow(blur_radius=25, color="#DDE2F4"),
        height=250,
        width=360,
        alignment=ft.alignment.center,
    )

    def update_preview(e=None):
        preview_title.value = txt_title.value.strip() or "Your task title will appear here..."
        preview_desc.value = txt_description.value.strip() or "Start writing your task description to see a live preview here..."
        preview_date.value = f"Created on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        preview_card.update()

    txt_title.on_change = update_preview
    txt_description.on_change = update_preview

    # --- GUARDAR ------------------------------------------------------------
    async def save_task(e):

        if not txt_title.value.strip():
            loadSnackbar(page, "Title is required", "red")
            return

        loader.visible = True
        page.update()

        title = txt_title.value.strip()
        description = txt_description.value.strip()
        json_data = {
            "content": {
                 "title": title , 
                 "description": description,
                 "date": datetime.now().strftime('%Y-%m-%d %H:%M')
            },
            "id_category": id_category
        }

        headers = HEADERS
        headers["Authorization"] = f"Bearer {token_session}"

        response = await request.post(f"{REQUEST_URL}/tasks", headers=headers, data=json.dumps(json_data))

        data = response.json()

        print("✅ Task added:", json_data)
        loadSnackbar(page, "Task successfully added!", "#4e73df")

        # clearInputsForm(page, [txt_title, txt_description])
        update_preview()
        loader.visible = False
        page.update()

    btn_save = ft.FilledButton(
        "Save Task",
        icon=ft.icons.SAVE,
        style=ft.ButtonStyle(
            bgcolor="#4e73df",
            color=ft.colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=20,
        ),
        height=55,
        width=360,
        on_click=save_task,
    )

    # --- UI PRINCIPAL -------------------------------------------------------
    form = ft.Column(
        [
            ft.Text("Create new task", size=24, weight=ft.FontWeight.BOLD, color="#4e73df"),
            ft.Divider(height=10, color="transparent"),
            txt_title,
            txt_description,
            preview_card,
            # ft.Divider(height=15, color="transparent"),
            btn_save,
        ],
        spacing=14,
        scroll=ft.ScrollMode.AUTO,
        alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True,
    )

    container = ft.Container(
        content=form,
        padding=20,
        border_radius=16,
        bgcolor="#FFFFFF",
        shadow=ft.BoxShadow(blur_radius=25, color="#E0E0E0"),
        expand=True,
    )

    footer = footer_navbar(page=page, current_path=current_path, dispatches={})

    # --- ENSAMBLA LA PÁGINA -------------------------------------------------
    return addElementsPage(page, [
        ft.Container(expand=True, gradient=setGradient("black-blue")),
        container,
        footer,
    ])
