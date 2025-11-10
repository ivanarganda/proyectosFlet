import flet as ft
import random
import time
import threading
from helpers.utils import addElementsPage, notify_error, notify_success
from middlewares.auth import middleware_auth
from Games.bin.__bin_tetris import get_player_status
from params import HEADERS, REQUEST_URL

GRID_WIDTH = 13
GRID_HEIGHT = 20
CELL_SIZE = 26
COLORS = ["#38bdf8", "#f97316", "#a855f7", "#22c55e", "#eab308", "#ef4444", "#14b8a6"]

SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[1, 1], [1, 1]],  # O
    [[0, 1, 0], [1, 1, 1]],  # T
    [[1, 1, 0], [0, 1, 1]],  # S
    [[0, 1, 1], [1, 1, 0]],  # Z
    [[1, 0, 0], [1, 1, 1]],  # J
    [[0, 0, 1], [1, 1, 1]],  # L
]


def render_tetris(page: ft.Page, scores, load_scores):
    try:
        if scores.get("status") == 401 and scores.get("message") == "Unauthorized":
            handle_logout(page)

        session = middleware_auth(page)
        token = session.get("token",None)

        page.title = "🧩 Tetris Modern"
        page.bgcolor = "#0f172a"
        page.window_width = 500
        page.window_height = 850

        # =========================
        # VARIABLES GLOBALES
        # =========================
        grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        current_shape = None
        current_pos = [0, GRID_WIDTH // 2 - 1]
        color = random.choice(COLORS)

        [data] = scores.get("message", None)
        if data is None:
            page.go("/menu")

        score = data.get("score")
        level = data.get("level")
        prestige = data.get("prestige")

        lines_cleared = data.get("lines_cleared")

        running = False
        paused = False
        lock = threading.Lock()
        cells = []

        btn_pause = None
        btn_start = None

        fall_speed = 0.3
        thread_stop_event = threading.Event()
        game_thread = None
        dlg = None

        # =========================
        # FUNCIONES AUXILIARES
        # =========================
        def stop_game_thread():
            """Detiene el hilo principal del juego de forma segura"""
            nonlocal game_thread, running
            running = False
            thread_stop_event.set()
            if game_thread and game_thread.is_alive():
                game_thread.join(timeout=0.5)
            thread_stop_event.clear()
            game_thread = None

        def is_valid_position(shape, pos):
            for y, row in enumerate(shape):
                for x, cell in enumerate(row):
                    if cell:
                        new_x = pos[1] + x
                        new_y = pos[0] + y
                        if new_x < 0 or new_x >= GRID_WIDTH or new_y >= GRID_HEIGHT:
                            return False
                        if new_y >= 0 and grid[new_y][new_x]:
                            return False
            return True

        def spawn_new_shape():
            nonlocal current_shape, current_pos, color, running
            current_shape = random.choice(SHAPES)
            color = random.choice(COLORS)
            current_pos = [0, GRID_WIDTH // 2 - len(current_shape[0]) // 2]
            if not is_valid_position(current_shape, current_pos):
                running = False
                show_game_over()

        def rotate_shape():
            nonlocal current_shape
            rotated = [list(row) for row in zip(*current_shape[::-1])]
            if is_valid_position(rotated, current_pos):
                current_shape = rotated

        def place_shape():
            for y, row in enumerate(current_shape):
                for x, cell in enumerate(row):
                    if cell:
                        grid[current_pos[0] + y][current_pos[1] + x] = color

        def clear_lines():
            nonlocal grid, score, lines_cleared, level, fall_speed, prestige
            full_rows = [i for i, row in enumerate(grid) if all(row)]
            for i in full_rows:
                del grid[i]
                grid.insert(0, [0 for _ in range(GRID_WIDTH)])
            if full_rows:
                lines = len(full_rows)
                lines_cleared += lines
                score += 100 * lines

                try:
                    if prestige is None or not isinstance(prestige, int):
                        prestige = 1
                    level_data = get_player_status(
                        prestige=prestige,                # el prestigio actual del jugador
                        score=score,               # puntuación total acumulada
                        file="tetris_levels.json"  # tu archivo de configuración
                    )

                    level, prestige_temp, low, high, score_local, progress_level, progress_global, global_score, title = level_data
                    prestige = prestige_temp  # ✅ actualiza el valor global

                    # mostrar progreso visual o debug
                    print(f"[DEBUG] Prestige {prestige} | Level {level} | {score_local}/{high} ({progress_level}%)")

                    txt_prestige.value = f"🏅 Prestige {prestige}"
                    txt_level.value = f"⚙️ Level {level} ({progress_level}%)"
                    txt_score.value = f"🏆 {score_local} / {high} pts"
                    txt_global.value = f"🌐 Global {progress_global}%"
                    progress_bar.value = progress_level / 100.0


                except Exception as ex:
                    print(f"[ERROR LEVEL SYSTEM] {ex}")
                
                if lines_cleared // 5 >= level:
                    level += 1
                    fall_speed = max(0.05, fall_speed - 0.02)
                update_labels()

        def move_shape(dx, dy):
            nonlocal current_pos
            new_pos = [current_pos[0] + dy, current_pos[1] + dx]
            if is_valid_position(current_shape, new_pos):
                current_pos = new_pos
            elif dy == 1:
                place_shape()
                clear_lines()
                spawn_new_shape()

        def reset_game():
            import asyncio
            nonlocal grid, score, level, lines_cleared, fall_speed, data, prestige, token

            grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]

            try:
                data = asyncio.run(load_scores(2, token, page))
                if not data or data.get("error"):
                    notify_error(page, "❌ Error loading scores, starting new game.")
                    data = {"score": 0, "level": 1, "prestige": 1, "lines_cleared": 0}
            except Exception as ex:
                print(f"[RESET ERROR] {ex}")
                data = {"score": 0, "level": 1, "prestige": 1, "lines_cleared": 0}

            [data] = scores.get("message", None)

            score = data.get("score", 0)
            level = data.get("level", 1)
            prestige = data.get("prestige", 1)
            lines_cleared = data.get("lines_cleared", 0)
            fall_speed = 0.3

            update_labels()
            refresh_grid()

        def save_scores():
            import asyncio, requests_async

            async def s_score():
                nonlocal token
                headers = HEADERS.copy()

                if not token:
                    notify_error(page, "⚠️ No hay sesión válida. Inicia sesión nuevamente.")
                    return {"status": 401, "message": "Unauthorized"}

                headers["Authorization"] = f"Bearer {token}"        

                json_data = {
                    "prestige": prestige,
                    "level": level,
                    "score": score,
                    "lines_cleared": lines_cleared,
                }

                try:
                    response = await requests_async.put(
                        f"{REQUEST_URL}/games/scores?id=2",
                        headers=headers,
                        json=json_data,
                        timeout=10  # evita bloqueos si el servidor no responde
                    )

                    # si el servidor responde sin JSON (error HTML)
                    try:
                        return response.json()
                    except Exception:
                        return {"status": response.status_code, "message": response.text}

                except Exception as ex:
                    return {"status": 500, "message": f"Network error: {ex}"}

            res = asyncio.run(s_score())

            if res.get("status") == 201:
                notify_success(page, res.get("message", "Progress saved") + " 💾")
                time.sleep(1)
                page.go('/menu')
            else:
                msg = res.get("message", "Unable to save progress! ❌")
                notify_error(page, f"{msg} (status {res.get('status')})")



        def update_labels():
            """Actualiza los labels con datos reales del jugador"""
            nonlocal prestige
            print( prestige )
            try:
                level_data = get_player_status(
                    prestige=prestige, score=score, file="tetris_levels.json"
                )
                level, prestige, low, high, score_local, progress_level, progress_global, global_score, title = level_data

                # Textos principales
                txt_prestige.value = f"🏅 Prestige {prestige}"
                txt_level.value = f"⚙️ Level {level} ({progress_level}%)"
                txt_score.value = f"🏆 {score_local} / {high} pts"
                txt_global.value = f"🌐 Global {progress_global}%"

                # Barra de progreso
                progress_bar.value = progress_level / 100.0

            except Exception as ex:
                print(f"[HUD ERROR] {ex}")

            page.update()

        def show_game_over(e=None):
            global dlg
            content = ft.Column(
                [
                    ft.Text("💀 GAME OVER", size=26, weight="bold", color="#f87171", text_align=ft.TextAlign.CENTER),
                    ft.Divider(height=10, color="transparent"),
                    ft.Text(f"🏆 Final Score: {score}", size=18, color="#e2e8f0"),
                    ft.Text(f"⚙️ Level Reached: {level}", size=16, color="#94a3b8"),
                    ft.Text(f"📏 Lines Cleared: {lines_cleared}", size=16, color="#94a3b8"),
                    ft.Divider(height=20, color="transparent"),
                    ft.Row(
                        [
                            ft.ElevatedButton("🔁 Play Again", icon=ft.Icons.PLAY_ARROW,
                                bgcolor="#38bdf8", color="white",
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                                on_click=lambda _:restart_game()),
                            ft.ElevatedButton("💾 Save Progress", icon=ft.Icons.SAVE,
                                bgcolor="#22c55e", color="white",
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                                on_click=lambda e: save_scores()),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    ft.Row(
                        [
                            ft.ElevatedButton("▶️ Resume Game", icon=ft.Icons.PLAY_CIRCLE,
                                bgcolor="#0ea5e9", color="white",
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                                on_click=resume_game),
                            ft.ElevatedButton("🏠 Exit", icon=ft.Icons.EXIT_TO_APP,
                                bgcolor="#ef4444", color="white",
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                                on_click=exit_game),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
            )

            dlg = ft.AlertDialog(
                modal=True,
                shape=ft.RoundedRectangleBorder(radius=20),
                bgcolor=ft.colors.with_opacity(0.15, "#0f172a"),
                content_padding=20,
                inset_padding=ft.padding.all(30),
                content=ft.Container(
                    width=360,
                    padding=20,
                    border_radius=20,
                    gradient=ft.LinearGradient(
                        colors=["#1e293b", "#334155", "#0f172a"],
                        begin=ft.Alignment(0, -1),
                        end=ft.Alignment(0, 1),
                    ),
                    shadow=ft.BoxShadow(blur_radius=25, color="#000000"),
                    content=content,
                ),
            )

            page.dialog = dlg
            dlg.open = True
            page.update()

        def refresh_grid():
            for y in range(GRID_HEIGHT):
                for x in range(GRID_WIDTH):
                    color_ = "#0f172a"
                    if grid[y][x]:
                        color_ = grid[y][x]
                    cells[y][x].bgcolor = color_
            if current_shape:
                for y, row in enumerate(current_shape):
                    for x, cell in enumerate(row):
                        if cell:
                            gx = current_pos[1] + x
                            gy = current_pos[0] + y
                            if 0 <= gx < GRID_WIDTH and 0 <= gy < GRID_HEIGHT:
                                cells[gy][gx].bgcolor = color
            page.update()

        def build_grid():
            grid_controls = []
            for y in range(GRID_HEIGHT):
                row = []
                for x in range(GRID_WIDTH):
                    cell = ft.Container(
                        width=CELL_SIZE,
                        height=CELL_SIZE,
                        bgcolor="#0f172a",
                        border_radius=5,
                        border=ft.border.all(1, "#1e293b"),
                        shadow=ft.BoxShadow(blur_radius=5, color="#000000", spread_radius=0.3),
                    )
                    row.append(cell)
                cells.append(row)
                grid_controls.append(ft.Row(row, spacing=1))
            return ft.Container(
                content=ft.Column(grid_controls, spacing=1),
                border_radius=12,
                padding=6,
                gradient=ft.LinearGradient(
                    colors=["#1e293b", "#334155", "#0f172a"],
                    begin=ft.Alignment(0, -1),
                    end=ft.Alignment(0, 1),
                ),
                shadow=ft.BoxShadow(blur_radius=20, color="#000000"),
            )

        def on_key_press(e: ft.KeyboardEvent):
            if not running:
                return
            key = e.key.lower()
            if key == "a":
                move_shape(-1, 0)
            elif key == "d":
                move_shape(1, 0)
            elif key == "s":
                move_shape(0, 1)
            elif key == "w":
                rotate_shape()
            refresh_grid()

        def game_loop():
            nonlocal running, paused
            try:
                while running and not thread_stop_event.is_set():
                    if not paused:
                        with lock:
                            move_shape(0, 1)
                            refresh_grid()
                        time.sleep(fall_speed)
                    else:
                        time.sleep(0.1)
            except Exception as ex:
                print(f"[ERROR EN LOOP] {ex}")
                running = False
                show_game_over()

        def restart_game():
            nonlocal running, paused
            try:
                paused = False
                running = False
                thread_stop_event.set()

                # ✅ Cerrar correctamente el diálogo si existe
                if page.dialog:
                    try:
                        page.dialog.open = False
                        page.update()
                    except Exception:
                        pass  # en caso de que no tenga .open disponible

                time.sleep(0.1)

                # ✅ Reiniciar estado del juego
                reset_game()
                thread_stop_event.clear()
                running = True
                spawn_new_shape()

                notify_success(page, "🔁 New game started!")

                # ✅ Lanzar un hilo limpio del bucle de caída
                threading.Thread(target=game_loop, daemon=True).start()

                # ✅ Refrescar botones
                btn_start.visible = False
                btn_pause.visible = True
                page.update()

            except Exception as ex:
                notify_error(page, f"Error restarting: {ex}")

        def start_game(e=None):
            nonlocal running, game_thread, paused
            paused = False
            thread_stop_event.clear()
            running = True
            reset_game()
            spawn_new_shape()
            notify_success(page, "Game started 🎮")

            if game_thread and game_thread.is_alive():
                thread_stop_event.set()
                time.sleep(0.1)

            game_thread = threading.Thread(target=game_loop, daemon=True)
            game_thread.start()

            btn_start.visible = False
            btn_pause.visible = True
            page.update()

        def pause_game(e=None):
            nonlocal paused
            paused = True
            show_game_over()

        def resume_game(e=None):
            nonlocal paused, running
            if not running:
                return
            paused = False
            running = True
            if page.dialog and page.dialog.open:
                page.dialog.open = False
                page.update()
            notify_success(page, "Game resumed ▶️")

        def exit_game(e=None):
            nonlocal running
            running = False
            thread_stop_event.set()
            notify_success(page, "Game exited 🚪")
            page.go("/menu")

        # =========================
        # INTERFAZ DE USUARIO
        # =========================
        page.on_keyboard_event = on_key_press

        hidden_input = ft.TextField(visible=False, autofocus=True, on_blur=lambda e: e.control.focus())
        page.overlay.append(hidden_input)


        txt_title = ft.Text("🧩 TETRIS MODERN", size=28, weight="bold", color="#38bdf8")

        level_data = get_player_status(
            prestige=prestige,                # el prestigio actual del jugador
            score=score,               # puntuación total acumulada
            file="tetris_levels.json"  # tu archivo de configuración
        )

        level, prestige_temp, low, high, score_local, progress_level, progress_global, global_score, title = level_data

        # Barra de progreso visual para el nivel
        progress_bar = ft.ProgressBar(
            value=0,            # 0 a 1
            bar_height=6,
            bgcolor="#1e293b",
            color="#38bdf8",
            border_radius=ft.border_radius.all(10),
            expand=True,
        )

        btn_start = ft.ElevatedButton(
            "▶️ START GAME",
            bgcolor="#38bdf8",
            color="white",
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
            on_click=start_game,
        )

        btn_pause = ft.ElevatedButton(
            "🚪 EXIT",
            bgcolor="#ef4444",
            color="white",
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
            on_click=pause_game,
            visible=False,
        )

        controls_row = ft.Row(
            [
                ft.IconButton(ft.Icons.ARROW_LEFT, icon_color="#38bdf8", on_click=lambda e: move_shape(-1, 0)),
                ft.IconButton(ft.Icons.ARROW_UPWARD, icon_color="#22c55e", on_click=lambda e: rotate_shape()),
                ft.IconButton(ft.Icons.ARROW_RIGHT, icon_color="#38bdf8", on_click=lambda e: move_shape(1, 0)),
                ft.IconButton(ft.Icons.ARROW_DOWNWARD, icon_color="#facc15", on_click=lambda e: move_shape(0, 1)),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )

        txt_prestige = ft.Text(f"🏅 Prestige {prestige}", size=15, weight="bold", color="#facc15")
        txt_level = ft.Text(f"⚙️ Level {level} ({progress_level}%)", size=16, color="#e2e8f0")
        txt_score = ft.Text(f"🏆 {score_local} / {high} pts", size=16, color="#e2e8f0")
        txt_global = ft.Text(f"🌐 Global {progress_global}%", size=14, color="#94a3b8")

        stats_panel = ft.Container(
            content=ft.Column(
                [
                    ft.Row([txt_prestige, txt_level],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    progress_bar,
                    ft.Row([txt_score, txt_global],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ],
                spacing=5,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            bgcolor="#1e293b",
            padding=12,
            border_radius=15,
            shadow=ft.BoxShadow(blur_radius=20, color="#000000"),
        )

        layout = ft.Column(
            [txt_title, stats_panel, build_grid(), btn_start, btn_pause, controls_row],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.START,
            spacing=10,
        )

        # Barra de progreso
        progress_bar.value = progress_level / 100.0

        container = ft.Container(
            expand=True,
            alignment=ft.alignment.center,
            gradient=ft.RadialGradient(
                center=ft.Alignment(0, -0.5),
                radius=1.2,
                colors=["#0f172a", "#1e293b", "#0f172a"],
            ),
            content=ft.Container(
                width=400,
                padding=20,
                border_radius=20,
                shadow=ft.BoxShadow(blur_radius=35, color="#000000"),
                content=layout,
            ),
        )

        return addElementsPage(page, [container])

    except Exception as e:
        notify_error(page, f"Error loading Tetris: {e}")
        # ✅ Devolver un contenedor de error para evitar el NoneType
        return addElementsPage( page,  ft.Container(
            content=ft.Column(
                [
                    ft.Text("❌ Error loading Tetris", color="red", size=18),
                    ft.Text(str(e), color="white", size=14),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )
        )
