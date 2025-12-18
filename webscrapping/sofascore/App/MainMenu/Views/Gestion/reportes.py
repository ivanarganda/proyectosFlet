import os
import flet as ft
import requests
from params import *
from middlewares.auth import middleware_auth
from helpers.utils import addElementsPage
from footer_navegation.navegation import footer_navbar

reports_container = ft.Container(expand=True)
username = None
id_user = None

current_path = {
    "path": os.path.abspath(__file__),
    "folder": os.path.dirname(os.path.abspath(__file__)).split("\\")[-1],
    "file": __file__.split("\\")[-1],
}

def open_report( page, type , id_report ):

    routes = {
        "dashboard": "/info/dashboard"
    }

    route = routes.get( type , "")

    if route == "":
        
        return False

    query_params = f"?id_reporte={id_report}"

    path = f"{route}{query_params}"

    page.go( path )


def build_reports_table(reports, page):

    rows = [
        ft.DataRow(
            cells=[
                ft.DataCell(ft.Text(r["titulo"], weight=ft.FontWeight.BOLD)),
                ft.DataCell(ft.Text(r.get("descripcion", ""))),
                ft.DataCell(ft.Text(r["fecha_creacion"])),
                ft.DataCell(
                    ft.Row(
                        spacing=5,
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.PLAY_ARROW,
                                tooltip="Abrir",
                                on_click=lambda e, r=r: open_report(page, "dashboard", r["id_reporte"])
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE,
                                tooltip="Eliminar",
                                icon_color="red",
                                on_click=lambda e, r=r: delete_report(
                                    page, r["id_reporte"]
                                )
                            )
                        ]
                    )
                )
            ]
        )
        for r in reports
    ]

    return ft.DataTable(
        width=float("inf"),
        heading_row_color=ft.colors.GREY_900,
        columns=[
            ft.DataColumn(ft.Text("Título")),
            ft.DataColumn(ft.Text("Descripción")),
            ft.DataColumn(ft.Text("Fecha")),
            ft.DataColumn(ft.Text("Acciones")),
        ],
        rows=rows,
    )


def filter_reports(page, query):

    try:
        resp = requests.get(
            f"{REQUEST_URL}/reports/{id_user}",
            timeout=10
        )
        resp.raise_for_status()
        reports = resp.json()
    except:
        return

    if query:
        query = query.lower()
        reports = [
            r for r in reports
            if query in r["titulo"].lower()
        ]

    reports_container.content = (
        build_reports_table(reports, page)
        if reports
        else ft.Text("No hay reportes que coincidan.")
    )
    page.update()


def load_reports(page):

    print(id_user)

    try:
        resp = requests.get(
            f"{REQUEST_URL}/reports/{id_user}",
            timeout=10
        )
        resp.raise_for_status()
        reports = resp.json()
        print(reports)
    except Exception as ex:
        reports_container.content = ft.Text(
            f"Error cargando reportes: {ex}",
            color="red"
        )
        page.update()
        return

    if not reports:
        reports_container.content = ft.Text(
            "No tienes reportes guardados todavía."
        )
    else:
        reports_container.content = build_reports_table(reports, page)

    page.update()


def RenderReportes(page: ft.Page, params={}):

    global username, id_user

    session = middleware_auth(page)

    user = session.get("session", {}) or {}

    username = user.get("nombre", "Guest")
    id_user = int(user.get("id_usuario", 0))

    page.scroll = ft.ScrollMode.AUTO

    # ─────────── HEADER ───────────
    header = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        controls=[
            ft.Text(
                "📁 Mis reportes",
                size=22,
                weight=ft.FontWeight.BOLD
            ),
            ft.TextField(
                hint_text="Buscar reporte...",
                width=260,
                on_change=lambda e: filter_reports(
                    page, e.control.value
                )
            )
        ]
    )

    # ─────────── CONTENEDOR DINÁMICO ───────────
    reports_container.content = ft.ProgressRing()
    page.update()

    # ─────────── CARGA INICIAL ───────────
    load_reports(page)

    footer = ft.Container(
        content=footer_navbar(page=page, current_path=current_path, dispatches={}),
        expand=False
    )

    main_content = ft.Container(
        expand=True,
        padding=20,
        content=ft.Column(
            expand=True,
            spacing=20,
            controls=[
                header,
                reports_container
            ]
        )
    )

    layout = ft.Column(
        [
            ft.Container(
                content=ft.Column(
                    [
                        main_content
                    ],
                    scroll=ft.ScrollMode.AUTO
                ),
                expand=True,
                padding=ft.padding.only(bottom=10)
            ),
            footer
        ],
        expand=True,
        spacing=0
    )

    return addElementsPage(page, [layout])

