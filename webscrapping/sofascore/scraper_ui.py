import flet as ft
import threading
import time
from datetime import datetime
import requests
import os
import sys

# ==== IMPORTAR ORM Y HELPERS ====
sys.path.append(os.path.join(os.path.dirname(__file__), "DatabaseORM"))
from DatabaseORM.SQLiteORM import *
from helpers.sofa_utils import *
from params import API_KEY, DB

API = "https://api.football-data.org/v4"
HEADERS = {"X-Auth-Token": API_KEY}

RATE_SECONDS = 7
LAST_CALL = 0
STOP_FLAG = False


# ==========================================================
# PETICIÓN SEGURA (con rate limit + cancelación)
# ==========================================================
def safe_get(url, send_log):
    global LAST_CALL, STOP_FLAG
    if STOP_FLAG:
        return {}

    now = time.monotonic()
    diff = now - LAST_CALL
    if diff < RATE_SECONDS:
        time.sleep(RATE_SECONDS - diff)

    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        LAST_CALL = time.monotonic()

        if r.status_code == 429:
            send_log("⏳ 429 Too Many Requests → esperando…")
            time.sleep(10)
            return safe_get(url, send_log)

        if r.status_code != 200:
            send_log(f"❌ Error {r.status_code}: {url}")
            return {}

        return r.json()

    except Exception as e:
        send_log(f"❌ Error petición: {e}")
        return {}


# ==========================================================
# BACKGROUND SCRAPER
# ==========================================================
def run_scraper(send, update_progress):
    global STOP_FLAG
    STOP_FLAG = False

    db = SQLiteORM(DB)
    db.connect_DB()

    def log(msg):
        send(f"{msg}")

    log("🔌 Iniciando scraping…")

    # =====================================================
    # TEMPORADAS
    # =====================================================
    if STOP_FLAG: return
    log("📌 Cargando temporadas…")

    temporadas = [(year, f"{year}-{year+1}", year, year+1, 8, db.datetime())
                  for year in range(2021, datetime.now().year + 1)]

    db.insert_many("temporadas", temporadas)
    update_progress(10)
    log("✔ Temporadas insertadas")

    # =====================================================
    # EQUIPOS
    # =====================================================
    if STOP_FLAG: return
    log("📌 Descargando equipos…")

    d = safe_get(f"{API}/competitions/PD/teams", log)
    equipos = []
    ids = []

    for t in d.get("teams", []):
        equipos.append((t["id"], t["name"], t.get("shortName", ""), t.get("crest", "")))
        ids.append(t["id"])

    db.insert_many("equipos", equipos)
    update_progress(20)
    log(f"✔ Equipos insertados ({len(equipos)})")

    # =====================================================
    # JUGADORES
    # =====================================================
    all_players = []
    total = len(ids)
    count = 0

    for eq in ids:
        if STOP_FLAG: return
        d = safe_get(f"{API}/teams/{eq}", log)

        players = []
        for p in d.get("squad", []):
            players.append((p["id"], p["name"], p.get("dateOfBirth",""), "M", eq))

        all_players.extend(players)
        count += 1

        log(f"✔ Jugadores equipo {eq}: {len(players)}")
        update_progress(20 + int((count / total) * 30))

    db.insert_many("jugadores", all_players)
    log("✔ Jugadores insertados")
    update_progress(55)

    # =====================================================
    # ESTADIOS
    # =====================================================
    all_est = []
    count = 0

    for eq in ids:
        if STOP_FLAG: return
        d = safe_get(f"{API}/teams/{eq}", log)

        venue = d.get("venue", "Desconocido")
        addr = d.get("address", "Desconocido")
        all_est.append((eq * 1000, venue, addr, 0, eq))

        count += 1
        log(f"✔ Estadio equipo {eq}")
        update_progress(55 + int((count / total) * 15))

    db.insert_many("estadios", all_est)
    update_progress(70)
    log("✔ Estadios insertados")

    # =====================================================
    # PARTIDOS
    # =====================================================
    all_matches = []
    years = list(range(2023, datetime.now().year + 1))

    for year in years:
        if STOP_FLAG: return
        log(f"📌 Partidos temporada {year}")

        d = safe_get(f"{API}/competitions/PD/matches?season={year}", log)

        matches = []
        for m in d.get("matches", []):
            matches.append((
                m["id"], year, m.get("matchday"),
                m["homeTeam"]["id"], m["awayTeam"]["id"],
                m["homeTeam"]["id"] * 1000,
                m["utcDate"], m["status"],
                m["score"]["fullTime"]["home"],
                m["score"]["fullTime"]["away"]
            ))

        all_matches.extend(matches)
        log(f"✔ {len(matches)} partidos añadidos")
        update_progress(70 + int(((year - years[0] + 1) / len(years)) * 30))

    db.insert_many("partidos", all_matches)
    update_progress(100)
    log("🎉 ¡Scraping completado sin errores!")
    

# ==========================================================
# ======================= UI FLET ==========================
# ==========================================================
def main(page: ft.Page):
    page.title = "LaLiga Scraper"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.vertical_alignment = ft.MainAxisAlignment.START

    # ================= TOP BAR ===============
    title = ft.Text("⚽ Scraper LaLiga", size=26, weight=ft.FontWeight.BOLD)
    subtitle = ft.Text("Football-Data API • SQLite ORM", size=14, color="#555")

    # ================= PROGRESS ===============
    progress = ft.ProgressBar(width=550, value=0, bgcolor="#EEEEEE", color="#4CAF50")

    # ================= LOG BOX ===============
    log_box = ft.TextField(
        multiline=True,
        read_only=True,
        expand=True,
        border_color="#DDD",
        border_radius=10,
        text_size=13,
        bgcolor="#FAFAFA",
        focused_border_color="#4CAF50",
    )

    # ============= BUTTON ACTIONS =============
    def send_to_log(msg):
        log_box.value += msg + "\n"
        log_box.update()

    def update_progress_bar(v):
        progress.value = v / 100
        progress.update()

    def start_scraper(e):
        global STOP_FLAG
        STOP_FLAG = False
        log_box.value = ""
        progress.value = 0
        log_box.update()
        progress.update()

        threading.Thread(
            target=run_scraper,
            args=(send_to_log, update_progress_bar),
            daemon=True,
        ).start()

    def stop_scraper(e):
        global STOP_FLAG
        STOP_FLAG = True
        send_to_log("⛔ Se solicitó detención del scraping…")

    start_btn = ft.ElevatedButton(
        "▶ Iniciar scraping",
        on_click=start_scraper,
        bgcolor="#4CAF50",
        color="white",
        height=45,
        width=200,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
    )

    stop_btn = ft.ElevatedButton(
        "⛔ Parar",
        on_click=stop_scraper,
        bgcolor="#E53935",
        color="white",
        height=45,
        width=120,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
    )

    # ================= LAYOUT =================
    page.add(
        ft.Column(
            [
                title,
                subtitle,
                ft.Divider(height=10),
                progress,
                ft.Row([start_btn, stop_btn], spacing=10),
                ft.Text("LOG OUTPUT:", weight=ft.FontWeight.BOLD),
                log_box,
            ],
            spacing=15,
        )
    )


ft.app(target=main)