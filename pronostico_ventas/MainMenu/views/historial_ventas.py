import os
import flet as ft
import pandas as pd
from helpers.utils import addElementsPage
from footer_navegation.navegation import footer_navbar

current_path = {
    "path": os.path.abspath(__file__),
    "folder": os.path.dirname(os.path.abspath(__file__)).split("\\")[-1],
    "file": __file__.split("\\")[-1]
}

# --- Cargar dataset desde el archivo real ---
DATASET_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "all_stocks_5yr.csv")
df = pd.read_csv(DATASET_PATH)

# Solo nos quedamos con columnas útiles
df = df[["date", "open", "close", "high", "low", "volume", "Name"]]

def historial_ventas(page: ft.Page):

    # --- CONFIGURACIÓN DE LA PÁGINA ---
    page.title = "Historial de Acciones"
    page.window_width = 500
    page.window_height = 800
    page.resizable = False
    page.bgcolor = "#F6F4FB"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    # --- FUNCIÓN PARA FILTRAR ---
    def filtrar_dataset(e):
        accion = combo_accion.value
        if accion == "Todas":
            filtrado = df.head(100)  # limitar para no saturar
        else:
            filtrado = df[df["Name"] == accion].head(100)

        # Limpiar tabla y volver a llenar
        tabla.rows.clear()
        for _, fila in filtrado.iterrows():
            tabla.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(fila["date"])),
                        ft.DataCell(ft.Text(fila["Name"])),
                        ft.DataCell(ft.Text(f"{fila['open']:.2f}")),
                        ft.DataCell(ft.Text(f"{fila['close']:.2f}")),
                        ft.DataCell(ft.Text(f"{fila['volume']}")),
                    ]
                )
            )
        page.update()

    # --- SELECT (ComboBox) ---
    opciones = sorted(df["Name"].unique().tolist())
    combo_accion = ft.Dropdown(
        label="Selecciona una acción (empresa)",
        options=[ft.dropdown.Option("Todas")] + [ft.dropdown.Option(a) for a in opciones],
        value="Todas",
        on_change=filtrar_dataset,
        width=350,
        border_color="#5A2D9C",
    )

    # --- TABLA DE RESULTADOS ---
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
        heading_row_color=ft.colors.GREY_500,
        data_row_color={"hovered": "#F6F4FB"},
    )

    # Inicializar con primeras filas
    for _, fila in df.head(100).iterrows():
        tabla.rows.append(
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(fila["date"])),
                    ft.DataCell(ft.Text(fila["Name"])),
                    ft.DataCell(ft.Text(f"{fila['open']:.2f}")),
                    ft.DataCell(ft.Text(f"{fila['close']:.2f}")),
                    ft.DataCell(ft.Text(f"{fila['volume']}")),
                ]
            )
        )

    # --- INTERFAZ ---
    contenido = ft.Column(
        [
            ft.Text("📈 Historial de Acciones", size=26, weight=ft.FontWeight.BOLD, color="white"),
            combo_accion,
            ft.Container(height=20),
            tabla
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        scroll=ft.ScrollMode.AUTO,
        expand=True
    )

    footer = footer_navbar(page=page, current_path=current_path, dispatches={})
    layout = ft.Stack([contenido, ft.Container(
                content=footer,
                bottom=0,
                left=0,
                right=0,
                bgcolor="#F6F4FB",
                shadow=ft.BoxShadow(blur_radius=12, color=ft.colors.with_opacity(0.15, "black"))
            )], expand=True)

    return addElementsPage(page, [layout])
