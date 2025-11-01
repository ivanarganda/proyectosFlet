import os
import io
import base64
from dotenv import load_dotenv
import flet as ft
import pandas as pd
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from helpers.utils import addElementsPage, log_error
from footer_navegation.navegation import footer_navbar

# === CARGA ENTORNO ===
load_dotenv()

current_path = {
    "path": os.path.abspath(__file__),
    "folder": os.path.dirname(os.path.abspath(__file__)).split("\\")[-1],
    "file": os.path.basename(__file__),
}

# === CARGAR DATASET LOCAL ===
DATASET_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "all_stocks_5yr.csv")
df = pd.read_csv(DATASET_PATH)
df = df[["date", "open", "close", "high", "low", "volume", "Name"]]
df["date"] = pd.to_datetime(df["date"])

# === CARGAR RATES LOCALES ===
RATES_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "rates_yearly_symbols.json")
rates_df = pd.read_json(RATES_PATH)

# Obtener monedas únicas
available_currencies = sorted(rates_df["currency"].unique().tolist())

# --- Fechas mínimas y máximas ---
min_date = pd.to_datetime(df["date"].min())
max_date = pd.to_datetime(df["date"].max())

DEFAULT_NAME = "AAL" if "AAL" in df["Name"].unique() else df["Name"].unique()[0]
DEFAULT_CURRENCY = "USD"
current_currency = DEFAULT_CURRENCY
rate_currency = 1.0

filters = {
    "accion": DEFAULT_NAME,
    "fecha_inicio": str(min_date.date()),
    "fecha_fin": str(max_date.date()),
}


# === FUNCIONES DE CONVERSIÓN LOCAL ===
def get_local_rate(base_currency: str, target_currency: str, year: int = None) -> float:
    """Busca la tasa base→target más reciente en el JSON local."""
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


def historial_ventas(page: ft.Page):
    global current_currency, rate_currency

    page.title = "Historial de Acciones"
    page.window_width = 600
    page.window_height = 850
    page.bgcolor = "#F6F4FB"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    page_size = 50
    current_page = 1
    filtrado_global = df.copy()

    grafico_img = ft.Image(width=500, height=250, visible=False)
    tabla = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Fecha")),
            ft.DataColumn(ft.Text("Acción")),
            ft.DataColumn(ft.Text("Apertura")),
            ft.DataColumn(ft.Text("Cierre")),
            ft.DataColumn(ft.Text("Volumen")),
        ],
        rows=[],
        column_spacing=10,
        heading_row_color="#5A2D9C",
        data_row_color={"hovered": "#EEE"},
    )
    lbl_paginacion = ft.Text("", size=13, color="white")

    # === FUNCIONES DE TABLA ===
    def actualizar_tabla(df_filtrado):
        nonlocal filtrado_global
        filtrado_global = df_filtrado
        actualizar_pagina(1)

    def actualizar_pagina(pagina):
        nonlocal current_page
        total_filas = len(filtrado_global)
        total_paginas = max(1, (total_filas + page_size - 1) // page_size)
        current_page = max(1, min(pagina, total_paginas))
        start = (current_page - 1) * page_size
        end = start + page_size
        subset = filtrado_global.iloc[start:end]

        tabla.rows.clear()
        for _, fila in subset.iterrows():
            date_ = fila["date"].strftime("%Y-%m-%d")
            open_ = fila["open"] * rate_currency
            close_ = fila["close"] * rate_currency
            tabla.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(date_)),
                        ft.DataCell(ft.Text(fila["Name"])),
                        ft.DataCell(ft.Text(f"{open_:.2f} {current_currency}")),
                        ft.DataCell(ft.Text(f"{close_:.2f} {current_currency}")),
                        ft.DataCell(ft.Text(f"{fila['volume']}")),
                    ]
                )
            )

        lbl_paginacion.value = f"Página {current_page} de {total_paginas} ({total_filas} registros)"
        page.update()

    def siguiente_pagina(e): actualizar_pagina(current_page + 1)
    def anterior_pagina(e): actualizar_pagina(current_page - 1)

    botones_paginacion = ft.Row(
        [
            ft.ElevatedButton("⬅️ Anterior", on_click=anterior_pagina, width=120, bgcolor="#5A2D9C", color="white"),
            lbl_paginacion,
            ft.ElevatedButton("Siguiente ➡️", on_click=siguiente_pagina, width=120, bgcolor="#5A2D9C", color="white"),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
    )

    # === GRAFICO ===
    def actualizar_grafico(df_filtrado):
        if df_filtrado.empty:
            grafico_img.visible = False
            page.update()
            return
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.plot(df_filtrado["date"], df_filtrado["close"] * rate_currency, color="#5A2D9C", linewidth=2)
        ax.set_title(f"Tendencia del Precio de Cierre - {filters['accion']} ({current_currency})", fontsize=11)
        ax.set_xlabel("Fecha")
        ax.set_ylabel(f"Precio ({current_currency})")
        ax.grid(True, linestyle="--", alpha=0.4)
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        grafico_img.src_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        grafico_img.visible = True
        page.update()

    # === FECHAS ===
    fecha_inicio_val = ft.Text(filters["fecha_inicio"], color="#CCCCCC")
    fecha_fin_val = ft.Text(filters["fecha_fin"], color="#CCCCCC")

    def on_inicio_change(e):
        fecha_inicio_val.value = e.control.value.strftime("%Y-%m-%d")
        filters["fecha_inicio"] = fecha_inicio_val.value
        filtrar_dataset()

    def on_fin_change(e):
        fecha_fin_val.value = e.control.value.strftime("%Y-%m-%d")
        filters["fecha_fin"] = fecha_fin_val.value
        filtrar_dataset()

    picker_inicio = ft.DatePicker(on_change=on_inicio_change, first_date=min_date, last_date=max_date)
    picker_fin = ft.DatePicker(on_change=on_fin_change, first_date=min_date, last_date=max_date)
    page.overlay.append(picker_inicio)
    page.overlay.append(picker_fin)

    btn_inicio = ft.ElevatedButton("📅 Desde", on_click=lambda e: picker_inicio.pick_date(), bgcolor="#5A2D9C", color="white")
    btn_fin = ft.ElevatedButton("📅 Hasta", on_click=lambda e: picker_fin.pick_date(), bgcolor="#5A2D9C", color="white")

    # === FILTRO POR ACCIÓN ===
    acciones = sorted(df["Name"].unique().tolist())
    combo_accion = ft.Dropdown(
        label="Acción (empresa)",
        options=[ft.dropdown.Option(a) for a in acciones],
        value=DEFAULT_NAME,
        width=350,
        border_color="#5A2D9C",
        on_change=lambda e: filtrar_dataset(),
    )

    # === SELECTOR DE MONEDA LOCAL ===
    currencies = ft.Dropdown(
        label="Moneda",
        options=[ft.dropdown.Option(c) for c in available_currencies],
        value=DEFAULT_CURRENCY,
        width=150,
        border_color="#5A2D9C",
    )

    def on_currency_change(e):
        global rate_currency, current_currency
        new_currency = currencies.value

        snackbar = ft.SnackBar(ft.Text(f"💱 Convirtiendo valores a {new_currency}..."), bgcolor="#5A2D9C")
        page.snack_bar = snackbar
        snackbar.open = True
        page.update()

        rate_currency = get_local_rate(current_currency, new_currency)
        current_currency = new_currency

        snackbar.open = False
        filtrar_dataset()
        page.update()

    currencies.on_change = on_currency_change

    # === FILTRADO ===
    def filtrar_dataset(e=None):
        accion = combo_accion.value or DEFAULT_NAME
        start = pd.to_datetime(fecha_inicio_val.value)
        end = pd.to_datetime(fecha_fin_val.value)
        filters["accion"] = accion

        filtrado = df[(df["Name"] == accion) & (df["date"] >= start) & (df["date"] <= end)]
        actualizar_tabla(filtrado)
        actualizar_grafico(filtrado)

    # === UI ===
    titulo = ft.Text("📊 Historial de Acciones", size=26, weight=ft.FontWeight.BOLD, color="#CCCCCC")
    filtros = ft.Column(
        [
            ft.Text("📅 Rango de Fechas", size=18, weight=ft.FontWeight.BOLD),
            ft.Row([ft.Column([btn_inicio, fecha_inicio_val]), ft.Column([btn_fin, fecha_fin_val])], alignment=ft.MainAxisAlignment.CENTER, spacing=25),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=10,
    )

    contenido = ft.Column(
        [
            titulo,
            combo_accion,
            currencies,
            filtros,
            ft.Container(height=15),
            grafico_img,
            ft.Container(height=10),
            tabla,
            ft.Container(height=10),
            botones_paginacion,
            ft.Container(height=70),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    footer = footer_navbar(page=page, current_path=current_path, dispatches={})
    layout = ft.Stack(
        [
            ft.Container(content=contenido, expand=True),
            ft.Container(content=footer, bottom=0, left=0, right=0, bgcolor="#F6F4FB",
                         shadow=ft.BoxShadow(blur_radius=12, color=ft.colors.with_opacity(0.15, "#CCCCCC"))),
        ],
        expand=True,
    )

    filtrado_inicial = df[(df["Name"] == DEFAULT_NAME) & (df["date"] >= min_date) & (df["date"] <= max_date)]
    actualizar_tabla(filtrado_inicial)
    actualizar_grafico(filtrado_inicial)

    return addElementsPage(page, [layout])
