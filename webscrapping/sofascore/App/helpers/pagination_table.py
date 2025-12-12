import flet as ft

def PaginatedTable(
    page: ft.Page,
    title: str,
    columns: list,
    fetch_callback,
    page_size=10,
):
    data_cache = []
    page_index = 1

    # ==== ESTILOS MODERNOS UI-X LITE ====
    HEADER_BG = "#4E73DF"          # azul suave y moderno
    HEADER_TEXT = "white"

    ROW_ODD = "#F9FAFB"            # gris casi blanco
    ROW_EVEN = "#FFFFFF"

    TEXT_PRIMARY = "#2C3E50"
    TEXT_SECONDARY = "#6C757D"

    BORDER_COLOR = "#E1E5EA"

    # Tabla más compacta y moderna
    table_columns = [
        ft.DataColumn(
            label=ft.Text(
                col.replace("_", " ").upper(),
                size=12,
                weight="bold",
                color=HEADER_TEXT
            ),
            numeric=col.lower() not in ["jugador", "equipo"]
        )
        for col in columns
    ]

    datatable = ft.DataTable(
        columns=table_columns,
        rows=[],
        heading_row_color=HEADER_BG,
        heading_row_height=42,
        border=ft.border.all(0.4, BORDER_COLOR),
        horizontal_lines=ft.border.BorderSide(0.4, BORDER_COLOR),
        vertical_lines=ft.border.BorderSide(0.4, BORDER_COLOR),
        data_row_min_height=38,
        divider_thickness=0.4,
        column_spacing=18,
        show_checkbox_column=False,
    )

    loading_text = ft.Text("Cargando...", size=14, color="#4E73DF")

    pagination_label = ft.Text("Página 1 de 1", size=13, color=TEXT_SECONDARY)
    btn_prev = ft.TextButton("◀", disabled=True)
    btn_next = ft.TextButton("▶", disabled=True)

    # ========== TRUNCAR ID PARA QUE NO ROMPA LA UI ==========
    def truncate(value):
        value = str(value)
        return value[:8] + "…" if len(value) > 10 else value

    # =========================================================
    # RENDERIZAR PÁGINA
    # =========================================================
    def render_page():
        nonlocal page_index

        datatable.rows.clear()

        total_pages = max(1, (len(data_cache) + page_size - 1) // page_size)
        page_index = max(1, min(page_index, total_pages))
        start = (page_index - 1) * page_size
        end = start + page_size

        for idx, row in enumerate(data_cache[start:end]):
            bg = ROW_ODD if idx % 2 else ROW_EVEN

            cells = []
            for col in columns:
                val = row.get(col, "")

                # ID estilo lite (pequeño y gris)
                if col.lower() in ["id", "id_jugador"]:
                    cell_text = ft.Text(truncate(val), size=11, color=TEXT_SECONDARY)

                # valores numéricos más visibles
                elif isinstance(val, (int, float)):
                    cell_text = ft.Text(str(val), size=13, color=TEXT_PRIMARY, weight="bold")

                else:
                    cell_text = ft.Text(str(val), size=13, color=TEXT_PRIMARY)

                cells.append(ft.DataCell(cell_text))

            datatable.rows.append(
                ft.DataRow(
                    cells=cells,
                    color=bg,
                )
            )

        pagination_label.value = f"{page_index}/{total_pages}"
        btn_prev.disabled = page_index == 1
        btn_next.disabled = page_index == total_pages

        page.update()

    # =========================================================
    # BOTONES
    # =========================================================
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

    # =========================================================
    # CARGA INICIAL
    # =========================================================
    def load_data():
        nonlocal data_cache, page_index
        loading_text.visible = True
        datatable.rows.clear()
        page.update()

        data_cache = fetch_callback()
        page_index = 1

        loading_text.visible = False
        render_page()

    # =========================================================
    # LAYOUT FINAL LITE MODERNO
    # =========================================================
    container = ft.Column(
        [
            ft.Text(title, size=22, weight="bold", color=TEXT_PRIMARY),
            ft.Container(height=5),
            loading_text,
            ft.Container(
                datatable,
                bgcolor="white",
                border_radius=12,
                padding=12,
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=9,
                    color=ft.colors.with_opacity(0.12, "black")
                ),
            ),
            ft.Container(height=12),
            ft.Row(
                [
                    btn_prev,
                    pagination_label,
                    btn_next
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        ],
        expand=True,
        scroll=ft.ScrollMode.AUTO
    )

    return container, load_data
