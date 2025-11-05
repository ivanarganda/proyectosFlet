import flet as ft
import random
import time
import threading
from helpers.utils import addElementsPage, notify_error, notify_success


# =========================
# CONFIGURACIÓN PRINCIPAL
# =========================
GRID_WIDTH = 10
GRID_HEIGHT = 20
CELL_SIZE = 28
COLORS = ["#38bdf8", "#f97316", "#a855f7", "#22c55e", "#eab308", "#ef4444", "#14b8a6"]


# =========================
# FORMAS DE TETRIS
# =========================
SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[1, 1], [1, 1]],  # O
    [[0, 1, 0], [1, 1, 1]],  # T
    [[1, 1, 0], [0, 1, 1]],  # S
    [[0, 1, 1], [1, 1, 0]],  # Z
    [[1, 0, 0], [1, 1, 1]],  # J
    [[0, 0, 1], [1, 1, 1]],  # L
]


class TetrisGame(ft.UserControl):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.current_shape = None
        self.current_pos = [0, GRID_WIDTH // 2 - 1]
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.running = False
        self.lock = threading.Lock()
        self.color = random.choice(COLORS)
        self.cells = []

        # =========================
        # TEXTOS DE ESTADÍSTICAS
        # =========================
        self.txt_title = ft.Text("🧩 TETRIS MODERN", size=28, weight="bold", color="#38bdf8")
        self.txt_score = ft.Text("🏆 Score: 0", size=18, color="#e2e8f0")
        self.txt_level = ft.Text("⚙️ Level: 1", size=18, color="#e2e8f0")
        self.txt_lines = ft.Text("📏 Lines: 0", size=18, color="#e2e8f0")

        self.btn_start = ft.ElevatedButton(
            "▶️ START GAME",
            bgcolor="#38bdf8",
            color="white",
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
            on_click=self.start_game,
        )

    # =========================
    # LÓGICA DE JUEGO
    # =========================
    def start_game(self, e=None):
        if self.running:
            return
        self.reset_game()
        self.running = True
        self.spawn_new_shape()
        threading.Thread(target=self.game_loop, daemon=True).start()
        notify_success(self.page, "Game Started 🎮")

    def reset_game(self):
        self.grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.update_labels()
        self.refresh_grid()

    def spawn_new_shape(self):
        self.current_shape = random.choice(SHAPES)
        self.color = random.choice(COLORS)
        self.current_pos = [0, GRID_WIDTH // 2 - len(self.current_shape[0]) // 2]
        if not self.is_valid_position(self.current_shape, self.current_pos):
            self.running = False
            self.show_game_over()

    def rotate_shape(self):
        rotated = [list(row) for row in zip(*self.current_shape[::-1])]
        if self.is_valid_position(rotated, self.current_pos):
            self.current_shape = rotated

    def move_shape(self, dx, dy):
        new_pos = [self.current_pos[0] + dy, self.current_pos[1] + dx]
        if self.is_valid_position(self.current_shape, new_pos):
            self.current_pos = new_pos
        elif dy == 1:
            self.place_shape()
            self.clear_lines()
            self.spawn_new_shape()

    def is_valid_position(self, shape, pos):
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell:
                    new_x = pos[1] + x
                    new_y = pos[0] + y
                    if new_x < 0 or new_x >= GRID_WIDTH or new_y >= GRID_HEIGHT:
                        return False
                    if new_y >= 0 and self.grid[new_y][new_x]:
                        return False
        return True

    def place_shape(self):
        for y, row in enumerate(self.current_shape):
            for x, cell in enumerate(row):
                if cell:
                    self.grid[self.current_pos[0] + y][self.current_pos[1] + x] = self.color

    def clear_lines(self):
        full_rows = [i for i, row in enumerate(self.grid) if all(row)]
        for i in full_rows:
            del self.grid[i]
            self.grid.insert(0, [0 for _ in range(GRID_WIDTH)])
        if full_rows:
            lines = len(full_rows)
            self.lines_cleared += lines
            self.score += 100 * lines
            if self.lines_cleared // 10 >= self.level:
                self.level += 1
            self.update_labels()

    def update_labels(self):
        self.txt_score.value = f"🏆 Score: {self.score}"
        self.txt_level.value = f"⚙️ Level: {self.level}"
        self.txt_lines.value = f"📏 Lines: {self.lines_cleared}"
        self.page.update()

    def show_game_over(self):
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("💀 Game Over", size=24, weight="bold"),
            content=ft.Text(f"Final Score: {self.score}", size=18),
            actions=[
                ft.TextButton("🔁 Play Again", on_click=lambda e: self.start_game()),
                ft.TextButton("🏠 Exit", on_click=lambda e: self.page.go("/menu")),
            ],
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def game_loop(self):
        while self.running:
            with self.lock:
                self.move_shape(0, 1)
                self.refresh_grid()
            time.sleep(max(0.3 - (self.level * 0.02), 0.05))

    # =========================
    # RENDERIZADO
    # =========================
    def refresh_grid(self):
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                color = "#0f172a"
                if self.grid[y][x]:
                    color = self.grid[y][x]
                self.cells[y][x].bgcolor = color

        # Dibujar la pieza activa
        if self.current_shape:
            for y, row in enumerate(self.current_shape):
                for x, cell in enumerate(row):
                    if cell:
                        grid_x = self.current_pos[1] + x
                        grid_y = self.current_pos[0] + y
                        if 0 <= grid_x < GRID_WIDTH and 0 <= grid_y < GRID_HEIGHT:
                            self.cells[grid_y][grid_x].bgcolor = self.color
        self.update()

    def build_grid(self):
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
            self.cells.append(row)
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

    def on_key_press(self, e: ft.KeyboardEvent):
        if not self.running:
            return
        key = e.key.lower()
        if key == "arrowleft":
            self.move_shape(-1, 0)
        elif key == "arrowright":
            self.move_shape(1, 0)
        elif key == "arrowdown":
            self.move_shape(0, 1)
        elif key == "arrowup":
            self.rotate_shape()
        self.refresh_grid()

    def build(self):
        self.page.on_keyboard_event = self.on_key_press

        controls_row = ft.Row(
            [
                ft.IconButton(ft.Icons.ARROW_LEFT, icon_color="#38bdf8", on_click=lambda e: self.move_shape(-1, 0)),
                ft.IconButton(ft.Icons.ARROW_UPWARD, icon_color="#22c55e", on_click=lambda e: self.rotate_shape()),
                ft.IconButton(ft.Icons.ARROW_RIGHT, icon_color="#38bdf8", on_click=lambda e: self.move_shape(1, 0)),
                ft.IconButton(ft.Icons.ARROW_DOWNWARD, icon_color="#facc15", on_click=lambda e: self.move_shape(0, 1)),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )

        stats_panel = ft.Container(
            content=ft.Column(
                [self.txt_score, self.txt_level, self.txt_lines],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=4,
            ),
            bgcolor="#1e293b",
            padding=10,
            border_radius=12,
            shadow=ft.BoxShadow(blur_radius=15, color="#000000"),
        )

        panel = ft.Column(
            [
                self.txt_title,
                ft.Divider(height=5, color="transparent"),
                stats_panel,
                ft.Divider(height=10, color="transparent"),
                self.build_grid(),
                ft.Divider(height=10, color="transparent"),
                self.btn_start,
                ft.Divider(height=5, color="transparent"),
                controls_row,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
        )

        # Fondo degradado dinámico tipo “OmniMind”
        return ft.Container(
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
                content=panel,
            ),
        )


# =====================================================
# FUNCIÓN DE ENTRADA
# =====================================================
def render_tetris(page: ft.Page):
    try:
        page.title = "🧩 Tetris Modern"
        page.bgcolor = "#0f172a"
        page.window_width = 600
        page.window_height = 1200
        game = TetrisGame(page)
        return addElementsPage(page, [game])
    except Exception as e:
        notify_error(page, f"Error loading Tetris: {e}")