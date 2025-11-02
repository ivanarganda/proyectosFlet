import os
import io
import base64
import flet as ft
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import datetime


# === CONVERTIR FIGURA A BASE64 ==================================================
def fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=150)
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return img_b64


# === COMPONENTES UI =============================================================
def create_kpi_card(title, value, icon, color="#00e5ff"):
    """Tarjeta KPI moderna con hover, sombra y adaptabilidad."""
    card = ft.Container(
        content=ft.Column(
            [
                ft.Icon(icon, size=36, color=color),
                ft.Text(title, color="white", size=12),
                ft.Text(value, color="white", size=22, weight="bold"),
            ],
            alignment="center",
            horizontal_alignment="center",
            spacing=3,
        ),
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=["#1a2035aa", "#0b0f1acc"],
        ),
        border_radius=18,
        padding=15,
        border=ft.border.all(1, color="#00e5ff33"),
        shadow=ft.BoxShadow(blur_radius=10, color="#00000088", offset=ft.Offset(0, 3)),
        col={"xs": 12, "sm": 6, "md": 4, "lg": 2},
        animate=ft.animation.Animation(350, "easeOut"),
    )

    def on_hover(e: ft.HoverEvent):
        if e.data == "true":
            card.scale = ft.transform.Scale(1.05)
            card.shadow = ft.BoxShadow(blur_radius=16, color=f"{color}55", offset=ft.Offset(0, 4))
        else:
            card.scale = ft.transform.Scale(1.0)
            card.shadow = ft.BoxShadow(blur_radius=10, color="#00000088", offset=ft.Offset(0, 3))
        card.update()

    card.on_hover = on_hover
    return card


def create_chart_container(title, chart):
    """Contenedor estilizado para gráficos."""
    return ft.Container(
        content=ft.Column(
            [
                ft.Text(title, color="#00e5ff", size=18, weight="bold"),
                ft.Divider(color="#00e5ff33"),
                chart,
            ],
            spacing=10,
        ),
        bgcolor="#141a29",
        border_radius=16,
        padding=20,
        expand=True,
        shadow=ft.BoxShadow(blur_radius=12, color="#00000055"),
    )


# === DASHBOARD PRINCIPAL ========================================================
def main(page: ft.Page):
    page.title = "💹 Dashboard Financiero Premium"
    page.bgcolor = ft.LinearGradient(
        begin=ft.alignment.top_left,
        end=ft.alignment.bottom_right,
        colors=["#0b0f1a", "#141a29"],
    )
    page.padding = 25
    page.scroll = "auto"
    page.horizontal_alignment = "center"

    # --- DATASET ---
    DATASET_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "all_stocks_5yr.csv")
    df = pd.read_csv(DATASET_PATH)
    df["date"] = pd.to_datetime(df["date"])
    df["dispersion_pct"] = (df["high"] - df["low"]) / df["low"] * 100
    df["growth_rate"] = df.groupby("Name")["close"].pct_change() * 100

    acciones = sorted(df["Name"].unique())
    MIN_DATE_TS, MAX_DATE_TS = df["date"].min(), df["date"].max()
    MIN_DATE, MAX_DATE = MIN_DATE_TS.date(), MAX_DATE_TS.date()

    # --- CABECERA ---
    header = ft.Row(
        [
            ft.Icon(ft.Icons.SHOW_CHART, color="#00e5ff", size=32),
            ft.Text("Dashboard Financiero Premium", size=26, weight="bold", color="#00e5ff"),
        ],
        alignment="center",
        spacing=10,
        wrap=True,
    )

    # === DatePickers ===
    picker_inicio = ft.DatePicker(
        value=MIN_DATE,
        first_date=MIN_DATE,
        last_date=MAX_DATE,
        date_picker_entry_mode=ft.DatePickerEntryMode.CALENDAR_ONLY,
    )
    picker_fin = ft.DatePicker(
        value=MAX_DATE,
        first_date=MIN_DATE,
        last_date=MAX_DATE,
        date_picker_entry_mode=ft.DatePickerEntryMode.CALENDAR_ONLY,
    )
    page.overlay.extend([picker_inicio, picker_fin])

    date_inicio = ft.ElevatedButton(
        "📅 Desde",
        on_click=lambda e: picker_inicio.pick_date(),
        bgcolor="#5A2D9C",
        color="white",
        width=160,
    )
    date_fin = ft.ElevatedButton(
        "📅 Hasta",
        on_click=lambda e: picker_fin.pick_date(),
        bgcolor="#5A2D9C",
        color="white",
        width=160,
    )

    combo_accion = ft.Dropdown(
        label="Seleccionar acción",
        options=[ft.dropdown.Option(a) for a in acciones],
        value=acciones[0],
        width=220,
        bgcolor="#141a29",
        color="white",
        border_color="#00e5ff",
        focused_border_color="#00e5ff",
    )

    filtro_estado = ft.Text(
        f"📆 Del {MIN_DATE} al {MAX_DATE} | Acción: {acciones[0]}",
        color="#00e5ff",
        size=14,
        italic=True,
        text_align="center",
    )

    btn_filtrar = ft.ElevatedButton(
        text="Aplicar filtro",
        icon=ft.Icons.FILTER_ALT,
        bgcolor="#00e5ff",
        color="black",
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
    )

    # === PANEL DE FILTROS MEJORADO ===
    filtro_panel = ft.Container(
        content=ft.Column(
            [
                ft.ResponsiveRow(
                    [
                        ft.Container(ft.Column([ft.Text("Fecha inicio", color="#00e5ff"), date_inicio]), col={"xs": 12, "md": 3}),
                        ft.Container(ft.Column([ft.Text("Fecha fin", color="#00e5ff"), date_fin]), col={"xs": 12, "md": 3}),
                        ft.Container(ft.Column([ft.Text("Acción", color="#00e5ff"), combo_accion]), col={"xs": 12, "md": 3}),
                        ft.Container(ft.Column([ft.Text(" "), btn_filtrar]), col={"xs": 12, "md": 3}),
                    ],
                    alignment="center",
                    spacing=10,
                    run_spacing=10,
                ),
                ft.Divider(color="#00e5ff33"),
                filtro_estado,
            ],
            spacing=15,
            horizontal_alignment="center",
        ),
        bgcolor="#1a2035aa",
        border_radius=20,
        padding=20,
        shadow=ft.BoxShadow(blur_radius=12, color="#00000055"),
    )

    # === PLACEHOLDER DE GRÁFICOS ===
    transparent_placeholder = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mO0t7e5HgAFGwJ/lQ8m"
        "1QAAAABJRU5ErkJggg=="
    )

    def placeholder_chart():
        return ft.Container(
            content=ft.Image(src_base64=transparent_placeholder, fit=ft.ImageFit.CONTAIN, expand=True),
            bgcolor="#141a29",
            border_radius=12,
            padding=10,
            expand=True,
        )

    chart1, chart2, chart3, chart4, chart5 = [placeholder_chart() for _ in range(5)]

    # === KPIs ============================================================
    kpi_row = ft.ResponsiveRow(
        [
            create_kpi_card("Promedio Open", "--", ft.Icons.TRENDING_UP),
            create_kpi_card("Promedio Close", "--", ft.Icons.TRENDING_DOWN, "#ff9800"),
            create_kpi_card("Dispersión Media", "--", ft.Icons.PERCENT, "#cddc39"),
            create_kpi_card("Registros", "--", ft.Icons.DATA_USAGE, "#26a69a"),
            create_kpi_card("Máx Close", "--", ft.Icons.ARROW_UPWARD, "#4caf50"),
            create_kpi_card("Mín Close", "--", ft.Icons.ARROW_DOWNWARD, "#ef5350"),
        ],
        alignment="center",
        spacing=12,
    )

    kpi_container = ft.Container(content=kpi_row, alignment=ft.alignment.center, padding=10)

    # === FUNCIÓN ACTUALIZAR DASHBOARD ============================================
    def actualizar_dashboard(e=None):
        accion_sel = combo_accion.value

        if not picker_inicio.value or not picker_fin.value:
            return

        inicio = pd.to_datetime(picker_inicio.value)
        fin = pd.to_datetime(picker_fin.value)

        if inicio > fin:
            inicio, fin = fin, inicio

        dff = df[(df["Name"] == accion_sel) & (df["date"].between(inicio, fin))]

        if dff.empty:
            filtro_estado.value = f"⚠️ No hay datos entre {inicio.date()} y {fin.date()} para {accion_sel}"
            filtro_estado.color = "#ff9800"
            filtro_estado.update()
            return

        filtro_estado.value = f"📆 Del {inicio.date()} al {fin.date()} | Acción: {accion_sel}"
        filtro_estado.color = "#00e5ff"
        filtro_estado.update()

        prom_open = dff["open"].mean()
        prom_close = dff["close"].mean()
        dispersion = dff["dispersion_pct"].mean()
        total_registros = len(dff)
        max_close = dff["close"].max()
        min_close = dff["close"].min()
        avg_growth = dff["growth_rate"].mean()

        new_kpi_row = ft.ResponsiveRow(
            [
                create_kpi_card("Promedio Open", f"${prom_open:,.2f}", ft.Icons.TRENDING_UP),
                create_kpi_card("Promedio Close", f"${prom_close:,.2f}", ft.Icons.TRENDING_DOWN, "#ff9800"),
                create_kpi_card("Dispersión Media", f"{dispersion:.2f}%", ft.Icons.PERCENT, "#cddc39"),
                create_kpi_card("Promedio Crecimiento", f"{avg_growth:.2f}%", ft.Icons.TRENDING_FLAT, "#7e57c2"),
                create_kpi_card("Máx Close", f"${max_close:,.2f}", ft.Icons.ARROW_UPWARD, "#4caf50"),
                create_kpi_card("Mín Close", f"${min_close:,.2f}", ft.Icons.ARROW_DOWNWARD, "#ef5350"),
            ],
            alignment="center",
            spacing=12,
        )
        kpi_container.content = new_kpi_row
        kpi_container.update()

        # === GRÁFICOS ===
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(dff["date"], dff["open"], label="Open", color="#00e5ff", linewidth=2)
        ax.plot(dff["date"], dff["close"], label="Close", color="#ff9800", linewidth=2)
        ax.set_title(f"Evolución temporal de {accion_sel}", color="white")
        ax.legend()
        ax.grid(True, alpha=0.2)
        ax.set_facecolor("#141a29")
        fig.patch.set_facecolor("#0b0f1a")
        chart1.content.src_base64 = fig_to_base64(fig)

        top5 = df.groupby("Name")["volume"].sum().sort_values(ascending=False).head(5).reset_index()
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.bar(top5["Name"], top5["volume"], color="#00e5ff")
        ax.set_title("Top 5 acciones por volumen total", color="white")
        ax.set_xlabel("Acción", color="white")
        ax.set_ylabel("Volumen", color="white")
        ax.set_facecolor("#141a29")
        fig.patch.set_facecolor("#0b0f1a")
        plt.xticks(rotation=25, color="white")
        plt.yticks(color="white")
        chart2.content.src_base64 = fig_to_base64(fig)

        fig, ax = plt.subplots(figsize=(10, 4))
        dff.boxplot(column="dispersion_pct", ax=ax, patch_artist=True)
        ax.set_title("Dispersión (%)", color="white")
        ax.set_ylabel("%", color="white")
        ax.set_facecolor("#141a29")
        fig.patch.set_facecolor("#0b0f1a")
        plt.yticks(color="white")
        chart3.content.src_base64 = fig_to_base64(fig)

        dff = dff.copy()
        dff["rolling_mean"] = dff["close"].rolling(window=10).mean()
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(dff["date"], dff["close"], color="#00e5ff", label="Close", linewidth=1.8)
        ax.plot(dff["date"], dff["rolling_mean"], color="#7e57c2", linewidth=2.2, label="Promedio móvil (10d)")
        ax.legend()
        ax.set_title("Promedio móvil del precio de cierre", color="white")
        ax.grid(True, alpha=0.3)
        ax.set_facecolor("#141a29")
        fig.patch.set_facecolor("#0b0f1a")
        chart4.content.src_base64 = fig_to_base64(fig)

        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(dff["date"], dff["growth_rate"], color="#4caf50", linewidth=1.5)
        ax.axhline(0, color="white", alpha=0.3)
        ax.set_title("Tasa diaria de crecimiento (%)", color="white")
        ax.set_ylabel("Variación %", color="white")
        ax.grid(True, alpha=0.3)
        ax.set_facecolor("#141a29")
        fig.patch.set_facecolor("#0b0f1a")
        plt.yticks(color="white")
        plt.xticks(rotation=25, color="white")
        chart5.content.src_base64 = fig_to_base64(fig)

        for ch in [chart1, chart2, chart3, chart4, chart5]:
            ch.update()

    btn_filtrar.on_click = actualizar_dashboard

    # === LAYOUT FINAL ============================================================
    chart_grid = ft.ResponsiveRow(
        [
            ft.Container(create_chart_container("Evolución temporal", chart1), col={"xs": 12, "md": 6}),
            ft.Container(create_chart_container("Top 5 por volumen", chart2), col={"xs": 12, "md": 6}),
            ft.Container(create_chart_container("Dispersión por acción", chart3), col={"xs": 12, "md": 6}),
            ft.Container(create_chart_container("Promedio móvil (10 días)", chart4), col={"xs": 12, "md": 6}),
            ft.Container(create_chart_container("Tasa de crecimiento (%)", chart5), col={"xs": 12, "md": 12}),
        ],
        alignment="center",
        vertical_alignment="center",
        spacing=25,
        run_spacing=25,
    )

    page.add(
        header,
        ft.Divider(height=20),
        filtro_panel,
        ft.Divider(height=35),
        kpi_container,
        ft.Divider(height=35),
        chart_grid
    )

    actualizar_dashboard()
    page.update()


# === EJECUTAR APP ===============================================================
if __name__ == "__main__":
    ft.app(target=main)
