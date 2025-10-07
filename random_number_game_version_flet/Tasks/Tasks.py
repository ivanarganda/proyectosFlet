import flet as ft
from helpers.utils import getSession, addElementsPage, setGradient, setInputField

input_search_field = setInputField("search", placeholder="Look for...")

def loadTasks(page: ft.Page):

    return tasks = (
        ft.Column(
            [
                ft.Text("Icon"),
                ft.Text("Task1"),
                ft.Text("5 tasks")
            ]
        ),
        ft.Column(
            [
                ft.Text("Icon"),
                ft.Text("Task1"),
                ft.Text("5 tasks")
            ]
        ),
        ft.Column(
            [
                ft.Text("Icon"),
                ft.Text("Task1"),
                ft.Text("5 tasks")
            ]
        )

     ) # TODO fetch all tasks from api /tasks

    tasks = ft.GridView(
        expand=1,
        runs_count=5
        child_aspect_ratio=1.0,
        spacing=5,
        run_spacing=5,
    )

    return ft.Column(
        [
            ft.Text("Categories"),
            tasks
        ],
        width=page.window_width,
        alignment=ft.alignment.CENTER
    )

def ListTasks(page: ft.Page):
    # Fondo degradado azul

    input_search = ft.Container(
        input_search_field
    )

    backwallpaper = ft.Container(
        expand=True,
        gradient=setGradient("black-blue"),
        alignment=ft.alignment.top_center,
        content=
    )

    # Header fijo arriba del todo
    header = ft.Container(
        width=page.window_width,
        top=0,  # lo fija en la parte superior
        left=0,
        right=0,
        padding=ft.padding.only(left=25, right=25, top=40, bottom=10),
        content= ft.Column(
            [
                ft.Row(
                    [
                        # Columna izquierda: saludo + nombre
                        ft.Column(
                            [
                                ft.Text("Hello", size=22, color="white", weight=ft.FontWeight.BOLD),
                                ft.Text("Ivan_arganda_96", size=18, color="white"),  # TODO sesión
                            ],
                            spacing=4,
                            alignment=ft.MainAxisAlignment.START,
                            horizontal_alignment=ft.CrossAxisAlignment.START,
                            expand=True,
                        ),
                        # Avatar a la derecha
                        ft.CircleAvatar(
                            foreground_image_url="https://raw.githubusercontent.com/ivanarganda/images_assets/main/avatar_man.png",
                            radius=25,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                input_search
            ]
        )
        
    )

    # Card blanca en la parte inferior
    content_area = ft.Container(
        bgcolor="#F6F4FB",
        border_radius=ft.border_radius.only(top_left=30, top_right=30),
        height=400,  # altura de la card
        bottom=0,    # 👈 la anclamos al fondo
        left=0,
        right=0,
        alignment=ft.alignment.top_center,
        shadow=ft.BoxShadow(
            spread_radius=-10,
            blur_radius=25,
            color=ft.colors.with_opacity(0.3, "#000000")
        ),
    )

    # Stack general: degradado + card blanca + header arriba
    background = ft.Stack(
        [
            backwallpaper,  # fondo degradado
            content_area,   # card blanca encima del degradado
            header,         # header fijo arriba
        ],
        expand=True,
    )

    return background


def RenderTasks(page: ft.Page):
    page.title = "Tasks"
    page.window_width = 500
    page.window_height = 900
    page.window_resizable = False
    page.bgcolor = "#000000"  # fondo base detrás del degradado
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.START

    return addElementsPage(page, [ListTasks(page)])
