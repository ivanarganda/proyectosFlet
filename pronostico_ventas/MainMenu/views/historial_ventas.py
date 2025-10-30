import os
import io
import base64
import flet as ft
import pandas as pd
import matplotlib.pyplot as plt
from helpers.utils import addElementsPage
from footer_navegation.navegation import footer_navbar

# --- Función para años bisiestos ---
def leap_year(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

current_path = {
    "path": os.path.abspath(__file__),
    "folder": os.path.dirname(os.path.abspath(__file__)).split("\\")[-1],
    "file": os.path.basename(__file__)
}

# --- Cargar dataset real ---
DATASET_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "all_stocks_5yr.csv")
df = pd.read_csv(DATASET_PATH)
df = df[["date", "open", "close", "high", "low", "volume", "Name"]]
df["date"] = pd.to_datetime(df["date"])

def historial_ventas(page: ft.Page):

    # --- CONFIGURACIÓN DE LA PÁGINA ---
    page.title = "Historial de Acciones"
    page.window_width = 500
    page.window_height = 850
    page.bgcolor = "#F6F4FB"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    # --- RANGOS DE FECHA ---
    range_years = sorted(df["date"].dt.year.unique().tolist())
    range_months = list(range(1, 13))

    def get_days(year: int, month: int):
        feb_days = 29 if leap_year(year) else 28
        month_days = {1: 31, 2: feb_days, 3: 31, 4: 30, 5: 31, 6: 30,
                      7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
        return list(range(1, month_days[month] + 1))

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

    lbl_paginacion = ft.Text("", size=13, color="black")

    # --- FUNCIÓN: ACTUALIZAR TABLA CON PAGINACIÓN ---
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

    # --- NAVEGACIÓN DE PÁGINAS ---
    def siguiente_pagina(e):
        actualizar_pagina(current_page + 1)

    def anterior_pagina(e):
        actualizar_pagina(current_page - 1)

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
        ax.set_title("Tendencia del Precio de Cierre", fontsize=11)
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

    # --- FILTRAR EN FUNCIÓN DE SELECCIÓN ---
    def filtrar_dataset(e=None):
        accion = combo_accion.value
        year = combo_year.value
        month = combo_month.value
        day = combo_day.value

        filtrado = df.copy()

        if accion and accion != "Todas":
            filtrado = filtrado[filtrado["Name"] == accion]
        if year:
            filtrado = filtrado[filtrado["date"].dt.year == int(year)]
        if month:
            filtrado = filtrado[filtrado["date"].dt.month == int(month)]
        if day:
            filtrado = filtrado[filtrado["date"].dt.day == int(day)]

        actualizar_tabla(filtrado)
        actualizar_grafico(filtrado)

    # --- SELECTS ---
    acciones = sorted(df["Name"].unique().tolist())
    combo_accion = ft.Dropdown(
        label="Acción (empresa)",
        options=[ft.dropdown.Option("Todas")] + [ft.dropdown.Option(a) for a in acciones],
        value="Todas",
        width=350,
        border_color="#5A2D9C",
        on_change=filtrar_dataset,
    )

    combo_year = ft.Dropdown(
        label="Año",
        options=[ft.dropdown.Option(str(y)) for y in range_years],
        width=350,
        border_color="#5A2D9C",
        on_change=lambda e: mostrar_meses(),
    )

    combo_month = ft.Dropdown(
        label="Mes",
        options=[ft.dropdown.Option(str(m)) for m in range_months],
        width=350,
        border_color="#5A2D9C",
        visible=False,
        on_change=lambda e: mostrar_dias(),
    )

    combo_day = ft.Dropdown(
        label="Día",
        width=350,
        border_color="#5A2D9C",
        visible=False,
        on_change=filtrar_dataset,
    )

    # --- FUNCIONES PARA MOSTRAR SIGUIENTES FILTROS ---
    def mostrar_meses():
        if combo_year.value:
            combo_month.visible = True
            combo_day.visible = False
            page.update()
        filtrar_dataset()

    def mostrar_dias():
        if combo_year.value and combo_month.value:
            year = int(combo_year.value)
            month = int(combo_month.value)
            days = get_days(year, month)
            combo_day.options = [ft.dropdown.Option(str(d)) for d in days]
            combo_day.visible = True
            page.update()
        filtrar_dataset()

    # --- INTERFAZ ---
    titulo = ft.Text("📊 Historial de Acciones", size=26, weight=ft.FontWeight.BOLD, color="#1E1E1E")

    contenido = ft.Column(
        [
            titulo,
            combo_accion,
            combo_year,
            combo_month,
            combo_day,
            ft.Container(height=15),
            grafico_img,
            ft.Container(height=10),
            tabla,
            ft.Container(height=10),
            botones_paginacion,
            ft.Container(height=70),  # margen para footer
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

    # --- Inicializar con primeras filas ---
    actualizar_tabla(df.head(100))
    actualizar_grafico(df.head(100))

    return addElementsPage(page, [layout])
