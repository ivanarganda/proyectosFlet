import flet as ft
def renderRegisterView(page: ft.Page, username_field: ft.TextField, email_field: ft.TextField, password_field: ft.TextField, register: callable, toogle_view: callable, loader_overlay: ft.Container) -> ft.Stack:
    return ft.Stack([
        ft.Container(
            expand=True,
            image_src="https://raw.githubusercontent.com/ivanarganda/images_assets/main/sign-up-wallpaper.png",
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
                    username_field,
                    email_field,
                    password_field,
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "Let's play", 
                                bgcolor="#5A2D9C", 
                                color="white",
                                on_click=lambda e: page.run_task(register, e, page)  # 🔑 aquí
                            ),
                            # With switch mode
                            ft.Row(
                                [
                                    ft.Text("Do you have already an account?"),
                                    ft.TextButton("Sign in", on_click=lambda e: toogle_view(page, "login"))
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
        visible=False
    )