import flet as ft
from helpers.utils import addElementsPage, getSession

username = None
id_user = None
email = None
role = None
expired = None


def list_menu_items(page: ft.Page):
    # ✅ Definimos el sidebar fuera del callback
    sidebar = ft.Container(
        bgcolor="#FFFFFF",
        width=180,
        height=200,
        padding=15,
        visible=False,
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.IconButton(
                            icon=ft.icons.CLOSE,
                            icon_size=20,
                            icon_color="black",
                            on_click=lambda _: toggle_sidebar(page, sidebar),
                        )
                    ],
                    alignment=ft.MainAxisAlignment.START,
                ),
                ft.TextButton("🚪 Logout", on_click=lambda e: handle_logout(page)),
            ],
            spacing=10,
            alignment=ft.MainAxisAlignment.START,
        ),
        border_radius=ft.border_radius.all(20),
        shadow=ft.BoxShadow(blur_radius=15, color=ft.colors.GREY_300),
        animate=ft.Animation(200, "easeInOut"),
        margin=ft.margin.only(top=90, right=20),
        alignment=ft.alignment.top_right
    )

    # Header con avatar y botón apps
    header = ft.Row(
        [
            ft.Container(
                content=ft.CircleAvatar(
                    content=ft.Image(
                        src="https://raw.githubusercontent.com/ivanarganda/images_assets/main/avatar_man.png",
                        width=50,
                        height=50,
                        border_radius=100,
                        fit=ft.ImageFit.COVER
                    ),
                    radius=25
                ),
                alignment=ft.alignment.top_left,
                padding=ft.padding.only(left=20, top=20),
            ),
            ft.Container(
                content=ft.IconButton(
                    icon=ft.icons.APPS,
                    icon_size=28,
                    icon_color="black",
                    on_click=lambda _: toggle_sidebar(page, sidebar),  # ✅ Mismo sidebar
                ),
                alignment=ft.alignment.top_right,
                padding=ft.padding.only(right=20, top=20),
            ),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        expand=True,
    )

    # Título principal
    title = ft.Container(
        content=ft.Column(
            [
                ft.Text("Welcome back,", size=28, color="black"),
                ft.Text(f"{username}", size=28, color="black"),
                ft.Text(
                    "Let's Play & Joy!",
                    size=34,
                    weight=ft.FontWeight.BOLD,
                    color="black",
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.START,
            spacing=0,
        ),
        padding=ft.padding.only(left=25, top=20),
    )

    # Botones de menú
    def menu_button(icon_url: str, label: str, route: str, size: int = 40):
        return ft.Column(
            [
                ft.Container(
                    width=size + 40,
                    height=size + 40,
                    bgcolor="#F7F7F7",
                    border_radius=40,
                    content=ft.Image(src=icon_url, width=size + 30, height=size + 30),
                    alignment=ft.alignment.center,
                    on_click=lambda _: page.go(route),
                ),
                ft.Text(label, size=20, color="#636363"),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    menu_grid = ft.Column(
        [
            ft.Row(
                [
                    menu_button(
                        "https://raw.githubusercontent.com/ivanarganda/images_assets/main/icon_tasks.png",
                        "Tasks",
                        "/tasks",
                        size=35,
                    ),
                    menu_button(
                        "https://raw.githubusercontent.com/ivanarganda/images_assets/main/icon_game.png",
                        "Games",
                        "/games",
                        size=35,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_EVENLY,
            ),
            ft.Row(
                [
                    menu_button(
                        "https://raw.githubusercontent.com/ivanarganda/images_assets/main/icon-pingpong.png",
                        "Sport",
                        "/game",
                    ),
                    menu_button(
                        "https://raw.githubusercontent.com/ivanarganda/images_assets/main/icon-space.png",
                        "Logic",
                        "/game",
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_EVENLY,
            ),
        ],
        spacing=25,
        alignment=ft.MainAxisAlignment.CENTER,
    )

    arrow_down = ft.Container(
        content=ft.Icon(
            name=ft.icons.KEYBOARD_ARROW_DOWN_ROUNDED, size=32, color="black"
        ),
        alignment=ft.alignment.bottom_center,
        padding=ft.padding.only(bottom=20),
    )

    # Card principal
    white_card = ft.Stack(
        [
            ft.Container(
                bgcolor="white",
                width=360,
                height=740,
                border_radius=ft.border_radius.all(50),
                padding=0,
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
        expand=True
    )

    # Fondo + overlay (sidebar flotante)
    background = ft.Stack(
        [
            ft.Container(
                expand=True,
                bgcolor="#F6F4FB",
                alignment=ft.alignment.center,
                content=white_card,
            )
        ]
    )

    return background


def toggle_sidebar(page, sidebar):
    sidebar.visible = not sidebar.visible
    page.update()


def handle_logout(page: ft.Page):
    page.session.clear()
    page.client_storage.clear()
    page.go("/")


def renderMainMenu(page: ft.Page):
    global username, id_user, role, expired, email

    page.title = "Main Menu"
    page.window_width = 500
    page.window_height = 800
    page.resizable = False
    page.bgcolor = "#F6F4FB"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    user = getSession(page.client_storage.get("user") or "{}", True)
    username = user.get("username", "Guest")
    id_user = int(user.get("id", 0))
    role = user.get("role", None)
    expired = user.get("exp", None)
    email = user.get("email", None)

    return addElementsPage(page, [list_menu_items(page)])
