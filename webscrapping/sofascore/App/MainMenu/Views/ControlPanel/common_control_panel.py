files_column = ft.Column(scroll="auto", spacing=6)
# ================================================================
# LISTA DE FICHEROS _db
# ================================================================
def get_db_files():
    try:
        r = requests.get(f"{REQUEST_URL}/files/db", timeout=5)
        if r.status_code == 200:
            return r.json().get("files", [])
    except Exception as ex:
        log(f"Error cargando ficheros: {ex}", "error")
    return []


def refresh_files():
    files_column.controls.clear()
    for f in get_db_files():
        files_column.controls.append(
            ft.Container(
                content=ft.Text(f"📄 {f}", size=14),
                padding=10,
                bgcolor=ft.colors.GREY_100,
                border_radius=8
            )
        )
    log("Ficheros actualizados")
    page.update()


    refresh_files()