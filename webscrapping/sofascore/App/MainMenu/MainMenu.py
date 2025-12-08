import os
import flet as ft
import json
import asyncio
from params import ICONS, REQUEST_URL, HEADERS
from helpers.utils import addElementsPage, getSession, handle_logout, log_error, get_time_ago, convert_seconds
from footer_navegation.navegation import footer_navbar
from middlewares.auth import middleware_auth
import requests_async as request


# Variables globales de sesión
username = id_user = email = role = expired = token = None
footer = None
modal_games = None
games = []

current_path = {
    "path": os.path.abspath(__file__),
    "folder": os.path.dirname(os.path.abspath(__file__)).split("\\")[-1],
    "file": __file__.split("\\")[-1],
}

headers = HEADERS

# ===========================================================
# MENÚ: BOTONES PRINCIPALES
# ===========================================================
def menu_button(page: ft.Page, icon_url: str, label: str, route: str, on_callback=False, text_size: int= 20, size: int = 40):
    try:
        return ft.Column(
            [
                ft.Container(
                    width=size + 40,
                    height=size + 40,
                    bgcolor="#F7F7F7",
                    border_radius=40,
                    content=ft.Image(src=icon_url, width=size + 30, height=size + 30),
                    alignment=ft.alignment.center,
                    on_click=lambda _: (
                        safe_route(page, route)
                        if route != ""
                        else swipper_games_modal(page)
                        if on_callback == "modal"
                        else None
                    ),
                ),
                ft.Text(label, size=text_size, color="#636363"),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    except Exception as e:
        log_error(f"menu_button({label})", e)
        return ft.Text(f"⚠️ Error en {label}")



# ===========================================================
# MENÚ: CONTENIDO PRINCIPAL
# ===========================================================
def list_menu_items(page: ft.Page):
    
    try:
        # === BOTÓN LOGOUT =======================================================
        btn_log_out = ft.ElevatedButton(
            text="Log out",
            width=131,
            height=46,
            content=ft.Image(
                src=ICONS.get("log_out", ""),
                width=42,
                height=42,
                fit=ft.ImageFit.CONTAIN,
            ),
            style=ft.ButtonStyle(
                bgcolor="#667eea",
                color="#ffffff",
                elevation=3,
                shape=ft.RoundedRectangleBorder(radius=12),
                overlay_color=ft.Colors.with_opacity(0.1, "white"),
            ),
            on_click=lambda _: handle_logout(page),
        )

        # === AVATAR + INFO ======================================================
        avatar = ft.CircleAvatar(
            content=ft.Image(
                src="https://raw.githubusercontent.com/ivanarganda/images_assets/main/avatar_man.png",
                fit=ft.ImageFit.COVER,
            ),
            height=60,
            width=60,
            radius=100,
        )

        menu_section = ft.Column(
            [
                ft.Container(content=avatar, alignment=ft.alignment.center, padding=ft.padding.only(left=20, top=20)),
                ft.Text(username or "Guest", color="black", size=18, weight=ft.FontWeight.W_600),
                ft.Text("Data Analyst", color="#888888", size=13),
                ft.Divider(height=25, color=ft.Colors.with_opacity(0.3, "white"))
            ],
            horizontal_alignment=ft.CrossAxisAlignment.START,
            alignment=ft.MainAxisAlignment.START,
        )

        # === SIDEBAR ============================================================
        sidebar = ft.Container(
            width=200,
            height=page.window_height - (footer.height + 60),
            bgcolor=ft.colors.with_opacity(0.85, "#FFFFFF"),
            border_radius=ft.border_radius.only(top_right=30, bottom_right=30),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=25,
                color=ft.colors.with_opacity(0.25, "#000000"),
                offset=ft.Offset(0, 4),
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=25),
            content=ft.Column(
                [
                    ft.Container(
                        content=menu_section,
                    ),
                    ft.Container(expand=True),
                    ft.Container(
                        width=150,
                        height=46,
                        border_radius=ft.border_radius.all(12),
                        gradient=ft.LinearGradient(
                            begin=ft.Alignment(-1, 0),
                            end=ft.Alignment(1, 0),
                            colors=["#667eea", "#764ba2"],
                        ),
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.LOGOUT_ROUNDED, color="white", size=22),
                                ft.Text("Log out", color="white", size=15, weight=ft.FontWeight.W_500),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=8,
                        ),
                        on_click=lambda _: handle_logout(page),
                        shadow=ft.BoxShadow(blur_radius=12, color=ft.colors.with_opacity(0.2, "#000000")),
                        alignment=ft.alignment.center,
                        animate_scale=ft.Animation(200, "ease_in_out"),
                        on_hover=lambda e: setattr(e.control, "scale", 1.05 if e.data == "true" else 1),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            animate_offset=ft.Animation(350, "ease_in_out"),
            offset=ft.Offset(-1, 0),
            left=0,
            top=0,
            visible=False
        )


        # === HEADER =============================================================
        header = ft.Row(
            [
                ft.Container(content=avatar, alignment=ft.alignment.top_left, padding=ft.padding.only(left=20, top=20)),
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.Icons.APPS,
                        icon_size=28,
                        icon_color="black",
                        on_click=lambda _: toggle_sidebar(page, sidebar),
                    ),
                    alignment=ft.alignment.top_right,
                    padding=ft.padding.only(right=20, top=20),
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            expand=True,
        )

        # === TITULAR ============================================================
        title = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Welcome back,", size=28, color="black"),
                    ft.Text(f"{username or 'Guest'}", size=28, color="black"),
                    ft.Text("Let's Play & Joy!", size=34, weight=ft.FontWeight.BOLD, color="black"),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.START,
                spacing=0,
            ),
            padding=ft.padding.only(left=25, top=20),
        )

        # === BOTONES DE MENÚ ====================================================
        menu_grid = ft.Column(
            [
                ft.Row(
                    [
                        menu_button(page, ICONS.get("tasks", ""), "Scrapping", "/scrapping", size=35)
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                )
            ],
            spacing=25,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        arrow_down = ft.Container(
            content=ft.Icon(name=ft.Icons.KEYBOARD_ARROW_DOWN_ROUNDED, size=32, color="black"),
            alignment=ft.alignment.bottom_center,
            padding=ft.padding.only(bottom=20),
        )

        white_card = ft.Stack(
            [
                ft.Container(
                    bgcolor="white",
                    width=360,
                    height=740,
                    border_radius=ft.border_radius.all(50),
                    alignment=ft.alignment.top_center,
                    content=ft.Column(
                        [
                            header,
                            ft.Container(height=10),
                            title,
                            ft.Container(height=30),
                            menu_grid,
                            ft.Container(expand=True),
                            arrow_down,
                        ],
                        alignment=ft.MainAxisAlignment.START,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    shadow=ft.BoxShadow(blur_radius=20, color="#E0E0E0"),
                ),
                sidebar
            ],
            expand=True,
        )

        return [
            ft.Container(
                expand=True,
                bgcolor="#F6F4FB",
                alignment=ft.alignment.center,
                content=white_card,
            )
        ]

    except Exception as e:
        log_error("list_menu_items", e)
        return [ft.Text("❌ Error cargando menú principal")]


# ===========================================================
# FUNCIONES AUXILIARES
# ===========================================================
def swipper_games_modal(page):
    global modal_games

    modal_games.visible = not modal_games.visible

    if modal_games.visible:
        # 🔁 recargar juegos al abrir el modal
        new_games = asyncio.run(render_games(page))

        # Buscar el Column dentro del modal
        stack = modal_games.content  # Stack
        if not isinstance(stack, ft.Stack):
            return

        # Buscar el Container principal dentro del Stack
        container_main = None
        for ctrl in stack.controls:
            if isinstance(ctrl, ft.Container) and isinstance(ctrl.content, ft.Column):
                container_main = ctrl
                break

        if container_main:
            column_main = container_main.content
            # Buscar el Row donde están los juegos
            for ctrl in column_main.controls:
                if isinstance(ctrl, ft.Row):
                    ctrl.controls = new_games
                    break

        page.update()
    else:
        page.update()


def safe_route(page, route):
    """Protege el cambio de ruta para evitar errores de navegación."""
    try:
        if not route.startswith("/"):
            raise ValueError(f"Ruta inválida: {route}")
        page.go(route)
    except Exception as e:
        log_error("safe_route", e)
        sb = ft.SnackBar(ft.Text(f"Error al ir a {route}"))
        page.overlay.append(sb)
        sb.open = True
        page.update()


def toggle_sidebar(page, sidebar):
    try:
        sidebar.visible = not sidebar.visible
        sidebar.offset = ft.Offset(0, 0) if sidebar.offset.x < 0 else ft.Offset(-1, 0)
        page.update()
    except Exception as e:
        log_error("toggle_sidebar", e)


# ===========================================================
# FUNCIÓN PRINCIPAL DEL MENÚ
# ===========================================================
def renderMainMenu(page: ft.Page):
    global username, id_user, role, expired, email, token, footer, modal_games, headers

    session = middleware_auth(page)
    if not session or not isinstance(session, dict):
        log_error("renderMainMenu", TypeError("middleware_auth devolvió None o tipo no dict"))
        session = {}

    user = session.get("session", {}) or {}
    token = session.get("token")
    headers["Authorization"] = f"Bearer {token}"

    username = user.get("username", "Guest")
    id_user = int(user.get("id", 0))
    role = user.get("role")
    expired = user.get("exp")
    email = user.get("email")

    # === CONFIGURACIÓN DE LA PÁGINA ===
    page.title = "Main Menu"
    page.window_width = 550
    page.window_height = 800
    page.window_resizable = False
    page.bgcolor = "#F6F4FB"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    # === CREACIÓN DE MODAL Y FOOTER ===
    modal_games = create_modal_games(page)
    footer = footer_navbar(page=page, current_path=current_path, dispatches={})

    page.update()

    # === CONTENIDO PRINCIPAL ===
    main_content = list_menu_items(page)

    # === STACK GLOBAL ===
    stack = ft.Stack(
        [
            *main_content,  # menú principal
            footer,         # footer al fondo
            modal_games,    # 🔥 modal encima de todo
        ],
        expand=True,
    )

    return addElementsPage(page, [stack])

