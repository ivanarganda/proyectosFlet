# pages/equipos.py
import os
import flet as ft
import requests
from helpers.utils import addElementsPage, has_parameter_id
from footer_navegation.navegation import footer_navbar
from middlewares.auth import middleware_auth
from params import REQUEST_URL, HEADERS

# ======================================================
# KPI CARD
# ======================================================
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
    kpis = ft.Row(
        spacing=16,
        controls=[
            kpi_card("Total de equipos", "21", ft.Icons.GROUPS, "#2563EB"),
            kpi_card("Promedio de goles", "2.74", ft.Icons.SPORTS_SOCCER, "#16A34A"),
            kpi_card("KD vs jornada anterior", "+3", ft.Icons.TRENDING_UP, "#F59E0B"),
            kpi_card("Gasto total", "€1.2B", ft.Icons.EURO, "#DC2626"),
        ],
    )

    # ==================================================
    # BAR CHART – GOLES POR JUGADOR
    # ==================================================
    goals_chart = ft.Container(
        padding=16,
        border_radius=16,
        bgcolor="white",
        expand=True,
        content=ft.Column(
            spacing=12,
            controls=[
                ft.Text("Promedio de goles por jugador", size=18, weight=ft.FontWeight.BOLD),
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
                                    color="#2563EB",
                                    tooltip=f"{val} goles",
                                )
                            ],
                        )
                        for i, val in enumerate([5, 7, 3, 6, 4])
                    ],
                    border=ft.Border(
                        left=ft.BorderSide(1, "#E5E7EB"),
                        bottom=ft.BorderSide(1, "#E5E7EB"),
                    ),
                ),
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
    player_table = ft.Container(
        padding=16,
        border_radius=16,
        bgcolor="white",
        expand=True,
        content=ft.Column(
            spacing=12,
            controls=[
                ft.Text("Estadísticas del jugador", size=18, weight=ft.FontWeight.BOLD),
                ft.DataTable(
                    expand=True,
                    columns=[
                        ft.DataColumn(ft.Text("Jugador")),
                        ft.DataColumn(ft.Text("Goles")),
                        ft.DataColumn(ft.Text("Asistencias")),
                        ft.DataColumn(ft.Text("Rating")),
                    ],
                    rows=[
                        ft.DataRow(
                            cells=[
                                ft.DataCell(ft.Text("Jugador A")),
                                ft.DataCell(ft.Text("10")),
                                ft.DataCell(ft.Text("4")),
                                ft.DataCell(ft.Text("7.8")),
                            ]
                        )
                        for _ in range(5)
                    ],
                ),
            ],
        ),
    )

    # ==================================================
    # BAR CHART – PORTEROS
    # ==================================================
    keepers_chart = ft.Container(
        padding=16,
        border_radius=16,
        bgcolor="white",
        expand=True,
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

    # ==================================================
    # TABLE – MERCADO DE VALORES
    # ==================================================
    market_table = ft.Container(
        padding=16,
        border_radius=16,
        bgcolor="white",
        expand=True,
        content=ft.Column(
            spacing=12,
            controls=[
                ft.Text("Mercado de valores por equipo", size=18, weight=ft.FontWeight.BOLD),
                ft.DataTable(
                    expand=True,
                    columns=[
                        ft.DataColumn(ft.Text("Equipo")),
                        ft.DataColumn(ft.Text("Valor mercado")),
                    ],
                    rows=[
                        ft.DataRow(
                            cells=[
                                ft.DataCell(ft.Text("Equipo X")),
                                ft.DataCell(ft.Text("€120M")),
                            ]
                        )
                        for _ in range(5)
                    ],
                ),
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
            ft.Row(spacing=16, controls=[player_table, keepers_chart, market_table])
        ],
    ) ] )