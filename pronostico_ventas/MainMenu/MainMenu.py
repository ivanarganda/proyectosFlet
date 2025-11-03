import os
import flet as ft
from params import ICONS
from helpers.utils import addElementsPage, log_error
from footer_navegation.navegation import footer_navbar

current_path = {
    "path": os.path.abspath(__file__),
    "folder": os.path.dirname(os.path.abspath(__file__)).split("\\")[-1],
    "file": __file__.split("\\")[-1]
}

footer = None


def list_menu_items(page: ft.Page):

    try:
        # === BOTÓN LOG OUT =====================================================
        btn_log_out = ft.ElevatedButton(
            text="Log out",
            width=131,
            height=46,
            content=ft.Image(
                src=ICONS.get("log_out",""),  # ruta a tu icono
                width=42,
                height=42,
                fit=ft.ImageFit.CONTAIN,
            ),
            style=ft.ButtonStyle(
                bgcolor="#667eea",
                color="#ffffff",
                elevation=3,
                shape=ft.RoundedRectangleBorder(radius=12),
                overlay_color=ft.colors.with_opacity(0.1, "white"),
            ),
        )

        # === AVATAR + USUARIO ===================================================
        avatar = ft.CircleAvatar(
            content=ft.Image(
                src="https://raw.githubusercontent.com/ivanarganda/images_assets/main/avatar_man.png",
                fit=ft.ImageFit.COVER,
            ),
            height=60,
            width=60,
            radius=100,
        )

        # Bloque central con avatar, texto y menú
        menu_section = ft.Column(
            [
                ft.Container(
                    content=avatar,
                    alignment=ft.alignment.center,
                    padding=ft.padding.only(left=20, top=20)
                ),
                ft.Text("Ivan_arganda", color="#FFFFFF", size=18, weight=ft.FontWeight.W_600),
                ft.Text("Data Analyst", color="#EAEAEA", size=13),
                ft.Divider(height=25, color=ft.colors.with_opacity(0.3, "white")),
                ft.TextButton(
                    "📘 Sales log",
                    style=_menu_style(),
                    on_click=lambda _: safe_route(page, "/historial_ventas"),
                ),
                ft.TextButton(
                    "🧠 Sales forecasting",
                    style=_menu_style(),
                    on_click=lambda _: safe_route(page, "/prediccion_ventas"),
                ),
                ft.TextButton(
                    "📊 Dashboard stats",
                    style=_menu_style(),
                    on_click=lambda _: safe_route(page, "/dashboard"),
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.START,  # 🔹 Centra verticalmente el bloque
        )

        # === SIDEBAR ===========================================================
        sidebar = ft.Container(
            content=ft.Column(
                [
                    # --- SECCIÓN SUPERIOR: AVATAR + NOMBRE ---
                    ft.Container(
                        content=menu_section,
                        padding=ft.padding.only(top=10)
                    ),
                    # --- SECCIÓN INFERIOR: BOTÓN LOGOUT ---
                    ft.Container(
                        content=btn_log_out,
                        alignment=ft.alignment.bottom_center,
                        padding=ft.padding.only(bottom=10)
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            width=230,
            height=page.window_height - ( footer.height + 40 ),
            padding=20,
            border_radius=20,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=["#667EEA", "#6E64F9", "#764BA2"],
            ),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=20,
                color=ft.colors.with_opacity(0.25, "#000000"),
                offset=ft.Offset(0, 4),
            ),
            animate_offset=ft.Animation(350, "ease_in_out"),
            offset=ft.Offset(-1, 0),
            left=0,
            top=0,
            expand=True
        )



        # === HEADER ORIGINAL (sin tocar) ======================================
        header = ft.Row(
            [
                ft.Container(
                    content=avatar,
                    alignment=ft.alignment.top_left,
                    padding=ft.padding.only(left=20, top=20),
                ),
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.icons.APPS,
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

        title = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Let's analyze!",
                        size=34,
                        weight=ft.FontWeight.BOLD,
                        color="black",
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.START,
            ),
            padding=ft.padding.only(left=25, top=20),
        )

        # === GRID DE MENÚ ======================================================
        menu_grid = ft.Column(
            [
                ft.Row(
                    [
                        _menu_button(page,ICONS.get("log", ""), "Sales log", "/historial_ventas"),
                        _menu_button(page,ICONS.get("mind_stat", ""), "Sales forecasting", "/prediccion_ventas"),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                ),
                ft.Row(
                    [
                        _menu_button(page,ICONS.get("dashboard", ""), "Dashboard stats", "/dashboard"),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                ),
            ],
            spacing=25,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        # === TARJETA PRINCIPAL =================================================
        # Reemplaza SOLO la parte del "white_card" dentro de tu código actual por esto:

        white_card = ft.Container(
            bgcolor="white",
            width=360,
            height=740,
            border_radius=ft.border_radius.all(50),
            alignment=ft.alignment.center,
            content=ft.Column(
                [
                    header,  # parte superior (avatar + icono apps)
                    ft.Container(expand=2),  # 🔹 espacio superior (más pequeño)
                    ft.Column(
                        [
                            title,
                            ft.Container(height=25),
                            menu_grid,
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=25,
                    ),
                    ft.Container(expand=3),  # 🔹 espacio inferior (más grande, empuja el bloque hacia arriba)
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            shadow=ft.BoxShadow(blur_radius=20, color="#E0E0E0"),
        )




        # === LAYOUT GENERAL ====================================================
        layout = ft.Stack(
            [
                ft.Container(
                    expand=True,
                    bgcolor="#F6F4FB",
                    alignment=ft.alignment.center,
                    content=white_card,
                ),
                sidebar,
            ],
            expand=True,
        )

        return [layout]

    except Exception as e:
        log_error("list_menu_items", e)
        return [ft.Text("❌ Error cargando menú principal")]


# === FUNCIONES AUXILIARES =====================================================
def _menu_style(bg="#6E64F9"):
    return ft.ButtonStyle(
        color="#FFFFFF",
        bgcolor=ft.colors.with_opacity(0.25, bg),
        padding=ft.padding.symmetric(vertical=10, horizontal=15),
        shape=ft.RoundedRectangleBorder(radius=12),
        overlay_color=ft.colors.with_opacity(0.15, "white"),
        elevation=1,
    )


def _menu_button(page:ft.Page,icon_url: str, label: str, route: str, size: int = 35):
    return ft.Column(
        [
            ft.Container(
                width=size + 40,
                height=size + 40,
                bgcolor="#F7F7F7",
                border_radius=40,
                content=ft.Image(src=icon_url, width=size + 20, height=size + 20),
                alignment=ft.alignment.center,
                shadow=ft.BoxShadow(blur_radius=10, color="#EAEAEA"),
                on_click=lambda _: safe_route(page, route),
            ),
            ft.Text(label, size=16, color="#636363"),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )


def toggle_sidebar(page, sidebar):
    try:
        sidebar.offset = ft.Offset(0, 0) if sidebar.offset.x < 0 else ft.Offset(-1, 0)
        page.update()
    except Exception as e:
        log_error("toggle_sidebar", e)


def safe_route(page, route):
    try:
        page.go(route)
    except Exception as e:
        log_error("safe_route", e)
        ft.SnackBar(ft.Text(f"Error al ir a {route}")).open = True
        page.update()


def renderMainMenu(page: ft.Page):

    global footer
    page.title = "Main Menu"
    page.window_width = 500
    page.window_height = 800
    page.resizable = False
    page.bgcolor = "#F6F4FB"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    footer = footer_navbar(page=page, current_path=current_path, dispatches={})

    stack = ft.Stack(
        [
            *list_menu_items(page),
            ft.Container(
                content=footer,
                bottom=0,
                left=0,
                right=0,
                bgcolor="#F6F4FB",
                shadow=ft.BoxShadow(blur_radius=12, color=ft.colors.with_opacity(0.15, "black")),
            ),
        ],
        expand=True,
    )

    return addElementsPage(page, [stack])