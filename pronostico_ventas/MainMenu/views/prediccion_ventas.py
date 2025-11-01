import os
import io
import base64
import flet as ft
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from helpers.utils import addElementsPage, fit_model, setInputField, generateFooter, init_window, create_layout
from MainMenu.views.scripts_views import init_metadata  # common scripts which return metadata at the same root

current_path = init_metadata()

# --- Load dataset ---
DATASET_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "all_stocks_5yr.csv")
df = pd.read_csv(DATASET_PATH)
df = df[["date", "open", "close", "high", "low", "volume", "Name"]]


def prediccion_ventas(page: ft.Page):
    # --- PAGE SETTINGS ---
    init_window( page = page, title = "Forecast of company actions", size={"width": 600, "height": 850}, bg_color = "#F6F4FB" )

    # --- UI ELEMENTS ---
    titulo = ft.Text( "🔮 Forecast of company actions",size=28,weight=ft.FontWeight.BOLD,color="white",text_align=ft.TextAlign.CENTER )

    acciones = sorted(df["Name"].unique().tolist())
    combo_accion = setInputField( type_="dropdown", label="Choose an option", bg_color="#5A2D9C", border_color="#5A2D9C" , width=350, options=[ft.dropdown.Option(a) for a in acciones] )
    input_periodo = setInputField( type_="text", label="Forecast days", bg_color="black", placeholder="Ejemplo: 60", width=350, border_color="#5A2D9C", value="60" )

    boton = ft.ElevatedButton( text="Generate forecast", icon=ft.icons.AUTO_GRAPH, bgcolor="#5A2D9C", color="white", width=250 )

    mensaje = ft.Text( "", color="#cccccc", size=14, text_align=ft.TextAlign.CENTER )

    grafico_img = ft.Image( border_radius=ft.border_radius.all(10),src_base64=None,width=550,height=350,fit=ft.ImageFit.CONTAIN,visible=False )

    # --- FORECAST AND TRAINNING FUNCTION ---
    boton.on_click = lambda _: fit_model( page=page, combobox=combo_accion, data_frame=df , period_date=input_periodo, output_message=mensaje, chart=grafico_img )

    layout = create_layout(
        page=page,
        current_path=current_path,
        dispatches={},
        content_controls=[
            titulo,
            combo_accion,
            input_periodo,
            boton,
            mensaje,
            grafico_img,
        ],
        bgcolor="black",
    )

    return addElementsPage(page, [layout])