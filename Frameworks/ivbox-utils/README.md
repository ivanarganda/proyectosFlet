# **ivbox-utils**

🚀 **Utilidades reutilizables para ivbox y aplicaciones Flet en Python**

`ivbox-utils` es un conjunto de helpers y herramientas diseñadas para simplificar el desarrollo de aplicaciones con **Flet** y complementar el framework **ivbox**.

Está pensado para ser modular, limpio y reutilizable en múltiples proyectos.

---

## 📦 Instalación

### Instalación básica

```bash
pip install ivbox-utils
```

### Instalación con soporte para Flet (recomendada si usas ivbox)

```bash
pip install ivbox-utils[flet]
```

---

## 🧩 ¿Qué incluye?

El paquete está organizado en tres grandes módulos:

### ✅ `general`

Funciones independientes de Flet y útiles en cualquier proyecto de datos o automatización:

```python
from ivbox_utils.general.fs import read_file, get_files, generate_json
from ivbox_utils.general.security import make_id_hash
from ivbox_utils.general.time import now, time_ago
```

Incluye, entre otras cosas:

* Lectura unificada de archivos (`csv`, `json`, `xlsx`)
* Detección inteligente de claves e IDs
* Deduplicación automática de DataFrames
* Exportación flexible a múltiples formatos
* Manejo seguro de identificadores
* Utilidades de tiempo y fechas

---

### ✅ `app` (dependiente de Flet)

Herramientas pensadas para aplicaciones Flet:

```python
from ivbox_utils.app.auth import init_auth, getUserInfo
```

Incluye:

* Sistema base de autenticación
* Gestión de usuario autenticado
* Helpers para trabajar con `ft.Page`

---

### ✅ `ui` *(en desarrollo)*

Componentes visuales reutilizables para Flet que se irán ampliando progresivamente.

---

## ⚙️ Uso típico con ivbox

Si usas el framework **ivbox**, tus plantillas de proyecto podrán importar directamente:

```python
from ivbox_utils.app.auth import init_auth
from ivbox_utils.general.fs import read_file
```

Y funcionará automáticamente cuando tu CLI instale dependencias.

---

## 🛠️ Relación con ivbox

Este paquete está pensado para trabajar junto a:

```
pip install ivbox
```

Flujo recomendado:

```bash
pip install ivbox
pip install ivbox-utils[flet]

ivbox new MiApp --install
```

---

## 📁 Estructura del paquete

```
ivbox_utils/
  general/
    fs.py
    security.py
    time.py
  app/
    auth.py
  ui/
    (próximamente)
```

---

## 📌 Estado del proyecto

* ✅ Funcional
* 🛠️ En mejora continua
* 🚧 Nuevas utilidades en camino

---

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas!
Puedes abrir issues o pull requests en el repositorio de GitHub.

---

## 📄 Licencia

MIT

---

## ✍️ Autor

**Ivan González Valles (IGV)**
Desarrollador Python | Data & Automation | Flet enthusiast
