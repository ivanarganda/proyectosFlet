import flet as ft
from params import ICONS

TEXT_MAIN = "#1F2937"     # gris oscuro (texto principal)
TEXT_SECONDARY = "#6B7280"  # gris medio
BG_CARD = "white"


def build_card_prediccion_partidos(item):

    # =========================
    # COLORES SEGÚN PREDICCIÓN
    # =========================
    pred = item.get("prediccion", "")
    color_pred = (
        "#16A34A" if "Local" in pred else
        "#DC2626" if "Visitante" in pred else
        "#2563EB"
    )

    prob_local = float(item.get("prob_local", 0))
    prob_empate = float(item.get("prob_empate", 0))
    prob_visit = float(item.get("prob_visit", 0))

    # =========================
    # FILA PROBABILIDAD
    # =========================
    def prob_row(label, value, color):
        return ft.Row(
            controls=[
                ft.Text(
                    label,
                    width=70,
                    size=12,
                    color=TEXT_SECONDARY,
                ),
                ft.ProgressBar(
                    value=value,
                    expand=True,
                    height=8,
                    color=color,
                    bgcolor="#E5E7EB",
                    border_radius=6,
                ),
                ft.Text(
                    f"{value*100:.0f}%",
                    width=42,
                    size=12,
                    color=TEXT_MAIN,
                ),
            ],
            spacing=10,
        )

    # =========================
    # CARD
    # =========================
    return ft.Container(
        margin=ft.margin.symmetric(horizontal=12, vertical=8),
        padding=18,
        border_radius=18,
        bgcolor=BG_CARD,
        shadow=ft.BoxShadow(
            blur_radius=22,
            spread_radius=1,
            color=ft.colors.with_opacity(0.18, "black"),
            offset=ft.Offset(0, 6),
        ),
        content=ft.Column(
            spacing=16,
            controls=[
                # =========================
                # EQUIPOS
                # =========================
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Image(
                                    src=f"/static/escudos/{item['id_local']}.png",
                                    width=48,
                                    height=48,
                                    fit=ft.ImageFit.CONTAIN,
                                ),
                                ft.Text(
                                    item.get("local", ""),
                                    size=13,
                                    weight=ft.FontWeight.W_600,
                                    color=TEXT_MAIN,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                            ],
                        ),

                        ft.Text(
                            "VS",
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            color=TEXT_SECONDARY,
                        ),

                        ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Image(
                                    src=f"/static/escudos/{item['id_visitante']}.png",
                                    width=48,
                                    height=48,
                                    fit=ft.ImageFit.CONTAIN,
                                ),
                                ft.Text(
                                    item.get("visitante", ""),
                                    size=13,
                                    weight=ft.FontWeight.W_600,
                                    color=TEXT_MAIN,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                            ],
                        ),
                    ],
                ),

                # =========================
                # BADGE PREDICCIÓN
                # =========================
                ft.Container(
                    alignment=ft.alignment.center,
                    padding=ft.padding.symmetric(horizontal=14, vertical=6),
                    border_radius=20,
                    bgcolor=ft.colors.with_opacity(0.12, color_pred),
                    content=ft.Text(
                        pred,
                        size=14,
                        weight=ft.FontWeight.BOLD,
                        color=color_pred,
                    ),
                ),

                # =========================
                # PROBABILIDADES
                # =========================
                ft.Column(
                    spacing=8,
                    controls=[
                        ft.Text(
                            "Probabilidades",
                            size=13,
                            weight=ft.FontWeight.W_600,
                            color=TEXT_MAIN,
                        ),
                        prob_row("Local", prob_local, "#16A34A"),
                        prob_row("Empate", prob_empate, "#2563EB"),
                        prob_row("Visitante", prob_visit, "#DC2626"),
                    ],
                ),
            ],
        ),
    )

    

def build_card(type_,item):

    type_ = type_.lower()

    return {  
         
        "ml_partidos_prediccion": build_card_prediccion_partidos 
    
    }.get(type_, ft.Text("❌ Not fuund card") )(item) 
    