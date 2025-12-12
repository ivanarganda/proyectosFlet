from utils import *
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import time
import uuid


def crear_driver():
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--headless=new")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    return webdriver.Chrome(options=options)


def descargar_imagen(url_imagen, jugador, carpeta="imagenes"):
    os.makedirs(carpeta, exist_ok=True)
    driver = None

    try:
        driver = crear_driver()
        driver.get(url_imagen)
        time.sleep(1.5)

        nombre = f"{jugador}.png"
        ruta = os.path.join(carpeta, nombre)

        driver.save_screenshot(ruta)

        print(f"✅ Descargada: {ruta}")
        return True

    except Exception as e:
        print(f"❌ Error {url_imagen}: {e}")
        return False

    finally:
        if driver:
            driver.quit()

df = read_file("jugadores_laliga_imagenes.csv")
images_urls = df["Imagen"].dropna().tolist()
jugadores = df["Jugador"].dropna().tolist()

MAX_THREADS = 15   # 👈 recomendado con Selenium

ok, fail = 0, 0

with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
    futures = [
        executor.submit(descargar_imagen, url, jugadores[i], "imagenes_jugadores")
        for i, url in enumerate(images_urls,start=0)
    ]

    for future in as_completed(futures):
        if future.result():
            ok += 1
        else:
            fail += 1

print("\n📊 RESULTADO FINAL")
print(f"✅ Correctas: {ok}")
print(f"❌ Fallidas: {fail}")