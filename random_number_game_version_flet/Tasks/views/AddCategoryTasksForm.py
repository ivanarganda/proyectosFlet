import flet as ft
from helpers.utils import addElementsPage, loadLoader, loadSnackbar, setInputField

username_field = setInputField("text", label="Username")
email_field = setInputField("text", label="Email")
password_field = setInputField("text", label="Password")

loader_overlay = loadLoader()

def AddCategoryTasksForm( page: ft.Page, id_category):

    print(id_category)
    
    page.title = "Add task category"
    page.window_width = 600
    page.window_height = 800
    page.window_resizable = False

    return addElementsPage(
        page, 
        [
           ft.Stack([
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
        ]
    )
