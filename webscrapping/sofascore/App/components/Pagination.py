import flet as ft

def PaginationComponent(page, current_page_ref, pages_ref, callback):

    pagination_controls = ft.Row(alignment=ft.MainAxisAlignment.CENTER)

    def build_pagination():
        current_page = current_page_ref[0]
        pages = pages_ref[0]

        return ft.Row(
            [
                ft.IconButton(
                    ft.icons.ARROW_BACK,
                    disabled=current_page == 1,
                    on_click=prev_page
                ),

                ft.Row(
                    [
                        ft.Container(
                            padding=ft.padding.symmetric(horizontal=8, vertical=4),
                            bgcolor=ft.Colors.CYAN_500 if num == current_page else "transparent",
                            border_radius=8,
                            content=ft.Text(str(num)),
                            on_click=lambda e, p=num: go_to_page(p)
                        )
                        for num in range(1, pages + 1)
                    ]
                ),

                ft.IconButton(
                    ft.icons.ARROW_FORWARD,
                    disabled=current_page == pages,
                    on_click=next_page
                )
            ]
        )

    def refresh_pagination():
        pagination_controls.controls.clear()
        pagination_controls.controls.append(build_pagination())
        # ❌ NO llamar update() aquí
        # update lo hace el parent cuando se añada

    def next_page(e):
        current_page_ref[0] += 1
        callback()
        refresh_pagination()
        page.update()

    def prev_page(e):
        if current_page_ref[0] > 1:
            current_page_ref[0] -= 1
            callback()
            refresh_pagination()
            page.update()

    def go_to_page(p):
        current_page_ref[0] = p
        callback()
        refresh_pagination()
        page.update()

    # 👉 Primera construcción SÓLO de controls, sin update()
    refresh_pagination()

    return pagination_controls
