# **ivbox**

[![PyPI version](https://img.shields.io/pypi/v/ivbox.svg)](https://pypi.org/project/ivbox/)
[![Python](https://img.shields.io/pypi/pyversions/ivbox.svg)](https://pypi.org/project/ivbox/)
[![License](https://img.shields.io/pypi/l/ivbox.svg)](LICENSE)

🚀 **ivbox** es un framework ligero para Python enfocado en mejorar la **experiencia de desarrollo (DX)** mediante:

* estructuras de proyecto claras y repetibles,
* utilidades reutilizables probadas en proyectos reales, y
* scaffolding automático vía CLI para aplicaciones basadas en **Flet**.

ivbox no pretende reemplazar a Flet: **te ayuda a trabajar mejor con él.**

> Versión actual: **1.0.0**

---

## 🎯 Filosofía

ivbox sigue una regla simple:

> **Primero se repite. Luego se abstrae.**

Las abstracciones nacen de problemas reales, no de patrones teóricos.

---

## 🤔 ¿Por qué ivbox?

Al construir aplicaciones reales con Flet, suelen aparecer los mismos problemas:

* Arquitecturas poco claras
* Routing manual y repetitivo
* Falta de scaffolding (generadores de código)
* Duplicación de lógica entre proyectos
* Poca estandarización de estructura

ivbox nace para reducir esa fricción y ofrecer un punto de partida profesional y consistente.

---

## ✨ Características principales

* 📁 **Plantillas de proyecto listas para usar**
* ⚡ **CLI con scaffolding automático**
* 🧩 Integración nativa con **ivbox-utils**
* 🗄️ Base para trabajar con SQLite + ORM propio
* 🧱 Arquitectura modular y extensible
* 🧪 Construido desde casos reales de uso con Flet

---

## 📦 Instalación

```bash
pip install ivbox
```

> Recomendado también:

```bash
pip install ivbox-utils[flet]
```

---

## 🚀 Inicio rápido (lo importante)

### 1) Crea un nuevo proyecto en segundos

```bash
ivbox new MiApp --install
```

Esto generará automáticamente:

```
MiApp/
  App/
  Server/
```

con una estructura lista para ejecutar con Flet.

### 2) Ejecuta tu aplicación

```bash
cd MiApp
python App/main.py
```

---

## 🧠 Qué te da ivbox

### 🔹 Estructura estándar de proyecto

Un proyecto generado incluye por defecto:

```
App/
  main.py
  params.py
  components/
  helpers/
  middlewares/
  MainMenu/
    Views/

Server/
  api.py
  db.py
  auth.py
```

Esto permite:

* separar UI y backend,
* mantener orden y escalabilidad,
* y facilitar el trabajo en equipo.

---

### 🔹 CLI de scaffolding

Comandos principales:

```bash
ivbox new MiApp
ivbox create view Dashboard
ivbox create middleware Auth
ivbox create component PopupMenu
```

(La generación de views y middlewares está en desarrollo y creciendo con cada versión.)

---

### 🔹 Integración con ivbox-utils

ivbox trabaja de la mano con **ivbox-utils**, que aporta helpers listos para usar:

```python
from ivbox_utils.app.auth import init_auth
from ivbox_utils.general.fs import read_file
```

Flujo recomendado:

```bash
pip install ivbox
pip install ivbox-utils[flet]
ivbox new MiApp --install
```

---

## 🧩 Estado del proyecto

ivbox está en **desarrollo activo**:

* API puede cambiar hasta `1.0.0`
* Cada versión mejora estabilidad y ergonomía
* Los cambios nacen de uso real, no de teoría

---

## 🔢 Versionado

Seguimos **Semantic Versioning**:

* `0.x` → desarrollo activo
* `1.0.0` → API estable

---

## 🤝 Contribuciones

Son bienvenidas si:

1. Resuelven un problema real y repetido
2. Mantienen el proyecto simple
3. Aportan ejemplo mínimo de uso

Flujo sugerido:

1. Abrir issue describiendo el problema
2. Proponer solución mínima
3. Aportar ejemplo o test

---

## ✍️ Autor

**Ivan González Valles (IGV)**
Python | Data | Automation | Flet

🔗 GitHub: [https://github.com/ivanarganda](https://github.com/ivanarganda)

---

## 💡 Inspiración

ivbox está inspirado por frameworks que crecieron desde el uso real, como **Laravel**.

> *Build what hurts. Keep what repeats.*
