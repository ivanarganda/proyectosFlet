import flet as ft
import requests
from helpers.utils import log_error
from params import HEADERS, REQUEST_URL
import threading

# ==========================================================
# CARGA SINCRÓNICA DESDE LA API
# ==========================================================
def render_tasks_sync(token, id_category = None):
    """Devuelve las tareas de hoy en modo síncrono."""
    try:
        headers = HEADERS.copy()
        headers["Authorization"] = f"Bearer {token}"

        category = "" if id_category is None else f"?id={id_category}"

        response = requests.get(f"{REQUEST_URL}/tasks{category}", headers=headers)

        if response.status_code == 200:
            return response.json()  # { status, message }

        return {"status": response.status_code, "message": None}

    except Exception as e:
        print(f"❌ Error en render_tasks_sync: {e}")
        return {"status": 500, "message": str(e)}


# ==========================================================
# COMPONENTE PRINCIPAL
# ==========================================================
def ListTasks(page: ft.Page, t="TodayTasks", category=None, absolute=True, session={}):

    token = session.get("token")
    task_container = ft.Column([ft.Text("Cargando tareas...", color="#64748b")])

    print( token )

    # ======================================================
    # COMPONENTE VISUAL: TASK ITEM
    # ======================================================
    def task_item(icon, title, completed, color, number_color, number_value,
                  description=None, date=None, author=None):

        expanded = ft.Ref[ft.Container]()

        def toggle_expand(e):
            if expanded.current.height == 0:
                expanded.current.height = None
                expanded.current.opacity = 1
            else:
                expanded.current.height = 0
                expanded.current.opacity = 0

            e.page.update()

        # Mostrar detalles solo en AllTasks
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
                        ft.Text(f"📝 {description or 'No description'}", size=13),
                        ft.Text(f"📅 {date or 'No date'}", size=13),
                        ft.Text(f"👤 {author or 'Unknown'}", size=13),
                    ],
                ),
            )

        return ft.Container(
            on_click=toggle_expand if t == "AllTasks" else None,
            padding=ft.padding.symmetric(vertical=8, horizontal=10),
            margin=ft.margin.symmetric(vertical=5),
            border_radius=12,
            bgcolor="white",
            shadow=ft.BoxShadow(blur_radius=15, spread_radius=-5, color="#00000025"),
            ink=True,
            content=ft.Column(
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
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
                                        controls=[
                                            ft.Text(title, weight="bold", size=15),
                                            ft.Text(
                                                f"{completed} Completed",
                                                size=12,
                                                color="#8E8E93",
                                            ),
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
                                ),
                                width=30,
                                height=30,
                                border_radius=8,
                                bgcolor=number_color,
                                alignment=ft.alignment.center,
                            ),
                        ],
                    ),
                    *( [extra_details] if extra_details else [] ),
                ]
            ),
        )

    # ======================================================
    # CARGA DE TAREAS (SINCRÓNICO en hilo)
    # ======================================================
    def load_and_render_tasks_sync():
        data = render_tasks_sync(token, id_category=category if t == "TodayTasks" else None)
        print("📋 Datos recibidos:", data)

        task_container.controls.clear()

        if not data.get("message"):
            task_container.controls.append(
                ft.Container(
                    padding=30,
                    border_radius=18,
                    bgcolor="white",
                    alignment=ft.alignment.center,
                    shadow=ft.BoxShadow(
                        blur_radius=25, spread_radius=-10, color="#00000020"
                    ),
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=12,
                        controls=[
                            ft.Icon(
                                ft.icons.INBOX_OUTLINED,
                                size=64,
                                color="#94a3b8"
                            ),
                            ft.Text(
                                "No hay tareas para hoy",
                                size=18,
                                weight="bold",
                                color="#475569"
                            ),
                            ft.Text(
                                "Disfruta el día mientras tanto 😎",
                                size=14,
                                color="#64748b",
                                text_align="center"
                            ),
                        ],
                    ),
                )
            )
        else:
            for task in data["message"]:
                task_container.controls.append(
                    task_item(
                        ft.icons.CHECK_CIRCLE_OUTLINED,
                        task.get("title", "Sin título"),
                        task.get("completed", 0),
                        "#3DCAB0",
                        "#3DCAB0",
                        task.get("total", 0),
                        task.get("description"),
                        task.get("due_date"),
                        task.get("author"),
                    )
                )
            pass

    # ======================================================
    # EJECUTAR CARGA TRAS PRIMER FRAME (NO BLOQUEA UI)
    # ======================================================
    load_and_render_tasks_sync()

    # ESTE MÉTODO SIEMPRE EXISTE
    
    # ======================================================
    # CABECERA Y CONTENEDOR FINAL
    # ======================================================
    title_text = (
        "Last 3 tasks"
        if t == "TodayTasks"
        else f"All Tasks of the Category {category.get('name', '')}"
    )

    title = ft.Container(
        bgcolor="#1B2453",
        border_radius=20,
        padding=ft.padding.all(18),
        margin=ft.margin.only(bottom=10, top=5),
        shadow=ft.BoxShadow(blur_radius=15, spread_radius=-5, color="#00000033"),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Text(title_text, size=20, weight="bold", color="white"),
                ft.Icon(ft.icons.TODAY_OUTLINED, color="#8EE9D1"),
            ],
        ),
    )

    pos_props = {"bottom": 0, "left": 0, "right": 0} if absolute else {}

    return ft.Container(
        bgcolor="#F6F4FB",
        border_radius=ft.border_radius.only(top_left=30, top_right=30),
        height=450 if absolute else page.height - 50,
        padding=25,
        shadow=ft.BoxShadow(blur_radius=25, color="#00000033"),
        content=(
            # ============================================
            # TODAY TASKS → CON SCROLL
            # ============================================
            ft.Column(
                [
                    title,
                    ft.Column(
                        [ft.AnimatedSwitcher(content=task_container)],
                        scroll=ft.ScrollMode.AUTO,   # ✔ scroll aquí
                        expand=True
                    ),
                    ft.Divider(height=40)
                ],
                expand=True
            )
            if t == "TodayTasks"
            else
            # ============================================
            # ALL TASKS → SIN SCROLL
            # ============================================
            ft.Column(
                [
                    title,
                    ft.Column([
                        ft.AnimatedSwitcher(content=task_container, expand=True)
                    ],
                    scroll=ft.ScrollMode.AUTO
                    )
                    
                ],
                expand=True
            )
        ),
        **pos_props
    )


