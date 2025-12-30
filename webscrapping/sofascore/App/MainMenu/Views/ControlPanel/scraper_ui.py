import os
import flet as ft
import json
from helpers.utils import ( 
    addElementsPage, 
    get_modules, 
    render_radio, 
    notify_success,
    notify_warning,
    notify_error
)
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
selected_modules = {}
mode_radio = None
clear_previous_data_radio = None
validate_data_radio = None
output_save_radio = None

def RenderScrapper(page: ft.Page, params={}):

    page.window.width = 1000
    page.window.height = 800

    MODULES_MENU = get_modules() or {}

    running_scrapping = False

    def download_file( page, e:ft.ControlEvent, extension ):
        
        extensions = {
            "sql": "db",
            "json":"json",
            "excel": "xlsx",
            "csv":"csv"
        }

        ext = extensions.get(extension, None)

        if ext is None:
            notify_error(page,"Error en la descarga, no existe extension del fichero")
            return False
        
        file = f"info.{ext}"
        page.launch_url(f"{REQUEST_URL}/download/{file}")
        download_button.visible = False
        download_button.update()
        page.update()
        notify_success(page,"Descarga exitósa")

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
        run_button.value = "Running...."
        status_text.value = "Running..."
        log("Iniciando scraping vía API...")
        page.update()

        parameters_settings = {
            "mode": mode_radio.value,
            "clear_previous_data": clear_previous_data_radio.value,
            "validate_data": validate_data_radio.value,
            "output_save": output_save_radio.value
        }

        try:

            r = requests.post(f"{REQUEST_URL}/scrapping/start", json=json.dumps(parameters_settings))

        except Exception as ex:
            log(f"Error conectando con API: {ex}", "error")
            run_button.disabled = False
            run_button.value = "Ejecutar Scraper"
            status_text.value = "Error"
            page.update()
            return

        if r.status_code != 200:
            log("Error iniciando scraping", "error")
            run_button.disabled = False
            run_button.value = "Ejecutar Scraper"
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
            run_button.value = "Ejecutar Scraper"
            download_button.visible = True
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

    # RADIOS

    mode_container, mode_radio = render_radio( log, "full", ["Completo","Rápido"], ["full","fast"], "Modo" )

    clear_previous_data_container,clear_previous_data_radio = render_radio( log, "si", ["Si","No"], ["si","no"], "Limpieza previa" )

    validate_data_container,validate_data_radio = render_radio( log, "si", ["Si","No"], ["si","no"], "Validar datos" )

    output_save_container, output_save_radio = render_radio( log, "sql", ["SQL","CSV","Excel","JSON"], ["sql","csv","excel","json"], "Guardar como" )

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
                    mode_container,
                    clear_previous_data_container,
                    validate_data_container,
                    output_save_container
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

    download_button = ft.ElevatedButton(
        "Descargar",
        icon=ft.Icons.DOWNLOAD,
        on_click=lambda e: download_file(page, e, output_save_radio.value),
        bgcolor=ft.colors.BLUE_600,
        color=ft.colors.WHITE,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
            padding=ft.padding.symmetric(horizontal=20, vertical=12)
        ),
        visible=False
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
                    ft.Row([
                        run_button,
                        download_button
                    ]),
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
