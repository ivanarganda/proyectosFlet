import flet as ft
import matplotlib.pyplot as plt
import math
from io import BytesIO
import base64

# ----------------------------
#  COMPONENTE KPI
# ----------------------------
def kpi(title, value, color):
    return ft.Container(
        bgcolor=color,
        border_radius=10,
        padding=10,
        width=110,
        height=80,
        content=ft.Column(
            [
                ft.Text(title, size=12, color="white"),
                ft.Text(str(value), size=22, weight="bold", color="white")
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
    )


# ----------------------------
#  RADAR CHART
# ----------------------------
class RadarChart(ft.UserControl):
    def __init__(self, labels, values, size=300):
        super().__init__()
        self.labels = labels
        self.values = values
        self.size = size

    def build(self):
        img_data = self._create_radar_image()
        return ft.Image(src_base64=img_data, width=self.size, height=self.size)

    def _create_radar_image(self):
        labels = self.labels
        values = self.values

        N = len(values)
        angles = [n / float(N) * 2 * math.pi for n in range(N)]
        values = values + values[:1]
        angles = angles + angles[:1]

        fig, ax = plt.subplots(figsize=(3, 3), subplot_kw=dict(polar=True))

        ax.set_theta_offset(math.pi / 2)
        ax.set_theta_direction(-1)

        ax.plot(angles, values, linewidth=2)
        ax.fill(angles, values, alpha=0.3)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels)

        buf = BytesIO()
        plt.savefig(buf, format="png", dpi=120, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)

        return base64.b64encode(buf.read()).decode("utf-8")



# ----------------------------
#  TAB ATAQUE
# ----------------------------
def ataque_tab(stats):

    goles = sum(s.get("goals", 0) for s in stats)
    tiros = sum(s.get("totalShots", 0) for s in stats)
    xg = round(sum(s.get("expectedGoals", 0) for s in stats), 2)

    kpi_row = ft.Row(
        [
            kpi("Goles", goles, "green"),
            kpi("Tiros", tiros, "orange"),
            kpi("xG", xg, "#6A1B9A"),
        ],
        spacing=10
    )

    radar = RadarChart(
        labels=["Goles", "Tiros", "xG"],
        values=[goles, tiros, xg]
    )

    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Jornada")),
            ft.DataColumn(ft.Text("Goles")),
            ft.DataColumn(ft.Text("Tiros")),
            ft.DataColumn(ft.Text("xG")),
        ],
        rows=[
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(s["id_jornada"])),
                    ft.DataCell(ft.Text(s.get("goals", 0))),
                    ft.DataCell(ft.Text(s.get("totalShots", 0))),
                    ft.DataCell(ft.Text(s.get("expectedGoals", 0))),
                ]
            ) for s in stats
        ]
    )

    return ft.Column([ft.Text("Rendimiento Ofensivo", size=22), kpi_row, radar, table], spacing=20)


# ----------------------------
#  TAB DEFENSA
# ----------------------------
def defensa_tab(stats):

    tackles = sum(s.get("totalTackle", 0) for s in stats)
    inter = sum(s.get("interceptionWon", 0) for s in stats)
    recovery = sum(s.get("ballRecovery", 0) for s in stats)
    duels = sum(s.get("duelWon", 0) for s in stats)

    kpi_row = ft.Row(
        [
            kpi("Entradas", tackles, "#004D40"),
            kpi("Intercepciones", inter, "#1A237E"),
            kpi("Recuper.", recovery, "#4A148C"),
            kpi("Duelos", duels, "green"),
        ],
        spacing=10
    )

    radar = RadarChart(
        labels=["Entradas", "Intercepciones", "Recuper.", "Duelos"],
        values=[tackles, inter, recovery, duels]
    )

    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Jornada")),
            ft.DataColumn(ft.Text("Tackles")),
            ft.DataColumn(ft.Text("Intercep.")),
            ft.DataColumn(ft.Text("Recuper.")),
            ft.DataColumn(ft.Text("Duelos gan.")),
        ],
        rows=[
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(s["id_jornada"])),
                    ft.DataCell(ft.Text(s.get("totalTackle", 0))),
                    ft.DataCell(ft.Text(s.get("interceptionWon", 0))),
                    ft.DataCell(ft.Text(s.get("ballRecovery", 0))),
                    ft.DataCell(ft.Text(s.get("duelWon", 0))),
                ]
            ) for s in stats
        ]
    )

    return ft.Column([ft.Text("Impacto Defensivo", size=22), kpi_row, radar, table], spacing=20)


# ----------------------------
#  TAB PASES
# ----------------------------
def pases_tab(stats):

    total = sum(s.get("totalPass", 0) for s in stats)
    acc = sum(s.get("accuratePass", 0) for s in stats)

    long_total = sum(s.get("totalLongBalls", 0) for s in stats)
    long_acc = sum(s.get("accurateLongBalls", 0) for s in stats)

    precision = round(acc / total * 100, 1) if total > 0 else 0
    precision_long = round(long_acc / long_total * 100, 1) if long_total > 0 else 0

    kpi_row = ft.Row(
        [
            kpi("Pases Totales", total, "#0277BD"),
            kpi("Precisión %", precision, "green"),
            kpi("Largos %", precision_long, "orange"),
        ],
        spacing=10
    )

    radar = RadarChart(
        labels=["Totales", "Precisión", "Largos %"],
        values=[total, precision, precision_long]
    )

    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Jornada")),
            ft.DataColumn(ft.Text("Precisión")),
            ft.DataColumn(ft.Text("Pases Totales")),
            ft.DataColumn(ft.Text("Pases Largos")),
        ],
        rows=[
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(s["id_jornada"])),
                    ft.DataCell(ft.Text(f"{s.get('accuratePass',0)}/{s.get('totalPass',0)}")),
                    ft.DataCell(ft.Text(s.get("totalPass",0))),
                    ft.DataCell(ft.Text(s.get("totalLongBalls",0))),
                ]
            ) for s in stats
        ]
    )

    return ft.Column([ft.Text("Distribución y Juego", size=22), kpi_row, radar, table], spacing=20)


# ----------------------------
#  TAB GENERAL
# ----------------------------
def general_tab(stats):

    total_goals = sum(s.get("goals", 0) for s in stats)
    minutes = sum(s.get("minutesPlayed", 0) for s in stats)

    avg_rating = (
        round(sum(s.get("rating", 0) for s in stats) / len(stats), 2)
        if len(stats) > 0 else 0
    )

    kpi_row = ft.Row(
        [
            kpi("Goles", total_goals, "green"),
            kpi("Rating", avg_rating, "blue"),
            kpi("Minutos", minutes, "grey"),
        ],
        spacing=10
    )

    radar = RadarChart(
        labels=["Ataque", "Pases", "Defensa", "Rating", "Duelos"],
        values=[
            total_goals,
            sum(s.get("accuratePass", 0) for s in stats),
            sum(s.get("totalTackle", 0) for s in stats),
            avg_rating,
            sum(s.get("totalContest", 0) for s in stats)
        ]
    )

    return ft.Column([ft.Text("Resumen General", size=22), kpi_row, radar], spacing=20)
