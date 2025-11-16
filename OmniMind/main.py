import flet as ft
from helpers.utils import getSession, notify_error
from middlewares.auth import show_session_expired_dialog
from middlewares.dev import show_development_dialog
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
async def load_scores(game_id: int, token: str, page: ft.Page):
    """Carga las puntuaciones del juego desde la API con control de errores."""
    headers = HEADERS.copy()

    if not token:
        print("⚠️ Token vacío — sesión inválida")
        show_session_expired_dialog(page)
        return {"status": 401, "message": "Unauthorized"}

    headers["Authorization"] = f"Bearer {token}"

    try:
        response = await request.get(f"{REQUEST_URL}/games/scores?id={game_id}", headers=headers)

        # Si la API responde con error HTTP
        if response.status_code == 401:
            show_session_expired_dialog(page)
            return {"status": 401, "message": "Unauthorized"}
        elif response.status_code != 200:
            return {"status": response.status_code, "message": f"Error {response.status_code}"}

        # Parsear el cuerpo de respuesta
        try:
            return response.json()
        except json.JSONDecodeError:
            return {"status": 500, "message": "Invalid JSON response"}

    except Exception as e:
        print(f"❌ Error en load_scores({game_id}): {e}")
        return {"status": 500, "message": str(e)}

# ==========================================================
# MANEJADOR DE RUTAS (main router)
# ==========================================================
def route_change(e: ft.RouteChangeEvent):
    page = e.page
    page.views.clear()

    user_data = getSession(page.client_storage.get("user") or "{}")
    token = user_data.get("token", "")
    is_logged_in = user_data.get("is_logged_in", False)
    route = page.route

    print(f"🔁 Cargando ruta: {route}")

    async def load_and_render_game(game_id: int, renderer):
        """Carga puntuaciones y renderiza el juego."""
        try:
            scores = await load_scores(game_id, token, page)
            if scores.get("status") == 401:
                return
            view = ft.View(route, [renderer(page, scores, load_scores)])
            page.views.append(view)
            page.update()
        except Exception as ex:
            print(f"❌ Error en load_and_render_game: {ex}")
            notify_error(page, f"Error cargando juego: {ex}")

    def run_async_task(coro):
        """Ejecuta una corrutina de forma segura, sin warning."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(coro)
            else:
                loop.run_until_complete(coro)
        except RuntimeError:
            asyncio.run(coro)

    try:
        # === LOGIN ===
        if route == "/":
            page.views.append(ft.View("/", [renderTemplate(page)]))

        # === MENU PRINCIPAL ===
        elif route == "/menu":
            if not is_logged_in:
                page.views.append(ft.View("/menu", [ft.Text("")]))
                show_session_expired_dialog(page)
            else:
                page.views.append(ft.View("/menu", [renderMainMenu(page)]))

        # === TASKS ===
        elif route == "/tasks":
            page.views.clear()
            if not is_logged_in:
                page.views.append(ft.View("/tasks", controls=[ft.Text("")]))
                show_session_expired_dialog(page)
            else:
                page.views.append(ft.View("/tasks", controls=[RenderTasks(page)]))
            page.update()

        elif page.route.startswith("/category/create"):
            if not is_logged_in:
                page.views.append(ft.View("//category/create", [ft.Text("")]))
                show_session_expired_dialog(page)
            else: 
                page.views.append(ft.View("/category/create", [AddCategoryTasksForm(page)]))

        elif page.route.startswith("/tasks/create/"): 
            id_category = page.route.split("/")[-1]
            if not is_logged_in:
                page.views.append(ft.View(f"/tasks/create/{id_category}", [ft.Text("")]))
                show_session_expired_dialog(page)
            else: 
                page.views.append(ft.View(f"/tasks/create/{id_category}", [AddTaskForm(page, id_category)]))
        
        elif page.route.startswith("/category/details/"): 
            category = page.route.split("/")[-1] 
            if not is_logged_in:
                page.views.append(ft.View(f"/category/details/{category}", [ft.Text("")]))
                show_session_expired_dialog(page)
            else:
                page.views.append(ft.View(f"/category/details/{category}", [loadDetailsCategory(page, category)]))

        # === GAMES ===
        elif route == "/games/random_number":

            if not is_logged_in:
                page.views.append(ft.View(f"/games/random_number", [ft.Text("")]))
                show_session_expired_dialog(page)
            else:
                # Muestra una vista base vacía o con un mensaje
                page.views.append(
                    ft.View("/games/random_number", [
                        ft.Container(
                            alignment=ft.alignment.center,
                            content=ft.Text("⚙️ Cargando módulo...", color="white")
                        )
                    ])
                )

                # ✅ Mostrar el diálogo *fuera* de la vista TODO esta en desarrollo
                show_development_dialog(page, "Game of Random Number")

                page.update()
                return False
                run_async_task(load_and_render_game(1, renderGameRandomNumber ))
                
        elif route == "/games/chess":

            if not is_logged_in:
                page.views.append(ft.View(f"/games/chess", [ft.Text("")]))
                show_session_expired_dialog(page)
            else:
                # Muestra una vista base vacía o con un mensaje
                page.views.append(
                    ft.View("/games/chess", [
                        ft.Container(
                            alignment=ft.alignment.center,
                            content=ft.Text("⚙️ Cargando módulo...", color="white")
                        )
                    ])
                )

                # ✅ Mostrar el diálogo *fuera* de la vista TODO esta en desarrollo
                show_development_dialog(page, "Game of Chess")

                page.update()
                return False
                run_async_task(load_and_render_game(1, renderGameRandomNumber ))

        elif route == "/games/tetris":
            if not is_logged_in:
                page.views.append(ft.View("/games/tetris", [ft.Text("")]))
                show_session_expired_dialog(page)
            else:
                run_async_task(load_and_render_game(2, render_tetris ))

        # === 404 ===
        else:
            page.views.append(ft.View("/404", [ft.Text("Página no encontrada")]))
        
        page.update()

    except Exception as e:
        print(f"❌ Error al cambiar de ruta ({route}): {e}")
        snack = ft.SnackBar(ft.Text(f"Error: {e}"))
        page.overlay.append(snack)
        snack.open = True
        page.update()

# ==========================================================
# FUNCIÓN PRINCIPAL
# ==========================================================
def main(page: ft.Page):
    page.title = "OmniMind"
    page.on_route_change = route_change

    # Recuperar sesión
    user_data = getSession(page.client_storage.get("user") or "{}")
    is_logged_in = user_data.get("is_logged_in", False)

    if is_logged_in:
        print("✅ Sesión activa. Cargando menú principal...")
        page.go("/tasks")
    else:
        print("⚠️ No hay sesión activa. Redirigiendo al login...")
        page.go("/")


# ==========================================================
# INICIO DE APLICACIÓN
# ==========================================================
ft.app(target=main)
