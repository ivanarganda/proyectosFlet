import flet as ft
import json
import jwt  # PyJWT
from jwt import InvalidTokenError
import math
from datetime import datetime, timezone, timedelta
import platform
from components.PopupMenu import PopupMenuButton # TODO for testing
# from flet_popupmenu import PopupMenuButton # TODO for production
from params import HEADERS, REQUEST_URL

# ESPECIAL FUNCTIONS
def get_hostname():
    return platform.node()

def convert_seconds(seconds: float) -> dict:
    units = [
        ("years", 31556952),  # promedio (365.24 días)
        ("months", 2629746),  # promedio (30.44 días)
        ("days", 86400),
        ("hours", 3600),
        ("minutes", 60),
        ("seconds", 1),
    ]

    for name, factor in units:
        if seconds >= factor:
            value = seconds / factor
            return f"{value:.2f} {name}"
    
    return f"{seconds:.2f} seconds"  # por si acaso

def get_time_ago(date_str):
    """
    Devuelve tiempo transcurrido en formato legible.
    Admite fechas con o sin milisegundos y evita errores si date_str es None.
    """
    if not date_str or date_str.lower() == "none":
        return "No registered"

    try:
        # intentar con milisegundos
        start = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f")
    except ValueError:
        try:
            # intentar sin milisegundos
            start = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")
        except Exception:
            return "Invalid date"

    # Convertir UTC a hora local (España = UTC+1 invierno / +2 verano)
    start = start.replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=1)))

    now = datetime.now(timezone(timedelta(hours=1)))
    diff = (now - start).total_seconds()

    days = int(diff // 86400)
    hours = int((diff % 86400) // 3600)
    minutes = int((diff % 3600) // 60)
    seconds = int(diff % 60)

    # Formato legible
    if days > 0:
        return f"{days} d and {hours} h ago"
    elif hours > 0:
        return f"{hours} h and {minutes} min ago"
    elif minutes > 0:
        return f"{minutes} min ago"
    elif seconds >= 0:
        return f"{seconds} secs ago"
    else:
        return "Now"

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

# colors
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

def setInputField( type_ , label = "" , placeholder = "" , bg_color = "#F5F5F5" , border_color = "#E0E0E0" , focused_border_color = "#808080" ):
    defaultTextField = ft.TextField(keyboard_type=ft.KeyboardType.TEXT)
    return {
        "search": (
            ft.TextField(keyboard_type=ft.KeyboardType.TEXT, border_radius=5, border_color=border_color, focused_border_color=focused_border_color, border_width=1, prefix_icon=ft.Icons.SEARCH , hint_text=placeholder)
        ),
        "text": (
            ft.TextField(label=label, keyboard_type=ft.KeyboardType.TEXT, bgcolor=bg_color, border_radius=5, border_color=border_color )
        ),
        "password": (
            ft.TextField(label=label, keyboard_type=ft.KeyboardType.TEXT, bgcolor=bg_color, password=True, can_reveal_password=True, border_radius=5, border_color=border_color )
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

def animate_in(view: ft.Control, duration=400, offset=80):
    view.opacity = 0
    view.offset = ft.transform.Offset(0, 0.2)
    view.animate_opacity = ft.animation.Animation(duration, ft.AnimationCurve.EASE_OUT)
    view.animate_offset = ft.animation.Animation(duration, ft.AnimationCurve.EASE_OUT)
    view.opacity = 1
    view.offset = ft.transform.Offset(0, 0)
    return view

def animate_bounce(view: ft.Control, height=0.08, duration=250):
    view.offset = ft.transform.Offset(0, height)
    view.animate_offset = ft.animation.Animation(duration, ft.AnimationCurve.EASE_IN_OUT)
    view.offset = ft.transform.Offset(0, 0)
    return view

def animate_fade(view: ft.Control, duration=400, fade_in=True):
    view.opacity = 0 if fade_in else 1
    view.animate_opacity = ft.animation.Animation(duration, ft.AnimationCurve.EASE_IN_OUT)
    view.opacity = 1 if fade_in else 0
    return view

# --- Navegación y recarga ---
def safe_go(page: ft.Page, route: str):
    """Evita errores si la ruta no existe."""
    try:
        page.go(route)
    except Exception as e:
        log_error("safe_go", e)
        loadSnackbar(page, f"⚠️ Ruta inválida: {route}", "red")

def reload_page(page: ft.Page, delay_ms: int = 0):
    """Recarga visualmente la página."""
    async def do_reload():
        await asyncio.sleep(delay_ms / 1000)
        page.clean()
        page.update()
    asyncio.run(do_reload())

# --- Guardar y cargar JSON local (para stats o configuración) ---
def save_json(filepath: str, data: dict):
    """Guarda un dict como JSON (crea directorio si no existe)."""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        log_error("save_json", e)
        return False

def load_json(filepath: str, default: dict = {}):
    """Carga un JSON si existe, o devuelve default."""
    try:
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        return default
    except Exception as e:
        log_error("load_json", e)
        return default

# --- Tiempo y formato ---
def get_timestamp() -> str:
    """Devuelve la fecha/hora actual legible."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_day_name() -> str:
    """Devuelve el día de la semana (Lunes, Martes...)."""
    dias = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
    return dias[datetime.now().weekday()]

def get_time_diff(seconds: float) -> str:
    """Convierte segundos en formato mm:ss."""
    mins, secs = divmod(int(seconds), 60)
    return f"{mins:02d}:{secs:02d}"

# --- Notificaciones visuales con colores suaves ---
def notify_success(page, msg="✅ Operación completada"):
    loadSnackbar(page, msg, "#10b981")  # verde

def notify_warning(page, msg="⚠️ Atención"):
    loadSnackbar(page, msg, "#facc15")  # amarillo

def notify_error(page, msg="❌ Error inesperado"):
    loadSnackbar(page, msg, "#ef4444")  # rojo

# --- Mini sonido o vibración (en móviles/tablets compatibles) ---
def play_feedback(page: ft.Page, type_: str = "success"):
    """Muestra retroalimentación táctil/visual rápida."""
    icon_map = {
        "success": ft.Icons.CHECK_CIRCLE,
        "error": ft.Icons.ERROR_OUTLINE,
        "info": ft.Icons.INFO,
    }
    color_map = {
        "success": "#10b981",
        "error": "#ef4444",
        "info": "#3b82f6",
    }
    snack = ft.SnackBar(
        content=ft.Row([
            ft.Icon(icon_map.get(type_, ft.Icons.INFO), color=color_map.get(type_, "#3b82f6")),
            ft.Text({"success":"Done!","error":"Error!","info":"Info"}[type_])
        ]),
        bgcolor=color_map.get(type_, "#3b82f6"),
        duration=800
    )
    page.snack_bar = snack
    snack.open = True
    page.update()

# --- Ejecutor seguro universal (para callbacks, saves, etc.) ---
def safe_exec(func, context="operation"):
    """Ejecuta una función con control de error y log."""
    try:
        return func()
    except Exception as e:
        log_error(context, e)
        return None

# ABOUT TABLES

def safe_cell(value):
    return ft.DataCell(
        ft.Container(
            ft.Text("" if value is None else str(value), size=13, color="#2B2B2B"),
            expand=True,                      # <🔥 ancho completo de columna
            alignment=ft.alignment.center,    # opcional
        )
    )


def build_row(item, index, columns):
    return ft.DataRow(
        cells=[safe_cell(item.get(col)) for col in columns],
        color=ft.colors.BLUE_50 if index % 2 == 0 else None,
    )