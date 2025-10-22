import flet as ft
from params import WALLPAPERS

def renderChangePasswordView( page: ft.Page, email_field: ft.TextField, password_field_confirm: ft.TextField, password_field: ft.TextField, changePassword: callable, toogle_view: callable, loader_overlay: ft.Container )->ft.Stack:
    contentForm = ft.Column([
                        email_field,
                        password_field,
                        ft.Row(
                            [
                                ft.ElevatedButton(
                                    "Let's update password", 
                                    bgcolor="#5A2D9C", 
                                    color="white",
                                    on_click=lambda e: page.run_task(changePassword, e, page)  # 🔑 aquí
                                ),
                                # With switch mode
                                ft.Row(
                                    [
                                        ft.Text("I've already remmenbered the password?"),
                                        ft.TextButton("Sign up", on_click=lambda _: toogle_view(page, "login"))
                                    ]
                                )
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        )
                    ])
                    
    
    return ft.Stack([
        ft.Container(
            expand=True,
            image_src=WALLPAPERS["ch_password"],
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
                    contentForm
                ],
                spacing=20,
            )
        ),
        loader_overlay
        ],
        expand=True,
        visible=False
    )
