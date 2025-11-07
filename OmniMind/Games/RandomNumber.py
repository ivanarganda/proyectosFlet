import os
import flet as ft
import random, time, threading
from helpers.utils import (
    addElementsPage,
    loadSnackbar,
    notify_success,
    notify_error,
    get_timestamp,
    log_error,
)
from footer_navegation.navegation import footer_navbar
from middlewares.auth import middleware_auth

current_path = {
    "path": os.path.abspath(__file__),
    "folder": os.path.dirname(os.path.abspath(__file__)).split("\\")[-1],
    "file": __file__.split("\\")[-1],
}


def renderGameRandomNumber(page: ft.Page, scores):
    try:
        middleware_auth(page)
        page.title = "🎯 Random Number Battle"
        page.window_width = 450
        page.window_height = 900
        page.window_resizable = False
        page.bgcolor = "#0f172a"
        page.padding = 0
        page.scroll = "adaptive"

        # ========================
        # DATOS DEL JUGADOR
        # ========================
        [data] = scores.get("message", None)
        if data is None:
            page.go("/menu")

        score = data.get("score", 0)
        level = data.get("level", 1)
        duration_seconds = data.get("duration_seconds", 0)
        last_played = data.get("last_played", "")
        lines_cleared = data.get("lines_cleared", 0)  # mantenemos por consistencia

        # ========================
        # VARIABLES DEL JUEGO
        # ========================
        total_rounds = 5
        round_num = 1
        ai_score = 0
        target = random.randint(1, 10)
        start_time = time.time()
        time_limit = 60
        game_running = False
        paused = False
        stop_thread = threading.Event()
        dlg = None

        # ========================
        # INTERFAZ
        # ========================
        title = ft.Text("Logic Battle", size=16, color="#94a3b8")
        headline = ft.Text("Random Number Battle 🤖", size=30, weight="bold", color="#f1f5f9")
        subtitle = ft.Text(
            "Try to beat the AI guessing numbers between 1 and 10!",
            size=15,
            color="#a1a1aa",
            text_align="center",
        )

        txt_round = ft.Text(f"Round {round_num}/{total_rounds}", size=18, weight="bold", color="#f8fafc")
        txt_timer = ft.Text("⏱️ 01:00", size=18, weight="bold", color="#f8fafc")
        txt_feedback = ft.Text("", size=18, text_align="center", color="#f8fafc")
        txt_score = ft.Text(f"🧍 You: {score} | 🤖 AI: {ai_score}", size=18, weight="bold", color="#38bdf8")

        txt_last_played = ft.Text(f"📅 Last played: {last_played}", size=12, color="#94a3b8")
        txt_duration = ft.Text(f"⏱️ Time played: {int(duration_seconds)}s", size=12, color="#94a3b8")

        input_guess = ft.TextField(
            label="Enter a number (1-10)",
            width=220,
            height=50,
            text_align="center",
            border_radius=18,
            bgcolor="#f8fafc",
            border_color="#cbd5e1",
            color="#0f172a",
        )

        progress = ft.ProgressBar(width=250, color="#38bdf8", value=0)

        # ========================
        # FUNCIONES AUXILIARES
        # ========================
        def update_timer():
            """Cronómetro en hilo separado"""
            def tick():
                nonlocal game_running, paused
                while game_running and not stop_thread.is_set():
                    if not paused:
                        elapsed = time.time() - start_time
                        remaining = max(0, time_limit - elapsed)
                        mins, secs = divmod(int(remaining), 60)
                        txt_timer.value = f"⏱️ {mins:02}:{secs:02}"
                        progress.value = elapsed / time_limit
                        try:
                            page.update()
                        except:
                            break
                        if remaining <= 0:
                            end_game()
                            break
                    time.sleep(1)
            threading.Thread(target=tick, daemon=True).start()

        def ai_turn():
            nonlocal ai_score
            ai_guess = random.randint(1, 10)
            if ai_guess == target:
                ai_score += 1
                txt_feedback.value = "🤖 AI guessed correctly! (+1 point)"
                notify_error(page, "AI scored a point!")
            else:
                txt_feedback.value = "🤖 AI missed this round."
            txt_score.value = f"🧍 You: {score} | 🤖 AI: {ai_score}"
            page.update()

        def next_round():
            nonlocal round_num, target
            round_num += 1
            if round_num > total_rounds:
                end_game()
                return
            target = random.randint(1, 10)
            txt_round.value = f"Round {round_num}/{total_rounds}"
            txt_feedback.value = "🎲 New round started!"
            input_guess.value = ""
            page.update()

        def save_scores():
            """Guarda puntuación actual en DB"""
            print(f"💾 Guardando... Score={score}, Level={level}, Duration={int(time.time() - start_time)}s")
            notify_success(page, "Progress saved 💾")

        def reset_game(e=None):
            """Reinicia todo el juego"""
            nonlocal round_num, score, ai_score, target, start_time, game_running, paused
            stop_thread.set()
            paused = False
            game_running = False
            time.sleep(0.2)
            stop_thread.clear()

            round_num = 1
            score = 0
            ai_score = 0
            target = random.randint(1, 10)
            start_time = time.time()

            txt_round.value = f"Round {round_num}/{total_rounds}"
            txt_feedback.value = ""
            txt_score.value = f"🧍 You: {score} | 🤖 AI: {ai_score}"
            progress.value = 0
            input_guess.value = ""

            if page.dialog:
                try:
                    page.dialog.open = False
                    page.update()
                except:
                    pass

            game_running = True
            notify_success(page, "🔁 New game started!")
            update_timer()
            page.update()

        def end_game():
            nonlocal game_running, duration_seconds, last_played
            game_running = False
            stop_thread.set()
            elapsed = round(time.time() - start_time, 2)
            duration_seconds += elapsed
            last_played = get_timestamp()

            result_text = (
                f"🏁 Game Over!\n\n🧍 You: {score}\n🤖 AI: {ai_score}\n\n⏱️ Duration: {elapsed}s"
            )
            save_scores()

            content = ft.Column(
                [
                    ft.Text("💀 GAME OVER", size=26, weight="bold", color="#f87171", text_align="center"),
                    ft.Divider(height=10, color="transparent"),
                    ft.Text(result_text, size=18, color="#e2e8f0", text_align="center"),
                    ft.Divider(height=15, color="transparent"),
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "🔁 Play Again",
                                icon=ft.Icons.PLAY_ARROW,
                                bgcolor="#38bdf8",
                                color="white",
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                                on_click=reset_game,
                            ),
                            ft.ElevatedButton(
                                "💾 Save Progress",
                                icon=ft.Icons.SAVE,
                                bgcolor="#22c55e",
                                color="white",
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                                on_click=lambda e: save_scores(),
                            ),
                            ft.ElevatedButton(
                                "🏠 Exit",
                                icon=ft.Icons.EXIT_TO_APP,
                                bgcolor="#ef4444",
                                color="white",
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                                on_click=lambda e: page.go("/menu"),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
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

        def check_guess(e):
            nonlocal score, target
            if not game_running or paused:
                return
            try:
                guess = int(input_guess.value)
            except ValueError:
                loadSnackbar(page, "⚠️ Enter a valid number!", "red")
                return

            if not (1 <= guess <= 10):
                loadSnackbar(page, "⚠️ Number must be between 1 and 10.", "orange")
                return

            if guess == target:
                score += 1
                txt_feedback.value = random.choice(["🎯 Perfect!", "🔥 You nailed it!", "✨ Great shot!"])
                notify_success(page, "Correct! 🎉")
            else:
                txt_feedback.value = "❌ Wrong number!"
                notify_error(page, "Missed! 😢")

            txt_score.value = f"🧍 You: {score} | 🤖 AI: {ai_score}"
            page.update()

            ai_turn()
            threading.Timer(1.5, next_round).start()

        # ========================
        # LAYOUT FINAL
        # ========================
        btn_guess = ft.Container(
            content=ft.Row(
                [ft.Icon(ft.Icons.PLAY_ARROW, color="white"), ft.Text("Guess", color="white", size=18, weight="bold")],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            bgcolor="#38bdf8",
            border_radius=50,
            width=160,
            height=55,
            alignment=ft.alignment.center,
            shadow=ft.BoxShadow(blur_radius=15, color="#94a3b8"),
            on_click=check_guess,
        )

        card = ft.Container(
            width=380,
            bgcolor="#1e293b",
            border_radius=40,
            padding=25,
            shadow=ft.BoxShadow(spread_radius=2, blur_radius=25, color="#0f172a", offset=ft.Offset(0, 8)),
            content=ft.Column(
                [
                    title, headline, subtitle,
                    ft.Divider(height=10, color="transparent"),
                    txt_round, txt_timer, progress,
                    ft.Divider(height=10, color="transparent"),
                    input_guess, txt_feedback, txt_score, txt_duration, txt_last_played,
                    ft.Divider(height=20, color="transparent"),
                    btn_guess,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            ),
        )

        layout = ft.Row([ft.Container(content=card, alignment=ft.alignment.center)],
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER)

        footer = footer_navbar(page=page, current_path=current_path, dispatches={})
        footer.disabled = True

        stack = ft.Stack([layout, footer], expand=True)

        # === Inicia ===
        game_running = True
        update_timer()
        return addElementsPage(page, [stack])

    except Exception as e:
        log_error("renderGameRandomNumber", e)
        loadSnackbar(page, f"Error loading Random Number: {e}", "red")
