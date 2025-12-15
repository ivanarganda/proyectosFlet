-- KPIS
-- Total equipos liga
SELECT COUNT(*) FROM equipos e;

-- Promedio de goles
SELECT AVG( partidos.goles_local ) + AVG( partidos.goles_local ) FROM partidos;

-- Total equipos liga
WITH stats_por_jornada AS (
    SELECT
        p.id_jornada,

        -- Victorias = 1 punto
        SUM(
            CASE
                WHEN p.goles_local > p.goles_visitante THEN 1
                WHEN p.goles_visitante > p.goles_local THEN 1
                ELSE 0
            END
        ) AS victorias,

        -- Empates = 0.5 puntos
        SUM(
            CASE
                WHEN p.goles_local = p.goles_visitante THEN 0.5
                ELSE 0
            END
        ) AS empates

    FROM partidos p
    GROUP BY p.id_jornada
),
jornadas_ref AS (
    SELECT
        MAX(id_jornada) AS jornada_actual,
        (
            SELECT id_jornada
            FROM jornadas
            WHERE id_jornada < (SELECT MAX(id_jornada) FROM jornadas)
            ORDER BY id_jornada DESC
            LIMIT 1
        ) AS jornada_anterior
    FROM jornadas
),
j_actual AS (
    SELECT
        id_jornada,
        (victorias + empates) / 10 AS kd
    FROM stats_por_jornada s
    JOIN jornadas_ref j
        ON s.id_jornada = j.jornada_actual
),
j_anterior AS (
    SELECT
        id_jornada,
        (victorias + empates) / 10 AS kd
    FROM stats_por_jornada s
    JOIN jornadas_ref j
        ON s.id_jornada = j.jornada_anterior
)

-- =========================
-- RESULTADO FINAL
-- =========================

SELECT
    'JORNADA ACTUAL' AS tipo,
    id_jornada,
    kd AS KD
FROM j_actual

UNION ALL

SELECT
    'JORNADA ANTERIOR' AS tipo,
    id_jornada,
    kd AS KD
FROM j_anterior

UNION ALL

SELECT
    'PORCENTAJE TOTAL' AS tipo,
    NULL AS id_jornada,
    ( ROUND(
        j_actual.kd /
        NULLIF(j_anterior.kd, 0),
        2
    ) - 1 ) || "%" AS KD
FROM j_actual
CROSS JOIN j_anterior;
-- Total gastos
SELECT
    SUM(j.precio) AS valor_total
FROM jugadores j;

-- GRAFICOS
-- Promedo de goles por jugador y equipo usando BAR CHART
select
    id_jugador,
    avg( goals )
from jugadores_stats
where id_equipo = 2814
group by id_jugador;

-- Clasificacion por equipos usando BUMPY CHART
WITH resultados AS (
            -- Local
            SELECT
                p.id_local AS id_equipo,
                CASE
                    WHEN p.goles_local > p.goles_visitante THEN 3
                    WHEN p.goles_local = p.goles_visitante THEN 1
                    ELSE 0
                END AS puntos,
                p.goles_local AS gf,
                p.goles_visitante AS gc,
                CASE WHEN p.goles_local > p.goles_visitante THEN 1 ELSE 0 END AS victorias,
                CASE WHEN p.goles_local = p.goles_visitante THEN 1 ELSE 0 END AS empates,
                CASE WHEN p.goles_local < p.goles_visitante THEN 1 ELSE 0 END AS derrotas
            FROM partidos p

            UNION ALL

            -- Visitante
            SELECT
                p.id_visitante AS id_equipo,
                CASE
                    WHEN p.goles_visitante > p.goles_local THEN 3
                    WHEN p.goles_visitante = p.goles_local THEN 1
                    ELSE 0
                END AS puntos,
                p.goles_visitante AS gf,
                p.goles_local AS gc,
                CASE WHEN p.goles_visitante > p.goles_local THEN 1 ELSE 0 END AS victorias,
                CASE WHEN p.goles_visitante = p.goles_local THEN 1 ELSE 0 END AS empates,
                CASE WHEN p.goles_visitante < p.goles_local THEN 1 ELSE 0 END AS derrotas
            FROM partidos p
        ),

        clasificacion AS (
            SELECT
                e.id_equipo,
                e.nombre AS equipo,
                SUM(r.puntos) AS puntos,
                SUM(r.victorias) AS victorias,
                SUM(r.empates) AS empates,
                SUM(r.derrotas) AS derrotas,
                SUM(r.gf) AS goles_favor,
                SUM(r.gc) AS goles_contra,
                SUM(r.gf) - SUM(r.gc) AS diferencia_goles,
                RANK() OVER (
                    ORDER BY
                        SUM(r.puntos) DESC,
                        (SUM(r.gf) - SUM(r.gc)) DESC,
                        SUM(r.gf) DESC,
                        SUM(r.gc) ASC
                ) AS posicion
            FROM resultados r
            JOIN equipos e ON e.id_equipo = r.id_equipo
            GROUP BY e.id_equipo, e.nombre
        )

        SELECT *
        FROM clasificacion
        ORDER BY puntos DESC, diferencia_goles DESC, goles_favor DESC, goles_contra ASC;

-- Tabla de estadisticas por jugador
WITH _faltas AS ( select
    sub.faltas,
    sub.id_jugador,
    sub.totalShoots,
    FLOOR(sub.faltas % 2) AS rojas,
    faltas - FLOOR(sub.faltas % 2) AS amarillas
from (select id_jugador as id_jugador, COUNT(fouls) as faltas, SUM(totalShots) as totalShoots
               from jugadores_stats
               GROUP BY id_jugador
) as sub )
SELECT
    (
        select nombre from jugadores where id_jugador = f.id_jugador
    ) as jugador
    ,
    f.faltas,
    f.amarillas,
    f.rojas,
    ROUND(
        SUM(
                CASE
                    WHEN f.rojas > 0 THEN 1 ELSE 0
                END
        ), 0
    ) AS expulsiones,
    f.totalShoots
FROM _faltas f
GROUP BY f.id_jugador;

-- Valor de mercado
SELECT
    j.nombre,
    (select nombre from equipos where j.id_equipo = id_equipo) as equipo,
    j.precio
FROM jugadores j