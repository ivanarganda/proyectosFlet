import flet as ft

def Heading(
    text: str,
    level: int = 1,
    color: str = "#1B2453",
    align: str = "left",
    weight: ft.FontWeight = ft.FontWeight.BOLD,
    margin: int = 0
):
    # Tamaños estilo H1-H6
    sizes = {
        1: 28,
        2: 24,
        3: 20,
        4: 18,
        5: 16,
        6: 14,
    }

    variants = {
        "primary": "#1B2453",
        "secondary": "#64748b",
        "success": "#3DCAB0",
        "danger": "#ff5a5a"
    }

    # Asegurarte que no explote con level inválido
    size = sizes.get(level, 16)
    color = variants.get(color, color)

    return ft.Container(
        padding=ft.padding.all(margin),
        content=ft.Text(
            text,
            size=size,
            weight=weight,
            color=color,
            text_align=align,
        )
    )
