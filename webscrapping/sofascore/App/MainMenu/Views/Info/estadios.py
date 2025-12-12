# pages/equipos.py
import os
import flet as ft
import requests
from helpers.pagination_list import PaginatedList
from helpers.utils import addElementsPage
from .common_components_info import build_card
from footer_navegation.navegation import footer_navbar
from middlewares.auth import middleware_auth
from params import REQUEST_URL, HEADERS

current_path = {
    "path": os.path.abspath(__file__),
    "folder": os.path.dirname(os.path.abspath(__file__)).split("\\")[-1],
    "file": __file__.split("\\")[-1],
}

headers = HEADERS
label_page = "Pagina"

def RenderEstadios(page: ft.Page , params = {}):

    page.window.height=800
    page.window.width=900

    session = middleware_auth(page)

    token = session.get("token")
    headers["Authorization"] = f"Bearer {token}"

    def fetch_estadios():
        r = requests.get(f"{REQUEST_URL}/info/estadios", headers=HEADERS)
        return r.json().get("data", [])

    content, load_data = PaginatedList(
        page=page,
        title="Estadios de LaLiga",
        type_="estadios",
        fetch_callback=fetch_estadios,
        item_builder=build_card,
        page_size=12
    )

    load_data()

    footer = ft.Container(
        content=footer_navbar(page=page, current_path=current_path, dispatches={}),
        expand=False
    )

    main_content = content

    layout = ft.Column(
        [
            ft.Container(
                content=ft.Column(
                    [
                        main_content
                    ],
                    scroll=ft.ScrollMode.AUTO
                ),
                expand=True,
                padding=ft.padding.only(bottom=10)
            ),
            footer
        ],
        expand=True,
        spacing=0
    )

    return addElementsPage(page, [layout])
