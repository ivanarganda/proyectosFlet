# 🎲 Juego de Adivinar el Número

Un juego clásico de adivinar el número, escrito en **Python 3**, con sistema de **niveles de dificultad** y un sistema de **login/registro** con persistencia de sesión mediante tokens.  
El proyecto está modularizado en varios ficheros para mantener el código limpio y escalable.

---

## 🚀 Características

- **Menú principal dinámico** que se adapta al estado de sesión:
  - Si no hay sesión activa:
    1. Jugar como invitado  
    2. Iniciar sesión  
    3. Salir del juego  
  - Si hay sesión activa:
    1. Jugar como usuario autenticado  
    2. Cerrar sesión  
    3. Salir del juego  
- **Tres niveles de dificultad**:
  - Fácil → (1-10, 10 intentos, con pista)  
  - Medio → (1-20, 8 intentos, sin pista)  
  - Difícil → (1-30, 4 intentos, sin pista)  
- **Gestión de usuarios** con persistencia en `usuarios.txt`:
  - Registro de nuevos usuarios.  
  - Login de usuarios existentes.  
- **Gestión de sesión con token**:
  - `session_user.txt` guarda el usuario y su token activo.  
  - El menú principal se refresca automáticamente según haya sesión activa o no.  
- **Validación de entradas** (opciones de menú y rango de números).  
- Código organizado en **módulos independientes**.  

---

## 📂 Estructura del proyecto

```bash
random_number_game/
│
├── main.py              # Punto de entrada del programa (menú principal dinámico)
├── game_room.py         # Lógica del juego: niveles, validaciones, inicio de partida
├── registro_login.py    # Registro, login y logout de usuarios con gestión de tokens
├── utils.py             # Funciones auxiliares (menús, tokens, persistencia de sesión)
├── usuarios.txt         # Persistencia de usuarios registrados (ignorado en GitHub)
├── session_user.txt     # Usuario con sesión activa y token asociado
├── README.md            # Documentación del proyecto
└── __pycache__/         # Archivos compilados (ignorar)

```

## 🛠️ Requisitos

- Python 3.10+ (probado en Python 3.12)
- No requiere librerías externas (solo random y sys de la librería estándar).

## ▶️ Cómo ejecutar

**1.** Clonar o descargar este repositorio.

**2.** Abrir una terminal en la carpeta del proyecto.

**3.** Ejecutar:

``` bash
python main.py
```
## 🧑‍💻 Ejemplo de uso

**Caso 1: sin sesión activa**

``` text

--- Juego de Adivina el Número ---
1: Jugar como invitado
2: Jugar como usuario registrado
3: Salir

Selecciona una opción (1-3): 1

Nivel Fácil
Adivina el número entre 1 y 10 (tienes 10 intentos)

Te quedan 10 intentos
Escribe un número entre 1 y 10: 5
El número es mayor
...
🎉 ¡Acertaste el número!

Selecciona una opción (1-3): 2
Usuario: ivan
Contraseña: ****
✅ Sesión iniciada con éxito.
```

**Caso 2: con sesión activa**

``` text

--- Juego de Adivina el Número ---
1: Jugar como usuario autenticado
2: Cerrar sesión
3: Salir

Selecciona una opción (1-3): 1
Nivel Medio
Adivina el número entre 1 y 20 (tienes 8 intentos)

Te quedan 8 intentos
Escribe un número entre 1 y 20: 7
El número es mayor
...
🎉 ¡Acertaste el número!

```

## 📌 Próximas mejoras (ideas)

- Guardar récords de usuarios (mejor tiempo / menor cantidad de intentos).
- Sistema de puntuaciones y ranking.
- Expiración de tokens de sesión tras cierto tiempo.
- Interfaz gráfica con Tkinter.
- Exportar usuarios y estadísticas a JSON o SQLite.

## 📄 Licencia

Este proyecto es de uso libre para practicar Python. 🚀

## 🗑️ .gitignore

Si vas a subirlo a GitHub, crea un archivo llamado .gitignore en la raíz del proyecto con este contenido:

``` gitignore

# Archivos compilados de Python
__pycache__/
*.pyc
*.pyo
*.pyd

# Configuración de entornos virtuales
venv/
.env/

# Configuración de IDEs
.vscode/
.idea/

# Archivos del sistema
.DS_Store
Thumbs.db

# Archivos de usuario
usuarios.txt
session_user.txt
```
⚠️ Nota: he añadido usuarios.txt al .gitignore para que no subas las contraseñas de prueba a GitHub 😉.

## 🙍‍♂️ Archivo de usuarios y sesiones

El archivo usuarios.txt almacena los usuarios registrados y sigue la siguiente estructura:

``` bash
# nombre;contraseña
example;example
example2;example2
```

El archivo session_user.txt almacena el token que esta compuesto por el usuario;contraseña

👉 Con esto ya tienes todo: `README.md` con la documentación del proyecto y `.gitignore` para mantener limpio tu repo.  

¿Quieres que además te prepare el **comando paso a paso para inicializar el repo en GitHub** (git init, commit, push, etc.) para que lo publiques directamente?
```
