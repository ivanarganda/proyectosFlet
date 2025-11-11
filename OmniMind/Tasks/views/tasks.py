import flet as ft
from helpers.utils import log_error
import asyncio
import requests_async as request
import json
from params import HEADERS, REQUEST_URL
from middlewares.auth import middleware_auth 

tasks_data = []
headers = HEADERS
token = None

async def render_today_tasks(): # TODO pending to develop
    global tasks_data
    tasks_data.clear()
    async def load_today_tasks():
        global headers, token
        headers = HEADERS.copy()
        headers["Authorization"] = f"Bearer {token}"

        response = await request.get(f"{REQUEST_URL}/tasks", headers=headers )
        return response
    tasks_data = asyncio.create_task( load_today_tasks() )
    
    if data.get("status") == 200:
        for key, item in enumerate( data.get("message")):
            pass


def ListTasks(page: ft.Page, t="TodayTasks", category=None, absolute=True):
    global tasks_data
    session = middleware_auth(page)
    token = session.get("token","")
    """
    Muestra la lista de tareas.
    Si t == "TodayTasks": muestra solo datos básicos (icono, título, completadas...).
    Si t == "AllTasks": permite hacer slide down para ver detalles (descripción, fecha, autor).
    """

    # --- Validación del tipo ---
    types_ = ["TodayTasks", "AllTasks"]
    if t not in types_:
        log_error(f"Type '{t}' not recognized in ListTasks. Defaulting to 'TodayTasks'.")
        t = "TodayTasks"

    # --- Componente visual: Task Item ---
    def task_item(icon, title, completed, color, number_color, number_value,
                  description=None, date=None, author=None):
        # Contenedor principal de la tarea
        base_row = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(
                    spacing=15,
                    controls=[
                        ft.Container(
                            content=ft.Icon(icon, color="white", size=22),
                            width=48,
                            height=48,
                            border_radius=15,
                            bgcolor=color,
                            alignment=ft.alignment.center,
                        ),
                        ft.Column(
                            spacing=3,
                            alignment=ft.MainAxisAlignment.CENTER,
                            controls=[
                                ft.Text(title, weight="bold", size=15, color="#1E1E1E"),
                                ft.Text(f"{completed} Completed", size=12, color="#8E8E93"),
                            ],
                        ),
                    ],
                ),
                ft.Container(
                    content=ft.Text(
                        str(number_value),
                        color="white",
                        weight="bold",
                        size=14,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    width=30,
                    height=30,
                    border_radius=8,
                    bgcolor=number_color,
                    alignment=ft.alignment.center,
                ),
            ],
        )
        """Crea una tarjeta de tarea, con o sin detalles expandibles."""
        expanded = ft.Ref[ft.Container]()
        def toggle_expand(e):
            if expanded.current.height == 0:
                expanded.current.height = None
                expanded.current.opacity = 1
            else:
                expanded.current.height = 0
                expanded.current.opacity = 0
            e.page.update()
    
        # --- Si es AllTasks: añadimos bloque expandible ---
        extra_details = None
        if t == "AllTasks":
            extra_details = ft.Container(
                ref=expanded,
                height=0,
                opacity=1,
                animate_opacity=300,
                animate_size=ft.animation.Animation(300, "easeOut"),
                padding=ft.padding.only(left=60, top=5, bottom=5, right=10),
                content=ft.Column(
                    spacing=3,
                    alignment=ft.MainAxisAlignment.START,
                    controls=[
                        ft.Text(f"📝 {description or 'No description'}", size=13, color="black"),
                        ft.Text(f"📅 {date or 'No date'}", size=13, color="black"),
                        ft.Text(f"👤 {author or 'Unknown'}", size=13, color="black"),
                    ],
                ),
            )

        # --- Contenedor con animación y sombra ---
        container = ft.Container(
            on_click=toggle_expand if t == "AllTasks" else None,
            content=ft.Column(
                controls=[base_row] + ([extra_details] if extra_details else []),
            ),
            padding=ft.padding.symmetric(vertical=8, horizontal=10),
            margin=ft.margin.symmetric(vertical=5),
            border_radius=12,
            bgcolor="white",
            shadow=ft.BoxShadow(blur_radius=15, spread_radius=-5, color="#00000025"),
            ink=True,
        )

        return container

    # --- Título dinámico ---
    title_text = (
        "Today's Task"
        if t == "TodayTasks"
        else f"All Tasks of the Category {category.get('name', '') if isinstance(category, dict) else ''}"
    )

    if t == "TodayTasks":
        title = ft.Container(
            bgcolor="#1B2453",  # Azul oscuro elegante
            border_radius=20,
            padding=ft.padding.all(18),
            margin=ft.margin.only(bottom=10, top=5),
            shadow=ft.BoxShadow(
                blur_radius=15,
                spread_radius=-5,
                color=ft.colors.with_opacity(0.2, "#000000"),
            ),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text(
                        title_text,
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color="white",
                    ),
                    ft.Icon(ft.icons.TODAY_OUTLINED, color="#8EE9D1", size=24),
                ],
            ),
        )
    else:
        title = ft.Container(
            bgcolor="#1B2453",  # Azul oscuro elegante
            border_radius=20,
            padding=ft.padding.all(18),
            margin=ft.margin.only(bottom=10, top=5),
            shadow=ft.BoxShadow(
                blur_radius=15,
                spread_radius=-5,
                color=ft.colors.with_opacity(0.2, "#000000"),
            ),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Column(
                        alignment=ft.MainAxisAlignment.START,
                        spacing=4,
                        controls=[
                            ft.Text(
                                "You are on Track",
                                size=17,
                                weight=ft.FontWeight.BOLD,
                                color="white",
                            ),
                            ft.Row(
                                spacing=5,
                                controls=[
                                    ft.Icon(ft.icons.CHECK_CIRCLE_OUTLINED, color="#8EE9D1", size=16),
                                    ft.Text(
                                        "50% Progress have made",
                                        size=13,
                                        color="#D8D8F0",
                                    ),
                                ],
                            ),
                        ],
                    ),
                    # Fondo decorativo de puntos (como en el diseño)
                    ft.Container(
                        width=50,
                        height=35,
                        content=ft.Stack(
                            controls=[
                                ft.Container(
                                    bgcolor=ft.colors.with_opacity(0.08, "white"),
                                    border_radius=50,
                                )
                                for _ in range(8)
                            ],
                        ),
                    ),
                ],
            ),
        )

    tasks_data = [
        (ft.icons.BRUSH_OUTLINED, "Sketching", 2, "#3DCAB0", "#3DCAB0", 4,
            "Refinando el boceto inicial", "2025-10-26", "ivan_arganda96"),
        (ft.icons.TABLE_CHART_OUTLINED, "Wireframing", 0, "#7B68EE", "#D2C8FF", 2,
            "Definiendo estructura base", "2025-10-25", "pedrin"),
        (ft.icons.MONITOR_OUTLINED, "Visual Design", 4, "#FF7A3C", "#FF7A3C", 4,
            "Creación de la UI final", "2025-10-24", "rocio"),
    ]

    tasks = ft.Column(
        spacing=10,
        controls=[
            task_item(*t) for t in tasks_data
        ],
    )

    # --- Contenedor principal inferior ---
    pos_props = {"bottom": 0, "left": 0, "right": 0} if absolute else {}
    return ft.Container(
        bgcolor="#F6F4FB",
        border_radius=ft.border_radius.only(top_left=30, top_right=30),
        height=450 if absolute else page.height - 50,
        alignment=ft.alignment.top_center,
        shadow=ft.BoxShadow(
            spread_radius=-10,
            blur_radius=25,
            color=ft.colors.with_opacity(0.3, "#000000"),
        ),
        content=ft.Column(
            [
                ft.Container(
                    content=title,
                    padding=ft.padding.only(top=25, bottom=10),
                    alignment=ft.alignment.center_left,
                ),
                ft.AnimatedSwitcher(
                    content=tasks,
                    transition=ft.AnimatedSwitcherTransition.FADE,
                    duration=500,
                    reverse_duration=300,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.padding.only(left=25, right=25, bottom=20),
        **pos_props
    )
