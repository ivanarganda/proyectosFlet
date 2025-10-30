import flet as ft
import json
import jwt  # PyJWT
from jwt import InvalidTokenError
import math

# --------------------------
# Función auxiliar para logs
# --------------------------
def log_error(context: str, error: Exception):
    print(f"❌ Error en {context}: {type(error).__name__} -> {error}")

def validate_inputs(page, username=None, email=None, password=None):
    """Valida campos antes de enviar al servidor."""
    try:
        if username is not None and not username.strip():
            raise ValueError("Username is required.")
        if email is not None:
            if not email.strip():
                raise ValueError("Email is required.")
            if "@" not in email or "." not in email:
                raise ValueError("Invalid email format.")
        if password is not None:
            if len(password.strip()) < 4:
                raise ValueError("Password must be at least 4 characters.")
        return True
    except ValueError as ve:
        loadSnackbar(page, f"⚠️ {ve}", "red")
        page.update()
        return False

# --- Validación HEX estricta ---
def is_valid_hex(color: str) -> bool:
    import re
    # Admite formatos tipo #FFF o #FFFFFF
    return bool(re.fullmatch(r"#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})", color))

# --- Detección de colores claros ---
def is_light_color(hex_color: str) -> bool:
    try:
        hex_color = hex_color.lstrip("#")
        if len(hex_color) == 3:
            hex_color = "".join([c * 2 for c in hex_color])  # expandir #FFF → #FFFFFF
        r, g, b = [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
        return (r + g + b) / 3 > 200
    except Exception:
        return False

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

def open_bg_picker(e):
        def on_pick(color_hex):
            bg_color_field.value = color_hex
            bg_color_field.update()
            update_preview()
        page.dialog = build_color_dialog("Pick background color", bg_color_field.value, on_pick)
        page.dialog.open = True
        page.update()

def open_text_picker(e):
    def on_pick(color_hex):
        text_color_field.value = color_hex
        text_color_field.update()
        update_preview()
    page.dialog = build_color_dialog("Pick text color", text_color_field.value, on_pick)
    page.dialog.open = True
    page.update()

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

def setCarrousel(page, nodes, on_view_category, on_add_task):
    items = []

    for node in nodes:
        # ---------- 1. Validar y parsear content ----------
        content = node.get("content", {})

        # Si el content viene como string JSON -> convertirlo
        if isinstance(content, str):
            try:
                content = json.loads(content)
            except json.JSONDecodeError:
                print(f"⚠️ No se pudo parsear el content del nodo: {content}")
                content = {}

        if not isinstance(content, dict):
            print(f"⚠️ Formato inesperado en content: {type(content)}")
            continue

        # ---------- 2. Crear los textos ----------
        parts = []
        for k, data in content.items():
            # Saltar bg_color porque no se renderiza como texto
            if k == "bg_color":
                continue

            # data podría no ser dict (seguridad)
            if not isinstance(data, dict):
                print(f"⚠️ Valor inesperado en '{k}': {data}")
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

        # ---------- 3. Botón de añadir tarea ----------
        id_category_task = node.get("id_category", {}).get("id", None)
        category_name = node.get("category", {}).get("name", None)
        parts.append(
            ft.Row(
                [
                    ft.Container(
                        content=ft.IconButton(
                            icon=ft.icons.ADD,
                            icon_size=28,
                            icon_color="gray",
                            on_click=lambda _, id=id_category_task: on_add_task(page, id) if on_add_task else None
                        ),
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(
                        content=ft.IconButton(
                            icon=ft.icons.REMOVE_RED_EYE_OUTLINED,
                            icon_size=28,
                            icon_color="gray",
                            on_click=lambda _, category=f'{{"id": "{id_category_task}", "name": "{category_name}"}}': on_view_category(
                                page=page,
                                t="AllTasks",
                                category=category
                            ) if on_view_category else None

                        ),
                        alignment=ft.alignment.center,
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            )
        )

        # ---------- 4. Construir la tarjeta ----------
        bg_color = content.get("bg_color", {}).get("title", "#F0F0F0")  # valor por defecto
        card = ft.Container(
            width=160,
            height=200,
            bgcolor=bg_color,
            border_radius=20,
            padding=15,
            shadow=ft.BoxShadow(blur_radius=8, color=ft.colors.GREY_300),
            content=ft.Column(
                parts,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5,
            ),
        )
        items.append(card)

    # ---------- 5. Devolver la fila con scroll horizontal ----------
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
        ),
        "password": (
            ft.TextField(label=label, keyboard_type=ft.KeyboardType.TEXT, bgcolor=bg_color, border_radius=5, border_color=border_color , password=True , can_reveal_password=True )
        )
    }.get(type_, defaultTextField )

def handle_logout(page: ft.Page):
    page.session.clear()
    page.client_storage.clear()
    page.go("/")


def getSession( data , decrypt=False ):

    data = json.loads( data )

    user_data = data
    
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