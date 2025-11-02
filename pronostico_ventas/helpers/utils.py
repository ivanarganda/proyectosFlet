import os
import io
import base64
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import flet as ft
import json
import jwt  # PyJWT
from jwt import InvalidTokenError
import math
from prophet import Prophet
from footer_navegation.navegation import footer_navbar

def init_window(
    page: ft.Page,
    title: str = "Test",
    size: dict = None,
    bg_color: str = "white",
    alignment: dict = None,
):
    """
    Inicializa una ventana Flet con parámetros personalizados.
    """

    # ✅ Valores por defecto seguros
    if size is None:
        size = {"width": 300, "height": 300}

    if alignment is None:
        alignment = {
            "horizontal": ft.CrossAxisAlignment.CENTER,
            "vertical": ft.MainAxisAlignment.START,
        }

    # ✅ Asignación correcta
    width = size.get("width", 300)
    height = size.get("height", 300)
    horizontal = alignment.get("horizontal", ft.CrossAxisAlignment.CENTER)
    vertical = alignment.get("vertical", ft.MainAxisAlignment.START)

    # ✅ Aplicar propiedades de ventana
    page.title = title
    page.window_width = width
    page.window_height = height
    page.bgcolor = bg_color
    page.horizontal_alignment = horizontal
    page.vertical_alignment = vertical

    # (Opcional) fuerza actualización inicial
    page.update()


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

def setInputField(
    type_: str,
    label: str = "",
    placeholder: str = "",
    value: str = "",
    color: str = "white",
    bg_color: str = "#F5F5F5",
    border_color: str = "#E0E0E0",
    focused_border_color: str = "#808080",
    options=None,
    width: int = 350,
    read_only: bool = False
):
    """
    Crea un campo de entrada genérico en Flet.

    type_ puede ser uno de:
      - "search"
      - "text"
      - "password"
      - "dropdown"

    Retorna un control Flet (TextField o Dropdown) según el tipo especificado.
    """
    if options is None:
        options = []

    # Campo por defecto si no se reconoce el tipo
    default_field = ft.TextField(keyboard_type=ft.KeyboardType.TEXT)

    field_types = {
        "search": ft.TextField(
            value=value,
            keyboard_type=ft.KeyboardType.TEXT,
            border_radius=5,
            border_color=border_color,
            color=color,
            focused_border_color=focused_border_color,
            border_width=1,
            prefix_icon=ft.icons.SEARCH,
            hint_text=placeholder,
            width=width,
            read_only=read_only
        ),
        "text": ft.TextField(
            label=label,
            value=value,
            keyboard_type=ft.KeyboardType.TEXT,
            bgcolor=bg_color,
            border_radius=5,
            border_color=border_color,
            color=color,
            hint_text=placeholder,
            width=width,
            read_only=read_only
        ),
        "password": ft.TextField(
            label=label,
            value=value,
            keyboard_type=ft.KeyboardType.TEXT,
            bgcolor=bg_color,
            border_radius=5,
            border_color=border_color,
            color=color,
            password=True,
            can_reveal_password=True,
            hint_text=placeholder,
            width=width,
            read_only=read_only
        ),
        "dropdown": ft.Dropdown(
            label=label,
            bgcolor=bg_color,
            color=color,
            border_radius=5,
            options=options,
            width=width,
            border_color=border_color,
            disabled=read_only
        ),
    }

    return field_types.get(type_, default_field)

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

def generateFooter( page:ft.Page, current_path: dict, dispatches={} ):

    footer = footer_navbar(page=page, current_path=current_path, dispatches=dispatches)
    footer_container = ft.Container(
        content=footer,
        bgcolor="#F6F4FB",
        bottom=0,
        left=0,
        right=0,
        height=60,
        alignment=ft.alignment.center,
        shadow=ft.BoxShadow(blur_radius=12, color=ft.colors.with_opacity(0.15, "black"))
    )
    return footer_container

    
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
    return ft.Stack(elements, expand=True) 

# ABOUT LAYOUT
def create_layout(
    page: ft.Page,
    content_controls: list,
    current_path: dict,
    dispatches: dict,
    bgcolor: str = "#F6F4FB",
    footer_bg: str = "#F6F4FB",
    padding_v: int = 20,
    padding_h: int = 15,
    spacing: int = 20,
):
    """
    Crea una estructura visual completa con:
      - un cuerpo que ocupa toda la pantalla
      - un footer fijo en la parte inferior

    Parámetros:
      page: objeto ft.Page
      content_controls: lista de controles (Column, Text, Dropdown, etc.)
      current_path: diccionario con información del módulo actual
      bgcolor: color de fondo principal
      footer_bg: color del fondo del footer
      padding_v, padding_h: márgenes verticales y horizontales del contenido
      spacing: espacio entre elementos del cuerpo
    """

    # --- COLUMNA PRINCIPAL (contenido central con scroll) ---
    contenido = ft.Column(
        content_controls,
        alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=spacing,
        expand=True,
        scroll=ft.ScrollMode.AUTO,
    )

    # --- CONTENEDOR PRINCIPAL (ocupa todo el alto disponible) ---
    body_container = ft.Container(
        content=contenido,
        expand=True,
        padding=ft.padding.symmetric(vertical=padding_v, horizontal=padding_h),
        bgcolor=bgcolor,
        alignment=ft.alignment.top_center,
    )

    # --- FOOTER FIJO (generado con tu función existente) ---
    footer_container = generateFooter( page=page, current_path=current_path, dispatches=dispatches )

    # --- LAYOUT FINAL ---
    layout = ft.Stack(
        [
            body_container,  # cuerpo ocupa todo el espacio
            footer_container  # footer fijo al fondo
        ],
        expand=True,
    )

    return layout



# ABOUT MACHINE LEARNING
def fit_model(page:ft.Page, combobox:ft.Dropdown, data_frame:pd.DataFrame , period_date:ft.TextField, output_message: ft.Text, chart: ft.Image ):
        try:
            accion = combobox.value
            dias = int(period_date)

            if not accion:
                output_message.value = "⚠️ Choose an option before continuing"
                page.update()
                return

            output_message.value = f"Predicting company actions from {accion}..."
            chart.visible = False
            page.update()

            # --- Filter data ---
            data = data_frame[data_frame["Name"] == accion][["date", "close"]].copy()
            data.rename(columns={"date": "ds", "close": "y"}, inplace=True)
            data["ds"] = pd.to_datetime(data["ds"])

            # --- Prophet Model ---
            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=False,
                daily_seasonality=False,
                seasonality_mode="multiplicative"
            )
            model.fit(data)

            # --- Forward forecast ---
            future = model.make_future_dataframe(periods=dias)
            forecast = model.predict(future)
            forecast["is_future"] = forecast["ds"] > data["ds"].max()

            # --- Chartting ---
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.plot(data["ds"], data["y"], label="Real data", color="#1f77b4", linewidth=1.8)
            ax.plot(
                forecast.loc[forecast["is_future"], "ds"],
                forecast.loc[forecast["is_future"], "yhat"],
                label="Forward forecast",
                color="#ff7f0e",
                linewidth=1.2
            )
            ax.fill_between(
                forecast["ds"],
                forecast["yhat_lower"],
                forecast["yhat_upper"],
                color="gray",
                alpha=0.2,
                label="Confidence interval"
            )

            ax.set_title(f"Close foreacast - {accion}", fontsize=14)
            ax.set_xlabel("Date")
            ax.set_ylabel("Close price")
            ax.legend()
            plt.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format="png", bbox_inches="tight")
            plt.close(fig)
            buf.seek(0)
            img_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")

            chart.src_base64 = img_base64
            chart.visible = True
            output_message.value = f"✅ Predicted to {accion} for ({dias} days)."
            page.update()

        except Exception as ex:
            output_message.value = f"❌ Error: {ex}"
            page.update()

def use_currency_conversor():
    pass


# ------------------------------
# MONEDAS Y CONVERSIONES LOCALES
# ------------------------------
def get_local_rate(rates_df: pd.DataFrame, base_currency: str, target_currency: str, year: int = None) -> float:
    """Busca la tasa base→target en el JSON local de divisas."""
    if base_currency == target_currency:
        return 1.0

    try:
        if year is None:
            year = rates_df["year"].max()
        base_row = rates_df[(rates_df["currency"] == base_currency) & (rates_df["year"] == year)]
        target_row = rates_df[(rates_df["currency"] == target_currency) & (rates_df["year"] == year)]

        if base_row.empty or target_row.empty:
            return 1.0

        base_rate = base_row["rate"].values[0]
        target_rate = target_row["rate"].values[0]
        return target_rate / base_rate
    except Exception as e:
        log_error("get_local_rate", e)
        return 1.0


# ------------------------------
# TABLAS Y GRÁFICOS REUTILIZABLES
# ------------------------------
def paginate_table(df: pd.DataFrame, page_size: int, current_page: int):
    """Devuelve el subconjunto de datos correspondiente a la página actual."""
    total_filas = len(df)
    total_paginas = max(1, (total_filas + page_size - 1) // page_size)
    current_page = max(1, min(current_page, total_paginas))
    start = (current_page - 1) * page_size
    end = start + page_size
    return df.iloc[start:end], total_paginas


def update_table(table: ft.DataTable, df_subset: pd.DataFrame, currency: str, rate: float):
    """Actualiza el contenido de una tabla con datos filtrados."""
    table.rows.clear()
    for _, fila in df_subset.iterrows():
        date_ = fila["date"].strftime("%Y-%m-%d")
        open_ = fila["open"] * rate
        close_ = fila["close"] * rate
        table.rows.append(
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(date_)),
                    ft.DataCell(ft.Text(fila["Name"])),
                    ft.DataCell(ft.Text(f"{open_:.2f} {currency}")),
                    ft.DataCell(ft.Text(f"{close_:.2f} {currency}")),
                    ft.DataCell(ft.Text(f"{fila['volume']}")),
                ]
            )
        )


def update_chart(page: ft.Page, chart_img: ft.Image, df: pd.DataFrame, rate: float, title: str, currency: str):
    """Genera un gráfico en base64 desde un DataFrame filtrado."""
    if df.empty:
        chart_img.visible = False
        page.update()
        return

    fig, ax = plt.subplots(figsize=(6, 3))
    ax.plot(df["date"], df["close"] * rate, color="#5A2D9C", linewidth=2)
    ax.set_title(f"{title} ({currency})", fontsize=11)
    ax.set_xlabel("Date")
    ax.set_ylabel(f"Price ({currency})")
    ax.grid(True, linestyle="--", alpha=0.4)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)

    chart_img.src_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    chart_img.visible = True
    page.update()