# pages/equipos.py
import os
import flet as ft
import requests
from helpers.utils import addElementsPage, has_parameter_id
from footer_navegation.navegation import footer_navbar
from middlewares.auth import middleware_auth
from params import REQUEST_URL, HEADERS
import json
import pandas as pd
import base64
from io import BytesIO

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

selected_equipo_id = 24264  # por defecto
chart_container = ft.Container()
table_player_container = ft.Container()
table_market_table = ft.Container()

# ======================================================
# KPI CARD
# ======================================================
def render_dropdown_equipos(page: ft.Page, callback, container ):

    r = requests.get(f"{REQUEST_URL}/info/equipos").json()

    return ft.Dropdown(
        label="Equipo",
        width=350,
        value=int(selected_equipo_id),
        options=[
            ft.dropdown.Option(
                key=int(i.get("id_equipo")),      # índice como key
                text=i.get("nombre")           # nombre del equipo
            )
            for i in r.get("data")
        ],
        on_change=lambda e: on_change_equipo(e, page, callback, container),
    )

def on_change_equipo(e: ft.ControlEvent, page: ft.Page, callback: callable, container):

    global selected_equipo_id
    selected_equipo_id = int(e.control.value)

    container.content = callback(selected_equipo_id)
    page.update()

def kpi_card(title, value, icon, color):

    return ft.Container(
        expand=True,
        padding=16,
        border_radius=16,
        bgcolor="white",
        shadow=ft.BoxShadow(
            blur_radius=16,
            color=ft.colors.with_opacity(0.15, "black"),
        ),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Column(
                    spacing=4,
                    controls=[
                        ft.Text(title, size=13, color="#6B7280"),
                        ft.Text(value, size=26, weight=ft.FontWeight.BOLD),
                    ],
                ),
                ft.Icon(icon, size=36, color=color),
            ],
        ),
    )

def build_market_player_table(id_equipo: int):

    import flet as ft

    rows = [
        ft.DataRow(
            cells=[
                ft.DataCell(ft.Text("Equipo X")),
                ft.DataCell(ft.Text("€120M")),
            ]
        )
        for _ in range(8)
    ]

    return ft.Container(
        padding=16,
        border_radius=16,
        bgcolor="white",
        content=ft.Column(
            spacing=12,
            controls=[
                ft.Text(
                    "Mercado de valores por equipo",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                ),

                # 🔑 MISMA ALTURA FIJA QUE LA OTRA
                ft.Container(
                    height=320,
                    content=ft.Column(
                        scroll=ft.ScrollMode.AUTO,
                        controls=[
                            ft.DataTable(
                                column_spacing=24,
                                horizontal_margin=16,
                                columns=[
                                    ft.DataColumn(ft.Text("Equipo")),
                                    ft.DataColumn(ft.Text("Valor mercado")),
                                ],
                                rows=rows,
                            )
                        ],
                    ),
                ),
            ],
        ),
    )


def build_table_stats_jugador(id_equipo: int):

    import flet as ft
    import requests

    data = requests.get(
        f"{REQUEST_URL}/dashboard/stats-jugador/{id_equipo}"
    ).json()

    rows = [
        ft.DataRow(
            cells=[
                ft.DataCell(ft.Text(p.get("jugador", "-"))),
                ft.DataCell(ft.Text(str(p.get("faltas", 0)))) ,
                ft.DataCell(ft.Text(str(p.get("amarillas", 0)))) ,
                ft.DataCell(ft.Text(str(p.get("rojas", "-")))) ,
                ft.DataCell(ft.Text(str(p.get("expulsiones", "-")))) ,
                ft.DataCell(ft.Text(str(p.get("totalShoots", "-")))) ,
            ]
        )
        for p in data
    ]

    return ft.Container(
        padding=16,
        border_radius=16,
        bgcolor="white",
        content=ft.Column(
            spacing=12,
            controls=[
                ft.Text(
                    "Estadísticas del jugador",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                ),

                # 🔑 CONTENEDOR DE ALTURA FIJA
                ft.Container(
                    height=320,
                    content=ft.Column(
                        scroll=ft.ScrollMode.AUTO,
                        controls=[
                            ft.DataTable(
                                column_spacing=28,
                                horizontal_margin=20,
                                columns=[
                                    ft.DataColumn(ft.Text("Jugador")),
                                    ft.DataColumn(ft.Text("Faltas")),
                                    ft.DataColumn(ft.Text("Amarillas")),
                                    ft.DataColumn(ft.Text("Rojas")),
                                    ft.DataColumn(ft.Text("Expulsiones")),
                                    ft.DataColumn(ft.Text("Remates")),
                                ],
                                rows=rows,
                            )
                        ],
                    ),
                ),
            ],
        ),
    )


def build_bar_chart_jugadores_goles(id_equipo: int):

    import pandas as pd
    import flet as ft
    import requests

    data = requests.get(
        f"{REQUEST_URL}/dashboard/goles-jugador/{id_equipo}"
    ).json()

    if not isinstance(data, list):
        raise ValueError(f"Formato inválido recibido: {type(data)}")

    df = pd.DataFrame(data)

    df["avg_goals"] = pd.to_numeric(df["avg_goals"], errors="coerce")
    df = df[df["avg_goals"] > 0]

    if df.empty:
        return ft.Text("No hay jugadores con goles")

    df = (
        df.sort_values("avg_goals", ascending=False)
          .head(20)  # más jugadores → scroll útil
          .reset_index(drop=True)
    )

    max_y = round(df["avg_goals"].max() + 0.15, 2)

    bar_groups = [
        ft.BarChartGroup(
            x=i,
            bar_rods=[
                ft.BarChartRod(
                    from_y=0,
                    to_y=row["avg_goals"],
                    width=22,
                    color="#2563EB",
                    border_radius=8,
                )
            ],
        )
        for i, row in df.iterrows()
    ]

    chart = ft.BarChart(
        max_y=max_y,
        bar_groups=bar_groups,
        left_axis=ft.ChartAxis(
            title=ft.Text("Goles / partido", size=12),
            labels_size=42,
            labels_interval=0.1,
        ),
        bottom_axis=ft.ChartAxis(
            labels=[
                ft.ChartAxisLabel(
                    value=i,
                    label=ft.Text(
                        row["jugador"],
                        rotate=45,
                        size=11,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                )
                for i, row in df.iterrows()
            ],
            labels_size=90,
        ),
        interactive=True,
    )

    # 🔥 SCROLL HORIZONTAL
    return ft.Container(
        padding=20,
        border_radius=20,
        bgcolor="white",
        shadow=ft.BoxShadow(
            blur_radius=18,
            color=ft.colors.with_opacity(0.15, "black"),
        ),
        content=ft.Column(
            spacing=14,
            controls=[
                ft.Text(
                    "Promedio de goles por jugador",
                    size=17,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Row(
                    scroll=ft.ScrollMode.AUTO,   # 👈 SCROLL X
                    controls=[
                        ft.Container(
                            width=max(900, len(df) * 70),  # 👈 ancho dinámico
                            height=360,
                            content=chart,
                        )
                    ],
                ),
            ],
        ),
    )



# ======================================================
# DASHBOARD VIEW
# ======================================================
def RenderDashboard(page: ft.Page, params={}):

    page.bgcolor = "#F3F4F6"
    page.scroll = ft.ScrollMode.AUTO

    page.window.width = 1200

    # ==================================================
    # KPIs
    # ==================================================
    r = requests.get(f"{REQUEST_URL}/dashboard/kpis").json()

    kd_jornada_actual = r["kd_variacion"][0]["kd_jornada_actual"]
    kd_jornada_anterior = r["kd_variacion"][0]["kd_jornada_anterior"]
    id_jornada_anterior = r["kd_variacion"][0]["id_jornada_anterior"]
    id_jornada_actual = r["kd_variacion"][0]["id_jornada_actual"]
    percentage_kd = r["kd_variacion"][0]["porcentaje"]

    kpis = ft.Row(
        spacing=16,
        controls=[
            kpi_card("Total equipos", r["total_equipos"], ft.Icons.GROUPS, "#2563EB"),
            kpi_card("Promedio goles", r["promedio_goles"], ft.Icons.SPORTS_SOCCER, "#16A34A"),
            ft.Container(
                expand=True,
                padding=16,
                border_radius=16,
                bgcolor="white",
                shadow=ft.BoxShadow(
                    blur_radius=16,
                    color=ft.colors.with_opacity(0.15, "black"),
                ),
                content=ft.Container(
                    expand=True,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                spacing=6,
                                controls=[
                                    
                                    ft.Row(
                                        controls=[
                                            ft.Text("Tasa KD partidos", size=13, color="#6B7280")
                                        ],
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    ),

                                    ft.Row(
                                        spacing=20,
                                        controls=[
                                            ft.Row(
                                                spacing=6,
                                                controls=[
                                                    ft.Text(f"Jrd {id_jornada_anterior}", size=22, weight=ft.FontWeight.BOLD),
                                                    ft.Text(f"{kd_jornada_anterior}", size=18),
                                                ],
                                            ),
                                            ft.Row(
                                                spacing=6,
                                                controls=[
                                                    ft.Text(f"Jrd {id_jornada_actual}", size=22, weight=ft.FontWeight.BOLD),
                                                    ft.Text(f"{kd_jornada_actual}", size=18),
                                                ],
                                            ),
                                        ],
                                    ),
                                ],
                            ),

                            ft.Column([
                                ft.Icon(
                                    ft.Icons.TRENDING_UP if kd_jornada_actual > kd_jornada_anterior else ft.Icons.TRENDING_DOWN,
                                    size=36,
                                    color="#9333EA",
                                ),
                                ft.Text(f"{percentage_kd}%", size=13, color="#6B7280"),
                            ],
                            alignment=ft.CrossAxisAlignment.START
                            )

                            
                        ],
                    ),
                )

            ),
            kpi_card("Total gastos", f"€{r['total_gastos']}", ft.Icons.EURO, "#DC2626"),
        ]
    )

    chart_container.content = build_bar_chart_jugadores_goles(selected_equipo_id)

    goals_chart = ft.Container(
        expand=True,
        content=ft.Column(
            spacing=12,
            controls=[
                render_dropdown_equipos(page, build_bar_chart_jugadores_goles, chart_container),
                chart_container,
            ],
        ),
    )



    # ==================================================
    # LINE CHART – CLASIFICACIÓN (BUMPY STYLE)
    # ==================================================
    classification_chart = ft.Container(
        padding=16,
        border_radius=16,
        bgcolor="white",
        expand=True,
        content=ft.Column(
            spacing=12,
            controls=[
                ft.Text("Clasificación por equipo", size=18, weight=ft.FontWeight.BOLD),
                ft.LineChart(
                    expand=True,
                    data_series=[
                        ft.LineChartData(
                            data_points=[
                                ft.LineChartDataPoint(x, y)
                                for x, y in enumerate([5, 4, 3, 2, 1])
                            ],
                            color="#2563EB",
                            stroke_width=3,
                        )
                    ],
                ),
            ],
        ),
    )

    # ==================================================
    # TABLE – ESTADÍSTICAS JUGADOR
    # ==================================================

    

    # ==================================================
    # BAR CHART – PORTEROS
    # ==================================================
    keepers_chart = ft.Container(
        expand=1,
        padding=16,
        border_radius=16,
        bgcolor="white",
        content=ft.Column(
            spacing=12,
            controls=[
                ft.Text("Ranking de porteros (paradas)", size=18, weight=ft.FontWeight.BOLD),
                ft.BarChart(
                    expand=True,
                    bar_groups=[
                        ft.BarChartGroup(
                            x=i,
                            bar_rods=[
                                ft.BarChartRod(
                                    from_y=0,
                                    to_y=val,
                                    width=18,
                                    color="#16A34A",
                                )
                            ],
                        )
                        for i, val in enumerate([25, 30, 18, 22, 28])
                    ],
                ),
            ],
        ),
    )

    table_player_container.content = build_table_stats_jugador(selected_equipo_id)

    player_table = ft.Container(
        expand=7,
        content=ft.Column(
            spacing=12,
            controls=[
                render_dropdown_equipos(page, build_table_stats_jugador, table_player_container ),
                table_player_container,
            ],
        ),
    )

    # ==================================================
    # TABLE – MERCADO DE VALORES
    # ==================================================
    table_market_table.content = build_market_player_table(selected_equipo_id)

    market_table = ft.Container(
        expand=3,
        content=ft.Column(
            spacing=12,
            controls=[
                render_dropdown_equipos(page, build_market_player_table, table_market_table ),
                table_market_table,
            ],
        ),
    )

    # ==================================================
    # LAYOUT FINAL
    # ==================================================
    return addElementsPage( page,[ ft.Column(
        spacing=16,
        controls=[
            kpis,
            ft.Row(spacing=16, controls=[goals_chart, classification_chart]),
            ft.Row(spacing=16, controls=[player_table, market_table])
        ]
    ) ] )