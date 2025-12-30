import flet as ft
import json
from helpers.utils import get_modules
import requests
import pprint
import json
from pathlib import Path
import os
import uuid
from params import *

files_column = ft.Column(scroll="auto", spacing=6)

# ================================================================
# LISTA DE FICHEROS _db
# ================================================================
def get_db_files():

    try:

        r = requests.get(f"{REQUEST_URL}/files/db", timeout=5)

        if r.status_code == 200:

            return r.json().get("files", [])

    except Exception as ex:

        log(f"Error cargando ficheros: {ex}", "error")

    return []

def change_module_file_content(page: ft.Page, e: ft.ControlEvent):

    content_module = get_modules()

    if e.control.label in content_module:
        content_module[e.control.label]["enabled"] = e.control.value

    r = requests.put(
        f"{REQUEST_URL}/settings/panel/module",
        json=json.dumps(content_module)
    )

    if r.status_code == 200:
        # 🔁 REFRESCO VISUAL
        e.control.update()      # refresca el checkbox
        page.update()           # refresca la página completa

def handle_selected_module(page,e: ft.ControlEvent, log, colors_checkboxes):

    value, colour = parse_checkbox_radio_value(e, colors_checkboxes)

    log(f"Módulos seleccionados: {value}", colour)

    change_module_file_content(page,e)

    return e.control.value

def parse_checkbox_radio_value(e: ft.ControlEvent, colors_checkboxes):

    mapped_values = {
        True: "Enabled",
        False: "Disabled"
    }

    return (
        mapped_values.get(e.control.value, e.control.value),
        colors_checkboxes.get(e.control.value, "info")
    )

def refresh_files():
    files_column.controls.clear()
    for f in get_db_files():
        files_column.controls.append(
            ft.Container(
                content=ft.Text(f"📄 {f}", size=14),
                padding=10,
                bgcolor=ft.colors.GREY_100,
                border_radius=8
            )
        )
    log("Ficheros actualizados")

    page.update()

    refresh_files()