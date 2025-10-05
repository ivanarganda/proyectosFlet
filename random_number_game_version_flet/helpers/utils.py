import flet as ft
import json
import jwt  # PyJWT
from jwt import InvalidTokenError

def getSession( data , decrypt=False ):
    if isinstance(data, str):
        # Si es string JSON → parsear
        user_data = json.loads(data)
    elif isinstance(data, dict):
        # Si Flet ya lo devolvió como dict
        user_data = data
    else:
        user_data = {}
    
    if decrypt:
        # Aquí iría la lógica de desencriptación si se implementa
        if "token" in user_data:
            try:
                decoded = jwt.decode(user_data["token"], "secret", algorithms=["HS256"])
                return decoded
            except InvalidTokenError:
                return {}
        else:
            return {}
        
    return user_data

def regexes():
    return {
        "email": r"^\S+@\S+\.\S+$",
        "password": r"^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{8,}$"
    }
    
def loadLoader():
    return ft.Stack(
        [
            # Fondo semitransparente
            ft.Container(expand=True, bgcolor=ft.colors.with_opacity(0.5, "black")),
            # Loader centrado
            ft.Container(
                content=ft.ProgressRing(
                    width=60,
                    height=60,
                    stroke_width=6,
                    color="white"
                ),
                alignment=ft.alignment.center
            )
        ],
        expand=True,
        visible=False
    )
    
def loadSnackbar( page: ft.Page, message: str, color: str ):
    page.snack_bar = ft.SnackBar(ft.Text(message), bgcolor=color)
    page.snack_bar.open = True
    page.update()
    
def clearInputsForm( page, inputs ):
    for input_ in inputs:
        input_.value = ""
    page.update()

def addElementsPage(page, elements):
    for element in elements:
        page.add(element)
    page.update()
    return ft.Stack(elements, expand=True)  # ✅ devuelve algo visible