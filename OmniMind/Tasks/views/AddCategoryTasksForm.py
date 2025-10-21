# AddCategoryTasksForm.py — versión UI-X moderna con preview ampliada y botón inferior

import os
import flet as ft
from helpers.utils import (
    loadLoader, addElementsPage, clearInputsForm, loadSnackbar,
    setInputField, build_color_dialog, open_bg_picker,open_text_picker, is_valid_hex,is_light_color
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
def AddCategoryTasksForm(page: ft.Page):

    global user_session, token_session

    session = middleware_auth(page) # check session

    user_session = session.get("session")
    token_session = session.get("token")

    page.title = "New Category"
    page.window_width = 420
    page.window_height = 800
    page.window_resizable = False
    page.bgcolor = "#F6F4FB"

    # ---------- Estado / fields ----------
    category_name = ft.TextField(
        label="Category name",
        hint_text="Work, Personal, Study...",
        border_radius=10,
        bgcolor="#FFFFFF",
        border_color="#E0E0E0",
        prefix_icon=ft.icons.LABEL
    )

    icon_field = ft.TextField(
        label="Icon (emoji or text)",
        hint_text="✅ 📚 💡",
        border_radius=10,
        bgcolor="#FFFFFF",
        border_color="#E0E0E0",
        prefix_icon=ft.icons.EMOJI_EMOTIONS
    )

    bg_color_field = ft.TextField(
        label="Background color (HEX)",
        hint_text="#5A2D9C",
        value="",
        border_radius=10,
        bgcolor="#FFFFFF",
        border_color="#E0E0E0",
        prefix_icon=ft.icons.BRUSH
    )

    text_color_field = ft.TextField(
        label="Text color (HEX)",
        hint_text="#000000",
        value="#1A1A1A",
        border_radius=10,
        bgcolor="#FFFFFF",
        border_color="#E0E0E0",
        prefix_icon=ft.icons.COLOR_LENS
    )

    # ---------- Preview ----------
    preview_icon = ft.Text("🔖", size=34)
    preview_title = ft.Text(
        "Category",
        size=20,
        weight=ft.FontWeight.BOLD,
        color=text_color_field.value,
        text_align=ft.TextAlign.CENTER
    )

    preview_card = ft.Container(
        width=280,
        height=100,
        border_radius=20,
        bgcolor=bg_color_field.value or "white",
        alignment=ft.alignment.center,
        content=ft.Column(
            [preview_icon, preview_title],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8
        ),
        shadow=ft.BoxShadow(blur_radius=25, color="#DDE2F4"), 
    )

    preview_header = ft.Text(
        "Live Preview",
        size=18,
        weight=ft.FontWeight.BOLD,
        color="#4e73df"
    )

    preview_section = ft.Container(
        content=ft.Column(
            [
                preview_header,
                ft.Divider(height=8, color="#4e73df"),
                preview_card
            ],
            spacing=12,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        ),
        padding=20,
        margin=ft.margin.only(top=20, bottom=10),
        bgcolor="#FFFFFF",
        border_radius=16,
        shadow=ft.BoxShadow(blur_radius=25, color="#E0E0E0"),
        alignment=ft.alignment.center
    )

    # ---------- Actualización dinámica ----------
    def update_preview():
        bg_value = (bg_color_field.value or "").strip()
        text_value = (text_color_field.value or "").strip()

        # --- Validación: si hay solo "#" o el valor es inválido → no tocar nada
        if bg_value == "#" or (bg_value and not is_valid_hex(bg_value)):
            return  # 🚫 Salir sin actualizar nada visual

        # --- Fallbacks ---
        bg = bg_value if is_valid_hex(bg_value) else "#ECECEC"
        fg = text_value if is_valid_hex(text_value) else "#000000"

        preview_card.bgcolor = bg
        preview_card.border = ft.border.all(1, "#D0D0D0") if is_light_color(bg) else None
        preview_card.bgcolor = (bg_color_field.value or "#ECECEC").strip() or "#ECECEC"
        preview_icon.value = (icon_field.value or "🔖")
        preview_title.value = (category_name.value or "Category")
        preview_title.color = (text_color_field.value or "#000000").strip() or "#000000"
        preview_card.update()

    category_name.on_change = lambda e: update_preview()
    icon_field.on_change = lambda e: update_preview()
    bg_color_field.on_change = lambda e: update_preview()
    text_color_field.on_change = lambda e: update_preview()

    # ---------- Pickers ----------
    bg_picker_btn = ft.IconButton(
        icon=ft.icons.COLORIZE, tooltip="Pick background color", on_click=open_bg_picker
    )
    text_picker_btn = ft.IconButton(
        icon=ft.icons.FORMAT_COLOR_TEXT, tooltip="Pick text color", on_click=open_text_picker
    )

    # ---------- Submit ----------
    async def save_category(e):
        name = (category_name.value or "").strip()
        icon = (icon_field.value or "").strip()
        bg = (bg_color_field.value or "").strip()
        fg = (text_color_field.value or "").strip()

        if not name:
            loadSnackbar(page, "Name is required", "red")
            return

        # Following template 
        # {"bg_color": {"title": "orange"}, "icon": {"title": "\u2705", "size": 28}, "task": {"title": "Study Python", "size": 18, "weight": 400}, "count": {"title": "0 tasks", "color": "black"}}

        print("✅ Saving category:")
        print("  name:", name)
        print("  icon:", icon)
        print("  bg:", bg)
        print("  text color:", fg)

        json_data = {

            "category":name,
            "content": { "bg_color": {"title": bg}, "icon": {"title": icon, "size": 28}, "task": {"title": name, "size": 18, "weight": 400}, "count": {"title": "0 tasks", "color": "black"} }

        }

        headers = HEADERS

        response = await request.post(f"{REQUEST_URL_TEST}/tasks/categories", headers=headers, data=json.dumps(json_data))

        data = response.json()

        loadSnackbar(page, "Category created!", "#4e73df")
        clearInputsForm(page, [category_name, icon_field, bg_color_field, text_color_field])
        update_preview()

    btn_save = ft.FilledButton(
        "Create Category",
        icon=ft.icons.SAVE,
        style=ft.ButtonStyle(
            bgcolor="#4e73df",
            color=ft.colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=20
        ),
        height=55,
        width=360,
        on_click=save_category
    )

    # ---------- Layout del formulario ----------
    form = ft.Column(
        [
            ft.Text("Create new category", size=24, weight=ft.FontWeight.BOLD, color="#4e73df"),
            # ft.Divider(height=5, color="transparent"),
            preview_section,
            category_name,
            icon_field,
            ft.Row([bg_color_field, bg_picker_btn], spacing=10),
            ft.Row([text_color_field, text_picker_btn], spacing=10),
            # ft.Divider(height=15, color="transparent"),
            btn_save,
        ],
        spacing=14,
        alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        scroll=ft.ScrollMode.AUTO,
        expand=True
    )

    white_card = ft.Container(
        content=form,
        padding=20,
        border_radius=16,
        bgcolor="#FFFFFF",
        shadow=ft.BoxShadow(blur_radius=25, color="#E0E0E0"),
        expand=True
    )

    footer = footer_navbar(page=page, current_path=current_path, dispatches={})

    # ---------- Fondo / estructura ----------
    background = ft.Container(
        expand=True,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_center,
            end=ft.alignment.bottom_center,
            colors=["#E6E9F0", "#EEF1F5"]
        ),
    )

    # ---------- Página final ----------
    return addElementsPage(
        page,
        [
            ft.Stack(
                [
                    background,
                    white_card,
                    footer
                ],
                expand=True
            )
        ]
    )
