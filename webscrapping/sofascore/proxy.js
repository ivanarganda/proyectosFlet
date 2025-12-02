const express = require("express");
const { chromium } = require("playwright");
const app = express();
const PORT = 3000;

/**
 * CONFIG:
 * {
 *   url: "https://api.sofascore.app/.../seasons",
 *   intercept: false | {
 *      match: "/events/round/5",   // substring a detectar
 *   }
 * }
 */

async function request_URL(res, config) {
    try {
        const browser = await chromium.launch({ headless: true });
        const page = await browser.newPage();

        let interceptedData = null;

        // Si hay interceptación XHR
        if (config.intercept) {
            page.on("response", async (response) => {
                const reqUrl = response.url();
                if (reqUrl.includes(config.intercept.match)) {
                    try {
                        interceptedData = await response.json();
                    } catch {}
                }
            });
        }

        // Cargar página / endpoint
        await page.goto(config.url, { waitUntil: "networkidle" });

        let result;

        if (config.intercept) {
            // Si se esperaba XHR pero no llegó nada
            if (!interceptedData) {
                throw new Error("No se pudo interceptar la respuesta XHR");
            }
            result = interceptedData;
        } else {
            // Para endpoints JSON directos
            const text = await page.textContent("body");
            result = JSON.parse(text);
        }

        await browser.close();

        console.log( config.url );
        

        if (config.url.includes(`/season/`) && config.url.includes(`/events/`) && config.url.includes(`/round/`) ){

            console.log(  result.events );
            

            let eventosMapeados = result.events.map(ev => ({
                id: ev.id || null,
                inicio: ev.startTimestamp || null,
                estado_partido: ev.status?.type || null,

                id_estadio: ev.venue || {},

                id_equipo_local: ev.homeTeam?.id || null,
                id_equipo_visitante: ev.awayTeam?.id || null,

                nombre_equipo_local: ev.homeTeam?.name || null,
                nombre_equipo_visitante: ev.awayTeam?.name || null,

                goles_equipo_local: ev.homeScore?.current || 0,
                goles_equipo_visitante: ev.awayScore?.current || 0
            }));

            console.log( eventosMapeados );

            result = eventosMapeados

        }

        res.json(result);

    } catch (err) {
        res.status(500).json({ error: err.toString() });
    }
}

// ============================
// Proxy endpoints
// ============================
app.get("/temporadas", async (req, res) => {
    request_URL(res,  { 'url': `https://api.sofascore.app/api/v1/unique-tournament/8/seasons` });
});

app.get("/equipos", async (req, res) => {
    request_URL(res,  { 'url': `https://api.sofascore.app/api/v1/unique-tournament/8/teams` });
});

app.get("/partido/:id_partido", async (req, res) =>{
    request_URL(res,  { 'url': `https://api.sofascore.app/api/v1/event/${id_partido}` });
})

app.get("/jornadas/:id_temporada", async (req, res) => {
    request_URL(res, { 'url': `https://api.sofascore.app/api/v1/unique-tournament/8/season/${req.params.id_temporada}/rounds ` });
});

app.get("/partidos/:id_temporada/:ronda", async (req, res) => {
    request_URL(res,  { 'url': `https://api.sofascore.app/api/v1/unique-tournament/8/season/${req.params.id_temporada}/events/round/${req.params.ronda}` });
});

app.listen(PORT, () => {
  console.log(`Servidor proxy en http://localhost:${PORT}`);
});
