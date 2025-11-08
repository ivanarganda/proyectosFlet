import flet as ft
from helpers.utils import getSession
from LoginRegisterForm.LoginRegisterForm import renderTemplate
from MainMenu.MainMenu import renderMainMenu
from Tasks.Tasks import RenderTasks
from Tasks.views.details_category import loadDetailsCategory
from Tasks.views.AddCategoryTasksForm import AddCategoryTasksForm
from Tasks.views.AddTaskForm import AddTaskForm
from Games.RandomNumber import renderGameRandomNumber
from Games.Tetris import render_tetris
from params import REQUEST_URL, HEADERS
import requests_async as request
import asyncio


# ==========================================================
# CARGA DE PUNTUACIONES CON MANEJO DE ERRORES
# ==========================================================
async def load_scores(game_id: int, token: str):
    headers = HEADERS.copy()
    headers["Authorization"] = f"Bearer {token}"

    try:
        response = await request.get(f"{REQUEST_URL}/games/scores?id={game_id}", headers=headers)
        if response.status_code == 401:
            return {"error": "session_expired"}
        elif response.status_code != 200:
            return {"error": f"HTTP {response.status_code}"}

        data = response.json()
        return data

    except Exception as e:
        print(f"❌ Error en load_scores({game_id}): {e}")
        return {"error": str(e)}


# ==========================================================
# DIALOGO DE SESIÓN EXPIRADA
# ==========================================================
def show_session_expired_dialog(page: ft.Page):
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("⚠️ Sesión expirada", size=18, weight=ft.FontWeight.BOLD),
        content=ft.Text(
            "Tu sesión ha caducado o es inválida.\nPor favor, vuelve a iniciar sesión.",
            size=14,
        ),
        actions=[
            ft.TextButton(
                "Ir al login",
                on_click=lambda e: (
                    setattr(dialog, "open", False),
                    page.overlay.remove(dialog),
                    page.update(),
                    page.go("/")
                ),
            )
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    if dialog not in page.overlay:
        page.overlay.append(dialog)
    dialog.open = True
    page.update()
    return dialog


# ==========================================================
# MANEJADOR PRINCIPAL
# ==========================================================
def main(page: ft.Page):
    page.title = "OmniMind"
    page.on_route_change = route_change

    # Recuperar sesión
    user_data = getSession(page.client_storage.get("user") or "{}")
    is_logged_in = user_data.get("is_logged_in", False)

    # Redirigir según sesión
    if not is_logged_in:
        print("⚠️ No hay sesión activa. Redirigiendo al login...")
        page.go("/")
    else:
        print("✅ Sesión activa. Cargando menú principal...")
        page.go("/menu")


# ==========================================================
# MANEJADOR DE RUTAS
# ==========================================================
def route_change(e: ft.RouteChangeEvent):
    page = e.page
    page.views.clear()

    user_data = getSession(page.client_storage.get("user") or "{}")
    token = user_data.get("token", "")
    is_logged_in = user_data.get("is_logged_in", False)

    try:
        # ============================
        # RUTA DE LOGIN (PÚBLICA)
        # ============================
        if page.route == "/":
            page.views.append(ft.View("/", [renderTemplate(page)]))

        # ============================
        # RUTAS PROTEGIDAS
        # ============================
        elif page.route == "/menu":
            if not is_logged_in:
                return show_session_expired_dialog(page)
            page.views.append(ft.View("/menu", [renderMainMenu(page)]))

        elif page.route == "/games":
            if not is_logged_in:
                return show_session_expired_dialog(page)
            page.views.append(ft.View("/games", [ft.Text("Selecciona un juego")]))

        elif page.route == "/games/random_number":
            if not is_logged_in:
                return show_session_expired_dialog(page)
            scores = asyncio.run(load_scores(1, token))
            if "error" in scores:
                if scores["error"] == "session_expired":
                    return show_session_expired_dialog(page)
            page.views.append(ft.View("/games/random_number", [renderGameRandomNumber(page, scores)]))

        elif page.route == "/games/tetris":
            if not is_logged_in:
                return show_session_expired_dialog(page)
            scores = asyncio.run(load_scores(2, token))
            if "error" in scores:
                if scores["error"] == "session_expired":
                    return show_session_expired_dialog(page)
            page.views.append(ft.View("/games/tetris", [render_tetris(page, scores)]))

        elif page.route == "/tasks":
            if not is_logged_in:
                return show_session_expired_dialog(page)
            page.views.append(ft.View("/tasks", [RenderTasks(page)]))

        elif page.route.startswith("/category/create"):
            if not is_logged_in:
                return show_session_expired_dialog(page)
            page.views.append(ft.View("/category/create", [AddCategoryTasksForm(page)]))

        elif page.route.startswith("/tasks/create/"):
            if not is_logged_in:
                return show_session_expired_dialog(page)
            id_category = page.route.split("/")[-1]
            page.views.append(ft.View(f"/tasks/create/{id_category}", [AddTaskForm(page, id_category)]))

        elif page.route.startswith("/category/details/"):
            if not is_logged_in:
                return show_session_expired_dialog(page)
            category = page.route.split("/")[-1]
            page.views.append(ft.View(f"/category/details/{category}", [loadDetailsCategory(page, category)]))

        page.update()

    except Exception as e:
        print(f"❌ Error al cambiar de ruta ({page.route}): {e}")
        page.snack_bar = ft.SnackBar(ft.Text(f"Error: {e}"))
        page.snack_bar.open = True
        page.update()


# ==========================================================
# INICIO DE APLICACIÓN
# ==========================================================
ft.app(target=main)
