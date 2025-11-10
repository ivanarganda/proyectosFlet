import flet as ft
from helpers.utils import getSession, handle_logout, log_error
def middleware_auth( page )-> dict:
    try:
        # Sesión
        session = page.client_storage.get("user") or "{}"
        token_session = getSession( session ).get("token",None)
        user_session = getSession( session, True ) or None

        if token_session == None or user_session == None:
            handle_logout(page)

        # Optional object to get whatever necessary items 
        return {
            "token": token_session,
            "session": user_session
        }
    except Exception as e:
        log_error("⚠️ middleware_auth error:", e)
        handle_logout(page)

# ==========================================================
# DIALOGO DE SESIÓN EXPIRADA
# ==========================================================
def show_session_expired_dialog(page: ft.Page):
    print("⚠️ Mostrando diálogo de sesión expirada...")

    def go_to_login(e=None):
        dialog.open = False
        page.update()
        page.go("/")

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("⚠️ Sesión expirada", size=18, weight=ft.FontWeight.BOLD),
        content=ft.Text(
            "Tu sesión ha caducado o es inválida.\nPor favor, vuelve a iniciar sesión.",
            size=14,
        ),
        actions=[ft.TextButton("Ir al login", on_click=go_to_login)],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    # ⚠️ Correcto en versiones ≥0.24.0
    if dialog not in page.overlay:
        page.overlay.append(dialog)

    dialog.open = True
    page.update()

    return dialog