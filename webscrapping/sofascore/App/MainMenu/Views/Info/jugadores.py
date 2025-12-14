# pages/equipos.py
import os
import flet as ft
import requests
from helpers.pagination_list import PaginatedList
from helpers.utils import addElementsPage, has_parameter_id, get_ids
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

def RenderJugadores(page: ft.Page , params = {}):

    page.window.height=800
    page.window.width=900

    session = middleware_auth(page)

    token = session.get("token")
    headers["Authorization"] = f"Bearer {token}"

    def apply_filters():
        qp = []

        if filter_id.value.strip():
            qp.append(f"id={filter_id.value.strip()}")

        query_string = "&".join(qp)
        page.go(f"/info/jugadores?{query_string}")

    options, key_id, key_name = get_ids("/info/equipos", [ "id_equipo", "nombre" ])

    filter_id = ft.Dropdown(
        label="Equipo",
        options=[ft.dropdown.Option( text=op[key_name], key=op[key_id] ) for op in options],
        value=params.get("id") if params else "",
        width=350,
        border_color="#5A2D9C",
        on_change=lambda e: apply_filters()
    )

    def on_change_id(e: ft.ControlEvent):
        page.go( f"/info/jugadores?id={e.control.va}" )

    def fetch_jugadores():
        query_param = ""

        if has_parameter_id(params):
            lista = [f"{k}={v}" for k,v in params.items() if v not in ("", None, "None")]
            query_param = "?" + "&".join(lista)

        r = requests.get(
            f"{REQUEST_URL}/info/jugadores{query_param}",
            headers=HEADERS
        )

        return r.json().get("data", [])


    content, load_data = PaginatedList(
        page=page,
        title="Jugadores de LaLiga",
        type_="jugadores",
        fetch_callback=fetch_jugadores,
        item_builder=build_card,
        page_size=12
    )

    load_data()

    footer = ft.Container(
        content=footer_navbar(page=page, current_path=current_path, dispatches={}),
        expand=False
    )

    main_content = content

    filters_bar = ft.Row(
        [
            filter_id,
            # filter_name,
        ],
        spacing=10
    )

    layout = ft.Column(
        [
            ft.Container(filters_bar, padding=10),
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
