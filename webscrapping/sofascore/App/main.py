import flet as ft
from helpers.utils import getSession, notify_error
from middlewares.auth import show_session_expired_dialog
from middlewares.dev import show_development_dialog
from LoginRegisterForm.LoginRegisterForm import renderTemplate
from MainMenu.MainMenu import renderMainMenu
from params import REQUEST_URL, HEADERS
import requests_async as request
import asyncio
from urllib.parse import parse_qs

# MANAGEMENT
from MainMenu.Views.ControlPanel.scraper_ui import RenderScrapper

# INFO
from MainMenu.Views.Info.partidos import RenderPartidos
from MainMenu.Views.Info.jugadores import RenderJugadores
from MainMenu.Views.Info.estadios import RenderEstadios
from MainMenu.Views.Info.equipos import RenderEquipos
from MainMenu.Views.Info.selecciones import RenderSelecciones
from MainMenu.Views.Info.clasificaciones.clasificaciones import RenderClasificaciones
from MainMenu.Views.Info.estadisticas.estadisticas import RenderDashboard

# ML
from MainMenu.Views.ML.prediccion_resultados import RenderMLPrediccionResultados

MANAGEMENT_VIEWS = {
    "/management/scrapping": RenderScrapper,
}

# Mapa de ruta → componente
INFO_VIEWS = {
    "/info/partidos": RenderPartidos,
    "/info/jugadores": RenderJugadores,
    "/info/estadios": RenderEstadios,
    "/info/equipos": RenderEquipos,
    "/info/selecciones": RenderSelecciones,
    "/info/clasificaciones": RenderClasificaciones,
    "/info/dashboard": RenderDashboard
}

STATS_VIEWS = {
    "stats/"
}

ML_VIEWS = {
    "/ml/predicciones/resultados":RenderMLPrediccionResultados
}

is_logged_in = False

def render_view(page, dispatches_views, route):

    global is_logged_in

    if "?" in route:
        route_only, raw_params = route.split("?", 1)
        params = {k: v[0] for k, v in parse_qs(raw_params).items()}
    else:
        route_only = route
        params = {}

    view_func = dispatches_views.get(route_only)
    if view_func is None:
        return ft.View(
            "/404",
            controls=[ft.Text(f"❌ Ruta no encontrada: {route_only}", size=20)]
        )

    if not is_logged_in:
        show_session_expired_dialog(page)
        return ft.View(
            route_only,
            controls=[ft.Text("Sesión expirada...")]
        )

    try:
        view_content = view_func(page, params)
    except Exception as e:
        print("❌ Error renderizando vista:", e)
        return ft.View(
            "/500",
            controls=[ft.Text(f"❌ Error interno: {str(e)}")]
        )

    return ft.View(
        route_only,
        controls=[view_content],
        scroll=ft.ScrollMode.AUTO
    )

def create_view(page, dispatches, route):

    page.views.clear()
    page.views.append(render_view(page, dispatches, route))
    page.update()

def route_change(e: ft.RouteChangeEvent):

    global is_logged_in

    page = e.page
    page.views.clear()

    user_data = getSession(page.client_storage.get("user") or "{}")
    token = user_data.get("token", "")
    is_logged_in = user_data.get("is_logged_in", False)
    route = page.route

    print(f"🔁 Cargando ruta: {route}")

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
        elif "management" in route:

            create_view( page, MANAGEMENT_VIEWS , route )
        
        # === INFO ===
        elif "info" in route:
                 
            create_view( page, INFO_VIEWS , route )

        # === INFO ===
        elif "ml" in route:
                 
            create_view( page, ML_VIEWS , route )

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