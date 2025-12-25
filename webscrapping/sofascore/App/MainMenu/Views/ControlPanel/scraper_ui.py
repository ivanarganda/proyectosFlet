import os
import flet as ft
import json
from helpers.utils import addElementsPage, get_modules
import threading
import time
import requests
from footer_navegation.navegation import footer_navbar
from .common_control_panel import handle_selected_module
from datetime import datetime
from params import *
import glob

current_path = {
    "path": os.path.abspath(__file__),
    "folder": os.path.dirname(os.path.abspath(__file__)).split("\\")[-1],
    "file": __file__.split("\\")[-1],
}

colors_checkboxes = {
    True: "success",
    False: "error"
}

panel_settings = None
ref_panel_settings = ft.Ref[ft.Container]()

MODULES_MENU = get_modules() or {}

MODULES_MENU = json.loads(MODULES_MENU)

selected_modules = {}

def RenderScrapper(page: ft.Page, params={}):

    page.window.width = 1000
    page.window.height = 800

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

    # ------------------------------------------------------------
    # PROGRESS + LOG VIEW
    # ------------------------------------------------------------
    logs = ft.ListView(expand=True, spacing=6, auto_scroll=True)
    progress_bar = ft.ProgressBar(width=400)
    status_text = ft.Text("Idle", size=13, color=ft.colors.GREY_700)

    def log(msg, level="info"):
        color = {
            "info": ft.colors.GREY_800,
            "success": ft.colors.GREEN_700,
            "error": ft.colors.RED_700
        }.get(level, ft.colors.GREY_800)

        now = datetime.now().strftime("%H:%M:%S")
        logs.controls.append(
            ft.Text(f"[{now}] {msg}", size=13, color=color)
        )
        page.update()

    # ------------------------------------------------------------
    # SCRAPING VIA API
    # ------------------------------------------------------------
    def run_scraper_clicked(e):
        run_button.disabled = True
        status_text.value = "Running..."
        log("Iniciando scraping vía API...")
        page.update()

        try:
            r = requests.post(f"{REQUEST_URL}/scrapping/start")
        except Exception as ex:
            log(f"Error conectando con API: {ex}", "error")
            run_button.disabled = False
            status_text.value = "Error"
            page.update()
            return

        if r.status_code != 200:
            log("Error iniciando scraping", "error")
            run_button.disabled = False
            status_text.value = "Error"
            page.update()
            return

        def poll_status():
            while True:
                try:
                    r = requests.get(f"{REQUEST_URL}/scrapping/status").json()

                    current = r.get("current", 0)
                    total = r.get("total", 1)
                    step = r.get("step", "Procesando...")

                    progress_bar.value = current / total if total else 0
                    status_text.value = step
                    log(step)
                    page.update()

                    if r.get("finished"):
                        log("Scraping finalizado correctamente ✅", "success")
                        status_text.value = "Finished ✅"
                        break

                    if r.get("error"):
                        log(f"ERROR: {r['error']}", "error")
                        status_text.value = "Error"
                        break

                    time.sleep(1)

                except Exception as ex:
                    log(f"Error polling estado: {ex}", "error")
                    status_text.value = "Error"
                    break

            run_button.disabled = False
            page.update()

        threading.Thread(target=poll_status, daemon=True).start()

    run_button = ft.ElevatedButton(
        "Ejecutar Scraper",
        icon=ft.Icons.PLAY_ARROW,
        on_click=run_scraper_clicked,
        bgcolor=ft.colors.BLUE_600,
        color=ft.colors.WHITE,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
            padding=ft.padding.symmetric(horizontal=20, vertical=12)
        )
    )

    # ------------------------------------------------------------
    # CHECKBOXES
    # ------------------------------------------------------------
    checkboxes = ft.Column(controls=[])

    checkboxes.controls.extend([
        ft.Checkbox(
            label=module["name"],
            value=module.get("enabled"),
            on_change=lambda e: handle_selected_module(
                page,
                e,
                log,
                colors_checkboxes
            )
        )
        for module in MODULES_MENU.values()
    ])

    # ------------------------------------------------------------
    # PANEL DE CONFIGURACIÓN
    # ------------------------------------------------------------
    panel_settings = ft.Column(
        [
            ft.Column(
                [
                    ft.Text("Modo", size=16, weight="bold"),
                    ft.RadioGroup(
                        content=ft.Column([
                            ft.Radio(label="Completo", value="full"),
                            ft.Radio(label="Rápido", value="fast"),
                        ]),
                        value="full",
                        on_change=lambda e: log(
                            f"Modo cambiado a: {e.control.value}",
                            "info"
                        )
                    ),
                ]
            ),
            ft.Column(
                [
                    ft.Text("Módulos habilitados", size=16, weight="bold"),
                    checkboxes,
                ]
            )
        ],
        scroll=ft.ScrollMode.AUTO,
        height=400
    )

    page.update()

    # ------------------------------------------------------------
    # LAYOUT FINAL
    # ------------------------------------------------------------
    footer = ft.Container(
        content=footer_navbar(page=page, current_path=current_path, dispatches={}),
        expand=False
    )

    main_content = ft.Container(
        content=ft.Row([
            ft.Column(
                [
                    ft.Text("Panel de Scraping", size=22, weight="bold"),
                    ft.Divider(),
                    run_button,
                    progress_bar,
                    status_text,
                    ft.Divider(),
                    ft.Container(content=panel_settings)
                ],
                spacing=16,
                expand=True,
            ),

            ft.VerticalDivider(width=1),

            ft.Column(
                [
                    ft.Text("Logs del proceso", size=18, weight="bold"),
                    ft.Container(
                        content=logs,
                        bgcolor=ft.colors.GREY_50,
                        border_radius=10,
                        border=ft.border.all(1, ft.colors.GREY_300),
                        padding=12,
                        height=610
                    )
                ],
                expand=True,
            )
        ]),
        expand=True
    )

    layout = ft.Column(
        [
            main_content,
            footer,
        ],
        expand=True,
    )

    return addElementsPage(page, [layout])
