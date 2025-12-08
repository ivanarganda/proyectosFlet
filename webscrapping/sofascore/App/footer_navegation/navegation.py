import flet as ft

def footer_navbar(page: ft.Page, current_path = {} , dispatches = {} ):

    func_add_category, args_add_category = dispatches.get("add_category", (lambda *a, **k: None, []))

    full_path = current_path["path"]
    folder = current_path["folder"]
    file = current_path["file"]

    page.bgcolor = ft.colors.WHITE

    footer = ft.Container(
        content=ft.Row(
            [
                ft.IconButton(ft.icons.HOME, on_click=lambda _: page.go("/menu"), icon_color="#4e73df"),
                ft.IconButton(ft.icons.SEARCH, icon_color="#4e73df"),
                ft.FloatingActionButton(on_click=lambda _: func_add_category(*args_add_category), icon=ft.icons.ADD, bgcolor="#4e73df", visible= folder == 'Tasks' ),
                ft.FloatingActionButton(on_click=lambda _: page.go("/tasks"), icon=ft.icons.ARROW_BACK, bgcolor="#4e73df", visible= (folder == 'views') and (file == 'AddCategoryTasksForm.py') ),
                ft.FloatingActionButton(on_click=lambda _: page.go("/tasks"), icon=ft.icons.ARROW_BACK, bgcolor="#4e73df", visible= (folder == 'views') and (file == 'AddTaskForm.py') ),
                ft.FloatingActionButton(on_click=lambda _: page.go("/tasks"), icon=ft.icons.ARROW_BACK, bgcolor="#4e73df", visible= (folder == 'views') and (file == 'details_category.py') ),
                ft.FloatingActionButton(on_click=lambda _: page.go("/menu"), icon=ft.icons.ARROW_BACK, bgcolor="#4e73df", visible= (folder == 'profile') and (file == 'profile.py') ),
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
