import flet as ft
import asyncio
from helpers.utils import loadLoader, addElementsPage, clearInputsForm

email_field = ft.TextField(label="Email")
password_field = ft.TextField(label="Password", password=True)

loader_overlay = loadLoader()

async def login(e, page: ft.Page):
    
    global email_field, password_field, loader
    
    loader_overlay.visible = True
    
    page.update()

    # Simular tarea larga sin bloquear la UI
    await asyncio.sleep(5)

    email, password = email_field.value, password_field.value

    page.snack_bar = ft.SnackBar(ft.Text(f"Hola {email}!"), bgcolor="green")
    page.snack_bar.open = True

    clearInputsForm(page, [email_field, password_field])

    loader_overlay.visible = False
    
    page.update()

def renderTemplate(page: ft.Page):
    
    page.title = "Login"
    page.window_width = 600
    page.window_height = 800
    page.window_resizable = False

    addElementsPage(
        page, 
        [
            ft.Stack(
                [
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
                                ft.ElevatedButton(
                                    "Let's play", 
                                    bgcolor="#5A2D9C", 
                                    color="white",
                                    on_click=lambda e: page.run_task(login, e, page)  # 🔑 aquí
                                )
                            ],
                            spacing=20
                        )
                    ),
                    loader_overlay
                ],
                expand=True
            )
        ]
    )
