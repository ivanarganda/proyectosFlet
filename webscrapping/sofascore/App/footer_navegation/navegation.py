import flet as ft

def footer_navbar(
    page: ft.Page, 
    current_path={}, 
    dispatches={}, 
    absolute: bool = False
):

    folder = current_path.get("folder", "")

    func_add_category, args_add_category = dispatches.get(
        "add_category", 
        (lambda *a, **k: None, [])
    )

    # Si es absoluto, agregamos las props permitidas para Stack
    positioning = {}
    if absolute:
        positioning = dict(left=0, right=0, bottom=0)

    footer = ft.Container(
        content=ft.Row(
            [
                ft.IconButton(
                    ft.icons.HOME,
                    on_click=lambda _: page.go("/menu"),
                    icon_color="#4e73df"
                ),
                ft.IconButton(ft.icons.SEARCH, icon_color="#4e73df"),
                ft.FloatingActionButton(
                    on_click=lambda _: page.go("/menu"),
                    icon=ft.icons.ARROW_BACK, 
                    bgcolor="#4e73df",
                    visible=(folder in ("ControlPanel", "Info", "clasificaciones", "ML", "estadisticas", "Gestion"))
                ),
                ft.IconButton(ft.icons.NOTIFICATIONS, icon_color="#4e73df"),
                ft.IconButton(
                    ft.icons.PERSON, 
                    icon_color="#4e73df", 
                    visible=(folder != 'Profile')
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_AROUND
        ),
        bgcolor=ft.colors.WHITE,
        border_radius=ft.border_radius.only(top_left=20, top_right=20),
        shadow=ft.BoxShadow(blur_radius=15, color=ft.colors.GREY_400),
        padding=ft.padding.symmetric(vertical=8),
        height=70,
        
        # Si absolute=False → NO rompe Column layout
        # Si absolute=True → Se usan left/right/bottom correctamente dentro de un Stack
        **positioning
    )

    return footer
