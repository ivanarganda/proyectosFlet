import os
import flet as ft
import requests
from params import REQUEST_URL, HEADERS
from middlewares.auth import middleware_auth
from .estadisticas import *
from footer_navegation.navegation import footer_navbar

current_path = {
    "path": os.path.abspath(__file__),
    "folder": os.path.dirname(os.path.abspath(__file__)).split("\\")[-1],
    "file": __file__.split("\\")[-1],
}

headers = HEADERS

def RenderEstadisticasJugadores(page: ft.Page):

    session = middleware_auth(page)

    token = session.get("token")
    headers["Authorization"] = f"Bearer {token}"

    def fetch_stats():
        r = requests.get(f"{REQUEST_URL}/info/estadisticas_jugador", headers=HEADERS)
        return r.json().get("data", [])

    stats = fetch_stats()

    footer = ft.Container(
        content=footer_navbar(page=page, current_path=current_path, dispatches={}),
        expand=False
    )

    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(text="GENERAL", content=general_tab(stats)),
            ft.Tab(text="ATAQUE", content=ataque_tab(stats)),
            ft.Tab(text="PASES", content=pases_tab(stats)),
            ft.Tab(text="DEFENSA", content=defensa_tab(stats)),
        ]
    )

    layout = ft.Column(
        [
            tabs
        ],
        scroll=ft.ScrollMode.AUTO
    )

    return layout
