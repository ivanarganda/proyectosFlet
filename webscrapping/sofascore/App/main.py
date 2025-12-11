import flet as ft
from helpers.utils import getSession, notify_error
from middlewares.auth import show_session_expired_dialog
from middlewares.dev import show_development_dialog
from LoginRegisterForm.LoginRegisterForm import renderTemplate
from MainMenu.MainMenu import renderMainMenu
from MainMenu.Views.ControlPanel.scraper_ui import RenderScrapper
from params import REQUEST_URL, HEADERS
import requests_async as request
import asyncio

from MainMenu.Views.Info.partidos import RenderPartidos
from MainMenu.Views.Info.jugadores import RenderJugadores
from MainMenu.Views.Info.estadiscitas_jugadores import RenderEstadisticasJugadores
from MainMenu.Views.Info.estadios import RenderEstadios
from MainMenu.Views.Info.equipos import RenderEquipos
from MainMenu.Views.Info.selecciones import RenderSelecciones
from MainMenu.Views.Info.clasificaciones import RenderClasificaciones

# Mapa de ruta → componente
INFO_VIEWS = {
    "/info/partidos": RenderPartidos,
    "/info/jugadores": RenderJugadores,
    "/info/estadisticas_jugador": RenderEstadisticasJugadores,
    "/info/estadios": RenderEstadios,
    "/info/equipos": RenderEquipos,
    "/info/selecciones": RenderSelecciones,
    "/info/clasificaciones": RenderClasificaciones
}

# ==========================================================
# CARGA DE PUNTUACIONES CON MANEJO DE ERRORES
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
        elif route == "/scrapping":
            page.views.clear()
            if not is_logged_in:
                page.views.append(ft.View("/scrapping", controls=[ft.Text("")]))
                show_session_expired_dialog(page)
            else:
                page.views.append(ft.View("/scrapping", controls=[RenderScrapper(page)]))
            page.update()
        
        # === INFO ===
        elif "/info" in route:
            
            if route not in INFO_VIEWS:
                page.views.append(ft.View("/404", [ft.Text("Página no encontrada")]))
                return

            page.views.clear()

            if not is_logged_in:
                page.views.append(ft.View(route, controls=[ft.Text("")]))
                show_session_expired_dialog(page)
            else:
                print(route)
                page.views.append(ft.View(route, controls=[INFO_VIEWS.get(route)(page)]))

            page.update()

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
    page.title = "Sofascore management"
    page.on_route_change = route_change

    # Recuperar sesión
    user_data = getSession(page.client_storage.get("user") or "{}")
    is_logged_in = user_data.get("is_logged_in", False)

    if is_logged_in:
        print("✅ Sesión activa. Cargando menú principal...")
        page.go("/menu")
    else:
        print("⚠️ No hay sesión activa. Redirigiendo al login...")
        page.go("/")

# ==========================================================
# INICIO DE APLICACIÓN
# ==========================================================
ft.app(target=main)