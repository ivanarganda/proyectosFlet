import os
import flet as ft
import requests

from helpers.pagination_table_pro import PaginatedTablePRO
from params import REQUEST_URL, HEADERS

# -----------------------------
# METADATA
# -----------------------------
current_path = {
    "path": os.path.abspath(__file__),
    "folder": os.path.dirname(os.path.abspath(__file__)).split("\\")[-1],
    "file": __file__.split("\\")[-1],
}

TAB_KEYS = ["goals", "minutes", "matches", "assists"]
TAB_LABELS = ["Goleadores", "Minutos", "Partidos", "Asistencias"]


# -----------------------------
# VISTA PRINCIPAL
# -----------------------------
def RenderClasificacionesJugadores(page: ft.Page):

    page.window.width = 1000
    page.window.height = 900

    # CONTENEDOR CENTRAL (AQUÍ CAMBIA TODO)
    content_container = ft.Container(expand=True)

    # -----------------------------
    # CARGA DE DATOS SEGÚN TAB
    # -----------------------------
    def load_clasificacion(by: str):

        # Loader inmediato
        content_container.content = ft.ProgressRing()
        page.update()

        try:
            r = requests.get(
                f"{REQUEST_URL}/info/clasificaciones/jugadores",
                params={"by": by},
                headers=HEADERS,
                timeout=10
            )
            r.raise_for_status()
            data = r.json().get("data", [])
        except Exception as ex:
            content_container.content = ft.Text(
                f"Error cargando datos: {ex}",
                color="red"
            )
            page.update()
            return

        if not data:
            content_container.content = ft.Text(
                "No hay datos disponibles",
                size=16
            )
            page.update()
            return

        # Columnas dinámicas (sin IDs)
        columns = [
            c for c in data[0].keys()
            if not c.lower().startswith("id")
        ]

        # Tabla paginada
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

    # -----------------------------
    # TABS (SOLO CAMBIAN ESTADO)
    # -----------------------------
    tabs = ft.Tabs(
        selected_index=0,
        on_change=lambda e: load_clasificacion(
            TAB_KEYS[e.control.selected_index]
        ),
        tabs=[
            ft.Tab(text=label)
            for label in TAB_LABELS
        ]
    )

    # CARGA INICIAL
    load_clasificacion(TAB_KEYS[0])

    # -----------------------------
    # LAYOUT FINAL
    # -----------------------------
    return ft.Column(
        spacing=0,
        controls=[
            tabs,
            ft.Divider(height=2),
            content_container
        ]
    )
