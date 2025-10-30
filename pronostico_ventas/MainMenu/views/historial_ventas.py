import os
import io
import base64
import flet as ft
import pandas as pd
import requests
import matplotlib
matplotlib.use("Agg")  # ✅ sin interfaz gráfica
import matplotlib.pyplot as plt
from helpers.utils import addElementsPage
from footer_navegation.navegation import footer_navbar

current_path = {
    "path": os.path.abspath(__file__),
    "folder": os.path.dirname(os.path.abspath(__file__)).split("\\")[-1],
    "file": os.path.basename(__file__),
}

# --- Cargar dataset real ---
DATASET_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "all_stocks_5yr.csv")
df = pd.read_csv(DATASET_PATH)
df = df[["date", "open", "close", "high", "low", "volume", "Name"]]
df["date"] = pd.to_datetime(df["date"])

# --- Fechas mínimas y máximas ---
min_date = pd.to_datetime(df["date"].min())
max_date = pd.to_datetime(df["date"].max())

# --- Acción por defecto ---
DEFAULT_NAME = "A" if "A" in df["Name"].unique() else df["Name"].unique()[0]

DEFAULT_CURRENCY = "USD"
# Make a conversion currency, possibility to change later

filters = {
    "accion": DEFAULT_NAME,
    "fecha_inicio": str(min_date),
    "fecha_fin": str(max_date),
}


def historial_ventas(page: ft.Page):
    # --- CONFIGURACIÓN DE LA PÁGINA ---
    page.title = "Historial de Acciones"
    page.window_width = 600
    page.window_height = 850
    page.bgcolor = "#F6F4FB"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    # --- VARIABLES DE ESTADO ---
    page_size = 50
    current_page = 1
    filtrado_global = df.copy()

    # --- ELEMENTOS DE INTERFAZ ---
    grafico_img = ft.Image(width=450, height=250, visible=False)
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

    lbl_paginacion = ft.Text("", size=13, color="#FFFFFF")

    # --- FUNCIONES AUXILIARES ---
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
            tabla.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(fila["date"].strftime("%Y-%m-%d"))),
                        ft.DataCell(ft.Text(fila["Name"])),
                        ft.DataCell(ft.Text(f"{fila['open']:.2f}")),
                        ft.DataCell(ft.Text(f"{fila['close']:.2f}")),
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

    # --- FUNCIÓN: GRAFICAR DATOS ---
    def actualizar_grafico(df_filtrado):
        if df_filtrado.empty:
            grafico_img.visible = False
            page.update()
            return

        fig, ax = plt.subplots(figsize=(6, 3))
        ax.plot(df_filtrado["date"], df_filtrado["close"], color="#5A2D9C", linewidth=2)
        ax.set_title(f"Tendencia del Precio de Cierre - {filters['accion']}", fontsize=11)
        ax.set_xlabel("Fecha")
        ax.set_ylabel("Precio")
        ax.grid(True, linestyle="--", alpha=0.4)
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        grafico_img.src_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        grafico_img.visible = True
        page.update()

    # --- CALENDARIOS ---
    fecha_inicio_val = ft.Text(filters["fecha_inicio"], color="black")
    fecha_fin_val = ft.Text(filters["fecha_fin"], color="black")

    def on_inicio_change(e):
        fecha_inicio_val.value = e.control.value.strftime("%Y-%m-%d")
        filters["fecha_inicio"] = fecha_inicio_val.value
        page.update()
        filtrar_dataset()

    def on_fin_change(e):
        fecha_fin_val.value = e.control.value.strftime("%Y-%m-%d")
        filters["fecha_fin"] = fecha_fin_val.value
        page.update()
        filtrar_dataset()

    picker_inicio = ft.DatePicker(
        on_change=on_inicio_change,
        first_date=min_date,
        last_date=max_date,
        date_picker_entry_mode=ft.DatePickerEntryMode.CALENDAR_ONLY,
    )

    picker_fin = ft.DatePicker(
        on_change=on_fin_change,
        first_date=min_date,
        last_date=max_date,
        date_picker_entry_mode=ft.DatePickerEntryMode.CALENDAR_ONLY,
    )

    page.overlay.append(picker_inicio)
    page.overlay.append(picker_fin)

    btn_inicio = ft.ElevatedButton(
        text="📅 Seleccionar fecha inicial",
        on_click=lambda e: picker_inicio.pick_date(),
        bgcolor="#5A2D9C",
        color="white",
    )

    btn_fin = ft.ElevatedButton(
        text="📅 Seleccionar fecha final",
        on_click=lambda e: picker_fin.pick_date(),
        bgcolor="#5A2D9C",
        color="white",
    )

    # --- FILTRO POR ACCIÓN ---
    acciones = sorted(df["Name"].unique().tolist())
    combo_accion = ft.Dropdown(
        label="Acción (empresa)",
        options=[ft.dropdown.Option(a) for a in acciones],
        value=DEFAULT_NAME,  # 👈 valor inicial por defecto
        width=350,
        border_color="#5A2D9C",
        on_change=lambda e: filtrar_dataset(),
    )

    # --- FILTRADO GENERAL ---
    def filtrar_dataset(e=None):
        accion = combo_accion.value or DEFAULT_NAME
        start = pd.to_datetime(fecha_inicio_val.value)
        end = pd.to_datetime(fecha_fin_val.value)
        filtrado = df.copy()

        filters["accion"] = accion
        filtrado = filtrado[(filtrado["Name"] == accion) &
                            (filtrado["date"] >= start) &
                            (filtrado["date"] <= end)]

        actualizar_tabla(filtrado)
        actualizar_grafico(filtrado)

    # --- INTERFAZ ---
    titulo = ft.Text("📊 Historial de Acciones", size=26, weight=ft.FontWeight.BOLD, color="#CCCCCC")

    filtros = ft.Column(
        [
            ft.Text("📅 Rango de Fechas", size=18, weight=ft.FontWeight.BOLD),
            ft.Row(
                [
                    ft.Column([btn_inicio, fecha_inicio_val]),
                    ft.Column([btn_fin, fecha_fin_val]),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=25,
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=10,
    )

    contenido = ft.Column(
        [
            titulo,
            combo_accion,
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

    # --- FOOTER ---
    footer = footer_navbar(page=page, current_path=current_path, dispatches={})
    layout = ft.Stack(
        [
            ft.Container(content=contenido, expand=True),
            ft.Container(
                content=footer,
                bottom=0,
                left=0,
                right=0,
                bgcolor="#F6F4FB",
                shadow=ft.BoxShadow(blur_radius=12, color=ft.colors.with_opacity(0.15, "black")),
            ),
        ],
        expand=True,
    )

    # --- Inicialización ---
    filtrado_inicial = df[
        (df["Name"] == DEFAULT_NAME) &
        (df["date"] >= min_date) &
        (df["date"] <= max_date)
    ]

    actualizar_tabla(filtrado_inicial)
    actualizar_grafico(filtrado_inicial)

    return addElementsPage(page, [layout])
