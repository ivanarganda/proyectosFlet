import os
import flet as ft
import pandas as pd
from datetime import date

from helpers.utils import (
    addElementsPage,
    log_error,
    generateFooter,   # si tu create_layout ya lo llama, puedes no usarlo aquí
    init_window,
    create_layout,
    get_local_rate,
    update_table,
    update_chart,
    paginate_table,
)
from MainMenu.views.scripts_views import init_metadata
from MainMenu.views.components.DatePicker import init_date_picker

# === METADATA Y RUTAS ===
current_path = init_metadata()

# === DATASETS ===
BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..")
DATASET_PATH = os.path.join(BASE_DIR, "all_stocks_5yr.csv")
RATES_PATH = os.path.join(BASE_DIR, "rates_yearly_symbols.json")

df = pd.read_csv(DATASET_PATH)[["date", "open", "close", "high", "low", "volume", "Name"]]
df["date"] = pd.to_datetime(df["date"])
rates_df = pd.read_json(RATES_PATH)

# === CONFIGURACIÓN INICIAL ===
available_currencies = sorted(rates_df["currency"].unique().tolist())
min_date_ts, max_date_ts = df["date"].min(), df["date"].max()
# ✅ convertir a date nativo para DatePicker
MIN_DATE = min_date_ts
MAX_DATE = max_date_ts

DEFAULT_NAME = "AAL" if "AAL" in df["Name"].unique() else df["Name"].unique()[0]
DEFAULT_CURRENCY = "USD"
previous_currency = DEFAULT_CURRENCY
current_currency = DEFAULT_CURRENCY
new_currency = current_currency
rate_currency = 1.0

txt_current = ft.Text(DEFAULT_CURRENCY, color="#CCCCCC")
txt_arrow = ft.Text("→", color="#CCCCCC")
txt_new = ft.Text(new_currency, color="#CCCCCC")


# === INTERFAZ PRINCIPAL ===
def historial_ventas(page: ft.Page):
    global current_currency, rate_currency, new_currency

    init_window(
        page=page,
        title="Actions log",
        size={"width": 600, "height": 850},
        bg_color="#F6F4FB",
        alignment={
            "horizontal": ft.CrossAxisAlignment.CENTER,
            "vertical": ft.MainAxisAlignment.CENTER,
        },
    )

    # --- VARIABLES ---
    page_size = 50
    current_page = 1
    filtrado_global = df.copy()

    # --- COMPONENTES ---
    grafico_img = ft.Image(width=500, height=300, visible=False)
    tabla = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Date")),
            ft.DataColumn(ft.Text("Action")),
            ft.DataColumn(ft.Text("Open")),
            ft.DataColumn(ft.Text("Close")),
            ft.DataColumn(ft.Text("Volume")),
        ],
        rows=[],
        column_spacing=10,
        heading_row_color="#5A2D9C",
        data_row_color={"hovered": "#EEE"},
    )
    lbl_paginacion = ft.Text("Page 1 of 1 (0 records)", size=13, color="white")

    # === PAGINACIÓN ===
    def actualizar_tabla(df_filtrado):
        nonlocal filtrado_global, current_page
        filtrado_global = df_filtrado
        subset, total_paginas = paginate_table(filtrado_global, page_size, current_page)
        update_table(tabla, subset, new_currency, rate_currency)
        lbl_paginacion.value = f"Page {current_page} of {total_paginas} ({len(filtrado_global)} records)"
        lbl_paginacion.visible = True
        page.update()

    def cambiar_pagina(delta):
        nonlocal current_page
        current_page += delta
        subset, total_paginas = paginate_table(filtrado_global, page_size, current_page)
        update_table(tabla, subset, new_currency, rate_currency)
        lbl_paginacion.value = f"Page {current_page} of {total_paginas} ({len(filtrado_global)} records)"
        lbl_paginacion.visible = True
        page.update()

    botones_paginacion = ft.Row(
        [
            ft.ElevatedButton(
                "⬅️ Previous",
                on_click=lambda e: cambiar_pagina(-1),
                width=120,
                bgcolor="#5A2D9C",
                color="white",
            ),
            lbl_paginacion,
            ft.ElevatedButton(
                "Next ➡️",
                on_click=lambda e: cambiar_pagina(1),
                width=120,
                bgcolor="#5A2D9C",
                color="white",
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=15,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # --- FILTROS ---
    acciones = sorted(df["Name"].unique().tolist())
    combo_accion = ft.Dropdown(
        label="Action",
        options=[ft.dropdown.Option(a) for a in acciones],
        value=DEFAULT_NAME,
        width=350,
        border_color="#5A2D9C",
    )

    currencies = ft.Dropdown(
        label="Currency",
        options=[ft.dropdown.Option(c) for c in available_currencies],
        value=DEFAULT_CURRENCY,
        width=150,
        border_color="#5A2D9C",
    )

    # Texts visibles con el rango actual
    fecha_inicio_val = ft.Text(MIN_DATE.strftime("%Y-%m-%d"), color="#CCCCCC")
    fecha_fin_val = ft.Text(MAX_DATE.strftime("%Y-%m-%d"), color="#CCCCCC")

    # --- FILTROS GENERALES ---
    def filtrar_dataset(e=None):
        accion = combo_accion.value or DEFAULT_NAME
        start = pd.to_datetime(fecha_inicio_val.value, format="%Y-%m-%d")
        end = pd.to_datetime(fecha_fin_val.value, format="%Y-%m-%d")

        # asegurar coherencia de rango (start <= end)
        if start > end:
            start, end = end, start
            fecha_inicio_val.value = start.strftime("%Y-%m-%d")
            fecha_fin_val.value = end.strftime("%Y-%m-%d")

        filtrado = df[(df["Name"] == accion) & (df["date"] >= start) & (df["date"] <= end)]
        actualizar_tabla(filtrado)
        update_chart(page, grafico_img, filtrado, rate_currency, f"Close trend - {accion}", current_currency)

    date_picker = init_date_picker(
        page,
        filtrar_dataset,
        fecha_inicio_val,
        fecha_fin_val,
        MIN_DATE,
        MAX_DATE,
        df
    )

    rango_fechas = date_picker["component"]
    btn_inicio = date_picker["btn_inicio"]
    fecha_inicio_val = date_picker["fecha_inicio_val"]
    btn_fin = date_picker["btn_fin"]
    fecha_fin_val = date_picker["fecha_fin_val"]

    def on_currency_change(e):
        global rate_currency, current_currency, new_currency
        new_currency = currencies.value
        rate_currency = get_local_rate(rates_df, current_currency, new_currency)
        current_currency = DEFAULT_CURRENCY
        txt_new.value = new_currency
        txt_current.value = DEFAULT_CURRENCY
        page.update()
        filtrar_dataset()

    currencies.on_change = on_currency_change
    combo_accion.on_change = filtrar_dataset

    # --- UI ---
    titulo = ft.Text("📊 Actions log", size=26, weight=ft.FontWeight.BOLD, color="#CCCCCC")
    print( new_currency )
    filtros = ft.Column(
        [
            ft.Text("📅 Date range", size=18, weight=ft.FontWeight.BOLD),
            rango_fechas,
            ft.Text("💰 Currency state", size=18, weight=ft.FontWeight.BOLD),
            ft.Row(
                [
                    txt_current,
                    txt_arrow,
                    txt_new,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=25,
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=10,
    )

    # --- LAYOUT FINAL ---
    layout = create_layout(
        page=page,
        current_path=current_path,
        dispatches={},
        content_controls=[
            titulo,
            combo_accion,
            currencies,
            filtros,
            grafico_img,
            tabla,
            botones_paginacion,
            ft.Container(height=70),
        ],
        bgcolor="black",
    )

    lbl_paginacion.visible = True

    # --- CARGA INICIAL ---
    filtrado_inicial = df[
        (df["Name"] == DEFAULT_NAME) &
        (df["date"] >= min_date_ts) &
        (df["date"] <= max_date_ts)
    ]

    actualizar_tabla(filtrado_inicial)
    update_chart(page, grafico_img, filtrado_inicial, rate_currency, f"Close trend - {DEFAULT_NAME}", current_currency)

    return addElementsPage(page, [layout])