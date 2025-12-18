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


def RenderClasificacionesEquipos(page: ft.Page):

    content_container = ft.Container(expand=True)

    def load():
        content_container.content = ft.ProgressRing()
        page.update()

        r = requests.get(
            f"{REQUEST_URL}/info/clasificaciones/equipos",
            headers=HEADERS
        )
        data = r.json().get("data", [])

        if not data:
            content_container.content = ft.Text("No hay datos")
        else:
            columns = [c for c in data[0].keys() if not c.lower().startswith("id")]

            table, load_table = PaginatedTablePRO(
                page=page,
                title="",
                columns=columns,
                fetch_callback=lambda: data,
                page_size=15
            )

            load_table()
            content_container.content = table

        page.update()

    load()

    return content_container
