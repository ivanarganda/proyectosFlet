import flet as ft
from LoginRegisterForm.LoginRegisterForm import renderTemplate

def main(page: ft.Page):
    renderTemplate(page)

ft.app(target=main)
