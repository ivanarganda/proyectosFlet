import os
import flet as ft
import requests
from helpers.utils import addElementsPage
from .common_components_info import RenderList, build_card
from footer_navegation.navegation import footer_navbar
from middlewares.auth import middleware_auth
from params import REQUEST_URL, HEADERS

current_path = {
    "path": os.path.abspath(__file__),
    "folder": os.path.dirname(os.path.abspath(__file__)).split("\\")[-1],
    "file": __file__.split("\\")[-1],
}

headers = HEADERS
label_page = "Jornada"

def RenderPartidos(page: ft.Page):

    session = middleware_auth(page)

    token = session.get("token")
    headers["Authorization"] = f"Bearer {token}"

    cards_grid = ft.ResponsiveRow(
        spacing=10,
        run_spacing=10,
    )

    page.window.width = 1200
    page.window.height = 800

    # ➤ LISTA VACÍA (scroll automático)
    cards_grid = ft.ResponsiveRow()

    loading_text = ft.Text("Cargando partidos...", size=14, color="#1976D2")

    # PAGINACIÓN
    page_index = 1
    page_size = 10
    data_cache = []

    pagination_label = ft.Text("{label_page} 1 de 1", size=13, color="#424242")
    btn_prev = ft.TextButton("◀ Anterior", disabled=True)
    btn_next = ft.TextButton("Siguiente ▶", disabled=True)

    def render_page():
        nonlocal page_index, cards_grid

        cards_grid.controls.clear()

        total_pages = max(1, (len(data_cache) + page_size - 1) // page_size)
        page_index = max(1, min(page_index, total_pages))

        start = (page_index - 1) * page_size
        end = start + page_size

        for item in data_cache[start:end]:
            cards_grid.controls.append(
                ft.Container(
                    content=build_card("partidos",item),
                    col={"xs": 12, "sm": 6, "md": 4, "lg": 3}  # RESPONSIVE REAL
                )
            )

        pagination_label.value = f"{label_page} {page_index} de {total_pages}"
        btn_prev.disabled = page_index == 1
        btn_next.disabled = page_index == total_pages

        page.update()

    def prev_page(e):
        nonlocal page_index
        page_index -= 1
        render_page()

    def next_page(e):
        nonlocal page_index
        page_index += 1
        render_page()

    btn_prev.on_click = prev_page
    btn_next.on_click = next_page

    # ----------- CARGA DATOS -----------
    def load_partidos():
        nonlocal data_cache, page_index, cards_grid

        loading_text.visible = True
        cards_grid.controls.clear()
        page.update()

        try:
            response = requests.get(f"{REQUEST_URL}/info/partidos", headers=headers)
            data_cache = response.json().get("data", [])

            page_index = 1
            render_page()

        except Exception as e:
            cards_grid.controls.append(ft.Text(f"❌ Error: {e}"))

        loading_text.visible = False
        page.update()

    # ----------- UI FINAL -----------
    content = RenderList(
        "Información de partidos",
        loading_text,
        cards_grid,
        load_partidos,
        extra_footer=ft.Row(
            [btn_prev, pagination_label, btn_next],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20,
        )
    )

    load_partidos()

    footer = footer_navbar(page=page, current_path=current_path, dispatches={})

    main_content = content

    # === STACK GLOBAL ===
    stack = ft.Stack(
        [
            ft.Container(
                content= ft.Column([
                    main_content
                ],
                scroll=ft.ScrollMode.AUTO,
                ),
                expand=True,
                padding=ft.padding.only(bottom=60),   # espacio para el footer
            ),

            footer
        ],
        expand=True,
    )


    return addElementsPage(page, [stack])
