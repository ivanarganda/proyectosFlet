## DISPONIBLE EN INGLES Y ESPAÑOL

# (VERSION INGLES)

# Flet Popup Menu

A customizable and ready-to-use popup menu component for **Flet** applications.  
It provides edit/delete dialogs, dynamic form generation for editing items, API communication,  
and a flexible callback system for UI updates across modules.

---

## 🚀 Installation

```bash
pip install flet_popupmenu
```

## Import

```python
from flet_popupmenu import PopupMenuButton
```

## Use

- Initialize function called "PopupMenuButton" whose arguments are:

```python
def PopupMenuButton(
    page: ft.Page,
    id: int,
    item_to_edit: dict = None,
    alias: str = "item",
    request_url: dict = None,
    callback=None,
    callbacks: dict = {}
):
```

🔍 ARGUMENTS EXPLAINED

Below is exactly what each argument does, and which ones are optional.

🔵 Required Arguments

✔ page: ft.Page

Current Flet page — required for dialogs, updates, and UI rendering.

✔ id: int

Unique identifier of the item being edited or deleted.

🟡 Optional Arguments (EXPLAINED IN DETAIL)

🟡 item_to_edit: dict = None (optional)

If provided → the popup shows a form for editing the item.

If omitted → the “edit” option is disabled automatically.

Structure example:

```python
item_to_edit = {
    "title":  { "value": "Task A", "type": "text" },
    "state":  {
        "value": 1,
        "type": "dropdown",
        "options": { 0: "Pending", 1: "Completed" }
    }
}
```

If your item has no editable fields → simply pass None

🟡 alias: str = "item" (optional)

Name used in dialog messages.
Examples:

- "Task"

- "User"

- "Product"

If not set → defaults to "item".

🟡 request_url: dict = None (optional but RECOMMENDED)

Defines URLs for:

- deleting the item

- editing the item

Structure:

```python

request_url = {
    "delete": {
        "url": "https://api.com/items?id=3",
        "headers": headers
    },
    "edit": {
        "url": "https://api.com/items?id=3",
        "headers": headers
    }
}

```

If omitted:

- delete button will do nothing

- edit button will do nothing

- no errors will be thrown

🟡 callback=None (optional)

Function executed **after a successful delete/edit**.

Use it for UI refresh:

```python
callback = refresh_tasks
```

⚠️ IMPORTANT:
The callback must NOT require arguments.
It must be a simple callable:

```python
def refresh_tasks():
    ...
```

🟡 `callbacks: dict = {} ` &nbsp; (optional, advanced)

Allows triggering multiple auxiliary functions across your app.

This is useful if deleting/editing a task also needs to:

- reload categories

- refresh dashboards

- reload summary counters

```python
callbacks={
    "load_categories": {
        "function": refresh_categories,
        "args": []
    },
    "update_dashboard": {
        "function": refresh_dashboard,
        "args": []
    }
}
```

If omitted → only the main callback (if any) will run.

🟡 `Layout: dict = {} ` &nbsp; (optional, advanced)

Allows setting layout of popup container. Values are: **top, left, right, bottom, alignment, border_radius, bg_color**

```python

layout = {
    "top": int | 8,
    "left": int | 0,
    "right": int | 8,
    "bottom": int | 0,
    "alignment": "[top_right | top_center | top_left | right | center | left | bottom_right | bottom_center | bottom_left]" | ft.Alignment.top_right,
    "border_radius": int # In case exists, will set width amd heght as 40x40 to cover image according background
}

```

🌟 FULL EXAMPLE (RECOMMENDED)

🟦 STRUCTURE

2 files:

```cmd
app.py         → main module
tasks.py       → module where PopupMenuButton is used
```

🟩 1️⃣ app.py — MAIN FILE (DEFINE CALLBACKS)

```python
# app.py
import flet as ft
from tasks import render_tasks_list

# ------- CALLBACKS DEFINED HERE IN -------
def refresh_tasks():
    """
    Refreshes the task list. Gets executed after deleting/editing.
    IMPORTANT: Must not require args.
    """
    print("✔ refresh_tasks() executed (UI update here).")

def refresh_categories():
    """
    Example of a secondary function fired from callbacks argument.
    It can reload categories, counters, dashboards, etc.
    """
    print("✔ refresh_categories() executed (extra UI update).")


def main(page: ft.Page):
    page.title = "Callback Example"
    page.vertical_alignment = ft.MainAxisAlignment.START

    # ------- PASS CALLBACKS TO MODULE -------
    content = render_tasks_list(
        page=page,
        callback_main=refresh_tasks,
        callbacks_extra={
            "reload_categories": {
                "function": refresh_categories,
                "args": []
            }
        }
    )

    page.add(content)


ft.app(target=main)
```

🟩 2️⃣ tasks.py — Where is used PopupMenuButton (RECIVES CALLBACKS)

```python
# tasks.py
import flet as ft
from flet_popupmenu import PopupMenuButton


def render_tasks_list(page: ft.Page, callback_main=None, callbacks_extra=None):
    """
    callback_main: main refresh function (optional)
    callbacks_extra: dict with extra functions to run (optional)
    """

    # Simulated API task
    task = {
        "id": 3,
        "title": "Example Task",
        "description": "This is a sample description",
        "state": 1,
    }

    # Editable fields
    item_to_edit = {
        "id": { "value": task["id"], "type": "identifier", "disabled": True },
        "title": { "value": task["title"], "type": "text" },
        "description": { "value": task["description"], "type": "text" },
        "state": {
            "value": task["state"],
            "type": "dropdown",
            "options": {
                0: "Pending",
                1: "Completed",
                2: "In progress"
            }
        }
    }

    # Example headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer <token>"
    }

    popup = PopupMenuButton(
        page=page,
        id=task["id"],
        item_to_edit=item_to_edit,
        alias="Task",
        request_url={
            "delete": {
                "url": f"https://example.com/tasks?id={task['id']}",
                "headers": headers
            },
            "edit": {
                "url": f"https://example.com/tasks?id={task['id']}",
                "headers": headers
            }
        },

        # 🔥 MAIN CALLBACK (typically refresh list)
        callback=callback_main,

        # 🔥 EXTRA CALLBACKS (optional)
        callbacks=callbacks_extra
    )

    return ft.Column(
        controls=[
            ft.Text("Task List Example", size=20, weight="bold"),
            ft.ListTile(
                leading=ft.Icon(ft.icons.TASK),
                title=ft.Text(task["title"]),
                subtitle=ft.Text(task["description"]),
                trailing=popup
            )
        ]
    )
```

🟧 What exacly happens when the user deletes or edits:

&nbsp;&nbsp;&nbsp; **1.** Popup sends a delete or an edit request to your API\
 &nbsp;&nbsp;&nbsp; **2.** If API responses OK → PopupMenuButton runs:

```scss
callback_main()
callbacks_extra["reload_categories"]["function"](*args)
```

It called by example:

✔ refresh_tasks() → to reload the list
✔ refresh_categories() → to update other system parts

&nbsp;&nbsp;&nbsp; **3.** Defenitely, the UI turns into completelly optimized.

⭐ His finallity:

- How to separate logic across multiple files

- How to pass a function from the main file

- How to receive and use it within the component

- How to use advanced callbacks

- How to write functions without arguments

- How to refresh the UI after actions

⚠️ COMMON MISTAKES TO AVOID

- Do not pass callbacks that expect parameters. All functions must be def func(): ...

- Ensure your API ends with a valid JSON response.

- If item_to_edit is None, editing will be disabled.

- If request_url is None, delete/edit buttons will do nothing.

- The options key is only for dropdowns.

🧾 License

MIT License.

❤️ Contributions Welcome

Open a pull request or issue on GitHub.
Suggestions and improvements are welcome!

---

# 🚀 ¿Do you even want **badges** for PyPI too?

Can add:

- ✔ PyPI version
- ✔ Python versions
- ✔ Wheel status
- ✔ Download counts
- ✔ License badge
- ✔ Supported OS

Only say:

👉 **“Put badges too**

# (VERSIÓN EN ESPAÑOL)

# Menú Emergente Flet

Un componente de menú emergente personalizable y listo para usar para aplicaciones **Flet**.  
Proporciona diálogos de edición/eliminación, generación dinámica de formularios para editar elementos, comunicación con API  
y un sistema flexible de callbacks para actualizar la interfaz de usuario en todos los módulos.

---

## 🚀 Instalación

```bash
pip install flet_popupmenu
```

## Importación

```python
from flet_popupmenu import PopupMenuButton
```

## Uso

- Inicializa la función "PopupMenuButton" cuyos argumentos son:

```python
def PopupMenuButton(
    page: ft.Page,
    id: int,
    item_to_edit: dict = None,
    alias: str = "item",
    request_url: dict = None,
    callback=None,
    callbacks: dict = {}
):
```

🔍 EXPLICACIÓN DE ARGUMENTOS

A continuación se detalla para qué sirve cada argumento y cuáles son opcionales.

🔵 Argumentos obligatorios

✔ page: ft.Page

Página actual de Flet — necesaria para diálogos, actualizaciones y renderizado de la UI.

✔ id: int

Identificador único del elemento a editar o eliminar.

🟡 Argumentos opcionales (EXPLICADOS EN DETALLE)

🟡 item_to_edit: dict = None (opcional)

Si se proporciona → el menú muestra un formulario para editar el elemento.

Si se omite → la opción “editar” se desactiva automáticamente.

Ejemplo de estructura:

```python
item_to_edit = {
    "title":  { "value": "Tarea A", "type": "text" },
    "state":  {
        "value": 1,
        "type": "dropdown",
        "options": { 0: "Pendiente", 1: "Completada" }
    }
}
```

Si tu elemento no tiene campos editables → simplemente pasa None.

🟡 alias: str = "item" (opcional)

Nombre usado en los mensajes de diálogo.
Ejemplos:

- "Tarea"
- "Usuario"
- "Producto"

Si no se define → por defecto es "item".

🟡 request_url: dict = None (opcional pero RECOMENDADO)

Define URLs para:

- eliminar el elemento
- editar el elemento

Estructura:

```python
request_url = {
    "delete": {
        "url": "https://api.com/items?id=3",
        "headers": headers
    },
    "edit": {
        "url": "https://api.com/items?id=3",
        "headers": headers
    }
}
```

Si se omite:

- el botón eliminar no hará nada
- el botón editar no hará nada
- no se lanzarán errores

🟡 callback=None (opcional)

Función ejecutada **tras eliminar/editar exitosamente**.

Úsala para refrescar la UI:

```python
callback = refresh_tasks
```

⚠️ IMPORTANTE:
El callback NO debe requerir argumentos.
Debe ser una función simple:

```python
def refresh_tasks():
    ...
```

🟡 `callbacks: dict = {} ` &nbsp; (opcional, avanzado)

Permite disparar múltiples funciones auxiliares en tu app.

Útil si al eliminar/editar una tarea también necesitas:

- recargar categorías
- refrescar dashboards
- recargar contadores resumen

```python
callbacks={
    "load_categories": {
        "function": refresh_categories,
        "args": []
    },
    "update_dashboard": {
        "function": refresh_dashboard,
        "args": []
    }
}
```

Si se omite → solo se ejecuta el callback principal (si existe).

🌟 EJEMPLO COMPLETO (RECOMENDADO)

🟦 ESTRUCTURA

2 archivos:

```cmd
app.py         → módulo principal
tasks.py       → módulo donde se usa PopupMenuButton
```

🟩 1️⃣ app.py — ARCHIVO PRINCIPAL (DEFINE CALLBACKS)

```python
# app.py
import flet as ft
from tasks import render_tasks_list

# ------- CALLBACKS DEFINIDOS AQUÍ -------
def refresh_tasks():
    """
    Refresca la lista de tareas. Se ejecuta tras eliminar/editar.
    IMPORTANTE: No debe requerir argumentos.
    """
    print("✔ refresh_tasks() ejecutado (actualización de UI).")

def refresh_categories():
    """
    Ejemplo de función secundaria disparada desde callbacks.
    Puede recargar categorías, contadores, dashboards, etc.
    """
    print("✔ refresh_categories() ejecutado (actualización extra de UI).")


def main(page: ft.Page):
    page.title = "Ejemplo de Callback"
    page.vertical_alignment = ft.MainAxisAlignment.START

    # ------- PASA CALLBACKS AL MÓDULO -------
    content = render_tasks_list(
        page=page,
        callback_main=refresh_tasks,
        callbacks_extra={
            "reload_categories": {
                "function": refresh_categories,
                "args": []
            }
        }
    )

    page.add(content)


ft.app(target=main)
```

🟩 2️⃣ tasks.py — Donde se usa PopupMenuButton (RECIBE CALLBACKS)

```python
# tasks.py
import flet as ft
from flet_popupmenu import PopupMenuButton


def render_tasks_list(page: ft.Page, callback_main=None, callbacks_extra=None):
    """
    callback_main: función principal de refresco (opcional)
    callbacks_extra: dict con funciones extra a ejecutar (opcional)
    """

    # Tarea simulada de API
    task = {
        "id": 3,
        "title": "Tarea Ejemplo",
        "description": "Esta es una descripción de muestra",
        "state": 1,
    }

    # Campos editables
    item_to_edit = {
        "id": { "value": task["id"], "type": "identifier", "disabled": True },
        "title": { "value": task["title"], "type": "text" },
        "description": { "value": task["description"], "type": "text" },
        "state": {
            "value": task["state"],
            "type": "dropdown",
            "options": {
                0: "Pendiente",
                1: "Completada",
                2: "En progreso"
            }
        }
    }

    # Ejemplo de headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer <token>"
    }

    popup = PopupMenuButton(
        page=page,
        id=task["id"],
        item_to_edit=item_to_edit,
        alias="Tarea",
        request_url={
            "delete": {
                "url": f"https://example.com/tasks?id={task['id']}",
                "headers": headers
            },
            "edit": {
                "url": f"https://example.com/tasks?id={task['id']}",
                "headers": headers
            }
        },

        # 🔥 CALLBACK PRINCIPAL (normalmente refresca la lista)
        callback=callback_main,

        # 🔥 CALLBACKS EXTRA (opcional)
        callbacks=callbacks_extra
    )

    return ft.Column(
        controls=[
            ft.Text("Ejemplo de Lista de Tareas", size=20, weight="bold"),
            ft.ListTile(
                leading=ft.Icon(ft.icons.TASK),
                title=ft.Text(task["title"]),
                subtitle=ft.Text(task["description"]),
                trailing=popup
            )
        ]
    )
```

🟧 ¿Qué ocurre exactamente al eliminar o editar?

&nbsp;&nbsp;&nbsp; **1.** El popup envía una petición de eliminación o edición a tu API\
&nbsp;&nbsp;&nbsp; **2.** Si la API responde OK → PopupMenuButton ejecuta:

```scss
callback_main()
callbacks_extra["reload_categories"]["function"](*args)
```

Ejemplo de llamada:

✔ refresh_tasks() → para recargar la lista  
✔ refresh_categories() → para actualizar otras partes del sistema

&nbsp;&nbsp;&nbsp; **3.** Finalmente, la UI queda completamente optimizada.

⭐ Su finalidad:

- Cómo separar la lógica en varios archivos
- Cómo pasar una función desde el archivo principal
- Cómo recibirla y usarla en el componente
- Cómo usar callbacks avanzados
- Cómo escribir funciones sin argumentos
- Cómo refrescar la UI tras acciones

⚠️ ERRORES COMUNES A EVITAR

- No pases callbacks que requieran parámetros. Todas las funciones deben ser def func(): ...
- Asegúrate de que tu API devuelva una respuesta JSON válida.
- Si item_to_edit es None, la edición estará deshabilitada.
- Si request_url es None, los botones de eliminar/editar no harán nada.
- La clave options solo es para dropdowns.

🧾 Licencia

Licencia MIT.

❤️ ¡Contribuciones bienvenidas!

Abre un pull request o issue en GitHub.
¡Se aceptan sugerencias y mejoras!

---

# 🚀 ¿Quieres también **badges** para PyPI?

Se pueden añadir:

- ✔ Versión PyPI
- ✔ Versiones de Python
- ✔ Estado Wheel
- ✔ Contador de descargas
- ✔ Badge de licencia
- ✔ SO soportados

Solo di:

👉 **“Pon badges también”**
