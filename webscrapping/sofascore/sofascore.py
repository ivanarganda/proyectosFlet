from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time
from bs4 import BeautifulSoup
import pandas as pd

def get_html(url):
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)
    time.sleep(5)  # Esperar que cargue JS
    html = driver.page_source
    driver.quit()
    return html

url = "https://www.sofascore.com/es-la/torneo/futbol/spain/laliga/8#id:77559,tab:statistics"
html = get_html(url)
soup = BeautifulSoup(html, "html.parser")

# Ejemplo: extraer bloques de estadísticas
dfs = []
for section in soup.find_all("section"):
    # depende del HTML: hay que inspeccionar
    rows = []
    for div in section.find_all("div", recursive=True):
        text = div.get_text(" ", strip=True)
        if text:
            rows.append(text)
    if len(rows) > 10:  # umbral arbitrario
        df = pd.DataFrame(rows, columns=["text"])
        dfs.append(df)

print("Found", len(dfs), "dataframes")
for i, df in enumerate(dfs):
    print("### DataFrame", i)
    print(df.head(10))
