import flet as ft
from helpers.utils import loadLoader, addElementsPage, clearInputsForm, loadSnackbar, setInputField, build_color_dialog

def AddCategoryTasksForm(page: ft.Page):
    page.title = "New Category"
    page.window_width = 420
    page.window_height = 800
    page.window_resizable = False
    page.bgcolor = "#F6F4FB"

    # ---------- Estado / fields ----------
    category_name = ft.TextField(
        label="Category name",
        hint_text="Work, Personal, Study...",
    )
    icon_field = ft.TextField(
        label="Icon (emoji or text)",
        hint_text="✅ 📚 💡",
    )

    bg_color_field = ft.TextField(
        label="Background color (HEX)",
        hint_text="#5A2D9C",
        value="#F0F0FF",
    )
    text_color_field = ft.TextField(
        label="Text color (HEX)",
        hint_text="#000000",
        value="#1A1A1A",
    )

    # ---------- Preview ----------
    preview_icon = ft.Text("🔖", size=28)
    preview_title = ft.Text("Category", size=18, weight=ft.FontWeight.BOLD, color=text_color_field.value)

    preview_card = ft.Container(
        width=220,
        height=120,
        border_radius=20,
        bgcolor=bg_color_field.value,
        alignment=ft.alignment.center,
        content=ft.Column(
            [preview_icon, preview_title],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=6
        ),
        shadow=ft.BoxShadow(blur_radius=14, color=ft.colors.GREY_300),
    )

    def update_preview():
        preview_card.bgcolor = (bg_color_field.value or "#ECECEC").strip() or "#ECECEC"
        preview_icon.value = (icon_field.value or "🔖")
        preview_title.value = (category_name.value or "Category")
        preview_title.color = (text_color_field.value or "#000000").strip() or "#000000"
        preview_card.update()

    # Vincular cambios a preview
    category_name.on_change = lambda e: update_preview()
    icon_field.on_change = lambda e: update_preview()
    bg_color_field.on_change = lambda e: update_preview()
    text_color_field.on_change = lambda e: update_preview()    

    # Abrir pickers
    def open_bg_picker(e):
        def on_pick(color_hex):
            bg_color_field.value = color_hex
            bg_color_field.update()
            update_preview()
        page.dialog = build_color_dialog("Pick background color", bg_color_field.value, on_pick)
        page.dialog.open = True
        page.update()

    def open_text_picker(e):
        def on_pick(color_hex):
            text_color_field.value = color_hex
            text_color_field.update()
            update_preview()
        page.dialog = build_color_dialog("Pick text color", text_color_field.value, on_pick)
        page.dialog.open = True
        page.update()

    # ---------- Botones para abrir diálogos ----------
    bg_picker_btn = ft.IconButton(
        icon=ft.icons.COLOR_LENS, tooltip="Pick background color", on_click=open_bg_picker
    )
    text_picker_btn = ft.IconButton(
        icon=ft.icons.FORMAT_COLOR_TEXT, tooltip="Pick text color", on_click=open_text_picker
    )

    # ---------- Submit ----------
    def save_category(e):
        name = (category_name.value or "").strip()
        icon = (icon_field.value or "").strip()
        bg = (bg_color_field.value or "").strip()
        fg = (text_color_field.value or "").strip()

        if not name:
            page.snack_bar = ft.SnackBar(ft.Text("Name is required"))
            page.snack_bar.open = True
            page.update()
            return

        # Aquí llamarías a tu API /tasks/categories para guardar
        print("Saving category:")
        print("  name:", name)
        print("  icon:", icon)
        print("  bg:", bg)
        print("  text color:", fg)

        page.snack_bar = ft.SnackBar(ft.Text("Category created!"))
        page.snack_bar.open = True
        page.update()
        # page.go("/tasks")

    # ---------- Layout del formulario ----------
    form = ft.Column(
        [
            ft.Text("Preview", size=20, weight=ft.FontWeight.BOLD),
            preview_card,
            ft.Container(height=20),

            category_name,
            icon_field,

            ft.Row([bg_color_field, bg_picker_btn], spacing=10, alignment=ft.MainAxisAlignment.START),
            ft.Row([text_color_field, text_picker_btn], spacing=10, alignment=ft.MainAxisAlignment.START),

            ft.Container(height=24),
            ft.ElevatedButton(
                "Create Category",
                bgcolor="#5A2D9C",
                color="white",
                height=50,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15)),
                on_click=save_category
            ),
        ],
        spacing=12,
        alignment=ft.MainAxisAlignment.START,
    )

    # ---------- Card blanca ----------
    white_card = ft.Container(
        bgcolor="white",
        border_radius=ft.border_radius.only(top_left=40, top_right=40),
        padding=20,
        alignment=ft.alignment.top_center,
        height=650,
        content=form,
        shadow=ft.BoxShadow(blur_radius=20, color=ft.colors.GREY_300),
    )

    # ---------- Fondo ----------
    background = ft.Stack(
        [
            ft.Container(
                expand=True,
                image_src="https://raw.githubusercontent.com/ivanarganda/images_assets/main/form-wallpaper.png",
                image_fit=ft.ImageFit.COVER,
            ),
            white_card,
        ],
        expand=True,
    )

    return addElementsPage(
        page, 
        [
            background
        ]
    )
