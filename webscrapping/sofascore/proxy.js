const express = require("express");
const { chromium } = require("playwright");

const app = express();
const PORT = 3000;

// ============================
// 1. OBTENER TEMPORADAS
// ============================
async function obtenerTemporadas() {
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();

    await page.goto("https://api.sofascore.app/api/v1/unique-tournament/8/seasons", {
        waitUntil: "networkidle"
    });

    const data = await page.textContent("body");
    await browser.close();

    return JSON.parse(data);
}


// ============================
// 2. OBTENER JORNADAS (RONDA)
// ============================
async function obtenerJornadas(idTemporada) {
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();

    const url = `https://api.sofascore.app/api/v1/unique-tournament/8/season/${idTemporada}/rounds`;

    await page.goto(url, { waitUntil: "networkidle" });

    const data = await page.textContent("body");
    await browser.close();

    return JSON.parse(data);
}


// ============================
// 3. OBTENER PARTIDOS DE UNA RONDA
// ============================
async function obtenerPartidos(idTemporada, ronda) {
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();

    const urlWeb = `https://api.sofascore.app/api/v1/unique-tournament/8/season/${idTemporada}/events/round/${ronda}`;

    let partidosJSON = null;

    // Interceptar las peticiones XHR reales de la web
    page.on("response", async (response) => {
        const reqUrl = response.url();

        // la request que queremos contiene /events/round/<ronda>
        if (reqUrl.includes(`/events/round/${ronda}`)) {
            try {
                partidosJSON = await response.json();
            } catch (err) {}
        }
    });

    // Cargar la web como lo hace un usuario real
    await page.goto(urlWeb, { waitUntil: "networkidle" });

    // dar tiempo a XHR
    await page.waitForTimeout(2000);

    await browser.close();

    return partidosJSON;
}

// ============================
// RUTAS EXPRESS
// ============================
app.get("/temporadas", async (req, res) => {
    try {
        const result = await obtenerTemporadas();
        res.json(result);
    } catch (err) {
        res.status(500).json({ error: err.toString() });
    }
});

app.get("/jornadas/:id_temporada", async (req, res) => {
    try {
        const result = await obtenerJornadas(req.params.id_temporada);
        res.json(result);
    } catch (err) {
        res.status(500).json({ error: err.toString() });
    }
});

app.get("/partidos/:id_temporada/:ronda", async (req, res) => {
    try {
        const result = await obtenerPartidos(req.params.id_temporada, req.params.ronda);
        res.json(result);
    } catch (err) {
        res.status(500).json({ error: err.toString() });
    }
});

app.listen(PORT, () => {
    console.log(`Servidor proxy en http://localhost:${PORT}`);
});
