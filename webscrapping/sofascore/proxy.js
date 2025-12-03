const express = require("express");
const { chromium } = require("playwright");
const app = express();
const PORT = 3000;

const LALIGA = 8;  // ID oficial de Sofascore

async function request_URL(res, config) {
    try {
        console.log(config.url);
        
        const browser = await chromium.launch({ headless: true });
        const page = await browser.newPage();
        let interceptedData = null;

        if (config.intercept) {
            page.on("response", async (response) => {
                if (response.url().includes(config.intercept.match)) {
                    try { interceptedData = await response.json(); } catch {}
                }
            });
        }

        await page.goto(config.url, { waitUntil: "networkidle" });

        let result;
        if (config.intercept) {
            if (!interceptedData)
                throw new Error("No se pudo interceptar la respuesta XHR");
            result = interceptedData;
        } else {
            result = JSON.parse(await page.textContent("body"));
        }

        await browser.close();

        // Evento por ronda → mapeo especial
        if (
            config.url.includes(`/season/`) &&
            config.url.includes(`/events/`) &&
            config.url.includes(`/round/`)
        ) {
            result = result.events.map(ev => ({
                id: ev.id,
                inicio: ev.startTimestamp,
                estado_partido: ev.status?.type,
                estadio: ev.venue,
                id_local: ev.homeTeam?.id,
                id_visitante: ev.awayTeam?.id,
                local: ev.homeTeam?.name,
                visitante: ev.awayTeam?.name,
                goles_local: ev.homeScore?.current || 0,
                goles_visitante: ev.awayScore?.current || 0
            }));
        }

        res.json(result);

    } catch (err) {
        res.status(500).json({ error: err.toString() });
    }
};

//
// ===========================================================
// LALIGA – COMPETICIÓN PRINCIPAL
// ===========================================================
//

// Info general del torneo LaLiga
app.get("/laliga", async (req, res) => {
    request_URL(res, { url: `https://api.sofascore.com/api/v1/unique-tournament/${LALIGA}` });
});

// Temporadas de LaLiga
app.get("/laliga/temporadas", async (req, res) => {
    request_URL(res, { url: `https://api.sofascore.com/api/v1/unique-tournament/${LALIGA}/seasons` });
});

// Equipos de LaLiga
app.get("/laliga/equipos/:id_temporada", async (req, res) => {
    request_URL(res, { url: `https://api.sofascore.com/api/v1/unique-tournament/${LALIGA}/season/${req.params.id_temporada}/teams` });
});

//
// ===========================================================
// TEMPORADA
// ===========================================================
//

// Datos de una temporada
app.get("/laliga/temporada/:id_temporada", async (req, res) => {
    request_URL(res, { url: `https://api.sofascore.com/api/v1/season/${req.params.id_temporada}` });
});

// Partidos de una temporada completa
app.get("/laliga/temporada/:id_temporada/partidos", async (req, res) => {
    request_URL(res, { url: `https://api.sofascore.com/api/v1/season/${req.params.id_temporada}/events` });
});

// Jornadas (rounds)
app.get("/laliga/temporada/:id_temporada/jornadas", async (req, res) => {
    request_URL(res, { url: `https://api.sofascore.com/api/v1/unique-tournament/${LALIGA}/season/${req.params.id_temporada}/rounds` });
});

// Partidos por jornada
app.get("/laliga/temporada/:id_temporada/jornada/:num_ronda", async (req, res) => {
    request_URL(res, {
        url: `https://api.sofascore.com/api/v1/unique-tournament/${LALIGA}/season/${req.params.id_temporada}/events/round/${req.params.num_ronda}`
    });
});

//
// ===========================================================
// EQUIPOS
// ===========================================================
//

// Info equipo
app.get("/laliga/equipo/:id_equipo", async (req, res) => {
    request_URL(res, { url: `https://api.sofascore.com/api/v1/team/${req.params.id_equipo}` });
});

// Jugadores del equipo
app.get("/laliga/equipo/:id_equipo/jugadores", async (req, res) => {
    request_URL(res, { url: `https://api.sofascore.com/api/v1/team/${req.params.id_equipo}/players` });
});

// Partidos del equipo
app.get("/laliga/equipo/:id_equipo/partidos", async (req, res) => {
    request_URL(res, { url: `https://api.sofascore.com/api/v1/team/${req.params.id_equipo}/events` });
});

// Estadísticas del equipo para una temporada
app.get("/laliga/equipo/:id_equipo/stats/:id_temporada", async (req, res) => {
    request_URL(res, {
        url: `https://api.sofascore.com/api/v1/team/${req.params.id_equipo}/unique-tournament/${LALIGA}/season/${req.params.id_temporada}/statistics`
    });
});

//
// ===========================================================
// JUGADORES
// ===========================================================
//

// Info jugador
app.get("/laliga/jugador/:id_jugador", async (req, res) => {
    request_URL(res, { url: `https://api.sofascore.com/api/v1/player/${req.params.id_jugador}` });
});

// Stats jugador global
app.get("/laliga/jugador/:id_jugador/stats", async (req, res) => {
    request_URL(res, { url: `https://api.sofascore.com/api/v1/player/${req.params.id_jugador}/statistics` });
});

// Histórico rendimiento
app.get("/laliga/jugador/:id_jugador/historico", async (req, res) => {
    request_URL(res, { url: `https://api.sofascore.com/api/v1/player/${req.params.id_jugador}/segments/overall` });
});

//
// ===========================================================
// PARTIDOS
// ===========================================================
//

// Info partido
app.get("/laliga/partido/:id_partido", async (req, res) => {
    request_URL(res, { url: `https://api.sofascore.com/api/v1/event/${req.params.id_partido}` });
});

// Stats partido
app.get("/laliga/partido/:id_partido/stats", async (req, res) => {
    request_URL(res, { url: `https://api.sofascore.com/api/v1/event/${req.params.id_partido}/statistics` });
});

// Alineaciones
app.get("/laliga/partido/:id_partido/lineups", async (req, res) => {
    request_URL(res, { url: `https://api.sofascore.com/api/v1/event/${req.params.id_partido}/lineups` });
});

// Timeline (goles, tarjetas…)
app.get("/laliga/partido/:id_partido/timeline", async (req, res) => {
    request_URL(res, { url: `https://api.sofascore.com/api/v1/event/${req.params.id_partido}/incidents` });
});

// Stats por jugador en partido
app.get("/laliga/partido/:id_partido/jugadores-stats", async (req, res) => {
    request_URL(res, { url: `https://api.sofascore.com/api/v1/event/${req.params.id_partido}/player-statistics` });
});

// Heatmap jugador en partido
app.get("/laliga/partido/:id_partido/jugador/:id_jugador/heatmap", async (req, res) => {
    request_URL(res, { url: `https://api.sofascore.com/api/v1/event/${req.params.id_partido}/player/${req.params.id_jugador}/heatmap` });
});

//
// ===========================================================
// TABLA DE CLASIFICACIÓN
// ===========================================================
//

app.get("/laliga/clasificacion/:id_temporada", async (req, res) => {
    request_URL(res, {
        url: `https://api.sofascore.com/api/v1/unique-tournament/${LALIGA}/season/${req.params.id_temporada}/standings`
    });
});

//
// ===========================================================
// ESTADÍSTICAS GLOBALES DE LA TEMPORADA (TOP JUGADORES)
// ===========================================================
//

app.get("/laliga/stats/:id_temporada", async (req, res) => {
    request_URL(res, {
        url: `https://api.sofascore.com/api/v1/unique-tournament/${LALIGA}/season/${req.params.id_temporada}/statistics`
    });
});

//
// ===========================================================
// BÚSQUEDA
// ===========================================================
//

app.get("/buscar/:texto", async (req, res) => {
    request_URL(res, { url: `https://api.sofascore.com/api/search/all?q=${req.params.texto}` });
});

app.listen(PORT, () => {
    console.log(`Servidor proxy LaLiga → http://localhost:${PORT}`);
});
