import flet as ft
import requests
from helpers.utils import addElementsPage, build_row
from .common_components_info import RenderTable
from params import REQUEST_URL

columns = [
    "id_partido", "id_temporada", "id_jornada", "local",
    "visitante", "estadio", "inicio", "goles_local",
    "goles_visitante", "estado"
]

def RenderPartidos(page: ft.Page):


    page.window.width = 1200
    page.window.height = 800

    # TABLA LITE
    table = ft.DataTable(
        columns=[
            ft.DataColumn(
                ft.Container(
                    ft.Text(col.upper(), size=12, weight="bold", color="#3949AB"),
                    alignment=ft.alignment.center,
                )
            )
            for col in columns
        ],
        rows=[],
        heading_row_color="#F5F5F5",
        data_row_min_height=42,
        divider_thickness=0.3,
        show_checkbox_column=False,
        # ❌ NO expand aquí
    )



    loading_text = ft.Text("Cargando partidos...", size=14, color="#1976D2")

    # PAGINACIÓN
    page_index = 1
    page_size = 10
    total_pages = 1
    data_cache = []

    pagination_label = ft.Text("Página 1 de 1", size=13, color="#424242")

    btn_prev = ft.TextButton("◀ Anterior", disabled=True)
    btn_next = ft.TextButton("Siguiente ▶", disabled=True)

    def render_page():
        nonlocal page_index, total_pages

        table.rows.clear()

        if not data_cache:
            page.update()
            return

        total_pages = max(1, (len(data_cache) + page_size - 1) // page_size)

        page_index = max(1, min(page_index, total_pages))

        start = (page_index - 1) * page_size
        end = start + page_size
        slice_data = data_cache[start:end]

        for idx, item in enumerate(slice_data):
            table.rows.append(build_row(item, idx, columns))

        pagination_label.value = f"Página {page_index} de {total_pages}"
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

    # CARGA DE DATOS
    def load_partidos():
        nonlocal data_cache, page_index

        loading_text.visible = True
        table.rows.clear()
        page.update()

        try:
            response = requests.get(f"{REQUEST_URL}/info/partidos")
            data_cache = response.json().get("data", [])

            page_index = 1
            render_page()

        except Exception as e:
            table.rows.append(
                ft.DataRow(
                    cells=[ft.DataCell(ft.Text(f"❌ Error: {e}"))] +
                          [ft.DataCell(ft.Text("")) for _ in range(len(columns) - 1)]
                )
            )

        loading_text.visible = False
        page.update()

    # UI FINAL — SUPER LITE
    content = RenderTable(
        "Información de partidos",
        loading_text,
        table,
        load_partidos,
        extra_footer=ft.Row(
            [
                btn_prev,
                pagination_label,
                btn_next
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20,
        )
    )

    load_partidos()

    return addElementsPage(page, [content])
