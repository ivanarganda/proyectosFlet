import os
import re
import ssl
import io
import base64
import asyncio
import concurrent.futures
import flet as ft
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from bs4 import BeautifulSoup
import requests
from io import StringIO
from queue import Queue

# ===============================================================
# CONFIGURACIÓN GLOBAL
# ===============================================================
ssl._create_default_https_context = ssl._create_unverified_context

BASE_URL = "https://coinmarketcap.com/historical/"
OUTPUT_DIR = "tablas_exportadas"
os.makedirs(OUTPUT_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
}

sns.set(style="whitegrid")

# ===============================================================
# FUNCIONES AUXILIARES
# ===============================================================
def fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=150)
    buf.seek(0)
    img_bytes = buf.read()
    buf.close()
    img_b64 = base64.b64encode(img_bytes).decode("utf-8").replace("\n", "").replace("\r", "")
    plt.close(fig)
    return img_b64


def get_num_pages(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text()
        match = re.search(r"Page\s+\d+\s+of\s+(\d+)", text)
        return int(match.group(1)) if match else 1
    except Exception:
        return 1


# ===============================================================
# FUNCIÓN SINCRÓNICA DE SCRAPING (EJECUTADA EN THREAD)
# ===============================================================
def do_scraping(q, stop_flag):
    try:
        r = requests.get(BASE_URL, headers=HEADERS)
        soup = BeautifulSoup(r.text, "html.parser")
        links = soup.find_all("a", href=re.compile(r"/historical/\d{8}/"))
        fechas = sorted(set(re.findall(r"\d{8}", " ".join([a["href"] for a in links]))))

        if not fechas:
            q.put(("log", "❌ No se encontraron fechas.\n"))
            return

        q.put(("log", f"✅ Fechas encontradas ({len(fechas)})...\n"))
        fechas = fechas[:5]
        total = len(fechas)

        for i, fecha in enumerate(fechas, start=1):
            if stop_flag["value"]:
                q.put(("log", "\n🛑 Scraping detenido por el usuario.\n"))
                return

            q.put(("log", f"\n📆 ({i}/{total}) Semana: {fecha}\n"))
            q.put(("progress", (i - 1) / total))

            fecha_url = f"{BASE_URL}{fecha}/"
            num_pages = get_num_pages(f"{fecha_url}?page=1")
            all_tables = []

            for page_num in range(1, num_pages + 1):
                if stop_flag["value"]:
                    return
                url = f"{fecha_url}?page={page_num}"
                r = requests.get(url, headers=HEADERS, timeout=10)
                html = r.text
                try:
                    tables = pd.read_html(StringIO(html))
                    for t in tables:
                        if not t.empty:
                            all_tables.append(t)
                except Exception as e:
                    q.put(("log", f"❌ Error leyendo página {page_num}: {e}\n"))

            if not all_tables:
                q.put(("log", f"⚠️ Sin tablas para {fecha}\n"))
                continue

            df = pd.concat(all_tables, ignore_index=True)
            df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
            df.columns = [str(c).strip().replace("\n", " ") for c in df.columns]
            for col in df.select_dtypes(include="object"):
                df[col] = df[col].map(lambda x: x.strip() if isinstance(x, str) else x)
            df = df.dropna(how="all").reset_index(drop=True)

            csv_path = os.path.join(OUTPUT_DIR, f"coinmarketcap_{fecha}.csv")
            df.to_csv(csv_path, index=False, encoding="utf-8-sig")

            q.put(("log", f"💾 Guardada semana {fecha}: {len(df)} filas\n"))

            num_cols = df.select_dtypes(include="number").columns.tolist()
            if num_cols:
                fig, ax = plt.subplots(figsize=(8, 4))
                sns.boxplot(data=df[num_cols], orient="h", ax=ax)
                ax.set_title(f"{fecha} — Boxplot de variables numéricas")
                img_b64 = fig_to_base64(fig)
                q.put(("chart", img_b64))

        q.put(("log", "\n🎉 Scraping completado.\n"))
        q.put(("progress", 1))

    except Exception as e:
        q.put(("log", f"❌ Error general: {e}\n"))


# ===============================================================
# APLICACIÓN FLET
# ===============================================================
def main(page: ft.Page):
    page.title = "CoinMarketCap Scraper UIX"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = ft.ScrollMode.ALWAYS

    log = ft.Text(value="", size=12, selectable=True)
    progress_bar = ft.ProgressBar(width=400, value=0)
    img_chart = ft.Image(width=650, height=320, visible=False)

    q = Queue()
    stop_flag = {"value": False}

    # === FUNCIONES DE UI =======================================================
    def log_update(text):
        log.value += text
        page.update()

    def update_progress(val):
        progress_bar.value = val
        page.update()

    # === ACTUALIZADOR ASÍNCRONO DE LA COLA ====================================
    async def process_queue():
        while not q.empty():
            msg_type, data = q.get()
            if msg_type == "log":
                log_update(data)
            elif msg_type == "progress":
                update_progress(data)
            elif msg_type == "chart":
                img_chart.src_base64 = data
                img_chart.visible = True
                page.update()

    async def periodic_updater():
        while True:
            await process_queue()
            await asyncio.sleep(0.2)

    # === BOTONES ==============================================================
    async def run_scraping(e):
        log.value = "📅 Iniciando scraping en segundo plano...\n"
        progress_bar.value = 0
        stop_flag["value"] = False
        page.update()

        loop = asyncio.get_running_loop()
        # Se lanza el scraping en un hilo separado
        loop.run_in_executor(None, do_scraping, q, stop_flag)

    def stop_scraping(e):
        stop_flag["value"] = True
        log.value += "\n🛑 Solicitud de parada enviada...\n"
        page.update()

    # === UI PRINCIPAL =========================================================
    page.add(
        ft.AppBar(title=ft.Text("CoinMarketCap Scraper UIX"), bgcolor="#141a29", color="white"),
        ft.Column(
            [
                ft.Text("Scraping histórico de CoinMarketCap", size=18, weight="bold"),
                ft.Row(
                    [
                        ft.ElevatedButton("Iniciar scraping", on_click=run_scraping, bgcolor="#00bcd4", color="white"),
                        ft.ElevatedButton("Detener scraping", on_click=stop_scraping, bgcolor="#e91e63", color="white"),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                progress_bar,
                img_chart,
                ft.Container(
                    height=400,
                    width=650,
                    border=ft.border.all(1, "#555"),
                    border_radius=10,
                    padding=10,
                    content=ft.ListView([log], auto_scroll=True, expand=True),
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    # Lanza el actualizador continuo en segundo plano
    page.run_task(periodic_updater)


# ===============================================================
# LANZAR APP
# ===============================================================
if __name__ == "__main__":
    ft.app(target=main)
