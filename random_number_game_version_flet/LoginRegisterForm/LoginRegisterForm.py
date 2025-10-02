import flet as ft

def renderTemplate( page: ft.Page):
    
    page.title = "Login"
    page.bgcolor = "white"
    page.window.height = 700
    page.window.width = 900
    page.theme_mode = ft.ThemeMode.DARK
    page.add(
        ft.Text("Login here", color="black")
    )
    
