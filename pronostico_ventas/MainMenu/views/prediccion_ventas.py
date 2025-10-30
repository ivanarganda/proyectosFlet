import os
import io
import base64
import flet as ft
import pandas as pd
import matplotlib.pyplot as plt
from prophet import Prophet
from helpers.utils import addElementsPage
from footer_navegation.navegation import footer_navbar

current_path = {
    "path": os.path.abspath(__file__),
    "folder": os.path.dirname(os.path.abspath(__file__)).split("\\")[-1],
    "file": os.path.basename(__file__)
}

# --- Cargar dataset ---
DATASET_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "all_stocks_5yr.csv")
df = pd.read_csv(DATASET_PATH)
df = df[["date", "open", "close", "high", "low", "volume", "Name"]]


def prediccion_ventas(page: ft.Page):
    page.title = "Predicción de Ventas"
    page.window_width = 600
    page.window_height = 850
    page.bgcolor = "#F6F4FB"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    # --- ELEMENTOS DE UI ---
    titulo = ft.Text("🔮 Predicción con Prophet", size=28, weight=ft.FontWeight.BOLD, color="#FFFFFF")

    acciones = sorted(df["Name"].unique().tolist())
    combo_accion = ft.Dropdown(
        label="Selecciona una acción",
        options=[ft.dropdown.Option(a) for a in acciones],
        width=350,
        border_color="#5A2D9C"
    )

    input_periodo = ft.TextField(
        label="Días a predecir",
        hint_text="Ejemplo: 60",
        width=350,
        border_color="#5A2D9C",
        value="60"
    )

    grafico_img = ft.Image(
        border_radius=ft.border_radius.all(10),
        src_base64=None,
        width=500,
        height=350,
        fit=ft.ImageFit.CONTAIN,
        visible=False
    )

    mensaje = ft.Text("", color="#FFFFFF", size=14)

    # --- FUNCIÓN DE ENTRENAMIENTO Y PREDICCIÓN ---
    def entrenar_modelo(e):
        try:
            accion = combo_accion.value
            dias = int(input_periodo.value)

            if not accion:
                mensaje.value = "⚠️ Selecciona una acción antes de continuar."
                page.update()
                return

            mensaje.value = f"Entrenando modelo Prophet para {accion}..."
            grafico_img.visible = False
            page.update()

            # --- Filtrar datos ---
            data = df[df["Name"] == accion][["date", "close"]].copy()
            data.rename(columns={"date": "ds", "close": "y"}, inplace=True)
            data["ds"] = pd.to_datetime(data["ds"])

            # --- Modelo Prophet ---
            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=False,
                daily_seasonality=False,
                seasonality_mode="multiplicative"
            )
            model.fit(data)

            # --- Predicción futura ---
            future = model.make_future_dataframe(periods=dias)
            forecast = model.predict(future)

            # --- Combinar datos reales + predicción ---
            cutoff = data["ds"].max()  # los datos reales
            forecast["is_future"] = forecast["ds"] > cutoff # datos futuros

            # --- GRAFICAR ---
            fig, ax = plt.subplots(figsize=(8, 4))
            # Datos reales (azul)
            ax.plot(
                data["ds"],
                data["y"],
                label="Datos reales",
                color="#1f77b4",
                linewidth=1.8
            )

            # Predicción futura (línea continua)
            ax.plot(
                forecast.loc[forecast["is_future"], "ds"],
                forecast.loc[forecast["is_future"], "yhat"],
                label="Predicción futura",
                color="#ff7f0e",
                linewidth=1
            )
            # Banda de incertidumbre (gris)
            ax.fill_between(
                forecast["ds"],
                forecast["yhat_lower"],
                forecast["yhat_upper"],
                color="gray",
                alpha=0.2,
                label="Intervalo de confianza"
            )

            ax.set_title(f"Predicción de cierre - {accion}", fontsize=14)
            ax.set_xlabel("Fecha")
            ax.set_ylabel("Precio de cierre")
            ax.legend()
            plt.tight_layout()

            # --- Guardar gráfico en buffer ---
            buf = io.BytesIO()
            plt.savefig(buf, format="png", bbox_inches="tight")
            plt.close(fig)
            buf.seek(0)

            # --- Convertir a base64 ---
            img_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")

            # --- Mostrar gráfico ---
            grafico_img.src_base64 = img_base64
            grafico_img.visible = True
            mensaje.value = f"✅ Modelo entrenado para {accion} ({dias} días)."
            page.update()

        except Exception as ex:
            mensaje.value = f"❌ Error: {ex}"
            page.update()

    # --- BOTÓN ---
    boton = ft.ElevatedButton(
        text="Generar Predicción",
        icon=ft.icons.AUTO_GRAPH,
        bgcolor="#5A2D9C",
        color="white",
        width=250,
        on_click=entrenar_modelo
    )

    # --- CONTENIDO PRINCIPAL ---
    contenido = ft.Column(
        [
            titulo,
            combo_accion,
            input_periodo,
            boton,
            ft.Container(height=10),
            mensaje,
            grafico_img,
            ft.Container(height=80),  # espacio para no tapar el footer
        ],
        alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=20,
        scroll=ft.ScrollMode.AUTO,
        expand=True
    )

    # --- FOOTER FIJO ABAJO ---
    footer = footer_navbar(page=page, current_path=current_path, dispatches={})

    layout = ft.Stack(
        [
            ft.Container(content=contenido, expand=True),
            ft.Container(
                content=footer,
                bottom=0,
                left=0,
                right=0,
                bgcolor="#F6F4FB",
                shadow=ft.BoxShadow(blur_radius=12, color=ft.colors.with_opacity(0.15, "black"))
            )
        ],
        expand=True
    )


    return addElementsPage(page, [layout])
