import flet as ft
from helpers.utils import addElementsPage, loadLoader, loadSnackbar, setInputField

title_category_field = setInputField("text", label="Category name")
select_picker_icon = setInputField("text", label="Picker icon")

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
                    image_src="https://raw.githubusercontent.com/ivanarganda/images_assets/main/form-wallpaper.png",
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
                            title_category_field,
                            select_picker_icon,
                            ft.Row(
                                [
                                    ft.ElevatedButton(
                                        "Add new category", 
                                        bgcolor="#5A2D9C", 
                                        color="white",
                                        on_click=lambda e: page.run_task(login, e, page)  # 🔑 aquí
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
