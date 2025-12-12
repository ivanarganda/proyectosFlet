import os
import flet as ft
import requests

from helpers.pagination_table import PaginatedTable
from helpers.pagination_table_pro import PaginatedTablePRO

from helpers.utils import addElementsPage
from footer_navegation.navegation import footer_navbar
from params import REQUEST_URL, HEADERS

current_path = {
    "path": os.path.abspath(__file__),
    "folder": os.path.dirname(os.path.abspath(__file__)).split("\\")[-1],
    "file": __file__.split("\\")[-1],
}

TAB_KEYS = ["goals", "minutes", "matches", "assists"]
TAB_TITLES = {
    "goals": "Pichichi",
    "minutes": "Minutos Jugados",
    "matches": "Partidos Jugados",
    "assists": "Máximos Asistentes",
}


def RenderClasificaciones(page: ft.Page, params=None):

    page.window.width = 1000
    page.window.height = 900

    def fetch_data(by: str):
        r = requests.get(
            f"{REQUEST_URL}/info/clasificaciones/jugadores?by={by}",
            headers=HEADERS
        )
        return r.json().get("data", [])

    def build_table(by: str):
        datos = fetch_data(by)

        if not datos:
            return ft.Text("No hay datos disponibles", size=16)

        columns = list(datos[0].keys())

        columns = [c for c in columns if not c.lower().startswith("id") ]

        table, load = PaginatedTablePRO(
            page=page,
            title=TAB_TITLES[by],
            columns=columns,
            fetch_callback=lambda: fetch_data(by),
            page_size=15
        )

        load()
        return table

    footer = ft.Container(
        content=footer_navbar(page=page, current_path=current_path, dispatches={}),
        expand=False
    )

    tabs = ft.Tabs(
        selected_index=0,
        expand=True,
        tabs=[
            ft.Tab(text="Goles", content=build_table("goals")),
            ft.Tab(text="Minutos", content=build_table("minutes")),
            ft.Tab(text="Partidos", content=build_table("matches")),
            ft.Tab(text="Asistencias", content=build_table("assists")),
        ]
    )

    layout = ft.Column(
        [
            ft.Column([tabs], expand=True),
            ft.Divider(height=2),
            footer
        ],
        expand=True,
        spacing=0
    )

    return addElementsPage(page, [layout])
