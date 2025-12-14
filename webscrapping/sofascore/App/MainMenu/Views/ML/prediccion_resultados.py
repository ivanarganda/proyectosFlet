# pages/partidos_prediccion.py
import os
import flet as ft
import requests

from helpers.pagination_list import PaginatedList
from helpers.utils import addElementsPage
from .common_components_ml import build_card
from footer_navegation.navegation import footer_navbar
from middlewares.auth import middleware_auth
from params import REQUEST_URL, HEADERS


# ======================================================
# PATH
# ======================================================
current_path = {
    "path": os.path.abspath(__file__),
    "folder": os.path.dirname(os.path.abspath(__file__)).split("\\")[-1],
    "file": __file__.split("\\")[-1],
}

label_page = "Simulación ML"


# ======================================================
# MAIN VIEW
# ======================================================
def RenderMLPrediccionResultados(page: ft.Page, params={}):

    # =========================
    # CONFIG PAGE
    # =========================
    page.window.width = 900
    page.window.height = 900
    page.scroll = None

    session = middleware_auth(page)
    token = session.get("token")
    HEADERS["Authorization"] = f"Bearer {token}"

    # =========================
    # STATE
    # =========================
    selected_jornada = {"value": None}
    has_generated = {"value": False}

    # =========================
    # FETCH JORNADAS
    # =========================
    def get_jornadas_disponibles():
        r = requests.get(
            f"{REQUEST_URL}/excel/jornadas_liga",
            headers=HEADERS
        )
        data = r.json().get("jornadas_futuras", [])

        if not data:
            return []

        jornadas = sorted(map(int, data))
        return jornadas

    jornadas = get_jornadas_disponibles()
    if jornadas:
        selected_jornada["value"] = jornadas[0]

    # =========================
    # RESULT CONTAINER (DINÁMICO)
    # =========================
    result_container = ft.Column(
        expand=True,
        spacing=16,
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Icon(ft.Icons.INSIGHTS, size=64, color="#9CA3AF"),
            ft.Text(
                "Selecciona una jornada y genera la simulación",
                size=16,
                color="#6B7280",
            )
        ]
    )

    # =========================
    # FETCH PARTIDOS ML
    # =========================
    def fetch_partidos():

        r = requests.post(
            f"{REQUEST_URL}/ml/forecasting/score",
            headers=HEADERS
        )
        data = r.json().get("data", {})

        partidos = []

        for jornada, lista in data.items():
            jornada_num = int(jornada.replace("Jornada_", ""))

            if jornada_num != selected_jornada["value"]:
                continue

            for partido in lista:
                partido["jornada"] = jornada
                partidos.append(partido)

        return partidos

    # =========================
    # PAGINATED LIST
    # =========================
    content, load_data = PaginatedList(
        page=page,
        title=f"Resultados simulados – Jornada {selected_jornada['value']}",
        type_="ml_partidos_prediccion",
        fetch_callback=fetch_partidos,
        item_builder=build_card,
        page_size=20,
    )

    # =========================
    # GENERAR SIMULACIÓN
    # =========================
    def on_generate():

        has_generated["value"] = True

        result_container.controls.clear()
        result_container.controls.append(
            ft.Column(
                expand=True,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.ProgressRing(
                        width=60,
                        height=60,
                        stroke_width=6,
                        color="#2563EB",
                    ),
                    ft.Container(height=12),
                    ft.Text(
                        "Simulando partidos...",
                        size=14,
                        color="#6B7280",
                    ),
                ],
            )
        )

        page.update()

        load_data()

        result_container.controls.clear()
        result_container.controls.append(content)
        page.update()

    # =========================
    # PANEL DE CONTROL (PRO)
    # =========================
    control_panel = ft.Container(
        padding=16,
        border_radius=16,
        bgcolor="white",
        shadow=ft.BoxShadow(
            blur_radius=20,
            color=ft.colors.with_opacity(0.15, "black"),
        ),
        content=ft.Row(
            spacing=12,
            alignment=ft.MainAxisAlignment.START,
            controls=[
                ft.Dropdown(
                    width=200,
                    label="Jornada",
                    value=str(selected_jornada["value"]),
                    options=[
                        ft.dropdown.Option(str(j)) for j in jornadas
                    ],
                    on_change=lambda e: selected_jornada.update(
                        {"value": int(e.control.value)}
                    ),
                ),
                ft.ElevatedButton(
                    text="Generar simulación",
                    icon=ft.Icons.PLAY_ARROW,
                    height=45,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=12),
                    ),
                    on_click=lambda _: on_generate(),
                )
            ]
        )
    )

    # =========================
    # HEADER
    # =========================
    header = ft.Container(
        padding=ft.padding.only(bottom=8),
        content=ft.Column(
            controls=[
                ft.Text(
                    "Simulación de partidos",
                    size=26,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    "Predicción de resultados basada en Machine Learning",
                    size=14,
                    color="#6B7280",
                )
            ]
        )
    )

    # =========================
    # FOOTER
    # =========================
    footer = ft.Container(
        content=footer_navbar(
        page=page,
        current_path=current_path,
        dispatches={},
    )
    )

    # =========================
    # LAYOUT FINAL
    # =========================
    layout = ft.Column(
        expand=True,
        spacing=0,
        controls=[
            # =========================
            # CONTENIDO (EMPUJA AL FOOTER)
            # =========================
            ft.Container(
                expand=True,   # 👈 ESTE es el ÚNICO expand
                padding=ft.padding.only(left=16, right=16, top=16),
                content=ft.Column(
                    expand=True,
                    spacing=16,
                    scroll=ft.ScrollMode.AUTO,
                    controls=[
                        header,
                        control_panel,
                        result_container,

                        # 🔥 ESPACIADOR REAL
                        ft.Container(expand=True),
                    ],
                ),
            ),

            # =========================
            # FOOTER FIJO ABAJO
            # =========================
            footer,
        ],
    )

    return addElementsPage(page, [layout])