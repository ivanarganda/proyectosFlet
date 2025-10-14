import flet as ft
import json
import jwt  # PyJWT
from jwt import InvalidTokenError
import math

# Colors
def setGradient( color ):
    return {
        'black-blue':ft.SweepGradient(
            center=ft.alignment.center,
            start_angle=0.0,
            end_angle=math.pi * 4,
            colors=[
                "0x00084F",
                "0x00084F",
                "0x2B2A2A",
                "0x2B2A2A",
                "0x2B2A2A"
            ],
            stops=[0.0, 0.63, 0.70, 0.66, 0.89],
        )
    }.get(color, "")

def setCarrousel(nodes):
    items = []

    for node in nodes:
        parts = []

        for k, data in node["content"].items():
            text_value = data.get("title", "")
            text_kwargs = {
                key: data[key]
                for key in ["size", "width", "color", "weight"]
                if key in data
            }
            parts.append(ft.Text(text_value, **text_kwargs))

        # cada tarea = una columna de textos
        card = ft.Container(
            width=160,
            height=120,
            bgcolor=f"{node["content"]["bg_color"]["title"]}",
            border_radius=20,
            padding=15,
            shadow=ft.BoxShadow(blur_radius=8, color=ft.colors.GREY_300),
            content=ft.Column(
                parts,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5,
            ),
        )
        items.append(card)

    # fila con scroll horizontal
    return ft.Row(
        controls=items,
        scroll=ft.ScrollMode.ALWAYS,
        spacing=15,
        alignment=ft.MainAxisAlignment.START,
    )


def setInputField( type_ , label = "" , placeholder = "" , bg_color = "#F5F5F5" , border_color = "#E0E0E0" , focused_border_color = "#808080" ):
    defaultTextField = ft.TextField(keyboard_type=ft.KeyboardType.TEXT)
    return {
        "search": (
            ft.TextField(keyboard_type=ft.KeyboardType.TEXT, border_radius=5, border_color=border_color, focused_border_color=focused_border_color, border_width=1, prefix_icon=ft.icons.SEARCH , hint_text=placeholder)
        ),
        "text": (
            ft.TextField(label=label, keyboard_type=ft.KeyboardType.TEXT, bgcolor=bg_color, border_radius=5, border_color=border_color )
        )
    }.get(type_, defaultTextField )


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