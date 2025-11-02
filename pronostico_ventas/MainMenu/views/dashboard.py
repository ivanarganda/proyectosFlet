import os, io, base64, datetime
import flet as ft
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

from helpers.utils import addElementsPage, create_layout
from MainMenu.views.scripts_views import init_metadata

# === METADATA Y RUTAS ===
current_path = init_metadata()
BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..")
DATASET_PATH = os.path.join(BASE_DIR, "all_stocks_5yr.csv")

# === FUNCIONES AUXILIARES =====================================================
def fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=150, transparent=True)
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return img_b64


def style_chart(ax, title):
    """Aplica estilo UI-X minimalista."""
    ax.set_facecolor("#0f172a")
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.grid(alpha=0.15, color="#64748b")
    ax.tick_params(colors="#e2e8f0", labelsize=9)
    ax.set_title(title, color="#e2e8f0", fontsize=12, pad=8, weight="bold")


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


def create_chart_container(title, chart):
    return ft.Container(
        content=ft.Column(
            [ft.Text(title, color="#94a3b8", size=15, weight="bold"), chart],
            spacing=10,
        ),
        bgcolor="#1e293bcc",
        border_radius=18,
        padding=20,
        expand=True,
        shadow=ft.BoxShadow(blur_radius=12, color="#00000033"),
    )


# === DASHBOARD ================================================================
def render_dashboard(page: ft.Page):
    page.title = "💹 Dashboard Financiero – UI-X Premium"
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

    # === FILTROS ==============================================================
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
        f"Del {MIN_DATE} al {MAX_DATE} | Acción: {acciones[0]}",
        color="#94a3b8",
        size=13,
        italic=True,
    )

    btn_filtrar = ft.ElevatedButton(
        "Actualizar",
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

    # === PLACEHOLDER IMÁGENES =================================================
    transparent = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mO0t7e5HgAFGwJ/lQ8m"
        "1QAAAABJRU5ErkJggg=="
    )
    def placeholder_chart():
        return ft.Image(src_base64=transparent, fit=ft.ImageFit.CONTAIN, expand=True)
    charts = [placeholder_chart() for _ in range(8)]

    # === KPIs ================================================================
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

    # === FUNCIÓN ACTUALIZAR ====================================================
    def actualizar_dashboard(e=None):
        accion_sel = combo_accion.value
        if not picker_inicio.value or not picker_fin.value:
            return

        inicio = pd.to_datetime(picker_inicio.value)
        fin = pd.to_datetime(picker_fin.value)
        if inicio > fin:
            inicio, fin = fin, inicio

        dff = df[(df["Name"] == accion_sel) & (df["date"].between(inicio, fin))].copy()

        if dff.empty:
            filtro_estado.value = f"⚠️ Sin datos entre {inicio.date()} y {fin.date()}"
            filtro_estado.color = "#fbbf24"
            filtro_estado.update()
            return

        filtro_estado.value = f"📊 {accion_sel} | {inicio.date()} → {fin.date()}"
        filtro_estado.color = "#94a3b8"
        filtro_estado.update()

        prom_open = dff["open"].mean()
        prom_close = dff["close"].mean()
        dispersion = dff["dispersion_pct"].mean()
        avg_growth = dff["growth_rate"].mean()
        max_close, min_close = dff["close"].max(), dff["close"].min()

        # KPIs actualizados
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
        kpi_container.update()

        # === GRÁFICOS PRINCIPALES =============================================
        # 1. Evolución temporal
        fig, ax = plt.subplots(figsize=(9, 4))
        ax.plot(dff["date"], dff["close"], color="#00e5ff", linewidth=1.8, label="Close")
        ax.plot(dff["date"], dff["open"], color="#7e57c2", linewidth=1.2, alpha=0.7, label="Open")
        style_chart(ax, f"Evolución temporal de {accion_sel}")
        ax.legend(facecolor="#1e293b", edgecolor="none", labelcolor="#cbd5e1", fontsize=8)
        charts[0].src_base64 = fig_to_base64(fig)

        # 2. Dispersión diaria
        fig, ax = plt.subplots(figsize=(9, 4))
        sns.boxplot(y=dff["dispersion_pct"], color="#00e5ff55", ax=ax)
        style_chart(ax, "Dispersión intradía (%)")
        charts[1].src_base64 = fig_to_base64(fig)

        # 3. Promedio móvil
        dff["rolling"] = dff["close"].rolling(window=10).mean()
        fig, ax = plt.subplots(figsize=(9, 4))
        ax.plot(dff["date"], dff["close"], color="#00e5ff", alpha=0.7, linewidth=1.2)
        ax.plot(dff["date"], dff["rolling"], color="#4caf50", linewidth=2)
        style_chart(ax, "Promedio móvil (10 días)")
        charts[2].src_base64 = fig_to_base64(fig)

        # 4. Top 5 volumen global
        top5 = df.groupby("Name")["volume"].sum().sort_values(ascending=False).head(5).reset_index()
        fig, ax = plt.subplots(figsize=(9, 4))
        sns.barplot(x="Name", y="volume", data=top5, hue="Name", legend=False, palette="cool", ax=ax)
        style_chart(ax, "Top 5 acciones por volumen total")

        charts[3].src_base64 = fig_to_base64(fig)

        # 5. Volumen medio diario por acción (nuevo)
        avg_vol = df.groupby("Name")["volume"].mean().sort_values(ascending=False).head(10).reset_index()
        fig, ax = plt.subplots(figsize=(9, 4))
        sns.barplot(x="Name", y="volume", data=avg_vol, hue="Name", legend=False, palette="mako", ax=ax)
        style_chart(ax, "Volumen medio diario (Top 10)")
        charts[4].src_base64 = fig_to_base64(fig)

        # 6. Dispersión mensual promedio
        dff["month"] = dff["date"].dt.to_period("M")
        disp_month = dff.groupby("month")["dispersion_pct"].mean().reset_index()
        fig, ax = plt.subplots(figsize=(9, 4))
        ax.plot(disp_month["month"].astype(str), disp_month["dispersion_pct"], marker="o", color="#ffb74d")
        style_chart(ax, "Volatilidad promedio mensual (%)")
        plt.xticks(rotation=45)
        charts[5].src_base64 = fig_to_base64(fig)

        # 7. Open vs Close scatter
        fig, ax = plt.subplots(figsize=(9, 4))
        ax.scatter(dff["open"], dff["close"], color="#00e5ff55", s=15)
        style_chart(ax, "Relación Open vs Close")
        charts[6].src_base64 = fig_to_base64(fig)

        # 8. Heatmap de crecimiento mensual
        dff["year"] = dff["date"].dt.year
        dff["month"] = dff["date"].dt.month
        heat = dff.groupby(["year", "month"])["growth_rate"].mean().unstack()
        fig, ax = plt.subplots(figsize=(9, 5))
        sns.heatmap(heat, cmap="coolwarm", center=0, ax=ax)
        style_chart(ax, "Mapa de calor de crecimiento promedio (%)")
        charts[7].src_base64 = fig_to_base64(fig)

        for c in charts:
            c.update()

    btn_filtrar.on_click = actualizar_dashboard

    # === GRID ================================================================
    grid = ft.ResponsiveRow(
        [
            ft.Container(create_chart_container("Evolución temporal", charts[0]), col={"xs": 12, "md": 6}),
            ft.Container(create_chart_container("Dispersión intradía", charts[1]), col={"xs": 12, "md": 6}),
            ft.Container(create_chart_container("Promedio móvil", charts[2]), col={"xs": 12, "md": 6}),
            ft.Container(create_chart_container("Top 5 volumen", charts[3]), col={"xs": 12, "md": 6}),
            ft.Container(create_chart_container("Volumen medio diario", charts[4]), col={"xs": 12, "md": 6}),
            ft.Container(create_chart_container("Volatilidad mensual", charts[5]), col={"xs": 12, "md": 6}),
            ft.Container(create_chart_container("Open vs Close", charts[6]), col={"xs": 12, "md": 6}),
            ft.Container(create_chart_container("Mapa de calor crecimiento", charts[7]), col={"xs": 12, "md": 12}),
        ],
        alignment="center",
        spacing=25,
        run_spacing=25,
    )

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
