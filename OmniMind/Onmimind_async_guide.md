# OmniMind – Guía rápida de asincronía en Python (Flet)

**Autor:** ivan gonzalez valles · **Proyecto:** OmniMind · **Fecha:** 2025-11-10

Esta guía compacta explica **cuándo** y **cómo** usar `asyncio.run`, `asyncio.create_task` y **threads** en tu app Flet.
Incluye ejemplos reales de OmniMind (router, carga de scores y Tetris).

---

## 1) Qué es cada cosa

### `asyncio.run(coro)`
- **Qué hace:** Ejecuta una corrutina y **bloquea** el hilo actual hasta terminar.
- **Cuándo usarlo:** En scripts, tareas puntuales *fuera* de un loop ya activo.
- **Evita usarlo** dentro de callbacks/eventos Flet (ya hay un loop → `RuntimeError`).

```python
import asyncio

async def cargar_scores():
    await asyncio.sleep(2)
    return {'status': 200}

# Script o arranque sin loop activo:
result = asyncio.run(cargar_scores())
```

---

### `asyncio.create_task(coro)` (o `asyncio.ensure_future(coro)`)
- **Qué hace:** Lanza una corrutina **sin bloquear** la UI. Se ejecuta en el loop actual.
- **Cuándo usarlo:** Cargas a API, animaciones, tareas concurrentes mientras la UI sigue viva.

```python
# En el router de OmniMind (Flet):
async def load_and_render_game(game_id, renderer):
    scores = await load_scores(game_id, token, page)
    page.views.append(ft.View(page.route, [renderer(page, scores, load_scores)]))
    page.update()

# No bloquea el hilo de UI:
asyncio.create_task(load_and_render_game(2, render_tetris))
```

**Patrón seguro cuando no sabes si el loop está corriendo:**

```python
def run_async_task(coro):
    loop = asyncio.get_event_loop()
    if loop.is_running():
        asyncio.ensure_future(coro)   # no bloquea
    else:
        loop.run_until_complete(coro) # ejecuta y bloquea (útil fuera de UI)
```

---

### `threading.Thread`
- **Qué hace:** Crea un hilo del SO para ejecutar código **en paralelo** al hilo principal.
- **Cuándo usarlo:** Bucles continuos y trabajo **CPU-bound** (p. ej., loop del Tetris).
- **No comparte el loop de asyncio**; conviven, pero son mundos distintos.

```python
import threading, time

def game_loop():
    while running:
        move_shape_down()
        time.sleep(0.3)

threading.Thread(target=game_loop, daemon=True).start()
```

---

## 2) Regla de oro (uso combinado)

- **I/O (esperas de red, disco, sockets):** `asyncio` (`await`, `create_task`).
- **CPU (cálculo/loops):** `threading` (o `multiprocessing` si es muy pesado).
- **Nunca bloquees el hilo de UI** con operaciones largas.

```
      UI Flet (main thread)
             │
     ┌───────┴────────┐
     │                │
 asyncio (I/O)     Threads (CPU/loops)
 create_task()     game_loop()
 await ...         time.sleep(...)
```

---

## 3) Ejemplos integrados de OmniMind

### 3.1 Router + carga asíncrona de juegos

```python
def route_change(e: ft.RouteChangeEvent):
    page = e.page
    route = page.route
    page.views.clear()

    async def load_and_render_game(game_id: int, renderer):
        try:
            scores = await load_scores(game_id, token, page)  # I/O (async)
            if scores.get("status") == 401:
                return
            view = ft.View(route, [renderer(page, scores, load_scores)])
            page.views.append(view)
            page.update()
        except Exception as ex:
            notify_error(page, f"Error cargando juego: {ex}")

    def run_async_task(coro):
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(coro)
            else:
                loop.run_until_complete(coro)
        except RuntimeError:
            asyncio.run(coro)

    if route == "/games/tetris":
        run_async_task(load_and_render_game(2, render_tetris))  # no bloquea la UI
    else:
        page.views.append(ft.View(route, [ft.Text("Vista")]))

    page.update()
```

### 3.2 Loop del Tetris en un **thread**

```python
def game_loop():
    nonlocal running, paused
    while running and not stop_event.is_set():
        if not paused:
            move_shape(0, 1)  # CPU / estado propio del juego
            refresh_grid()
            time.sleep(fall_speed)
        else:
            time.sleep(0.1)

threading.Thread(target=game_loop, daemon=True).start()
```

### 3.3 Cargar scores (I/O) de forma asíncrona

```python
async def load_scores(game_id: int, token: str, page: ft.Page):
    headers = HEADERS.copy()
    headers["Authorization"] = f"Bearer {token}"

    response = await request.get(f"{REQUEST_URL}/games/scores?id={game_id}", headers=headers)
    if response.status_code == 401:
        show_session_expired_dialog(page)
        return {'status': 401}
    return response.json()
```

---

## 4) Errores típicos y cómo evitarlos

1. **Llamar `asyncio.run()` dentro de un loop activo (Flet/Qt/Tk):**  
   → *Solución:* usa `create_task()` o el helper `run_async_task()`.

2. **Bloquear la UI con `time.sleep()` en el hilo principal:**  
   → *Solución:* ejecuta el loop de juego en un **thread** (`daemon=True`).

3. **Esperar I/O costoso en el hilo principal:**  
   → *Solución:* vuelve la función `async` y usa `await` o lánzala con `create_task()`.

4. **Dialogos de Flet no visibles tras `return` en router:**  
   → *Solución:* no cortes el `route_change`; deja una vista base y luego abre el diálogo por `page.overlay`.

---

## 5) Checklist profesional

- [ ] ¿La UI nunca se bloquea? (sin `sleep` en main thread)
- [ ] ¿Las llamadas a API se hacen con `await` / `create_task`?
- [ ] ¿Los loops del juego van en `threading.Thread(daemon=True)`?
- [ ] ¿El router no hace `asyncio.run()`?
- [ ] ¿Los diálogos se abren por `page.overlay` y no dentro de la vista?
- [ ] ¿Uso `run_async_task()` cuando no sé si hay loop?

---

## 6) Mini tabla comparativa

| Técnica                   | Bloquea UI | Ideal para     | Ejemplo OmniMind                  |
|--------------------------|------------|----------------|-----------------------------------|
| `asyncio.run(coro)`      | ✅ Sí      | Script puntual | Script de utilidades              |
| `asyncio.create_task()`  | ❌ No      | I/O concurrente| Cargar scores al entrar al juego  |
| `threading.Thread`       | ❌ No      | CPU/loops      | `game_loop` del Tetris            |

---

## 7) Plantilla recomendada

```python
def run_async_task(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(coro)
        else:
            loop.run_until_complete(coro)
    except RuntimeError:
        asyncio.run(coro)
```

**Regla final:** *I/O → asyncio* · *CPU/loop → thread* · *UI nunca se bloquea*.

---

**¿Siguiente paso?** Integrar esta guía en tu repo como `docs/async_guide.md` y añadir ejemplos ejecutables.
