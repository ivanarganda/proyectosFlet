import flet as ft
import math

ICON_MAP = {
    "goles": "⚽",
    "goals": "⚽",
    "asistencias": "🅰️",
    "assists": "🅰️",
    "minutos": "⏱️",
    "minutes": "⏱️",
    "partidos": "🎯",
    "matches": "🎯",
}

MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}


def PaginatedTablePRO(
    page: ft.Page,
    title: str,
    columns: list,
    fetch_callback,
    page_size=10,
    photo_key="photo",
):
    data_cache = []
    page_index = 1
    sort_column = None
    sort_desc = True

    # === UI COLORS ===
    HEADER_BG = "#4E73DF"
    HEADER_TEXT = "white"
    TEXT_PRIMARY = "#2C3E50"
    TEXT_SECONDARY = "#6C757D"
    ROW_ODD = "#F9FAFB"
    ROW_EVEN = "#FFFFFF"
    BORDER = "#E1E5EA"

    # --------------------------------------------------------
    # HELPERS
    # --------------------------------------------------------
    def get_icon(col: str):
        col = col.lower()
        return ICON_MAP.get(col, "")

    def truncate(value):
        value = str(value)
        return value[:10] + "…" if len(value) > 12 else value

    def progress_bar(value, max_value):
        if not isinstance(value, (int, float)) or max_value <= 0:
            return ft.Text(str(value), size=13)

        percent = max(0, min(value / max_value, 1))

        bar = ft.Container(
            width=70,
            height=10,
            bgcolor="#E8ECEF",
            border_radius=5,
            content=ft.Container(
                width=70 * percent,
                height=10,
                bgcolor="#4E73DF",
                border_radius=5,
            ),
        )
        return ft.Row([bar, ft.Text(str(value), size=12)], spacing=5)

    # --------------------------------------------------------
    # ORDENAR COLUMNAS
    # --------------------------------------------------------
    def sort_data(col):
        nonlocal data_cache, sort_column, sort_desc

        if sort_column == col:
            sort_desc = not sort_desc
        else:
            sort_column = col
            sort_desc = True

        try:
            data_cache = sorted(
                data_cache,
                key=lambda x: x.get(col, 0),
                reverse=sort_desc,
            )
        except:
            pass

        render_page()

    # --------------------------------------------------------
    # COLUMNAS DEL DATATABLE
    # --------------------------------------------------------
    table_columns = []

    for col in columns:
        label = f"{get_icon(col)} {col.replace('_', ' ').upper()}"

        table_columns.append(
            ft.DataColumn(
                label=ft.Text(label, size=12, weight="bold", color=HEADER_TEXT),
                on_sort=lambda e, c=col: sort_data(c),
                numeric=col.lower() not in ["jugador", "equipo"],
            )
        )

    datatable = ft.DataTable(
        columns=table_columns,
        rows=[],
        heading_row_color=HEADER_BG,
        border=ft.border.all(0.4, BORDER),
        data_row_min_height=52,
        show_checkbox_column=False,
        column_spacing=20,
    )

    pagination_label = ft.Text("1/1", size=13, color=TEXT_SECONDARY)
    btn_prev = ft.TextButton("◀", disabled=True)
    btn_next = ft.TextButton("▶", disabled=True)

    # --------------------------------------------------------
    # RENDERIZAR PAGINA
    # --------------------------------------------------------
    def render_page():
        nonlocal page_index

        datatable.rows.clear()

        total_pages = max(1, math.ceil(len(data_cache) / page_size))
        page_index = max(1, min(page_index, total_pages))

        start = (page_index - 1) * page_size
        end = start + page_size

        max_goals = max([d.get("goles", 0) for d in data_cache] + [1])

        for idx, row in enumerate(data_cache[start:end]):
            bg = ROW_ODD if idx % 2 == 0 else ROW_EVEN
            cells = []

            for col in columns:
                value = row.get(col, "")

                # --- Foto + Nombre ---
                if col.lower() == "jugador":
                    photo_url = row.get(photo_key)

                    avatar = (
                        ft.CircleAvatar(
                            foreground_image_url=photo_url,
                            radius=16,
                        )
                        if photo_url
                        else ft.CircleAvatar(
                            content=ft.Text(value[0], color="white"),
                            bgcolor="#4E73DF",
                            radius=16,
                        )
                    )

                    cells.append(
                        ft.DataCell(
                            ft.Row(
                                [avatar, ft.Text(value, size=14, color=TEXT_PRIMARY)],
                                spacing=10,
                            )
                        )
                    )
                    continue

                # --- Medallas top 3 ---
                if col.lower() in ["pos", "posicion", "rank"]:
                    medal = MEDALS.get(value, "")
                    cells.append(
                        ft.DataCell(ft.Text(f"{medal} {value}", size=14))
                    )
                    continue

                # --- Progress bar goles/asistencias ---
                if col.lower() in ["goles", "goals", "asistencias", "assists"]:
                    cells.append(ft.DataCell(progress_bar(value, max_goals)))
                    continue

                # --- Valores numéricos ---
                if isinstance(value, (int, float)):
                    cells.append(
                        ft.DataCell(ft.Text(str(value), size=13, weight="bold"))
                    )
                    continue

                # --- Por defecto ---
                cells.append(
                    ft.DataCell(
                        ft.Text(
                            str(value),
                            size=13,
                            color=TEXT_PRIMARY,
                        )
                    )
                )

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

    # --------------------------------------------------------
    # BOTONES
    # --------------------------------------------------------
    def next_page(e):
        nonlocal page_index
        page_index += 1
        render_page()

    def prev_page(e):
        nonlocal page_index
        page_index -= 1
        render_page()

    btn_prev.on_click = prev_page
    btn_next.on_click = next_page

    # --------------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------------
    def load_data():
        nonlocal data_cache, sort_column
        data_cache = fetch_callback()
        sort_column = None
        render_page()

    # --------------------------------------------------------
    # CONTENEDOR CENTRADO
    # --------------------------------------------------------
    centered_table = ft.Row(
        [
            ft.Container(
                datatable,
                width=900,      # 👈 ancho máximo centrado
                bgcolor="white",
                padding=20,
                border_radius=14,
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=8,
                    color=ft.colors.with_opacity(0.10, "black"),
                ),
            )
        ],
        alignment=ft.MainAxisAlignment.CENTER,
    )

    # --------------------------------------------------------
    # LAYOUT FINAL
    # --------------------------------------------------------
    return (
        ft.Column(
            [
                ft.Text(title, size=22, weight="bold", color=TEXT_PRIMARY),
                centered_table,
                ft.Row(
                    [btn_prev, pagination_label, btn_next],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            ],
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        ),
        load_data,
    )