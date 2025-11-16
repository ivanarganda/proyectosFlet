import flet as ft
import requests
from helpers.utils import log_error
from params import HEADERS, REQUEST_URL
import threading
from components.Pagination import PaginationComponent
from components.PopupMenu import PopupMenuButton

states = {
    0: {"color":"#FFA500", "label":"Pending", "label_color":"#000000", "icon": ft.icons.HOURGLASS_EMPTY , "bg_icon": "#FFB740"},      # Orange
    1: {"color":"#32CD32", "label":"Completed", "label_color":"#000000", "icon": ft.icons.CHECK_CIRCLE, "bg_icon": "#91D998"},    # Lime Green
    2: {"color":"#1E90FF", "label":"In progress", "label_color":"#000000", "icon": ft.icons.PLAY_ARROW, "bg_icon": "#54B0FF" }   # Dodger Blue
}

# ==========================================================
# CARGA SINCRÓNICA DESDE LA API
# ==========================================================
def render_tasks_sync(token, t, id_category=None, page_num=1, limit=5):
    """Devuelve las tareas de hoy en modo síncrono."""
    
    try:
        headers = HEADERS.copy()
        headers["Authorization"] = f"Bearer {token}"

        category = "" if t == "TodayTasks" else f"?id_category={id_category}"

        pagination = f"&page={page_num}&limit={limit}" if category else f""

        response = requests.get(f"{REQUEST_URL}/tasks{category}{pagination}", headers=headers)

        if response.status_code == 200:
            return response.json()  # { status, message }

        return {"status": response.status_code, "message": None}

    except Exception as e:
        print(f"❌ Error en render_tasks_sync: {e}")
        return {"status": 500, "message": str(e)}

# ==========================================================
# COMPONENTE PRINCIPAL
# ==========================================================
def ListTasks(page:ft.Page, t="TodayTasks", category=None, absolute=True, session={}):

    token = session.get("token")
    task_container = ft.Column([ft.Text("Loading tasks...", color="#64748b")])
    current_page = 1  # Use a mutable type to allow modification in nested functions
    page_size = 5
    data = len(render_tasks_sync(token,t, id_category=category["id"] if category else None, page_num=1, limit=100).get("message", []))  # Total tasks count

    pages = data // page_size + (1 if data % page_size > 0 else 0)
    current_page_ref = [1] # use page for pagination component
    pages_ref = [pages] # use pages for pagination component

    # ======================================================
    # COMPONENTE VISUAL: TASK ITEM
    # ======================================================
    def task_item(item, icon, title, status, color, number_color, number_value,
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

        content_task = ft.Column(
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
                                            bgcolor=states[status].get("bg_icon", "#E0E0E0"),
                                            alignment=ft.alignment.center,
                                        ),
                                        ft.Column(
                                            spacing=3,
                                            controls=[
                                                ft.Text(title, weight="bold", size=15),
                                                ft.Text(
                                                    f"{states[status].get('label', 'Unknown Status')}",
                                                    size=12,
                                                    color=states[status].get("label_color", "#000000")
                                                ),
                                            ],
                                        ),
                                    ],
                                )
                            ],
                        ),
                        *( [extra_details] if extra_details else [] ),
                    ]
                )

        item_to_edit = {
            "id": {
                "value": item.get("id"),
                "type": "identifier",
                "required": True,
                "disabled": True
            },
            "title": {
                "value": item.get("title"),
                "type": "text",
                "disabled": False
            },
            "description": {
                "value": item.get("description"),
                "type": "text",
                "disabled": False
            },
            "state": {
                "value": item.get("state"),
                "options": {
                    0: "Pending",
                    1: "Completed",
                    2: "In progress"
                },
                "type": "dropdown",
                "disabled": False
            }
        }

        return ft.Container(
            on_click=toggle_expand if t == "AllTasks" else None,
            padding=ft.padding.symmetric(vertical=8, horizontal=10),
            margin=ft.margin.symmetric(vertical=5),
            border_radius=12,
            bgcolor=states[status].get("color", "#E0E0E0"),
            shadow=ft.BoxShadow(blur_radius=15, spread_radius=-5, color="#00000025"),
            ink=True,
            content=ft.Stack([
                content_task,
                PopupMenuButton(
                    page=page,          # ✔ page real
                    id=item.get("id"),      # ✔ id real
                    item_to_edit=item_to_edit, # ✔ item real
                    request_url={
                        "delete": {
                            "url":f"{REQUEST_URL}/tasks?id={item.get('id')}",
                            "token":token
                        },
                        "edit": {
                            "url":f"{REQUEST_URL}/tasks?id={item.get('id')}",
                            "token":token
                        }
                    },
                    alias="task",
                    callback=load_and_render_tasks_sync
                )
            ]),
        )

    # ======================================================
    # CARGA DE TAREAS (SINCRÓNICO en hilo)
    # ======================================================
    def load_and_render_tasks_sync():

        nonlocal current_page, pages
        
        data = render_tasks_sync(token,t, id_category=None if t == "TodayTasks" else category["id"], page_num=current_page_ref[0], limit=page_size)

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
                status = task.get("state", 0)
                icon = states[status].get("icon", ft.icons.HELP_OUTLINED)
                if t != "TodayTasks":
                    task_container.controls.append(
                        task_item(
                            item=task,
                            icon=icon,
                            title=task.get("title", "Sin título"),
                            status=status,
                            color="#3DCAB0",
                            number_color="#3DCAB0",
                            number_value=task.get("id", 0),
                            description=task.get("description"),
                            date=task.get("created_at"),
                            author=task.get("autor"),
                        )
                    )
                else:
                    task_container.controls.append(
                        task_item(
                            item=task,
                            icon=icon,
                            title=task.get("title", "Sin título"),
                            status=status,
                            color="#8EE9D1",
                            number_color="#1B2453",
                            number_value=task.get("id", 0),
                        )
                    )

    # ======================================================
    # EJECUTAR CARGA TRAS PRIMER FRAME (NO BLOQUEA UI)
    # ======================================================
    load_and_render_tasks_sync()

    # ESTE MÉTODO SIEMPRE EXISTE
    if t != "TodayTasks":
        pagination_controls = PaginationComponent(
            page,
            current_page_ref,
            pages_ref,
            load_and_render_tasks_sync
        )
    
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

    final_layout = ft.Container(
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
                    ft.AnimatedSwitcher(
                        content=task_container,
                        transition=ft.AnimatedSwitcherTransition.FADE,
                        duration=300
                    )
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
                    ft.Container(
                        content=ft.Column(
                            [
                                title,
                                ft.AnimatedSwitcher(
                                    content=task_container,
                                    transition=ft.AnimatedSwitcherTransition.FADE,
                                    duration=300,
                                )
                            ],
                            scroll=ft.ScrollMode.AUTO,
                            expand=True
                        ),
                        expand=True
                    ),

                    ft.Container(
                        content=pagination_controls,
                        padding=10,
                        bgcolor="#ffffff",
                        border_radius=12,
                        shadow=ft.BoxShadow(blur_radius=15, color="#00000022")
                    ),
                    ft.Divider(height=20)
                ],
                expand=True
            )
        ),
        **pos_props
    )

    return final_layout