import flet as ft

def RenderTable(title, loading_text, content_table, callback, extra_footer=None):

    return ft.Column(
        [
            # Título
            ft.Text(
                f"📊 {title}",
                size=22,
                weight="bold",
                color="white",
            ),

            ft.Container(
                height=1,
                bgcolor="#E0E0E0",
                margin=ft.margin.only(bottom=10),
            ),

            loading_text,

            # Botón recargar
            ft.Row(
                [
                    ft.TextButton(
                        "↻ Recargar datos",
                        icon=ft.Icons.REFRESH,
                        style=ft.ButtonStyle(
                            color="#1565C0",
                            overlay_color="#E3F2FD",
                        ),
                        on_click=lambda e: callback(),
                    )
                ],
                alignment=ft.MainAxisAlignment.END,
            ),

            # ========= 🔥 CONTENEDOR RESPONSIVE DE TABLA =========
            ft.Container(
                bgcolor="white",
                padding=10,
                border_radius=10,
                shadow=ft.BoxShadow(
                    blur_radius=12,
                    spread_radius=1,
                    color=ft.colors.with_opacity(0.08, "black"),
                ),
                content=ft.Column(
                    [
                        # tabla con scroll horizontal
                        ft.Row(
                            [content_table],
                            scroll=ft.ScrollMode.AUTO,  # ✔ solo scroll horizontal
                        ),

                        # paginación pegada a la tabla
                        ft.Container(
                            extra_footer,
                            padding=10,
                            alignment=ft.alignment.center
                        ) if extra_footer else ft.Container(),
                    ],
                    spacing=10,
                    expand=False
                ),
                expand=True
            )
        ],
        expand=True,
        spacing=15,
        scroll=ft.ScrollMode.AUTO
    )