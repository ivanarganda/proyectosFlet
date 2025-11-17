import flet as ft
import json
import asyncio
import requests_async as request
import inspect
import textwrap
import ast
import re


def PopupMenuButton(
    page: ft.Page,
    id: int,
    item_to_edit: dict = None,
    alias: str = "item",
    request_url: dict = None,
    callback=None, # función a ejecutar tras confirmar acción
    callbacks={}
):

    fields = []

    def on_change_field(e, key):
        pass

    def parse_callbak_source( source, cb ):
        if source == "":
            print("Warning: Callback source code is empty.")
            return False
        for src_line in list(source.split('\n')):
            if "def" not in src_line and f"{cb.get("function").__name__}" not in src_line:
                if not re.match( r"^[A-Za-z_][A-Za-z0-9_]*\.controls\.clear\(\)$", src_line.strip() ) \
                or not re.match( r"^[A-Za-z_][A-Za-z0-9_]*\.controls\.append\(.+\)$", src_line.strip() ) \
                or "page.update()" in src_line.strip():
                    return {
                        "function": cb.get("function"),
                        "args": cb.get("args", [])
                    } , cb
        return False

    async def parse_request_url(request_url, action, json_data=None):

        requestes = [
            request.delete,
            request.put,
            request.post,
            request.get,
        ]

        actions = request_url.keys()
        methods = {}
        
        for req in requestes:
            for act in actions:
                if act == action:
                    methods[act] = req

        if not isinstance(request_url, dict):
            print("Invalid request_url format.")
            return None

        if action not in actions:
            print("Invalid action.")
            return None
        # Obtener configuración de la acción
        config = request_url.get(action)
        if not config:
            print(f"Missing '{action}' configuration.")
            return None

        url = config.get("url")
        headers = config.get("headers", {})
        token = config.get("token")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        method = methods[action]  # obtener la función correcta
        # Ejecutar async request (SIN json.dumps)
        response = await method(url, json=json_data, headers=headers)
        return response

        

    def get_context_callback(function):
        source = inspect.getsource(function)
        source = textwrap.dedent(source)
        tree = ast.parse(source)
        calls = []
        updates_ui = False

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                try:
                    if isinstance(node.func, ast.Attribute):
                        calls.append(
                            f"{node.func.value.id}.{node.func.attr}"
                        )
                        if node.func.attr == "update":
                            updates_ui = True
                    elif isinstance(node.func, ast.Name):
                        calls.append(node.func.id)
                except:
                    continue
        return {
            "function_name": function.__name__,
            "calls": calls,
            "updates_ui": updates_ui,
            "source": source
        }
    # ------------------------------
    # Cerrar diálogo
    # ------------------------------
    def close_dialog(e):
    
        dlg = e.page.dialog
        dlg.open = False
        excecutable = True
        callbacks_to_execute = {}
        if callback:
            callback()
        if callbacks:
            for cb in callbacks.values():
                cb.get("function")(*cb.get("args", []))
                buffer_value_callback = get_context_callback(cb.get("function"))
                
                if isinstance(buffer_value_callback, dict):
                    source = buffer_value_callback.get("source", "")
                    parsed_callback, cb = parse_callbak_source( source, cb )
                    if not parsed_callback:
                        continue
                    callbacks_to_execute[ cb.get("function") ] = parsed_callback
                else:
                    print("Warning: Callback context could not be retrieved.")
                    continue
        
        print("Callbacks to execute:", callbacks_to_execute)
        if callbacks_to_execute:
            for cb_exec in callbacks_to_execute.values():
                cb_exec.get("function")(*cb_exec.get("args", []))
            e.page.update()

    def default_on_callback():
        print("Default callback executed.")

    def default_render_callback():
        return ft.Text("No content available.")

    # Delete or edit 
    def delete(ev):
        async def send_delete_request(json_data):
            # Aquí iría la lógica para enviar la solicitud HTTP
            response = await parse_request_url(request_url, "delete", json_data)
            return response.json()

        if request_url and "delete" in request_url:
            response = asyncio.run(send_delete_request({}))
            print("Response data:", response)
        else:
            print("No delete URL provided.")

    def edit(ev):
        async def send_edit_request(json_data):
            # Aquí iría la lógica para enviar la solicitud HTTP
            response = await parse_request_url(request_url, "edit", json_data)
            return response.json()

        if request_url and "edit" in request_url:
            value_options_dropdown = {}      
            for pos, field in enumerate(fields):
                if isinstance(field, ft.Dropdown):
                    options = []
                    if isinstance(field.value, str):
                        for option in field.options:
                            options.append(option.key)
                        value_options_dropdown[field.label.lower()] = options

            json_data = dict((key, field.value) for key, field in zip(item_to_edit.keys(), fields))
            
            for key in json_data:
                for k, value in value_options_dropdown.items():
                    if key == k and json_data[key]:
                        value = json_data[key]
                        if value in value_options_dropdown[k]:
                            json_data[key] = (value_options_dropdown[k].index(value))

            # hacerlo asincrono que no bloquee la UI
            response = asyncio.run(send_edit_request(json_data))
            print("Response data:", response)

        else:
            print("No edit URL provided.")

    # ------------------------------
    # Render de contenido EDITAR
    # ------------------------------
    def render_edit_dialog():

        def render_edit_fields():

            nonlocal fields
            fields.clear()
            for key, properties in item_to_edit.items():
                type_ = properties.get("type", "text")
                value = properties.get("value", "")
                disabled = properties.get("disabled", True)
                if type_ == "text":
                    fields.append(ft.TextField(
                        label=key.capitalize(),
                        value=value,
                        on_change=lambda e: on_change_field(e, key),
                        disabled=disabled,
                    ))
                elif type_ == "identifier":

                    fields.append(ft.TextField(
                        label=key.capitalize(),
                        value=str(value),
                        disabled=True,
                    ))

                elif type_ == "number":

                    fields.append(ft.TextField(
                        label=key.capitalize(),
                        value=str(value),
                        disabled=disabled,
                        on_change=lambda e: on_change_field(e, key),
                        keyboard_type=ft.KeyboardType.NUMBER,
                    ))
                elif type_ == "dropdown":
                    options = properties.get("options", [])
                    fields.append(ft.Dropdown(
                        label=key.capitalize(),
                        options=[ft.dropdown.Option(opt) for key,opt in options.items()],
                        value=value,
                        on_change=lambda e: on_change_field(e, key),
                        disabled=disabled,
                    ))
                elif type_ == "checkbox":
                    fields.append(ft.Checkbox(
                        label=key.capitalize(),
                        value=bool(value),
                        on_change=lambda e: on_change_field(e, key),
                        disabled=disabled,
                    ))
                elif type_ == "date":
                    fields.append(ft.DatePicker(
                        label=key.capitalize(),
                        value=value,
                        on_change=lambda e: on_change_field(e, key),
                        disabled=disabled,
                    ))
                elif type_ == "time":
                    fields.append(ft.TimePicker(
                        label=key.capitalize(),
                        value=value,
                        on_change=lambda e: on_change_field(e, key),
                        disabled=disabled,
                    ))
                elif type_ == "textarea":
                    fields.append(ft.TextField(
                        label=key.capitalize(),
                        value=value,
                        on_change=lambda e: on_change_field(e, key),
                        disabled=disabled,
                        multiline=True,
                        min_lines=3,
                    ))
                elif type_ == "slider":
                    min_value = properties.get("min", 0)
                    max_value = properties.get("max", 100)
                    fields.append(ft.Slider(
                        label=key.capitalize(),
                        value=float(value),
                        min=min_value,
                        max=max_value,
                        divisions=10,
                        on_change=lambda e: on_change_field(e, key),
                        disabled=disabled,
                    ))
                elif type_ == "color":
                    fields.append(ft.ColorPicker(
                        label=key.capitalize(),
                        value=value,
                        on_change=lambda e: on_change_field(e, key),
                        disabled=disabled,
                    ))
            return fields

        if item_to_edit is None:
            return ft.Column(
                spacing=15,
                controls=[
                    ft.Text("No item to edit.", size=16, weight="bold"),
                    ft.Text("Please provide an item to edit."),
                ],
            )
        
        return ft.Column(
            spacing=15,
            controls=render_edit_fields(),
        )

    # ------------------------------
    # Render de contenido ELIMINAR
    # ------------------------------
    def render_delete_dialog():

        if item_to_edit is None:
            return ft.Column(
                spacing=15,
                controls=[
                    ft.Text("No item to delete.", size=16, weight="bold"),
                    ft.Text("Please provide an item to delete."),
                ],
            )
        return ft.Column(
            spacing=15,
            controls=[
                ft.Text(
                    f"Are you sure you want to delete the {alias} with ID {id}?",
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.RED_600,
                ),
                ft.Text(
                    "This action is irreversible.",
                    size=14,
                    color="#666",
                ),
            ],
        )

    # ------------------------------
    # DIÁLOGO BASE — PROFESIONAL
    # ------------------------------
    def show_dialog(title, render_callback, on_confirm=None, confirm_text="Accept"):
        dialog = ft.AlertDialog(
            modal=True,
            shape=ft.RoundedRectangleBorder(radius=18),
            title=ft.Text(title, size=20, weight="bold"),
            content=ft.Container(
                padding=10,
                content=render_callback(),
            ),
            actions=[
                ft.TextButton(
                    "Cancel",
                    on_click=close_dialog,
                    style=ft.ButtonStyle(color="#888"),
                ),
                ft.FilledButton(
                    text=confirm_text,
                    on_click=on_confirm or close_dialog,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=8),
                        bgcolor=ft.Colors.RED_500 if "Delete" in title else "#1B2453",
                        color="white",
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.dialog = dialog
        dialog.open = True
        page.update()

    # ------------------------------
    # EVENTO EDITAR
    # ------------------------------
    def on_edit(e):
        print(f"Edit {alias} {id}")
        show_dialog(
            title=f"Edit {alias}",
            render_callback=render_edit_dialog,
            on_confirm=lambda ev: (
                edit(ev) if item_to_edit else None, # ejecutar callback si existe
                close_dialog(ev),
            ),
            confirm_text="Save changes" if item_to_edit else "Accept",
        )

    # ------------------------------
    # EVENTO ELIMINAR
    # ------------------------------
    def on_delete(e):
        print(f"Delete {alias} {id}")
        show_dialog(
            title=f"Delete {alias}",
            render_callback=render_delete_dialog,
            on_confirm=lambda ev: (
                delete(ev) if item_to_edit else None, # ejecutar callback si existe
                close_dialog(ev),
            ),
            confirm_text="Delete" if item_to_edit else "Accept",
        )

    # ------------------------------
    # MENU POPUP MODERNO
    # ------------------------------
    return ft.Container(
        content=ft.PopupMenuButton(
            icon=ft.icons.MORE_VERT,
            tooltip="Options",
            items=[
                ft.PopupMenuItem(
                    text="Edit",
                    icon=ft.icons.EDIT,
                    on_click=on_edit,
                ),
                ft.PopupMenuItem(
                    text="Delete",
                    icon=ft.icons.DELETE_OUTLINE,
                    on_click=on_delete,
                ),
            ],
        ),
        alignment=ft.alignment.top_right,
        margin=ft.margin.only(top=8, right=8),
    )
