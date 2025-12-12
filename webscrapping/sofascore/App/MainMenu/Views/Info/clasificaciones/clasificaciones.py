import os
import flet as ft
import requests

from .clasificaciones_jugadores import RenderClasificacionesJugadores
from .clasificaciones_equipos import RenderClasificacionesEquipos

from helpers.utils import addElementsPage
from footer_navegation.navegation import footer_navbar
from params import REQUEST_URL, HEADERS

current_path = {
    "path": os.path.abspath(__file__),
    "folder": os.path.dirname(os.path.abspath(__file__)).split("\\")[-1],
    "file": __file__.split("\\")[-1],
}

def RenderClasificaciones(page: ft.Page, params=None):

    page.window.width = 1000
    page.window.height = 900

    # --- FOOTER DEFINIDO AQUÍ ---
    footer = ft.Container(
        content=footer_navbar(page=page, current_path=current_path, dispatches={}),
        expand=False
    )

    # --- TABS ---
    tabs = ft.Tabs(
        selected_index=0,
        expand=True,
        tabs=[
            ft.Tab(
                text="Jugadores",
                content=RenderClasificacionesJugadores(page)
            ),
            ft.Tab(
                text="Equipos",
                content=RenderClasificacionesEquipos(page)
            )
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
