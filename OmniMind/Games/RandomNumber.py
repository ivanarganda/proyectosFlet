import os
import flet as ft
import random, time, threading
import datetime
from datetime import datetime
from helpers.utils import (
    addElementsPage,
    loadSnackbar,
    notify_success,
    notify_error,
    animate_bounce,
    get_timestamp,
    log_error,
)
from footer_navegation.navegation import footer_navbar

current_path = {
    "path": os.path.abspath(__file__),
    "folder": os.path.dirname(os.path.abspath(__file__)).split("\\")[-1],
    "file": __file__.split("\\")[-1],
}

def renderGameRandomNumber(page: ft.Page, on_end_callback=None):
    try:
        page.title = "🎯 Random Number Battle"
        page.window_width = 450
        page.window_height = 900
        page.window_resizable = False
        page.bgcolor = "#000000"
        page.padding = 0
        page.scroll = "adaptive"

        # === VARIABLES DEL JUEGO ===
        total_rounds = 5
        round_num = 1
        score = 0
        ai_score = 0
        target = random.randint(1, 10)
        start_time = time.time()
        time_limit = 60
        game_running = True

        # === ELEMENTOS UI ===
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

        # === FUNCIONES ===
        def update_timer():
            """Usa threading para simular un cronómetro sin async ni Timer"""
            def tick():
                nonlocal game_running
                while game_running:
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
                txt_feedback.value = f"🤖 AI guessed {ai_guess}! (+1 point)"
                notify_error(page, "AI scored a point!")
            else:
                txt_feedback.value = f"🤖 AI tried {ai_guess}... failed."
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

        def end_game():
            nonlocal game_running
            game_running = False
            elapsed = round(time.time() - start_time, 2)
            result_text = (
                f"Game Over!\n\n🧍 You: {score}\n🤖 AI: {ai_score}\n\n⏱️ Duration: {elapsed}s"
            )
            result = {
                "game": "random_number",
                "score": score,
                "ai_score": ai_score,
                "time": get_timestamp(),
                "duration": elapsed,
            }
            if on_end_callback:
                on_end_callback(result)

            dlg = ft.AlertDialog(
                modal=True,
                title=ft.Text("🏁 Final Results", weight="bold"),
                content=ft.Text(result_text, size=16),
                actions=[
                    ft.TextButton("🔁 Play Again", on_click=lambda e: page.go("/games/random")),
                    ft.TextButton("🏠 Menu", on_click=lambda e: page.go("/games_menu")),
                ],
            )
            page.dialog = dlg
            dlg.open = True
            page.update()

        def check_guess(e):
            nonlocal score, target
            if not game_running:
                return
            try:
                if not input_guess.value.strip():
                    loadSnackbar(page, "⚠️ Enter a number!", "red")
                    return
                guess = int(input_guess.value)
            except ValueError:
                loadSnackbar(page, "⚠️ Only numbers allowed.", "red")
                return

            if not (1 <= guess <= 10):
                loadSnackbar(page, "Number must be between 1 and 10.", "red")
                return

            if guess == target:
                score += 1
                txt_feedback.value = random.choice(["🎯 Perfect!", "🔥 You nailed it!", "✨ Great shot!"])
                notify_success(page, "Correct! 🎉")
                animate_bounce(txt_feedback)
            else:
                txt_feedback.value = f"❌ Wrong! It was {target}."
                notify_error(page, "Missed! 😢")

            txt_score.value = f"🧍 You: {score} | 🤖 AI: {ai_score}"
            page.update()

            ai_turn()
            threading.Timer(1.5, next_round).start()

        # === BOTÓN PRINCIPAL ===
        btn_guess = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.PLAY_ARROW, color="white"),
                    ft.Text("Guess", color="white", size=18, weight="bold"),
                ],
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

        # === TARJETA PRINCIPAL ===
        card = ft.Container(
            width=380,
            bgcolor="#1e293b",
            border_radius=40,
            padding=25,
            shadow=ft.BoxShadow(spread_radius=2, blur_radius=25, color="#0f172a", offset=ft.Offset(0, 8)),
            content=ft.Column(
                [
                    title,
                    headline,
                    subtitle,
                    ft.Divider(height=10, color="transparent"),
                    txt_round,
                    txt_timer,
                    progress,
                    ft.Divider(height=10, color="transparent"),
                    input_guess,
                    txt_feedback,
                    txt_score,
                    ft.Divider(height=20, color="transparent"),
                    btn_guess,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            ),
        )

        layout = ft.Row(
            [ft.Container(content=card, alignment=ft.alignment.center)],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        footer = footer_navbar(page=page, current_path=current_path, dispatches={})
        stack = ft.Stack([layout, footer], expand=True)

        # Iniciar cronómetro (modo threading)
        update_timer()

        return addElementsPage(page, [stack])

    except Exception as e:
        log_error("renderGameRandomNumber", e)
        loadSnackbar(page, "Error loading the game.", "red")
