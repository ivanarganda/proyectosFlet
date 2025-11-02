import os
import io
import base64
import flet as ft
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import datetime

from helpers.utils import (
    addElementsPage, fit_model, setInputField,
    generateFooter, init_window, create_layout, update_chart
)
from MainMenu.views.scripts_views import init_metadata
from MainMenu.views.components.DatePicker import init_date_picker

# === METADATA ===
current_path = init_metadata()

# === DATASET ===
DATASET_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "all_stocks_5yr.csv")
df = pd.read_csv(DATASET_PATH)[["date", "open", "close", "high", "low", "volume", "Name"]]
df["date"] = pd.to_datetime(df["date"])

MIN_DATE = df["date"].max()
MAX_DATE = pd.to_datetime("2050-01-01 00:00:00")


def prediccion_ventas(page: ft.Page):
    # --- CONFIGURACIÓN DE PÁGINA ---
    init_window(
        page=page,
        title="Forecast of company actions",
        size={"width": 600, "height": 850},
        bg_color="#F6F4FB"
    )

    # === TÍTULO ===
    titulo = ft.Text(
        "🔮 Forecast of company actions",
        size=28,
        weight=ft.FontWeight.BOLD,
        color="white",
        text_align=ft.TextAlign.CENTER
    )

    # === COMBOBOX DE ACCIONES ===
    acciones = sorted(df["Name"].unique().tolist())
    combo_accion = setInputField(
        type_="dropdown",
        label="Choose an action",
        bg_color="#5A2D9C",
        border_color="#5A2D9C",
        width=350,
        options=[ft.dropdown.Option(a) for a in acciones]
    )

    # === INPUT DEL PERIODO ===
    input_periodo = setInputField(
        type_="text",
        label="Forecast horizon",
        bg_color="#222222",
        placeholder="YYYY-MM-DD → YYYY-MM-DD (días)",
        width=350,
        border_color="#5A2D9C",
        color="white",
        read_only=True,
        visible=False
    )


    # === MENSAJE Y GRÁFICO ===
    mensaje = ft.Text("", color="#cccccc", size=14, text_align=ft.TextAlign.CENTER)
    grafico_img = ft.Image(
        border_radius=ft.border_radius.all(10),
        src_base64=None,
        width=550,
        height=350,
        fit=ft.ImageFit.CONTAIN,
        visible=False
    )

    # === FILTRAR Y ACTUALIZAR GRÁFICO ===
    def filtrar_dataset(e=None):
        accion = combo_accion.value or df["Name"].iloc[0]

        start = datetime.strptime(fecha_inicio_val.value, "%Y-%m-%d")
        end = datetime.strptime(fecha_fin_val.value, "%Y-%m-%d")

        filtrado = df[(df["Name"] == accion) & (df["date"] >= start) & (df["date"] <= end)]

        if not filtrado.empty:
            update_chart(
                page,
                grafico_img,
                filtrado,
                1.0,  # rate
                f"{accion} trend ({(end - start).days} días)",
                "USD"
            )

    # === TEXTOS DE FECHAS ===
    fecha_inicio_val = ft.Text(MIN_DATE.strftime("%Y-%m-%d"), color="#CCCCCC")
    fecha_fin_val = ft.Text(MAX_DATE.strftime("%Y-%m-%d"), color="#CCCCCC")

    # === DATE PICKER ===
    date_picker = init_date_picker(
        page,
        filtrar_dataset,
        fecha_inicio_val,
        fecha_fin_val,
        MIN_DATE,
        MAX_DATE,
        df,
        input_periodo
    )

    rango_fechas = date_picker["component"]
    fecha_inicio_val = date_picker["fecha_inicio_val"]
    fecha_fin_val = date_picker["fecha_fin_val"]
    days = date_picker["diff"]["days"]

    # === BOTÓN DE PRONÓSTICO ===
    boton = ft.ElevatedButton(
        text="Generate forecast",
        icon=ft.icons.AUTO_GRAPH,
        bgcolor="#5A2D9C",
        color="white",
        width=250
    )

    def generar_forecast(e):
        # Extraer número de días del rango
        try:
            start = datetime.strptime(fecha_inicio_val.value, "%Y-%m-%d")
            end = datetime.strptime(fecha_fin_val.value, "%Y-%m-%d")
            diff_days = (end - start).days
        except Exception:
            diff_days = 60  # valor por defecto

        fit_model(
            page=page,
            combobox=combo_accion,
            data_frame=df,
            period_date=diff_days,  # número de días reales
            output_message=mensaje,
            chart=grafico_img
        )

    boton.on_click = generar_forecast

    # === LAYOUT FINAL ===
    layout = create_layout(
        page=page,
        current_path=current_path,
        dispatches={},
        content_controls=[
            titulo,
            combo_accion,
            rango_fechas,
            input_periodo,
            boton,
            mensaje,
            grafico_img,
        ],
        bgcolor="black",
    )

    page.update()
    return addElementsPage(page, [layout])