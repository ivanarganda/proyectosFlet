import os
import base64
import datetime
import asyncio
import flet as ft
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import webbrowser

from helpers.utils import addElementsPage, create_layout
from MainMenu.views.scripts_views import init_metadata


# === METADATA Y RUTAS ==========================================================
current_path = init_metadata()
BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..")
DATASET_PATH = os.path.join(BASE_DIR, "all_stocks_5yr.csv")


# === FUNCIONES AUXILIARES ======================================================
def create_kpi_card(title, value, icon, color="#00e5ff"):
    return ft.Container(
        content=ft.Column(
            [
                ft.Icon(icon, size=26, color=color),
                ft.Text(title, color="#cbd5e1", size=12),
                ft.Text(value, color=color, size=20, weight="bold"),
            ],
            alignment="center",
            spacing=3,
        ),
        bgcolor="#1e293b",
        border_radius=14,
        padding=15,
        shadow=ft.BoxShadow(blur_radius=10, color="#00000044"),
        col={"xs": 12, "sm": 6, "md": 4, "lg": 2},
    )


def open_dashboard_in_browser(figs, filename="dashboard.html"):
    """Combine various Plotly figures in one single interactive HTML and it is opened by the browser."""
    temp_dir = os.path.join(os.getcwd(), "temp_charts")
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, filename)

    html_parts = []
    for i, fig in enumerate(figs, start=1):
        html = fig.to_html(include_plotlyjs=("cdn" if i == 1 else False),
                           full_html=False,
                           config={"displayModeBar": False})
        html_parts.append(f"<div style='flex:1; min-width:45%; margin:10px;'>{html}</div>")

    html_template = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>Cotizations about company actions</title>
        <style>
            body {{
                background-color: #0f172a;
                color: #e2e8f0;
                font-family: 'Segoe UI', sans-serif;
                margin: 0;
                padding: 20px;
            }}
            h1 {{
                color: #00e5ff;
                text-align: center;
            }}
            .grid {{
                display: flex;
                flex-wrap: wrap;
                justify-content: center;
            }}
        </style>
    </head>
    <body>
        <h1>💹 Cotizations about company actions dashboard</h1>
        <div class="grid">
            {''.join(html_parts)}
        </div>
    </body>
    </html>
    """

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_template)

    webbrowser.open_new_tab(f"file://{file_path}")
    return ft.Text(f"🌐 Opened complete dashboard in the browser", color="#00e5ff", size=13)


# === DASHBOARD PRINCIPAL =======================================================
def render_dashboard(page: ft.Page):
    page.title = "💹 Cotizations about company actions dashboard"
    page.bgcolor = "#0f172a"
    page.padding = 25
    page.scroll = "auto"

    # === DATASET ===
    df = pd.read_csv(DATASET_PATH)
    df = df.dropna(subset=["high", "low", "open", "close"]).copy()
    df["date"] = pd.to_datetime(df["date"])
    df["mean_price"] = (df["high"] + df["low"]) / 2
    df["dispersion_pct"] = ((df["high"] - df["low"]) / df["mean_price"]) * 100
    df["growth_rate"] = df.groupby("Name")["close"].pct_change() * 100

    acciones = sorted(df["Name"].unique())
    MIN_DATE, MAX_DATE = df["date"].min().date(), df["date"].max().date()

    # === FILTROS ===============================================================
    picker_inicio = ft.DatePicker(value=MIN_DATE, first_date=MIN_DATE, last_date=MAX_DATE)
    picker_fin = ft.DatePicker(value=MAX_DATE, first_date=MIN_DATE, last_date=MAX_DATE)
    page.overlay.extend([picker_inicio, picker_fin])

    date_inicio = ft.ElevatedButton("📅 Desde", on_click=lambda e: picker_inicio.pick_date(),
                                    bgcolor="#334155", color="#e2e8f0")
    date_fin = ft.ElevatedButton("📅 Hasta", on_click=lambda e: picker_fin.pick_date(),
                                 bgcolor="#334155", color="#e2e8f0")

    combo_accion = ft.Dropdown(
        options=[ft.dropdown.Option(a) for a in acciones],
        value=acciones[0],
        bgcolor="#1e293b",
        color="#e2e8f0",
        border_color="#475569",
        width=220,
    )

    filtro_estado = ft.Text(
        f"From {MIN_DATE} to {MAX_DATE} | Action: {acciones[0]}",
        color="#94a3b8",
        size=13,
        italic=True,
    )

    btn_filtrar = ft.ElevatedButton(
        "Update",
        icon=ft.Icons.REFRESH,
        bgcolor="#00e5ff",
        color="black",
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
    )

    filtro_panel = ft.Container(
        content=ft.Column(
            [
                ft.ResponsiveRow(
                    [
                        ft.Container(date_inicio, col={"xs": 12, "md": 3}),
                        ft.Container(date_fin, col={"xs": 12, "md": 3}),
                        ft.Container(combo_accion, col={"xs": 12, "md": 3}),
                        ft.Container(btn_filtrar, col={"xs": 12, "md": 3}),
                    ],
                    alignment="center",
                    spacing=10,
                    run_spacing=10,
                ),
                filtro_estado,
            ],
            alignment="center",
            spacing=10,
        ),
        bgcolor="#1e293bcc",
        border_radius=16,
        padding=20,
        shadow=ft.BoxShadow(blur_radius=10, color="#00000055"),
    )

    # === KPI CONTAINER (antes del layout) ======================================
    kpi_container = ft.Container(
        content=ft.ResponsiveRow(
            [
                create_kpi_card("Prom. Open", "--", ft.Icons.TRENDING_UP),
                create_kpi_card("Prom. Close", "--", ft.Icons.TRENDING_DOWN, "#ff9800"),
                create_kpi_card("Disp. Media (%)", "--", ft.Icons.PERCENT, "#7dd3fc"),
                create_kpi_card("Crecimiento (%)", "--", ft.Icons.TRENDING_FLAT, "#7e57c2"),
                create_kpi_card("Máx Close", "--", ft.Icons.ARROW_UPWARD, "#4caf50"),
                create_kpi_card("Mín Close", "--", ft.Icons.ARROW_DOWNWARD, "#ef5350"),
            ],
            alignment="center",
            spacing=12,
        ),
        padding=10,
    )

    grid = ft.ResponsiveRow([], alignment="center", spacing=25, run_spacing=25)

    # === ACTUALIZAR DASHBOARD ==================================================
    def actualizar_dashboard(e=None):
        async def run_async():
            loading = ft.Container(
                content=ft.Column(
                    [
                        ft.ProgressRing(width=60, height=60, color="#00e5ff"),
                        ft.Text("Generating dashboard charts...", color="#00e5ff", size=16),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                alignment=ft.alignment.center,
                expand=True,
                bgcolor="#0f172acc",
            )
            page.overlay.append(loading)
            page.update()

            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, generar_graficos)

            page.overlay.remove(loading)
            page.update()

        asyncio.run(run_async())

    # === FUNCIÓN GENERAR GRÁFICOS =============================================
    def generar_graficos():
        accion_sel = combo_accion.value
        if not picker_inicio.value or not picker_fin.value:
            return

        inicio = pd.to_datetime(picker_inicio.value)
        fin = pd.to_datetime(picker_fin.value)
        if inicio > fin:
            inicio, fin = fin, inicio

        dff = df[(df["Name"] == accion_sel) & (df["date"].between(inicio, fin))].copy()
        if dff.empty:
            filtro_estado.value = f"⚠️ No data between {inicio.date()} and {fin.date()}"
            filtro_estado.color = "#fbbf24"
            filtro_estado.update()
            return

        filtro_estado.value = f"📊 {accion_sel} | {inicio.date()} → {fin.date()}"
        filtro_estado.color = "#94a3b8"
        filtro_estado.update()

        # === KPIs ==============================================================
        prom_open = dff["open"].mean()
        prom_close = dff["close"].mean()
        dispersion = dff["dispersion_pct"].mean()
        avg_growth = dff["growth_rate"].mean()
        max_close, min_close = dff["close"].max(), dff["close"].min()

        kpi_container.content = ft.ResponsiveRow(
            [
                create_kpi_card("Prom. Open", f"${prom_open:,.2f}", ft.Icons.TRENDING_UP),
                create_kpi_card("Prom. Close", f"${prom_close:,.2f}", ft.Icons.TRENDING_DOWN, "#ff9800"),
                create_kpi_card("Disp. Media", f"{dispersion:.2f}%", ft.Icons.PERCENT, "#7dd3fc"),
                create_kpi_card("Crecimiento", f"{avg_growth:.2f}%", ft.Icons.TRENDING_FLAT, "#7e57c2"),
                create_kpi_card("Máx Close", f"${max_close:,.2f}", ft.Icons.ARROW_UPWARD, "#4caf50"),
                create_kpi_card("Mín Close", f"${min_close:,.2f}", ft.Icons.ARROW_DOWNWARD, "#ef5350"),
            ],
            alignment="center",
            spacing=12,
        )

        # === GRÁFICOS ==========================================================
        figs = []

        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=dff["date"], y=dff["close"], mode="lines", name="Close", line=dict(color="#00e5ff")))
        fig1.add_trace(go.Scatter(x=dff["date"], y=dff["open"], mode="lines", name="Open", line=dict(color="#7e57c2")))
        fig1.update_layout(title=f"Evolución temporal de {accion_sel}", template="plotly_dark")
        figs.append(fig1)

        fig2 = px.box(dff, y="dispersion_pct", color_discrete_sequence=["#00e5ff"])
        fig2.update_layout(title="Dispersion (%)", template="plotly_dark")
        figs.append(fig2)

        dff["rolling"] = dff["close"].rolling(window=10).mean()
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=dff["date"], y=dff["close"], mode="lines", name="Close", line=dict(color="#00e5ff")))
        fig3.add_trace(go.Scatter(x=dff["date"], y=dff["rolling"], mode="lines", name="Media 10d", line=dict(color="#4caf50")))
        fig3.update_layout(title="Move average (10 days)", template="plotly_dark")
        figs.append(fig3)

        top5 = df.groupby("Name")["volume"].sum().nlargest(5).reset_index()
        fig4 = px.bar(top5, x="Name", y="volume", color="Name", title="Top 5 actions by total volume", template="plotly_dark")
        figs.append(fig4)

        avg_vol = df.groupby("Name")["volume"].mean().nlargest(10).reset_index()
        fig5 = px.bar(avg_vol, x="Name", y="volume", color="Name", title="Daily average volume (Top 10)", template="plotly_dark")
        figs.append(fig5)

        dff["month"] = dff["date"].dt.to_period("M")
        disp_month = dff.groupby("month")["dispersion_pct"].mean().reset_index()
        disp_month["month"] = disp_month["month"].astype(str)
        fig6 = px.line(disp_month, x="month", y="dispersion_pct", markers=True, title="Volatilidad promedio mensual (%)", template="plotly_dark")
        figs.append(fig6)

        fig7 = px.scatter(dff, x="open", y="close", color="date", color_continuous_scale="Viridis", title="Relación Open vs Close", template="plotly_dark")
        figs.append(fig7)

        dff["year"] = dff["date"].dt.year
        dff["month_num"] = dff["date"].dt.month
        heat = dff.groupby(["year", "month_num"])["growth_rate"].mean().unstack()
        fig8 = px.imshow(heat, color_continuous_scale="RdBu_r", title="Mapa de calor de crecimiento promedio (%)",
                         labels=dict(x="Mes", y="Año", color="Crecimiento %"))
        fig8.update_layout(template="plotly_dark")
        figs.append(fig8)

        msg = open_dashboard_in_browser(figs)
        grid.controls.clear()
        grid.controls.append(msg)
        grid.update()
        kpi_container.update()

    btn_filtrar.on_click = actualizar_dashboard

    # === LAYOUT ================================================================
    layout = create_layout(
        page=page,
        current_path=current_path,
        dispatches={},
        content_controls=[
            ft.Text("💹 Dashboard Financiero – UI-X Premium", color="#00e5ff", size=24, weight="bold"),
            ft.Divider(height=20, color="#00e5ff33"),
            filtro_panel,
            ft.Divider(height=25, color="#00e5ff22"),
            kpi_container,
            ft.Divider(height=25, color="#00e5ff22"),
            grid,
        ],
        bgcolor="black",
    )

    page.update()
    return layout, actualizar_dashboard
