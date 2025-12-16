# pages/equipos.py
import flet as ft
import requests
import pandas as pd
from params import REQUEST_URL

# ======================================================
# THEME (DARK + LIGHT)
# ======================================================
THEME = {
    "bg": "#0B0F14",
    "card": "#111827",
    "border": "#1F2937",
    "text": "#F9FAFB",
    "muted": "#9CA3AF",
    "primary": "#3B82F6",
    "accent": "#22C55E",
    "skeleton": "#1F2937",
}

# ======================================================
# GLOBAL STATE
# ======================================================
selected_equipo_id = 24264
kpi_mode = "global"

kpi_container = ft.Container()

chart_container = ft.Container(expand=True)
table_player_container = ft.Container(expand=True)
table_market_container = ft.Container(expand=True)
bumpy_container = ft.Container(expand=True)
top_saves_goalkeepers_container = ft.Container(expand=True)

# ======================================================
# KPI CARDS
# ======================================================
def kpi_card(title, value, icon, color):
    return ft.Container(
        expand=True,
        padding=16,
        border_radius=18,
        bgcolor=THEME["card"],
        border=ft.border.all(1, THEME["border"]),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Column(
                    spacing=4,
                    controls=[
                        ft.Text(title, size=13, color=THEME["muted"]),
                        ft.Text(
                            str(value),
                            size=26,
                            weight=ft.FontWeight.BOLD,
                            color=THEME["text"],
                        ),
                    ],
                ),
                ft.Icon(
                    icon,
                    size=32,
                    color=color,
                ),
            ],
        ),
    )



def kpi_kd_comparativo(data):

    kd = data["kd_variacion"][0]

    kd_actual = kd["kd_jornada_actual"]
    kd_anterior = kd["kd_jornada_anterior"]

    subida = kd_actual >= kd_anterior
    color = "#22C55E" if subida else "#EF4444"
    icon = ft.icons.TRENDING_UP if subida else ft.icons.TRENDING_DOWN
    signo = "+" if subida else ""

    return ft.Container(
        expand=True,
        padding=16,
        border_radius=18,
        bgcolor=THEME["card"],
        border=ft.border.all(1, THEME["border"]),
        content=ft.Column(
            spacing=6,
            controls=[
                ft.Text("Tasa KD", size=13, color=THEME["muted"]),

                # KD ACTUAL
                ft.Text(
                    f"{kd_actual}",
                    size=26,
                    weight=ft.FontWeight.BOLD,
                    color=THEME["text"],
                ),

                # VARIACIÓN
                ft.Row([

                    ft.Row(
                        spacing=6,
                        controls=[
                            ft.Icon(icon, size=18, color=color),
                            ft.Text(
                                f"{signo}{kd['porcentaje']}%",
                                size=13,
                                color=color,
                            ),
                            ft.Text(
                                f"vs J{kd['id_jornada_anterior']}",
                                size=12,
                                color=THEME["muted"],
                            ),
                        ],
                    ),
                    # KD ANTERIOR (👈 LO QUE FALTABA)
                    ft.Text(
                        f"Anterior (J{kd['id_jornada_anterior']}): {kd_anterior}",
                        size=11,
                        color=THEME["muted"],
                    ),
                ])

            ],
        ),
    )

def build_kpis():
    data = requests.get(f"{REQUEST_URL}/dashboard/kpis").json()

    return ft.ResponsiveRow(
        spacing=12,
        run_spacing=12,
        columns=12,
        controls=[
            ft.Container(
                height=120,
                col={"xs":12,"sm":6,"md":3},
                content=kpi_card(
                    "Equipos",
                    data["total_equipos"],
                    ft.icons.GROUPS,
                    THEME["primary"],
                ),
            ),
            ft.Container(
                height=120,
                col={"xs":12,"sm":6,"md":3},
                content=kpi_card(
                    "Promedio goles",
                    data["promedio_goles"],
                    ft.icons.SPORTS_SOCCER,
                    THEME["accent"],
                ),
            ),
            ft.Container(
                height=120,
                col={"xs":12,"sm":6,"md":3},
                content=kpi_kd_comparativo(data),
            ),
            ft.Container(
                height=120,
                col={"xs":12,"sm":6,"md":3},
                content=kpi_card(
                    "Total gastos",
                    f"€{data['total_gastos']} M",
                    ft.icons.EURO,
                    "#F59E0B",
                ),
            ),
        ],
    )

def build_team_kpis(id_equipo):
    r = requests.get(
        f"{REQUEST_URL}/dashboard/kpis-equipo/{id_equipo}"
    ).json()

    kd_list = r.get("kd_variacion", [])
    kd = kd_list[0] if kd_list else None

    controls = [
        ft.Container(
            height=120,
            col={"xs":12,"sm":6,"md":3},
            content=kpi_card(
                "PPG equipo",
                r.get("ppg", "-"),
                ft.icons.SPORTS,
                THEME["primary"],
            ),
        ),
        ft.Container(
            height=120,
            col={"xs":12,"sm":6,"md":3},
            content=kpi_card(
                "Dif. goles",
                r.get("diferencia_goles", "-"),
                ft.icons.TRENDING_UP,
                THEME["accent"],
            ),
        ),
        ft.Container(
            height=120,
            col={"xs":12,"sm":6,"md":3},
            content=kpi_card(
                "Goles / partido",
                r.get("goles_favor_partido", "-"),
                ft.icons.SPORTS_SOCCER,
                "#F59E0B",
            ),
        ),
    ]

    # 👉 Solo añadimos KD si existe
    if kd:
        controls.append(
            ft.Container(
                height=120,
                col={"xs":12,"sm":6,"md":3},
                content=kpi_card(
                    f"KD · J{kd.get('id_jornada_actual', '-')}",
                    kd.get("kd_jornada_actual", "-"),
                    ft.icons.SHOW_CHART,
                    THEME["primary"],
                ),
            )
        )

    return ft.ResponsiveRow(
        spacing=12,
        run_spacing=12,
        columns=12,
        controls=controls,
    )

# ======================================================
# KPI MODE SWITCH
# ======================================================
def kpi_mode_switch(page: ft.Page):
    return ft.SegmentedButton(
        selected={"global"},
        segments=[
            ft.Segment(
                value="global",
                label=ft.Text("Liga · Global"),
                icon=ft.Icon(ft.icons.PUBLIC),
            ),
            ft.Segment(
                value="team",
                label=ft.Text("Equipo"),
                icon=ft.Icon(ft.icons.SHIELD),
            ),
        ],
        on_change=lambda e: on_change_kpi_mode(e, page),
    )

def on_change_kpi_mode(e: ft.ControlEvent, page: ft.Page):
    global kpi_mode

    kpi_mode = list(e.control.selected)[0]

    if kpi_mode == "global":
        kpi_container.content = build_kpis()
    else:
        kpi_container.content = build_team_kpis(selected_equipo_id)

    page.update()

# ======================================================
# UI HELPERS
# ======================================================
def card(content, padding=16):
    return ft.Container(
        padding=padding,
        border_radius=18,
        bgcolor=THEME["card"],
        border=ft.border.all(1, THEME["border"]),
        content=content,
    )

def title(text):
    return ft.Text(
        text,
        size=18,
        weight=ft.FontWeight.BOLD,
        color=THEME["text"],
    )

def muted(text, size=12):
    return ft.Text(text, size=size, color=THEME["muted"])

# ======================================================
# SKELETON
# ======================================================
def skeleton(height=200):
    return ft.Container(
        height=height,
        border_radius=16,
        bgcolor=THEME["skeleton"],
        animate_opacity=300,
    )

# ======================================================
# TEAM SELECTOR
# ======================================================
def team_selector(page, on_change):
    data = requests.get(f"{REQUEST_URL}/info/equipos").json()["data"]

    return card(
        ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                title("Equipo seleccionado"),
                ft.Dropdown(
                    width=260,
                    value=str(selected_equipo_id),
                    options=[
                        ft.dropdown.Option(
                            key=str(e["id_equipo"]),
                            text=e["nombre"],
                        )
                        for e in data
                    ],
                    on_change=lambda e: on_change(e, page),
                ),
            ],
        ),
        padding=14,
    )

def on_team_change(e, page):
    global selected_equipo_id
    selected_equipo_id = int(e.control.value)

    chart_container.content = skeleton(360)
    bumpy_container.content = skeleton(360)
    table_player_container.content = skeleton(320)
    table_market_container.content = skeleton(320)
    top_saves_goalkeepers_container.content = skeleton(320)
    page.update()

    if kpi_mode == "global":

        kpi_container.content = build_kpis()
    
    else:

        kpi_container.content = build_team_kpis(selected_equipo_id)

    chart_container.content = build_goals_chart(selected_equipo_id)
    bumpy_container.content = build_bumpy_chart(selected_equipo_id)
    table_player_container.content = build_players_table(selected_equipo_id)
    table_market_container.content = build_market_table(selected_equipo_id)
    top_saves_goalkeepers_container.content = build_goalkeepers_table(selected_equipo_id)
    page.update()


# ======================================================
# CHART · GOLES POR JUGADOR
# ======================================================
def build_goals_chart(id_equipo):

    data = requests.get(
        f"{REQUEST_URL}/dashboard/goles-jugador/{id_equipo}"
    ).json()

    df = pd.DataFrame(data)
    df["avg_goals"] = pd.to_numeric(df["avg_goals"], errors="coerce")
    df = df[df["avg_goals"] > 0].head(20)

    if df.empty:
        return muted("No hay datos disponibles")

    bars = [
        ft.BarChartGroup(
            x=i,
            bar_rods=[
                ft.BarChartRod(
                    from_y=0,
                    to_y=row["avg_goals"],
                    width=18,
                    color=THEME["primary"],
                    border_radius=6,
                )
            ],
        )
        for i, row in df.iterrows()
    ]

    chart = ft.BarChart(
        max_y=df["avg_goals"].max() + 0.1,
        bar_groups=bars,
        interactive=True,
    )

    return card(
        ft.Column(
            height=420,
            expand=True,
            spacing=10,
            controls=[
                title("Insight clave · Goles por jugador"),
                muted("Quién decide los partidos"),
                ft.Row(
                    scroll=ft.ScrollMode.AUTO,
                    controls=[
                        ft.Container(
                            width=max(900, len(df) * 70),
                            height=360,
                            content=chart,
                        )
                    ],
                ),
            ],
        )
    )

# ======================================================
# BUMPY CHART · CLASIFICACIÓN
# ======================================================
def build_bumpy_chart(id_equipo):

    response = requests.get(
        f"{REQUEST_URL}/dashboard/bumpy-clasificacion/{id_equipo}"
    ).json()

    if not response:
        return muted("No hay datos de clasificación")

    selected_team = response.get("selected_team")
    data = response.get("data")
    colors = response.get("colors", {})

    max_jornadas = max(len(v) for v in data.values())
    max_posicion = max(max(v) for v in data.values())

    series = []

    for equipo, posiciones in data.items():

        is_focus = equipo == selected_team
        base_color = colors.get(equipo, "#9CA3AF")

        color = (
            base_color
            if is_focus
            else ft.colors.with_opacity(0.25, base_color)
        )

        stroke = 4 if is_focus else 2

        points = [
            ft.LineChartDataPoint(
                x=i + 1,
                y=max_posicion - pos + 1
            )
            for i, pos in enumerate(posiciones)
        ]

        series.append(
            ft.LineChartData(
                data_points=points,
                curved=True,
                stroke_width=stroke,
                color=color,
            )
        )

    return ft.Container(
        expand=True,
        height=420,
        padding=20,
        border_radius=20,
        bgcolor=THEME["card"],
        border=ft.border.all(1, THEME["border"]),
        content=ft.Column(
            spacing=14,
            controls=[
                title("Evolución de la clasificación (Bumpy chart)"),
                ft.LineChart(
                    expand=True,
                    min_x=1,
                    max_x=max_jornadas,
                    min_y=1,
                    max_y=max_posicion,
                    left_axis=ft.ChartAxis(
                        title=ft.Text("Posición"),
                        labels_size=40,
                    ),
                    bottom_axis=ft.ChartAxis(
                        title=ft.Text("Jornada"),
                        labels_size=40,
                    ),
                    data_series=series,
                ),
            ],
        ),
    )

# ======================================================
# TABLE · PORTEROS
# ======================================================
def build_goalkeepers_table(id_equipo):

    data = requests.get(
        f"{REQUEST_URL}/dashboard/ranking-paradas-porteros/{id_equipo}"
    ).json()

    rows = [
        ft.DataRow(
            cells=[
                ft.DataCell(ft.Text(p["jugador"])),
                ft.DataCell(ft.Text(p["equipo"])),
                ft.DataCell(ft.Text(str(p["total_paradas"]))),
                ft.DataCell(ft.Text(str(p["partidos"]))),
                ft.DataCell(
                    ft.Text(
                        str(p["paradas_por_partido"]),
                        color=THEME["primary"],
                    )
                ),
            ]
        )
        for p in data
    ]

    return card(
        ft.Column(
            expand=True,
            spacing=10,
            controls=[
                title("Ranking · Paradas de porteros"),
                ft.Container(
                    expand=True,
                    height=320,
                    content=ft.Column(
                        expand=True,
                        scroll=ft.ScrollMode.AUTO,
                        controls=[
                            ft.DataTable(
                                expand=True,
                                width=float("inf"),
                                heading_row_color=THEME["border"],
                                column_spacing=32,
                                horizontal_margin=20,
                                columns=[
                                    ft.DataColumn(ft.Text("Portero")),
                                    ft.DataColumn(ft.Text("Equipo")),
                                    ft.DataColumn(ft.Text("Total paradas")),
                                    ft.DataColumn(ft.Text("Partidos")),
                                    ft.DataColumn(ft.Text("PP")),
                                ],
                                rows=rows,
                            )
                        ],
                    ),
                ),
            ],
        )
    )

# ======================================================
# TABLE · JUGADORES
# ======================================================
def build_players_table(id_equipo):

    data = requests.get(
        f"{REQUEST_URL}/dashboard/stats-jugador/{id_equipo}"
    ).json()

    rows = [
        ft.DataRow(
            cells=[
                ft.DataCell(ft.Text(p["jugador"], color=THEME["text"])),
                ft.DataCell(ft.Text(str(p.get("faltas", 0)), color=THEME["muted"])),
                ft.DataCell(ft.Text(str(p.get("amarillas", 0)), color=THEME["muted"])),
                ft.DataCell(ft.Text(str(p.get("rojas", 0)), color=THEME["muted"])),
                ft.DataCell(ft.Text(str(p.get("expulsiones", 0)), color=THEME["muted"])),
                ft.DataCell(ft.Text(str(p.get("totalShoots", 0)), color=THEME["muted"])),
            ]
        )
        for p in data
    ]

    return card(
        ft.Column(
            expand=True,
            spacing=10,
            controls=[
                title("Detalle · Estadísticas del jugador"),
                ft.Container(
                    expand=True,
                    height=320,
                    content=ft.Column(
                        expand=True,
                        scroll=ft.ScrollMode.AUTO,
                        controls=[
                            ft.DataTable(
                                width=float("inf"),
                                expand=True,
                                heading_row_color=THEME["border"],
                                column_spacing=32,
                                horizontal_margin=24,
                                columns=[
                                    ft.DataColumn(ft.Text("Jugador")),
                                    ft.DataColumn(ft.Text("Faltas")),
                                    ft.DataColumn(ft.Text("Amarillas")),
                                    ft.DataColumn(ft.Text("Rojas")),
                                    ft.DataColumn(ft.Text("Exp.")),
                                    ft.DataColumn(ft.Text("Rem.")),
                                ],
                                rows=rows,
                            )
                        ],
                    ),
                ),
            ],
        )
    )

# ======================================================
# TABLE · MERCADO
# ======================================================
def build_market_table(id_equipo):

    data = requests.get(
        f"{REQUEST_URL}/dashboard/ranking-value-market-players/{id_equipo}"
    ).json()

    if not data:
        return muted("No hay datos de mercado")

    rows = [
        ft.DataRow(
            cells=[
                ft.DataCell(ft.Text(p["jugador"], weight=ft.FontWeight.W_500)),
                ft.DataCell(ft.Text(p["equipo"], color=THEME["muted"])),
                ft.DataCell(ft.Text(p.get("posicion", "-"), color=THEME["muted"])),
                ft.DataCell(
                    ft.Text(
                        p["precio"],
                        color=THEME["primary"],
                        weight=ft.FontWeight.BOLD,
                    )
                ),
            ]
        )
        for p in data
    ]

    return card(
        ft.Column(
            expand=True,
            spacing=12,
            controls=[
                title("💰 Ranking · Valor de mercado de jugadores"),
                ft.Container(
                    expand=True,
                    height=360,
                    content=ft.Column(
                        expand=True,
                        scroll=ft.ScrollMode.AUTO,
                        controls=[
                            ft.DataTable(
                                expand=True,
                                width=float("inf"),
                                heading_row_color=THEME["border"],
                                column_spacing=28,
                                horizontal_margin=20,
                                columns=[
                                    ft.DataColumn(ft.Text("Jugador")),
                                    ft.DataColumn(ft.Text("Equipo")),
                                    ft.DataColumn(ft.Text("Posición")),
                                    ft.DataColumn(ft.Text("Valor mercado")),
                                ],
                                rows=rows,
                            )
                        ],
                    ),
                ),
            ],
        )
    )

# ======================================================
# DASHBOARD VIEW
# ======================================================
def RenderDashboard(page: ft.Page, params={}):

    page.window.width = 1200
    page.bgcolor = THEME["bg"]
    page.scroll = ft.ScrollMode.AUTO

    chart_container.content = build_goals_chart(selected_equipo_id)
    bumpy_container.content = build_bumpy_chart(selected_equipo_id)
    table_player_container.content = build_players_table(selected_equipo_id)
    table_market_container.content = build_market_table(selected_equipo_id)
    top_saves_goalkeepers_container.content = build_goalkeepers_table(selected_equipo_id)

    kpi_container.content = build_kpis()

    return ft.Container(
        expand=True,
        padding=20,
        content=ft.Column(
            expand=True,
            spacing=20,
            controls=[

                # 🔹 Selector de equipo
                team_selector(page, on_team_change),

                # 🔹 Switch KPIs
                kpi_mode_switch(page),

                # 🔹 KPIs
                kpi_container,

                # ==================================================
                # CHARTS (Goles + Bumpy)
                # ==================================================
                ft.ResponsiveRow(
                    expand=True,
                    spacing=12,
                    columns=12,
                    controls=[
                        ft.Container(
                            expand=True,
                            col={
                                "xs": 12,
                                "sm": 12,
                                "md": 12,
                                "lg": 6,
                                "xl": 6,
                            },
                            content=chart_container,
                        ),
                        ft.Container(
                            expand=True,
                            col={
                                "xs": 12,
                                "sm": 12,
                                "md": 12,
                                "lg": 6,
                                "xl": 6,
                            },
                            content=bumpy_container,
                        ),
                    ],
                ),

                # ==================================================
                # TABLE · JUGADORES
                # ==================================================
                ft.ResponsiveRow(
                    expand=True,
                    spacing=12,
                    columns=12,
                    controls=[
                        ft.Container(
                            expand=True,
                            col={
                                "xs": 12,
                                "sm": 12,
                                "md": 12,
                                "lg": 12,
                                "xl": 12,
                            },
                            content=table_player_container,
                        ),
                    ],
                ),

                # ==================================================
                # TABLES · PORTEROS + MERCADO
                # ==================================================
                ft.ResponsiveRow(
                    expand=True,
                    spacing=12,
                    columns=12,
                    controls=[
                        ft.Container(
                            expand=True,
                            col={
                                "xs": 12,
                                "sm": 12,
                                "md": 12,
                                "lg": 12,
                                "xl": 7,
                            },
                            content=top_saves_goalkeepers_container,
                        ),
                        ft.Container(
                            expand=True,
                            col={
                                "xs": 12,
                                "sm": 12,
                                "md": 12,
                                "lg": 12,
                                "xl": 5,
                            },
                            content=table_market_container,
                        ),
                    ],
                ),
            ],
        ),
    )