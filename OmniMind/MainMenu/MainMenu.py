import os
import flet as ft
import json
import asyncio
from params import ICONS, REQUEST_URL, HEADERS
from helpers.utils import addElementsPage, getSession, handle_logout, log_error, get_time_ago
from footer_navegation.navegation import footer_navbar
from middlewares.auth import middleware_auth
import requests_async as request


# Variables globales de sesión
username = id_user = email = role = expired = token = None
footer = None
modal_games = None

current_path = {
    "path": os.path.abspath(__file__),
    "folder": os.path.dirname(os.path.abspath(__file__)).split("\\")[-1],
    "file": __file__.split("\\")[-1],
}

headers = HEADERS

def create_modal_games(page):

    async def load_games():

        response = await request.get( f"{REQUEST_URL}/games/scores" , headers=headers  )
        return response.json()


    data = asyncio.run( load_games() )

    if data.get("status") == 401 and data.get("message") == "Unauthorized":
        handle_logout(page)

    games = []

    for key, item in enumerate( data.get("message") ):
        last_played = get_time_ago(item.get('last_played', ''))
        games.append(
            ft.Container(
                content=ft.Column(
                    [
                        menu_button(page, ICONS.get(item.get("icon_name", ""), ""), item.get("alias", ""), item.get("path", ""), text_size=12),
                        ft.Text(f"🏆 {item.get('score', 0)} pts", size=11, color="#94a3b8"),
                        ft.Text(f"⚙️ Lv.{item.get('level', 1)}", size=11, color="#94a3b8"),
                        ft.Text(f"⏱️ {item.get('duration', 0)} s", size=11, color="#94a3b8"),
                        ft.Text(f"🔄 {last_played}", size=10, color="#64748b", text_align="center"),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                    spacing=2,
                )
            )
        )

    print( games )

    return ft.Container(
        content=ft.Stack(
            [
                ft.Container(
                    width=page.window_width - 40,
                    height=420,
                    bgcolor="#ffffff",
                    border_radius=25,
                    shadow=ft.BoxShadow(
                        spread_radius=1,
                        blur_radius=25,
                        color=ft.colors.with_opacity(0.25, "#000000"),
                        offset=ft.Offset(0, 5),
                    ),
                    content=ft.Column(
                        [
                            ft.Text(
                                "🎮 Choose your game",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color="#333333",
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Divider(height=10, color="transparent"),
                            ft.Row(
                                controls=games,
                                alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=10
                            ),
                            ft.Divider(height=20, color="transparent"),
                            ft.Text(
                                "Tap an icon to start playing!",
                                size=14,
                                color="#777777",
                                italic=True,
                                text_align=ft.TextAlign.CENTER,
                            )
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=15,
                    ),
                    alignment=ft.alignment.center,
                    padding=ft.padding.symmetric(horizontal=20, vertical=25),
                ),
                ft.Container(
                    width=48,
                    height=48,
                    right=10,
                    top=10,
                    bgcolor="#f5f5f5",
                    border_radius=30,
                    shadow=ft.BoxShadow(
                        blur_radius=10,
                        color=ft.colors.with_opacity(0.2, "#000000")
                    ),
                    content=ft.Icon(ft.Icons.CLOSE, size=28, color="#333333"),
                    alignment=ft.alignment.center,
                    on_click=lambda _: swipper_games_modal(page),
                    ink=True,
                )
            ]
        ),
        alignment=ft.alignment.center,
        bgcolor=ft.colors.with_opacity(0.4, "#000000"),  # fondo translúcido
        padding=ft.padding.all(20),
        border_radius=ft.border_radius.all(20),
        visible=True,  # lo mantenemos en el stack, pero invisible hasta que se muestre  TODO desabilitar
        expand=True,
    )


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
                ft.Divider(height=25, color=ft.Colors.with_opacity(0.3, "white")),
                ft.TextButton("📘 Tasks", on_click=lambda _: page.go("/tasks")),
                ft.TextButton("🧠 Games", on_click=lambda _: swipper_games_modal(page)),
                ft.TextButton("📊 Data management", on_click=lambda _: page.go("/dataMind")),
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
                        menu_button(page, ICONS.get("tasks", ""), "Tasks", "/tasks", size=35),
                        menu_button(page, ICONS.get("games", ""), "Games", "", on_callback='modal', size=35),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                ),
                ft.Row(
                    [
                        menu_button(page, ICONS.get("dataMind", ""), "Data management", "/dataMind"),
                        menu_button(page, ICONS.get("foro", ""), "Stats foro", "/foro"),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                ),
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

