import flet as ft
import threading
from datetime import datetime
from pathlib import Path
from params import INITTED_FOLDER
from scrap import run_scrapping  # <-- IMPORTA TU SCRIPT EXACTAMENTE
import glob


# ================================================================
# LISTA DE FICHEROS _db
# ================================================================
def get_db_files():
    pattern = f"{INITTED_FOLDER}*_db.*"
    files = glob.glob(pattern)
    return [Path(f).name for f in files]


# ================================================================
# PANEL DE CONTROL
# ================================================================
def main(page: ft.Page):
    page.title = "Scraping Control Panel"
    page.theme_mode = "light"
    page.padding = 20

    # ------------------------------------------------------------
    # LOG VIEW
    # ------------------------------------------------------------
    logs = ft.ListView(expand=True, spacing=6, auto_scroll=True)

    def log(msg):
        now = datetime.now().strftime("%H:%M:%S")
        logs.controls.append(
            ft.Text(f"[{now}] {msg}", size=13)
        )
        page.update()

    # ------------------------------------------------------------
    # LISTA DE FICHEROS
    # ------------------------------------------------------------
    files_column = ft.Column(scroll="auto")

    def refresh_files():
        files_column.controls.clear()
        for f in get_db_files():
            files_column.controls.append(
                ft.Container(
                    content=ft.Text(f"📄 {f}", size=14),
                    padding=10,
                    bgcolor="#f5f5f5",
                    border_radius=8
                )
            )
        log("Ficheros actualizados.")
        page.update()

    refresh_files()

    # ------------------------------------------------------------
    # LANZAR SCRAPING
    # ------------------------------------------------------------
    def run_scraper_clicked(e):
        run_button.disabled = True
        log("Iniciando proceso ETL + inserción en base de datos...")

        def task():
            try:
                run_scrapping()  # <-- EJECUTA TU SCRIPT ENTERO
                log("✔ Scraping + inserciones completadas.")
            except Exception as ex:
                log(f"❌ ERROR: {ex}")
            finally:
                run_button.disabled = False
                refresh_files()
                page.update()

        threading.Thread(target=task, daemon=True).start()

    run_button = ft.ElevatedButton(
        "🚀 Ejecutar Scraper",
        icon=ft.icons.DATASET,
        on_click=run_scraper_clicked,
        bgcolor="#1976D2",
        color="white",
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
    )

    refresh_button = ft.TextButton(
        "🔄 Actualizar lista",
        on_click=lambda e: refresh_files(),
    )

    # ------------------------------------------------------------
    # LAYOUT FINAL
    # ------------------------------------------------------------
    page.add(
        ft.Row(
            [
                # PANEL IZQUIERDO
                ft.Column(
                    [
                        ft.Text("⚙ Panel de Scraping", size=22, weight="bold"),
                        ft.Divider(),

                        run_button,
                        refresh_button,
                        ft.Divider(),

                        ft.Text("📂 Archivos generados (_db)", size=18),
                        ft.Container(
                            content=files_column,
                            padding=10,
                            bgcolor="#fafafa",
                            border_radius=10,
                            border=ft.border.all(1, "#ccc"),
                            width=330,
                            height=400
                        ),
                    ],
                    spacing=14,
                    expand=False,
                ),

                ft.VerticalDivider(width=2),

                # PANEL DE LOGS
                ft.Column(
                    [
                        ft.Text("📜 Logs del proceso", size=20),
                        ft.Container(
                            content=logs,
                            expand=True,
                            bgcolor="#eeeeee",
                            border_radius=10,
                            border=ft.border.all(1, "#aaa"),
                            padding=10
                        )
                    ],
                    expand=True
                )
            ],
            expand=True
        )
    )


if __name__ == "__main__":
    ft.app(target=main)