import flet as ft
from params import ICONS

# ML
def build_card_prediccion_partidos(item):

    # COLORES SEGÚN PREDICCIÓN
    pred = item["prediccion"]
    color_pred = (
        "#4CAF50" if "Local" in pred else 
        "#E53935" if "Visitante" in pred else 
        "#1976D2"
    )

    # BARRAS DE PROBABILIDAD
    prob_local = float(item["prob_local"])
    prob_visit = float(item["prob_visit"])
    prob_empate = float(item["prob_empate"])

    return ft.Container(
        padding=12,
        margin=6,
        border_radius=12,
        bgcolor="white",
        shadow=ft.BoxShadow(
            blur_radius=12,
            spread_radius=1,
            color=ft.colors.with_opacity(0.15, "black"),
        ),
        content=ft.Column(
            [
                # =========================
                #     EQUIPOS Y ESCUDOS
                # =========================
                ft.Row(
                    [
                        # Local
                        ft.Column(
                            [
                                ft.Container(
                                    image_src=f"/static/escudos/{item['id_local']}.png",
                                    width=40, height=40,
                                ),
                                ft.Text(item["local"], size=13, color="grey"),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),

                        ft.Text("VS", size=16, weight="bold"),

                        # Visitante
                        ft.Column(
                            [
                                ft.Container(
                                    image_src=f"/static/escudos/{item['id_visitante']}.png",
                                    width=40, height=40,
                                ),
                                ft.Text(item["visitante"], size=13, color="grey"),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),

                ft.Divider(height=10),

                # =========================
                #     PREDICCIÓN
                # =========================
                ft.Text(
                    f"Predicción: {item['prediccion']}",
                    size=16,
                    weight="bold",
                    color=color_pred,
                    text_align=ft.TextAlign.CENTER,
                ),

                ft.Divider(height=5),

                # =========================
                #     PROBABILIDADES
                # =========================
                ft.Column(
                    [
                        ft.Text("Probabilidades", size=13, weight="bold", color="grey"),

                        ft.Row([
                            ft.Text("Local", width=60),
                            ft.ProgressBar(value=prob_local, width=160),
                            ft.Text(f"{prob_local*100:.0f}%", width=40),
                        ]),

                        ft.Row([
                            ft.Text("Empate", width=60),
                            ft.ProgressBar(value=prob_empate, width=160, color="blue"),
                            ft.Text(f"{prob_empate*100:.0f}%", width=40),
                        ]),

                        ft.Row([
                            ft.Text("Visitante", width=60),
                            ft.ProgressBar(value=prob_visit, width=160, color="red"),
                            ft.Text(f"{prob_visit*100:.0f}%", width=40),
                        ]),
                    ],
                    spacing=4
                ),

                ft.Divider(height=10),

                # =========================
                #     ESTADÍSTICAS PREVIAS
                # =========================
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text("FORM Local", size=12, color="grey"),
                                ft.Text(str(item["form_local"]), size=14, weight="bold"),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER
                        ),
                        ft.Column(
                            [
                                ft.Text("FORM Visit.", size=12, color="grey"),
                                ft.Text(str(item["form_visit"]), size=14, weight="bold"),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_EVENLY
                ),
            ],
            spacing=10,
        ),
    )



# INFO
def build_jugadores_card(item):

    m_color = {
        "D": "#1E88E5",
        "G": "#43A047",
        "F": "#FB8C00",
        "M": "#E53935"
    }.get(item["posicion"], "grey")

    icon = item.get( "escudo")

    return ft.Container(
        padding=12,
        bgcolor="white",
        border_radius=12,
        shadow=ft.BoxShadow(blur_radius=12, color="#00000030"),
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Image(src=ICONS["profile_photo_football_player"], width=70, height=70, fit=ft.ImageFit.COVER),
                        ft.Image(src=icon, width=25, height=25, fit=ft.ImageFit.COVER)
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                ft.Text(item["nombre"], size=16, weight="bold"),
                ft.Text(item["posicion"], size=12, color=m_color),
                ft.Text(item["equipo"], size=12, color="grey"),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
    )

def build_equipo_card(item):
    return ft.Container(
        padding=12,
        border_radius=12,
        bgcolor="white",
        shadow=ft.BoxShadow(blur_radius=10, spread_radius=1, color=ft.colors.with_opacity(0.1, "black")),
        content=ft.Column(
            [
                ft.Image(src=item["escudo"], width=60, height=60),
                ft.Text(f"🏟 {item['estadio']}", size=12, color="grey"),
                ft.Text(item["nombre"], size=16, weight="bold")
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=6
        )
    )

def build_card_estadios( item ):

    return ft.Container(
        padding=12,
        margin=6,
        border_radius=12,
        bgcolor="white",
        shadow=ft.BoxShadow(
            blur_radius=10,
            spread_radius=1,
            color=ft.colors.with_opacity(0.15, "black"),
        ),
        content=ft.Column(
            [
                # ESTADIO Y HORA
                ft.Row(
                    [
                        ft.Column([
                            ft.Text(f"🏟️ {item['nombre']}", color="grey", size=12),
                            ft.Text(f"🌍 {item['lugar']}", color="grey", size=12),
                            ft.Text(f"⚖️ {item['capacidad']}", color="grey", size=12),
                            ft.Text(f"🛗 {item['equipo']}", color="grey", size=12),
                        ])
                        
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                )
            ],
            spacing=8
        )

    )


def build_card_partidos( item ):

    color_local = "green" if item["goles_local"] > item["goles_visitante"] else "grey"
    color_visit = "green" if item["goles_visitante"] > item["goles_local"] else "grey"

    return ft.Container(
        padding=12,
        margin=6,
        border_radius=12,
        bgcolor="white",
        shadow=ft.BoxShadow(
            blur_radius=10,
            spread_radius=1,
            color=ft.colors.with_opacity(0.15, "black"),
        ),
        content=ft.Column(
            [
                # ESCUDOS Y NOMBRES
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Container(
                                    image_src=item["escudo_local"],
                                    image_fit=ft.ImageFit.COVER,
                                    width=25,
                                    height=25,
                                ),
                                ft.Text(item["local"], color="grey")
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Column(
                            [
                                ft.Container(
                                    image_src=item["escudo_visitante"],
                                    image_fit=ft.ImageFit.COVER,
                                    width=25,
                                    height=25,
                                ),
                                ft.Text(item["visitante"], color="grey")
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                ),

                # ESTADIO Y HORA
                ft.Row(
                    [
                        ft.Column([
                            ft.Text(f"🏟 {item['estadio']}", color="grey", size=12),
                            ft.Text(f"⏱ {item['inicio']}", color="grey", size=12),
                        ])
                        
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                ),

                # RESULTADO
                ft.Row(
                    [
                        ft.Text(str(item["goles_local"]), color=color_local, size=22),
                        ft.Text("-", size=22),
                        ft.Text(str(item["goles_visitante"]), color=color_visit, size=22),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                )
            ],
            spacing=8
        )
    )

def RenderList(title, loading_text, list_container, callback, extra_footer=None):

    return ft.Column(
        [
            # ---------- TÍTULO ----------
            ft.Text(
                f"📋 {title}",
                size=24,
                weight="bold",
                color="white",
            ),

            ft.Container(
                height=3,
                bgcolor="white",
                opacity=0.15,
                border_radius=20,
                margin=ft.margin.only(bottom=12),
            ),

            loading_text,

            # Recargar
            ft.Row(
                [
                    ft.TextButton(
                        "↻ Recargar datos",
                        icon=ft.Icons.REFRESH,
                        style=ft.ButtonStyle(
                            color="#1565C0",
                            overlay_color="#E3F2FD",
                        ),
                        on_click=lambda e: callback(),
                    )
                ],
                alignment=ft.MainAxisAlignment.END,
            ),

            # ---------- CARD DE LISTA ----------
            ft.Container(
                bgcolor="white",
                padding=15,
                border_radius=12,
                shadow=ft.BoxShadow(
                    blur_radius=22,
                    spread_radius=1,
                    color=ft.colors.with_opacity(0.10, "black"),
                    offset=ft.Offset(0, 4),
                ),
                content=ft.Column(
                    [
                        list_container,  # Aquí se cargan los items de la lista

                        ft.Container(
                            extra_footer,
                            padding=10,
                            alignment=ft.alignment.center
                        ) if extra_footer else ft.Container(),
                    ],
                    spacing=10,
                ),
                expand=True,
            ),
        ],
        expand=True,
        spacing=20
    )


def RenderTable(title, loading_text, content_table, callback, extra_footer=None):

    return ft.Column(
        [
            # Título
            ft.Text(
                f"📊 {title}",
                size=22,
                weight="bold",
                color="white",
            ),

            ft.Container(
                height=1,
                bgcolor="#E0E0E0",
                margin=ft.margin.only(bottom=10),
            ),

            loading_text,

            # Botón recargar
            ft.Row(
                [
                    ft.TextButton(
                        "↻ Recargar datos",
                        icon=ft.Icons.REFRESH,
                        style=ft.ButtonStyle(
                            color="#1565C0",
                            overlay_color="#E3F2FD",
                        ),
                        on_click=lambda e: callback(),
                    )
                ],
                alignment=ft.MainAxisAlignment.END,
            ),

            # ========= 🔥 CONTENEDOR RESPONSIVE DE TABLA =========
            ft.Container(
                bgcolor="white",
                padding=10,
                border_radius=10,
                shadow=ft.BoxShadow(
                    blur_radius=12,
                    spread_radius=1,
                    color=ft.colors.with_opacity(0.08, "black"),
                ),
                content=ft.Column(
                    [
                        # tabla con scroll horizontal
                        ft.Row(
                            [content_table],
                            scroll=ft.ScrollMode.AUTO,  # ✔ solo scroll horizontal
                        ),

                        # paginación pegada a la tabla
                        ft.Container(
                            extra_footer,
                            padding=10,
                            alignment=ft.alignment.center
                        ) if extra_footer else ft.Container(),
                    ],
                    spacing=10,
                    expand=False
                ),
                expand=True
            )
        ],
        expand=True,
        spacing=15,
        scroll=ft.ScrollMode.AUTO
    )

def build_card(type_,item):

    type_ = type_.lower()

    return {  
        
        "partidos": build_card_partidos,
        "estadios": build_card_estadios,
        "equipos": build_equipo_card, 
        "jugadores": build_jugadores_card, 
        "ml_partidos_prediccion": build_card_prediccion_partidos 
    
    }.get(type_, ft.Text("❌ Not fuund card") )(item) 
    