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

# ---------- Helpers de color ----------
def close_dialog(e):
    e.page.dialog.open = False
    e.page.update()
def clamp(v, lo=0, hi=255): return max(lo, min(hi, int(v)))

def rgb_to_hex(r, g, b):
    return f"#{clamp(r):02X}{clamp(g):02X}{clamp(b):02X}"

def hex_to_rgb(hx, default=(90, 45, 156)):  # "#5A2D9C" por defecto
    try:
        h = hx.strip().lstrip("#")
        if len(h) == 3:
            h = "".join(c*2 for c in h)
        if len(h) != 6:
            return default
        r = int(h[0:2], 16)
        g = int(h[2:4], 16)
        b = int(h[4:6], 16)
        return (r, g, b)
    except:
        return default

def build_color_dialog(title: str, initial_hex: str, on_pick):
    # Paleta base (puedes ampliar)
    palette = [
        "#FF6B6B", "#FFD93D", "#6BCB77", "#4D96FF",
        "#9D4EDD", "#F72585", "#FF9E00", "#00B4D8",
        "#F0F0FF", "#EAEAEA", "#1A1A1A", "#5A2D9C",
    ]

    # Estado interno
    r, g, b = hex_to_rgb(initial_hex or "#5A2D9C")
    hex_field = ft.TextField(label="HEX", value=rgb_to_hex(r, g, b), width=140)
    swatch = ft.Container(width=36, height=36, bgcolor=rgb_to_hex(r, g, b), border_radius=8)

    r_slider = ft.Slider(min=0, max=255, divisions=255, value=r, label="{value}", expand=True)
    g_slider = ft.Slider(min=0, max=255, divisions=255, value=g, label="{value}", expand=True)
    b_slider = ft.Slider(min=0, max=255, divisions=255, value=b, label="{value}", expand=True)

    def apply_color_from_rgb():
        hx = rgb_to_hex(r_slider.value, g_slider.value, b_slider.value)
        hex_field.value = hx
        swatch.bgcolor = hx
        hex_field.update()
        swatch.update()
        # Callback inmediato para previsualizar “en vivo”
        on_pick(hx)

    def apply_color_from_hex():
        nonlocal r, g, b
        rr, gg, bb = hex_to_rgb(hex_field.value)
        r_slider.value, g_slider.value, b_slider.value = rr, gg, bb
        swatch.bgcolor = rgb_to_hex(rr, gg, bb)
        r_slider.update(); g_slider.update(); b_slider.update(); swatch.update()
        on_pick(swatch.bgcolor)

    def on_palette_click(col):
        hex_field.value = col
        apply_color_from_hex()

    r_slider.on_change = lambda e: apply_color_from_rgb()
    g_slider.on_change = lambda e: apply_color_from_rgb()
    b_slider.on_change = lambda e: apply_color_from_rgb()
    hex_field.on_change = lambda e: apply_color_from_hex()

    palette_controls = [
        ft.Container(
            width=32, height=32, bgcolor=c, border_radius=16,
            on_click=lambda e, col=c: on_palette_click(col),
            margin=4, shadow=ft.BoxShadow(blur_radius=6, color=ft.colors.GREY_300),
        ) for c in palette
    ]

    # Custom section (HEX + RGB sincronizados)
    custom_section = ft.Column(
        [
            ft.Row([hex_field, swatch], alignment=ft.MainAxisAlignment.START, spacing=12),
            ft.Row([ft.Text("R", width=16), r_slider]),
            ft.Row([ft.Text("G", width=16), g_slider]),
            ft.Row([ft.Text("B", width=16), b_slider]),
        ],
        spacing=10,
    )

    dlg = ft.AlertDialog(
        title=ft.Text(title, weight=ft.FontWeight.BOLD),
        content=ft.Column(
            [
                ft.Text("Palette", size=14, color="#666"),
                ft.Row(
                    controls=palette_controls,
                    spacing=8,
                    scroll=ft.ScrollMode.AUTO,
                    alignment=ft.MainAxisAlignment.START
                ),
                ft.Divider(height=24, color="#DDD"),
                ft.Text("Custom color", size=14, color="#666"),
                custom_section,
            ],
            width=340,
            height=320,
            scroll=ft.ScrollMode.AUTO
        ),
        actions=[
            ft.TextButton("Close", on_click=lambda e: close_dialog(e))
        ],
    )
    return dlg

def setCarrousel(page, nodes, on_add_task=None):
    items = []

    for node in nodes:
        parts = []

        for k, data in node["content"].items():
            if k == "bg_color":
                continue
            text_value = data.get("title", "")
            if not text_value:
                continue
            text_kwargs = {
                key: data[key]
                for key in ["size", "width", "color", "weight"]
                if key in data
            }
            parts.append(ft.Text(text_value, **text_kwargs))

        id_category_task = node["id_category"].get("id",None)
        parts.append(ft.Container(
            content=ft.IconButton(
                icon=ft.icons.ADD,
                icon_size=28,
                icon_color="gray",
                on_click=lambda _, id=id_category_task: on_add_task(page, id) if on_add_task else None
            ),
            alignment=ft.alignment.center,
        ))

        # cada tarea = una columna de textos
        card = ft.Container(
            width=160,
            height=200,
            bgcolor=node['content']['bg_color'],
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