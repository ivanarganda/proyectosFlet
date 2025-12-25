import os
import flet as ft
import json
import asyncio
from params import *
from helpers.utils import addElementsPage, getSession, handle_logout, log_error, get_time_ago, convert_seconds, get_modules
from footer_navegation.navegation import footer_navbar
from middlewares.auth import middleware_auth
import requests_async as request


# Variables globales de sesión
username = id_user = email = role = expired = token = None
footer = None
modal_games = None
games = []

sidebar_ref = ft.Ref[ft.Container]()

current_path = {
    "path": os.path.abspath(__file__),
    "folder": os.path.dirname(os.path.abspath(__file__)).split("\\")[-1],
    "file": __file__.split("\\")[-1],
}

headers = HEADERS

# ===========================================================
# MENÚ: BOTONES PRINCIPALES
# ===========================================================
def menu_button(page: ft.Page, icon_url: str, label: str, route: str, on_callback=False, text_size: int=18, size: int = 55):
    try:
        return ft.Column(
            [
                ft.Container(
                    width=size + 30,
                    height=size + 30,
                    border_radius=20,
                    bgcolor=SOFA_GRAY,
                    shadow=ft.BoxShadow(
                        blur_radius=12,
                        color=ft.colors.with_opacity(0.15, "black"),
                        offset=ft.Offset(0, 3),
                    ),
                    content=ft.Image(
                        src=icon_url,
                        width=size,
                        height=size,
                        fit=ft.ImageFit.CONTAIN
                    ),
                    alignment=ft.alignment.center,
                    on_click=lambda _: (
                        safe_route(page, route)
                        if route != ""
                        else swipper_games_modal(page)
                        if on_callback == "modal"
                        else None
                    ),
                    animate_scale=ft.Animation(150, "easeOut"),
                    on_hover=lambda e: setattr(e.control, "scale", 1.07 if e.data == "true" else 1),
                ),
                ft.Text(label, size=text_size, color=SOFA_TEXT, weight=ft.FontWeight.W_600),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=2,
        )
    except Exception as e:
        log_error("menu_button", e)
        return ft.Text("⚠️ Error")

def sidebar_item(label: str, icon: str, on_click):
    return ft.Container(
        padding=10,
        border_radius=10,
        content=ft.Row(
            [
                ft.Icon(icon, size=22, color="white"),
                ft.Text(label, color="white", size=16),
            ],
            spacing=12
        ),
        on_click=on_click,
        on_hover=lambda e: setattr(
            e.control,
            "bgcolor",
            "#1E2530" if e.data == "true" else None
        ),
        animate_scale=300
    )

def update_sidebar_height(page:ft.Page):
    if footer:
        sidebar_ref.current.height = page.window_height - ( footer.height * 2 )

# ===========================================================
# MENÚ: CONTENIDO PRINCIPAL
# ===========================================================
def list_menu_items(page: ft.Page):

    MODULES_MENU = json.loads(get_modules())

    content_tabs = ft.Tabs(
        tabs=[], 
        selected_index=0 if role == "admin" else 1,
        indicator_color=SOFA_BLUE,
        divider_color="transparent",
        expand=True
    )

    avatar = ft.CircleAvatar(
            content=ft.Image(
                src="https://raw.githubusercontent.com/ivanarganda/images_assets/main/avatar_man.png",
                fit=ft.ImageFit.COVER,
            ),
            height=60,
            width=60,
            radius=100,
        )
    
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
            ref=sidebar_ref,
            width=220,
            height=( page.window.height - ( footer.height * 2 ) ),
            bgcolor=SOFA_DARK,
            border_radius=ft.border_radius.only(top_right=30, bottom_right=30),
            padding=20,
            content=ft.Column(
                [
                    avatar,
                    ft.Divider(color="white", height=20),
                    ft.Text(username or "Guest", color="white", size=18, weight="bold"),
                    ft.Text(email or "", color="#A9A9A9", size=14),
                    ft.Container(height=20),

                    ft.Text("Navigation", size=14, color="#CCCCCC"),

                    ft.Container(height=10),
                    
                    sidebar_item("Partidos", ft.Icons.SPORTS_SOCCER, lambda _: safe_route(page, "/partidos")),
                    sidebar_item("Jugadores", ft.Icons.PERSON, lambda _: safe_route(page, "/jugadores")),
                    sidebar_item("Estadios", ft.Icons.STADIUM, lambda _: safe_route(page, "/estadios")),
                    sidebar_item("Equipos", ft.Icons.GROUP, lambda _: safe_route(page, "/equipos")),
                    sidebar_item("Selecciones", ft.Icons.PUBLIC, lambda _: safe_route(page, "/selecciones")),

                    ft.Container(expand=True),

                    ft.Container(
                        bgcolor=SOFA_BLUE,
                        padding=12,
                        border_radius=12,
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.LOGOUT, color="white"),
                                ft.Text("Cerrar sesión", color="white", weight="bold"),
                            ]
                        ),
                        on_click=lambda _: handle_logout(page)
                    ),
                ],
                spacing=14
            ),
            offset=ft.Offset(-1, 0),
            visible=False,
            animate_offset=ft.Animation(350, "easeInOut")
        )



        # === HEADER =============================================================
        header = ft.Container(
            padding=ft.padding.only(left=20, right=20, top=20, bottom=10),
            content=ft.Row(
                [
                    # Avatar del usuario
                    ft.Container(
                        content=ft.CircleAvatar(
                            content=ft.Image(
                                src="https://raw.githubusercontent.com/ivanarganda/images_assets/main/avatar_man.png",
                                fit=ft.ImageFit.COVER,
                            ),
                            radius=28,
                        ),
                        on_click=lambda _: None,  # futura navegación a perfil si quieres
                        animate_scale=ft.Animation(200, "easeOut"),
                        on_hover=lambda e: setattr(e.control, "scale", 1.07 if e.data == "true" else 1),
                    ),

                    # Título central
                    ft.Text(
                        "Football Hub",
                        size=26,
                        weight=ft.FontWeight.W_700,
                        color=SOFA_TEXT,
                    ),

                    # Botón menú lateral
                    ft.Container(
                        content=ft.Icon(
                            ft.Icons.MENU,
                            size=32,
                            color=SOFA_TEXT
                        ),
                        padding=ft.padding.all(6),
                        border_radius=20,
                        on_click=lambda _: toggle_sidebar(page, sidebar),
                        animate_scale=ft.Animation(200, "easeOut"),
                        on_hover=lambda e: setattr(e.control, "scale", 1.15 if e.data == "true" else 1),
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            )
        )

        # === TITULAR ============================================================
        title = ft.Container(
            padding=ft.padding.only(left=25, top=10, right=20),
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Image(
                                src="https://raw.githubusercontent.com/ivanarganda/images_assets/main/ball_blue.png",
                                width=40,
                                height=40
                            ),
                            ft.Text(
                                "Football Analytics",
                                size=32,
                                weight=ft.FontWeight.BOLD,
                                color=SOFA_BLUE,
                            ),
                        ],
                        spacing=12,
                        alignment=ft.MainAxisAlignment.START,
                    ),

                    ft.Text(
                        "Insights powered by SofaScore",
                        size=18,
                        color="#6C6C6C",
                    ),

                    ft.Container(
                        width=180,
                        height=6,
                        border_radius=20,
                        gradient=ft.LinearGradient(
                            colors=[SOFA_BLUE, "#4BA3FF"],
                            begin=ft.Alignment(-1, 0),
                            end=ft.Alignment(1, 0),
                        ),
                        margin=ft.margin.only(top=8),
                    ),
                ],
                spacing=6,
                horizontal_alignment=ft.CrossAxisAlignment.START,
                alignment=ft.MainAxisAlignment.START
            ),
        )

        # TABS
        tabs_card = ft.Container(
            padding=15,
            border_radius=20,
            bgcolor="white",
            expand=True,
            shadow=ft.BoxShadow(
                blur_radius=25,
                spread_radius=3,
                color=ft.colors.with_opacity(0.15, "black")
            ),
            content=ft.Column(
                controls=[
                    content_tabs
                ]
            )
        )

        if MODULES_MENU is not None:

            content_tabs.tabs.clear()

            tabs = []

            tabs = list(dict.fromkeys(
                MODULES_MENU[module]["tab"]
                for module in MODULES_MENU
            ))

            for tab in tabs:
                tab_modules = [
                    module for module in MODULES_MENU.values()
                    if module["tab"] == tab and module["enabled"]
                ]

                tab_control = ft.Tab(
                    text=tab,
                    content=ft.Container(
                        padding=20,
                        content=ft.ResponsiveRow(
                            controls=[
                                ft.Container(
                                    content=menu_button(
                                        page,
                                        ICONS.get(module_info["icon"].lower().replace(" ", "_"), ""),
                                        module_name,
                                        module_info["route"],
                                        size=40
                                    ),
                                    col={"xs": 6, "sm": 4, "md": 3},
                                )
                                for module_name, module_info in MODULES_MENU.items()
                                if module_info in tab_modules and module_info["type"] in (["admin", "mix"] if role == "admin" else ["mix", "user"])
                            ]
                        )
                    )
                )

                content_tabs.tabs.append(tab_control)

        page.update()

        # === CONTENEDOR PRINCIPAL SIN ESPACIO EXTRA ==========================
        white_card = ft.Container(
            bgcolor="white",
            expand=True,
            border_radius=40,
            shadow=ft.BoxShadow(blur_radius=30, color=ft.colors.with_opacity(0.25, "black")),
            content=ft.Stack(
                [
                   ft.Column(
                        [
                            header,
                            ft.Container(height=5),
                            title,
                            ft.Container(height=20),
                            tabs_card,
                            ft.Container(height=80),  # espacio para el footer
                        ],
                        spacing=20,
                        expand=True,  # ← CLAVE
                    ),
                    sidebar
                ]
            )
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

    username = user.get("nombre", "Guest")
    id_user = int(user.get("id", 0))
    role = user.get("role")
    expired = user.get("exp")
    email = user.get("email")

    # === CONFIGURACIÓN DE LA PÁGINA ===
    page.title = "Main Menu"
    page.window_width = 800
    page.window_height = 800
    page.window_resizable = False
    page.bgcolor = "#EDF1F5"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    def on_resize(e):
        update_sidebar_height(page)
        page.update()

    update_sidebar_height(page)
    page.on_resize = on_resize

    # === CREACIÓN DE MODAL Y FOOTER ===
    footer = footer_navbar(page=page, current_path=current_path, dispatches={}, absolute=True)

    page.update()

    # === CONTENIDO PRINCIPAL ===
    main_content = list_menu_items(page)

    # === STACK GLOBAL ===
    stack = ft.Stack(
        [
            *main_content,  # menú principal
            footer,         # footer al fondo
        ],
        expand=True,
    )

    return addElementsPage(page, [stack])

