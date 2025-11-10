import flet as ft
from helpers.utils import getSession, handle_logout, log_error, addElementsPage

def show_development_dialog(page: ft.Page, title: str = ""):
    print("⚠️ Mostrando diálogo de mantenimiento...")

    def go_to_menu(e=None):
        dialog.open = False
        page.update()
        page.go("/menu")

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("⚠️ En mantenimiento", size=18, weight=ft.FontWeight.BOLD),
        content=ft.Text(
            f"La aplicación está en desarrollo ({title})",
            size=14,
        ),
        actions=[ft.TextButton("Volver al menú", on_click=go_to_menu)],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    # Correcto en versiones ≥ 0.24.0
    if dialog not in page.overlay:
        page.overlay.append(dialog)

    dialog.open = True
    page.update()
