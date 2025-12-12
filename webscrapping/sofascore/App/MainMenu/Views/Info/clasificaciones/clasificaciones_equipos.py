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


def RenderClasificacionesEquipos(page: ft.Page, params=None):

    page.window.width = 1000
    page.window.height = 900

    def fetch_data():
        r = requests.get(
            f"{REQUEST_URL}/info/clasificaciones/equipos",
            headers=HEADERS
        )
        return r.json().get("data", [])

    def build_table():
        datos = fetch_data()

        if not datos:
            return ft.Text("No hay datos disponibles", size=16)

        columns = list(datos[0].keys())

        columns = [c for c in columns if not c.lower().startswith("id") ]

        table, load = PaginatedTablePRO(
            page=page,
            title="",
            columns=columns,
            fetch_callback=lambda: fetch_data(),
            page_size=15
        )

        load()
        return table

    table = build_table()

    layout = ft.Column(
        [
            ft.Column([table], expand=True),
            ft.Container(content=ft.Text(""),height=10)
        ],
        expand=True,
        spacing=0
    )

    return addElementsPage(page, [layout])
