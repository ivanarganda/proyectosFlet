import os
os.environ["BOTASAURUS_DEBUG"] = "0"
os.environ["BOTASAURUS_NO_PAUSE"] = "1"
os.environ["BOTASAURUS_PAGE_LOAD_TIMEOUT"] = "25"
from helpers.sofa_utils import *
import re
import csv
import time
import random
from params import *
from pandas import json_normalize # Para aplanar la columna 'country'
import ScraperFC as sfc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from ivbox.SQLiteORM import *

scraping_folder = SCRAPPING_FOLDER
output_filename = ""
current_round = 0

# Número de workers para ThreadPoolExecutor broswer
MAX_WORKERS = 1

# Numero de workers para ThreadPoolExecutor  procesamiento
PROCESSING_MAX_WORKERS = max(2, os.cpu_count() - 1)

# Output files
OUTPUT_PARTIDOS_LIGA = f"{scraping_folder}partidos_laliga.csv"

def retry_scrape(fn, url, retries=5, base_sleep=2):
    for attempt in range(1, retries + 1):
        try:
            return fn(url)
        except Exception as e:
            if attempt == retries:
                raise
            sleep = base_sleep * attempt
            print(f"⏳ Retry {attempt}/{retries} en {sleep}s | {url}")
            time.sleep(sleep)

def get_total_steps() -> int:

    db = SQLiteORM(DB)
    db.connect_DB()

    df = read_file(OUTPUT_PARTIDOS_LIGA)
    df = df[df["Jornada"].between(current_round, int(df["Jornada"].max()))]

    total_matches = df["URL"].drop_duplicates().count()

    already_matches_scraped = db.execute_query(f"""
        SELECT COUNT(*) AS n
        FROM partidos
        WHERE id_jornada >= {current_round}
    """).json[0]["n"]

    pending_matches = max(0, total_matches - already_matches_scraped)

    # --- STEPS ---
    match_steps = pending_matches * 1        # request + parse
    player_steps = pending_matches * 2       # batch jugadores

    return match_steps + player_steps

def reset_db_rounds()-> bool:
    
    try:

        db = SQLiteORM(DB)
        db.connect_DB()
        db.delete_all("jornadas")

        return True
    
    except Exception:

        print(f"Error: unable to delete all rounds")
        return False

def check_rounds_in_db()-> None:

    global current_round

    db = SQLiteORM(DB)
    db.connect_DB()
    cr = db.execute_query("SELECT MAX(id_jornada) as max_round FROM jornadas").json

    if cr and cr[0]["max_round"] is not None:
        current_round = int(cr[0]["max_round"])
    
    return None

def generate_urls_liga(on_callback=None) -> str | bool:

    global output_filename

    output_filename = init_path_object( OUTPUT_PARTIDOS_LIGA ).get("filename", "") # no queremos path completo por seguridad

    URL = "https://www.sofascore.com/es-la/torneo/futbol/spain/laliga/8#id:77559,tab:matches"
    EVENTS_CSS = "a[class^='event-hl-']"
    BTN_PREV_XPATH = '//*[@id="tabpanel-round"]/div/div[1]/div/button[1]'
    BTN_NEXT_XPATH = '//*[@id="tabpanel-round"]/div/div[1]/div/button[2]'

    def safe_click(driver, el):
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        driver.execute_script("arguments[0].click();", el)

    def is_disabled(btn):
        return (
            btn.get_attribute("disabled") is not None
            or (btn.get_attribute("aria-disabled") or "").lower() == "true"
        )

    def collect_round_urls(driver, seen, urls):
        for a in driver.find_elements(By.CSS_SELECTOR, EVENTS_CSS):
            href = a.get_attribute("href")
            if href and href not in seen:
                seen.add(href)
                urls.append(href)

    driver = None

    try:
        on_callback("Starting match URLs extraction...")
        # =========================
        # DRIVER
        # =========================
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--lang=es-ES")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--blink-settings=imagesEnabled=false")
        chrome_options.page_load_strategy = "eager"

        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 12)
        on_callback("Accesing to Sofascore league page...")
        driver.get(URL)

        # =========================
        # POPUPS
        # =========================
        try:
            on_callback("Checking cookies consent...")
            consent_btn = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(., 'Consentir') or contains(., 'Aceptar')]")
                )
            )
            safe_click(driver, consent_btn)
            on_callback("Cookies accepted.")
        except TimeoutException:
            on_callback("No cookies popup found.")
            pass

        try:
            on_callback("Checking any other popup...")
            close_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="portals"]//button'))
            )
            safe_click(driver, close_btn)
            on_callback("Popup closed.")
        except TimeoutException:
            on_callback("No other popup found.")
            pass

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, EVENTS_CSS)))
        on_callback("Urls loaded successfully")

        # =========================
        # IR A JORNADA 1
        # =========================
        on_callback("Navigating to the first round...")

        while True:
            prev_btn = wait.until(EC.presence_of_element_located((By.XPATH, BTN_PREV_XPATH)))
            if is_disabled(prev_btn):
                break

            first_event = driver.find_elements(By.CSS_SELECTOR, EVENTS_CSS)[0]
            safe_click(driver, prev_btn)
            wait.until(EC.staleness_of(first_event))
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, EVENTS_CSS)))

        on_callback("First round reached.")
        # =========================
        # RECORRER JORNADAS
        # =========================
        on_callback("Extracting match URLs from all rounds...")
        seen, urls = set(), []
        collect_round_urls(driver, seen, urls)
        on_callback(f"Inited collected {len(urls)} URLs so far.")

        while True:
            next_btn = wait.until(EC.presence_of_element_located((By.XPATH, BTN_NEXT_XPATH)))
            if is_disabled(next_btn):
                break

            first_event = driver.find_elements(By.CSS_SELECTOR, EVENTS_CSS)[0]
            safe_click(driver, next_btn)
            wait.until(EC.staleness_of(first_event))
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, EVENTS_CSS)))

            collect_round_urls(driver, seen, urls)
            on_callback(f"Collected {len(urls)} URLs so far.")

            if on_callback:
                on_callback(len(urls))

        if not urls:
            on_callback("No match URLs extracted.")
            raise RuntimeError("No se han extraído URLs de partidos")

        # =========================
        # LIMPIEZA Y VALIDACIÓN
        # =========================
        on_callback("Cleaning invalid URLs...")
        url_descartar = (
            "https://www.sofascore.com/es-la/football/match/"
            "getafe-osasuna/vgbsjhb#id:14083640"
        )
        urls = [u for u in urls if u != url_descartar]

        if len(urls) % 10 != 0:
            on_callback("Warning: URLs count not multiple of 10 matches per round.")
            print(f"⚠️ Advertencia: {len(urls)} URLs no múltiplo de 10")

        jornadas = [urls[i:i + 10] for i in range(0, len(urls), 10)]
        on_callback(f"Total rounds collected: {len(jornadas)}")

        # =========================
        # CSV
        # =========================
        on_callback(f"Generating file for URLs: {output_filename} ...")
        with open(OUTPUT_PARTIDOS_LIGA, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Jornada", "Partido", "URL"])

            for j_num, jornada in enumerate(jornadas, start=1):
                for p_num, url in enumerate(jornada, start=1):
                    writer.writerow([j_num, p_num, url])

        on_callback(f"File {output_filename} created successfully.")
        print(f"📂 Archivo '{OUTPUT_PARTIDOS_LIGA}' creado correctamente")
        return OUTPUT_PARTIDOS_LIGA

    except Exception as e:
        on_callback(f"Error in generate file {output_filename}: {type(e).__name__}: {e}")
        print(f"❌ Error in generate_partidos_liga → {type(e).__name__}: {e}")
        return False

    finally:
        if driver:
            driver.quit()
            on_callback("Closed browser.")

def generate_partidos_jornadas_stats(file_input, on_callback=None) -> str | bool:

    print(f"Current round in DB: {current_round}")

    total_jornadas = read_file(file_input).drop_duplicates("Jornada").shape[0]

    output_filename = init_path_object( file_input ).get("filename", "") # no queremos path completo por seguridad

    on_callback("Starting match stats extraction...")

    def scrape_partido_worker(
        sofascore,
        jornada: int,
        partido_num: Optional[int],
        url: str
    ) -> pd.DataFrame | None:
        """
        Worker concurrente por partido.
        Devuelve DataFrame o None si falla.
        """
        try:

            on_callback(f"Scraping Jornada {jornada} | Partido {partido_num}...")
            match = re.search(r"id:(\d+)", url)
            partido_id = match.group(1) if match else None

            df = retry_scrape(sofascore.scrape_team_match_stats, url)
            on_callback(f"Scraped Jornada {jornada} | Partido {partido_num}.")

            if df is None or df.empty:
                on_callback(f"No data for Jornada {jornada} | Partido {partido_num}.")
                raise ValueError("DataFrame vacío")

            df["Jornada"] = jornada
            df["Partido"] = partido_num
            df["id"] = partido_id

            on_callback(f"Processed Jornada {jornada} | Partido {partido_num}.")
            print(f"✅ Jornada {jornada} | Partido {partido_num} | ID {partido_id}")
            return df

        except Exception as e:
            on_callback(f"Error Jornada {jornada} | Partido {partido_num}: {e}")
            print(f"❌ Error Jornada {jornada} | Partido {partido_num}: {e}")
            return None

    on_callback(f"Preparing URLs from file: {output_filename} ...")
    sofascore = sfc.Sofascore()

    df_url = read_file(file_input)
    on_callback(f"Total URLs to process: {len(df_url)}")

    # Asegurar tipos
    df_url["Jornada"] = pd.to_numeric(df_url["Jornada"], errors="coerce")
    df_url["Partido"] = pd.to_numeric(df_url["Partido"], errors="coerce")

    df_url = (
        df_url
        .dropna(subset=["Jornada", "URL"])
        .sort_values(["Jornada", "Partido"])
    )
    on_callback("URLs prepared and sorted.")

    # Jornadas x a y
    df_url_filtrado = (
        df_url[df_url["Jornada"].between(current_round, int(total_jornadas)+1)]
        .drop_duplicates(subset=["Jornada", "Partido", "URL"])
    )

    on_callback(f"Filtered URLs for jornadas {current_round} to {total_jornadas}.")
    # ===============================
    # EXCEL
    # ===============================

    output_file = f"{scraping_folder}jornadas_{current_round}_{total_jornadas}_stats.xlsx"
    output_filename = init_path_object( output_file ).get("filename", "") # no queremos path completo por seguridad
    on_callback(f"Generating {output_filename} with match stats...")
    with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:

        on_callback("Starting per-round processing...")
        for j in sorted(df_url_filtrado["Jornada"].unique()):
            on_callback(f"Processing round {j}...")
            urls_jornada = df_url_filtrado[df_url_filtrado["Jornada"] == j]

            futures = []
            df_partidos = []
            on_callback(f"Scraping matches for round {j} with {len(urls_jornada)} matches...")
            with ThreadPoolExecutor(max_workers=PROCESSING_MAX_WORKERS) as executor:
                on_callback(f"Submitting match scraping tasks for round {j}...")
                for _, row in urls_jornada.iterrows():
                    on_callback(f"Submitting Jornada {j} | Partido {int(row['Partido']) if pd.notnull(row['Partido']) else None}...")
                    futures.append(
                        executor.submit(
                            scrape_partido_worker,
                            sofascore,
                            int(j),
                            int(row["Partido"]) if pd.notnull(row["Partido"]) else None,
                            row["URL"]
                        )
                    )
                on_callback(f"Waiting for match scraping tasks to complete for round {j}...")
                for future in as_completed(futures):
                    on_callback(f"Processing completed match task for round {j}...")
                    result = future.result()
                    on_callback(f"Processed completed match task for round {j}.")
                    if result is not None:
                        on_callback(f"Appending result for round {j}...")
                        df_partidos.append(result)
            on_callback(f"All matches scraped for round {j}.")
            if df_partidos:
                on_callback(f"Generating Excel sheet for round {j}...")
                df_jornada = pd.concat(df_partidos, ignore_index=True)
                hoja = f"Jornada_{int(j):02d}"
                df_jornada.to_excel(writer, sheet_name=hoja, index=False)
                on_callback(f"Generated Excel sheet for round {j} from {output_filename}")
                print(f"📄 Guardada hoja {hoja} ({len(df_partidos)} partidos)")
                on_callback(f"Generando la hoja jornada {j}")
                time.sleep(0.3 + random.uniform(0.1, 0.3))
            else:
                on_callback(f"No matches data for round {j}, stopping.")
                print(f"⛔ Jornada {j} sin partidos disponibles → fin del scraping")
                break
    on_callback(f"File {output_filename} created successfully.")
    print(f"\n✅ Proceso completado. Archivo: {output_file}")
    return output_file

def generate_partidos_jornadas_info(
    df_url: pd.DataFrame,
    start_jornada: int,
    end_jornada: int,
    max_workers: int = 8,
    on_callback=None
) -> str | bool:

    global current_round

    start_jornada = current_round

    def safe_cb(msg):
        if on_callback:
            on_callback(msg)

    safe_cb("Starting match info extraction...")

    # --------------------------------------------------
    # Helper: extraer info del partido
    # --------------------------------------------------
    def extract_match_info_from_json(match_data: dict) -> dict | None:

        if not match_data:
            return None

        partido_id = match_data.get("id")
        local = match_data.get("homeTeam", {}).get("name")
        visitante = match_data.get("awayTeam", {}).get("name")

        venue = match_data.get("venue", {})
        estadio = venue.get("name")
        capacidad = venue.get("capacity")

        coords = venue.get("venueCoordinates", {})
        latitud = coords.get("latitude")
        longitud = coords.get("longitude")

        home_score = match_data.get("homeScore", {}).get("current")
        away_score = match_data.get("awayScore", {}).get("current")

        resultado = (
            f"{home_score}-{away_score}"
            if home_score is not None and away_score is not None
            else "Pte"
        )

        timestamp = match_data.get("startTimestamp")
        fecha_partido = hora_partido = None

        if timestamp:
            try:
                if timestamp > 10_000_000_000:
                    timestamp /= 1000
                dt_object = datetime.fromtimestamp(timestamp)
                fecha_partido = dt_object.strftime("%d/%m/%Y")
                hora_partido = dt_object.strftime("%H:%M")
            except Exception:
                pass

        return {
            "id": partido_id,
            "Local": local,
            "Visitante": visitante,
            "Estadio": estadio,
            "Capacidad": capacidad,
            "Latitud": latitud,
            "Longitud": longitud,
            "Resultado": resultado,
            "Fecha": fecha_partido,
            "Hora": hora_partido,
        }

    # --------------------------------------------------
    # Preparación DataFrame
    # --------------------------------------------------
    df_url = df_url.copy()
    df_url["Jornada"] = pd.to_numeric(df_url["Jornada"], errors="coerce")
    df_url["Partido"] = pd.to_numeric(df_url["Partido"], errors="coerce")

    df_url = (
        df_url
        .dropna(subset=["Jornada", "URL"])
        .sort_values(["Jornada", "Partido"])
    )

    df_url_filtrado = df_url[
        df_url["Jornada"].between(start_jornada, end_jornada)
    ].drop_duplicates(subset=["Jornada", "Partido", "URL"])

    safe_cb(f"URLs a procesar: {len(df_url_filtrado)}")

    # --------------------------------------------------
    # PROCESO SECUENCIAL CON CORTE GLOBAL
    # --------------------------------------------------
    partidos_info = []
    stop_processing = False

    for jornada in sorted(df_url_filtrado["Jornada"].unique()):

        if stop_processing:
            break

        safe_cb(f"Processing Jornada {jornada}...")
        df_jornada = df_url_filtrado[df_url_filtrado["Jornada"] == jornada]

        for _, row in df_jornada.iterrows():

            sofascore = sfc.Sofascore()

            j = int(row["Jornada"])
            partido_num = int(row["Partido"]) if pd.notnull(row["Partido"]) else None
            url = row["URL"]

            try:
                match_data = sofascore.get_match_dict(url)
                meta = extract_match_info_from_json(match_data)

                if meta is None:
                    continue

                # ⛔ CORTE TOTAL SI HAY PARTIDO PENDIENTE
                if meta["Resultado"] == "Pte":
                    safe_cb(
                        f"⛔ Pending match detected → stopping at Jornada {j}, Partido {partido_num}"
                    )
                    stop_processing = True
                    break

                meta["Jornada"] = j
                meta["Partido"] = partido_num
                partidos_info.append(meta)

                print(
                    f"Jornada {j} - Partido {partido_num}: "
                    f"{meta['Local']} vs {meta['Visitante']} | {meta['Resultado']}"
                )

            except Exception as e:
                safe_cb(f"Error Jornada {j} Partido {partido_num}: {e}")
                print(f"❌ Error Jornada {j} Partido {partido_num}: {e}")

    # --------------------------------------------------
    # EXPORTACIÓN EXCEL
    # --------------------------------------------------
    if not partidos_info:
        print("\n❌ No se pudieron extraer datos.")
        return False

    df_meta = pd.DataFrame(partidos_info)

    output_file = f"{scraping_folder}jornadas_{start_jornada:02d}_{end_jornada:02d}_info.xlsx"
    output_filename = init_path_object(output_file).get("filename", "")

    safe_cb(f"Generating {output_filename} with match info...")

    column_order = [
        "Jornada", "Partido", "id", "Fecha", "Hora",
        "Local", "Visitante", "Resultado",
        "Estadio", "Capacidad", "Latitud", "Longitud"
    ]

    with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
        for jornada, df_jornada in df_meta.groupby("Jornada"):
            df_jornada[column_order].to_excel(
                writer,
                sheet_name=f"Jornada {int(jornada)}",
                index=False
            )

    print(f"\n✅ Proceso completado. Archivo: {output_filename}")
    return output_file

def generate_estadisticas_jugadores_por_jornada(
    df_url: pd.DataFrame,
    start_jornada: int,
    end_jornada: int,
    max_workers: int = 6,  # 👈 aquí sí tiene sentido
    on_callback=None
) -> str | bool:
    """
    Scraping SECUENCIAL (Chrome) + procesamiento paralelo (ThreadPool).
    """
    
    global current_round

    start_jornada = current_round

    on_callback("Starting player stats extraction...")

    print(
        f"Iniciando estadísticas de jugadores "
        f"(Jornadas {start_jornada} a {end_jornada})..."
    )

    # --------------------------------------------------
    # Preparación DataFrame
    # --------------------------------------------------
    try:
        on_callback("Preparing players stats URLs...")
        df_url = df_url.copy()
        df_url["Jornada"] = pd.to_numeric(df_url["Jornada"], errors="coerce")
        df_url["Partido"] = pd.to_numeric(df_url["Partido"], errors="coerce")

        df_url = (
            df_url
            .dropna(subset=["Jornada", "URL"])
            .sort_values(["Jornada", "Partido"])
        )

        df_url_filtrado = (
            df_url[df_url["Jornada"].between(start_jornada, end_jornada)]
            .drop_duplicates(subset=["Jornada", "Partido", "URL"])
        )
        on_callback(f"Filtered stats by rounds {start_jornada} to {end_jornada}.")

        if df_url_filtrado.empty:
            on_callback("No valid URLs to process.")
            print("❌ No hay URLs válidas para procesar.")
            return False

    except Exception as e:
        on_callback(f"Error preparing for player stats: {e}")
        print(f"❌ Error preparando DataFrame: {e}")
        return False

    on_callback(f"Total URLs to process: {len(df_url_filtrado)}")
    # --------------------------------------------------
    # FASE 1 — SCRAPING SECUENCIAL (NAVEGADOR)
    # --------------------------------------------------
    raw_results: List[Tuple[pd.DataFrame, int, int | None, str]] = []

    on_callback("Starting sequential scraping of player stats...")
    for _, row in df_url_filtrado.iterrows():
        on_callback(f"Scraping Jornada {int(row['Jornada'])} | Partido {int(row['Partido']) if pd.notnull(row['Partido']) else None}...")
        j = int(row["Jornada"])
        partido_num = int(row["Partido"]) if pd.notnull(row["Partido"]) else None
        url = row["URL"]

        match = re.search(r"id:(\d+)", url)
        partido_id = match.group(1) if match else None
        on_callback(f"Extracted match ID: {partido_id}")

        try:
            on_callback(f"Scraping player stats from match {row['Jornada']} | Partido {partido_num}...")
            sofascore = sfc.Sofascore()
            df_raw = sofascore.scrape_player_match_stats(url)
            on_callback(f"Scraped player stats for Jornada {j} | Partido {partido_num}.")

            if not isinstance(df_raw, pd.DataFrame) or df_raw.empty:
                on_callback(f"No player stats data for Jornada {j} | Partido {partido_num}.")
                print(f"⚠️ Jornada {j} Partido {partido_num}: sin datos")
                break
            
            on_callback(f"Collected raw player stats for Jornada {j} | Partido {partido_num}.")
            raw_results.append((df_raw, j, partido_num, partido_id))
            on_callback(f"Appended player stats for Jornada {j} | Partido {partido_num}.")
            print(f"✅ Scrape OK | Jornada {j} Partido {partido_num}")

        except Exception as e:
            on_callback(f"Error scraping Jornada {j} Partido {partido_num} | URL {url}: {e}")
            print(
                f"❌ Error scraping Jornada {j} Partido {partido_num} "
                f"| URL {url}: {e}"
            )
    on_callback("Sequential scraping of player stats completed.")
    if not raw_results:
        on_callback("No player stats data obtained.")
        print("❌ No se obtuvieron estadísticas de jugadores.")
        return False
    on_callback(f"Total raw results collected: {len(raw_results)}")
    # --------------------------------------------------
    # FASE 2 — PROCESAMIENTO PARALELO (THREAD POOL)
    # --------------------------------------------------
    def process_df(item) -> pd.DataFrame | None:
        on_callback("Processing raw data in parallel...")
        try:
            df, j, partido_num, partido_id = item

            on_callback(f"Normalizing data for Jornada {j} | Partido {partido_num}...")

            # Normalizar columna anidada "country"
            if "country" in df.columns:
                on_callback(f"Normalizing 'country' column for Jornada {j} | Partido {partido_num}...") 
                country_norm = (
                    json_normalize(df["country"], sep="_")
                    .add_prefix("country_")
                )
                df = pd.concat(
                    [
                        df.drop(columns=["country"]).reset_index(drop=True),
                        country_norm.reset_index(drop=True)
                    ],
                    axis=1
                )
                on_callback(f"'country' column normalized for Jornada {j} | Partido {partido_num}.")

            df["id"] = partido_id
            df["Jornada"] = j
            df["Partido"] = partido_num

            df = df.reset_index(drop=True)
            df = df.loc[:, ~df.columns.duplicated()]
            on_callback(f"Processed data for Jornada {j} | Partido {partido_num}.")
            return df

        except Exception:
            on_callback("Error processing raw data.")
            return None

    processed_dfs = []
    on_callback("Starting ThreadPool for data processing...")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        on_callback("Submitting data processing tasks...")
        futures = [executor.submit(process_df, item) for item in raw_results]
        on_callback("Waiting for data processing tasks to complete...")
        for future in as_completed(futures):
            on_callback("Processing completed data task...")
            result = future.result()
            if result is not None:
                on_callback("Appending processed data...")
                processed_dfs.append(result)
            on_callback("Processed data task completed.")
        on_callback("All data processing tasks completed.")
    on_callback("Data processing tasks completed.")

    if not processed_dfs:
        on_callback("No processed data obtained.")
        print("❌ Fallo en el procesamiento paralelo.")
        return False

    on_callback(f"Total processed data: {len(processed_dfs)}")
    # --------------------------------------------------
    # CONSOLIDACIÓN
    # --------------------------------------------------
    try:
        on_callback("Consolidating processed data...")
        df_stats = pd.concat(processed_dfs, ignore_index=True)
        df_stats = df_stats.loc[:, ~df_stats.columns.duplicated()]
        on_callback("Data consolidation completed.")
        print(f"📊 Datos consolidados: {df_stats.shape[0]} filas")
    except Exception as e:
        on_callback(f"Error consolidating data: {e}")
        print(f"❌ Error consolidando datos: {e}")
        return False

    on_callback("Preparing to export data to Excel...")
    # --------------------------------------------------
    # EXPORTACIÓN EXCEL
    # --------------------------------------------------
    output_stats = (
        f"{SCRAPPING_FOLDER}"
        f"estadisticas_jugadores_por_jornada_"
        f"{start_jornada:02d}_{end_jornada:02d}.xlsx"
    )

    output_filename = init_path_object( output_stats ).get("filename", "") # no queremos path completo por seguridad
    on_callback(f"Generating {output_filename} with player stats...")

    context_columns = ["Jornada", "Partido", "id"]

    try:
        on_callback(f"Writing player stats to Excel sheets by round from {output_filename}...")
        with pd.ExcelWriter(output_stats, engine="xlsxwriter") as writer:
            on_callback("Starting to write sheets by round...")
            for jornada, df_jornada in df_stats.groupby("Jornada"):
                on_callback(f"Writing sheet for round {jornada}...")
                cols = context_columns + [
                    c for c in df_jornada.columns if c not in context_columns
                ]
                on_callback(f"Columns ordered for round {jornada}.")
                df_jornada[cols].to_excel(
                    writer,
                    sheet_name=f"Jornada {int(jornada)}",
                    index=False
                )
                on_callback(f"Written sheet for round {jornada}.")
        on_callback(f"File {output_filename} created successfully.")

        print(f"🚀 Estadísticas exportadas en: {output_stats}")
        return output_stats

    except Exception as e:
        on_callback(f"Error writing Excel file: {e}")
        print(f"❌ Error escribiendo Excel: {e}")
        return False



if __name__ == "__main__":

    # Only for testing
    print(get_total_steps())