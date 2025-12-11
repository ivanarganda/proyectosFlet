# helpers/pagination_list.py

import flet as ft

def PaginatedList(
    page: ft.Page,
    title: str,
    type_:str,
    fetch_callback,        # función que devuelve la lista completa
    item_builder,          # función que construye cada tarjeta
    page_size=10,
):
    data_cache = []
    page_index = 1

    grid = ft.ResponsiveRow(spacing=10, run_spacing=10)
    loading_text = ft.Text("Cargando...", size=14, color="#1976D2")

    pagination_label = ft.Text("Página 1 de 1", size=13)
    btn_prev = ft.TextButton("◀ Anterior", disabled=True)
    btn_next = ft.TextButton("Siguiente ▶", disabled=True)

    def render_page():
        nonlocal page_index

        grid.controls.clear()

        total_pages = max(1, (len(data_cache) + page_size - 1) // page_size)
        page_index = max(1, min(page_index, total_pages))

        start = (page_index - 1) * page_size
        end = start + page_size

        for item in data_cache[start:end]:
            grid.controls.append(
                ft.Container(
                    content=item_builder(type_,item),
                    col={"xs": 12, "sm": 6, "md": 4, "lg": 3}
                )
            )

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

    # CARGAR DATOS
    def load_data():
        nonlocal data_cache, page_index

        loading_text.visible = True
        grid.controls.clear()
        page.update()

        data_cache = fetch_callback()
        page_index = 1
        render_page()

        loading_text.visible = False
        page.update()

    return ft.Column(
        [
            ft.Text(title, size=22, weight="bold", color="white"),
            loading_text,
            grid,
            ft.Row([btn_prev, pagination_label, btn_next], alignment=ft.MainAxisAlignment.CENTER),
        ],
        scroll=ft.ScrollMode.AUTO
    ), load_data
