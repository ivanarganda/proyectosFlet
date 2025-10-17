import flet as ft

def footer_navbar(page: ft.Page, current_path, addCategory ):

    full_path = current_path["path"]
    folder = current_path["folder"]
    file = current_path["file"]
    page.bgcolor = ft.colors.WHITE

    footer = ft.Container(
        content=ft.Row(
            [
                ft.IconButton(ft.icons.HOME, icon_color="#4e73df"),
                ft.IconButton(ft.icons.SEARCH, icon_color="#4e73df"),
                ft.FloatingActionButton(on_click=lambda _: addCategory(page), icon=ft.icons.ADD, bgcolor="#4e73df", visible= folder == 'Tasks' ),
                ft.IconButton(ft.icons.NOTIFICATIONS, icon_color="#4e73df"),
                ft.IconButton(ft.icons.PERSON, icon_color="#4e73df", visible= folder != 'Profile'),
            ],
            alignment=ft.MainAxisAlignment.SPACE_AROUND
        ),
        bgcolor="#ffffff",
        bottom=0,
        left=0,
        right=0,
        border_radius=ft.border_radius.only(top_left=20, top_right=20),
        shadow=ft.BoxShadow(blur_radius=15, color=ft.colors.GREY_400),
        padding=ft.padding.symmetric(vertical=8),
        height=70,
        expand=True
    )

    return footer
