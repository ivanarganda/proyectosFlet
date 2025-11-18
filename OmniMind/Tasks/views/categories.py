import json
import asyncio
import requests_async as request
import flet as ft
from params import *
from helpers.utils import log_error, loadSnackbar, setCarrousel

def loadTasksCategories(page: ft.Page, token, viewDetailsCategory, addTask, addCategory, callbacks={}):
    """Carga las categorías de tareas desde la API."""

    async def load_data():
        try:
            headers = HEADERS
            headers["Authorization"] = f"Bearer {token}"

            response = await request.get(
                f"{REQUEST_URL}/tasks/categories",
                headers=headers,
                timeout=10
            )

            if response.status_code != 200:
                print(f"⚠️ HTTP Error: {response.status_code}")
                try:
                    print("Response:", response.json())
                except Exception:
                    print("Response not JSON decodable.")
                return None

            try:
                data = response.json()
                if not isinstance(data, dict):
                    raise ValueError("Response JSON is not a dictionary.")
                return data
            except Exception as e:
                log_error("load_data.json", e)
                return None

        except (asyncio.TimeoutError, OSError, ConnectionError):
            loadSnackbar(page, "⚠️ Connection error or timeout while loading categories.", "red")
            return None

        except Exception as e:
            log_error("load_data", e)
            return None

    # Ejecutar la corrutina de forma segura
    try:
        data = asyncio.run(load_data())
    except RuntimeError:
        # Si ya hay un loop en ejecución (posible en Flet)
        data = asyncio.get_event_loop().run_until_complete(load_data())
    except Exception as e:
        log_error("loadTasksCategories.asyncio_run", e)
        data = None

    # Validar data
    if not data or "message" not in data or not data["message"]:
        print("⚠️ No se recibieron categorías o datos vacíos.")
        return ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.icons.CATEGORY_OUTLINED, size=80, color="#B0B0B0"),
                    ft.Text(
                        "No categories yet",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color="#555",
                    ),
                    ft.Text(
                        "Create your first category to organize your tasks.",
                        size=14,
                        color="#777",
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Divider(height=10, color="transparent"),
                    ft.ElevatedButton(
                        "Create Category",
                        icon=ft.icons.ADD_CIRCLE_OUTLINE,
                        bgcolor="#4e73df",
                        color="white",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                        height=45,
                        width=220,
                        on_click=lambda _: addCategory(page)
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            alignment=ft.alignment.center,
            padding=40,
            border_radius=20,
            bgcolor="#FFFFFF",
            shadow=ft.BoxShadow(blur_radius=25, color="#E0E0E0"),
            height=page.window_height - 400,
            expand=True
        )

    # Procesar datos recibidos
    newData = []
    for id_category, category_data in enumerate(data.get("message", []), start=1):
        tasks = category_data.get("tasks", 0)
        try:
            content = category_data.get("content", {})
            parsed_content = (
                json.loads(content)
                if isinstance(content, str)
                else content
            )
            if not isinstance(parsed_content, dict):
                raise ValueError("Parsed content is not a dict.")
        except Exception as e:
            log_error(f"parse_content id={id_category}", e)
            parsed_content = {}

        

        newData.append({
            "id_category": {"id": id_category},
            "tasks": {"total": tasks},
            "category": {"name": category_data.get("name", f"Category {id_category}")},
            "content": parsed_content
        })

    return setCarrousel(page, newData, on_view_category=viewDetailsCategory, on_add_task=addTask, on_callbacks=callbacks)