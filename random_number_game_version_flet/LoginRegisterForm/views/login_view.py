import flet as ft
def renderLoginView(page: ft.Page, email_field: ft.TextField, password_field: ft.TextField, login: callable, toogle_view: callable, loader_overlay: ft.Container) -> ft.Stack:
    return ft.Stack([
        ft.Container(
            expand=True,
            image_src="https://raw.githubusercontent.com/ivanarganda/images_assets/main/login-wallpaper.png",
            image_fit=ft.ImageFit.COVER
        ),
        ft.Container(
            bgcolor="white",
            border_radius=ft.border_radius.only(top_left=30, top_right=30),
            padding=20,
            alignment=ft.alignment.top_center,
            bottom=0, left=0, right=0,
            content=ft.Column(
                [
                    email_field,
                    password_field,
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "Let's play", 
                                bgcolor="#5A2D9C", 
                                color="white",
                                on_click=lambda e: page.run_task(login, e, page)  # 🔑 aquí
                            ),
                            # With switch mode
                            ft.Row(
                                [
                                    ft.Text("Don't have an account yet?"),
                                    ft.TextButton("Sign up", on_click=lambda _: toogle_view(page, "register"))
                                ]
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    )
                ],
                spacing=20,
            )
        ),
        loader_overlay
        ],
        expand=True,
        visible=True
    )