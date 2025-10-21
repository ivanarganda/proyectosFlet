import flet as ft
import asyncio
import json
import requests_async as request
from params import *
from helpers.utils import (
    loadLoader, addElementsPage, clearInputsForm,
    loadSnackbar, setInputField
)
from LoginRegisterForm.views.login_view import renderLoginView
from LoginRegisterForm.views.register_view import renderRegisterView

# -------------------------------
# Campos UI base
# -------------------------------
username_field = setInputField("text", label="Username")
email_field = setInputField("text", label="Email")
password_field = setInputField("text", label="Password")

login_view = None
register_view = None
loader_overlay = loadLoader()

# -------------------------------
# Función auxiliar para logs
# -------------------------------
def log_error(context: str, error: Exception):
    print(f"❌ Error en {context}: {type(error).__name__} -> {error}")

# -------------------------------
# Validaciones previas
# -------------------------------
def validate_inputs(page, username=None, email=None, password=None):
    """Valida campos antes de enviar al servidor."""
    try:
        if username is not None and not username.strip():
            raise ValueError("Username is required.")
        if email is not None:
            if not email.strip():
                raise ValueError("Email is required.")
            if "@" not in email or "." not in email:
                raise ValueError("Invalid email format.")
        if password is not None:
            if len(password.strip()) < 4:
                raise ValueError("Password must be at least 4 characters.")
        return True
    except ValueError as ve:
        loadSnackbar(page, f"⚠️ {ve}", "red")
        return False


# -------------------------------
# Registro
# -------------------------------
async def register(e, page: ft.Page):
    global email_field, password_field, username_field, loader_overlay

    loader_overlay.visible = True
    page.update()

    try:
        username, email, password = username_field.value, email_field.value, password_field.value

        if not validate_inputs(page, username, email, password):
            loader_overlay.visible = False
            page.update()
            return

        headers = HEADERS
        payload = {"username": username, "email": email, "password": password}

        response = await request.post(
            f"{REQUEST_URL}/users/register",
            headers=headers,
            data=json.dumps(payload),
            timeout=10
        )

        data = response.json()

        if data.get("status") != 200:
            raise Exception(data.get("message", "Registration failed."))

        if data.get("error"):
            raise Exception(data["error"])

        loadSnackbar(page, "✅ Account created successfully! Redirecting to login...", "green")
        await asyncio.sleep(2)
        toogle_view(page, "login")

    except (asyncio.TimeoutError, OSError, ConnectionError):
        loadSnackbar(page, "⚠️ Network error or timeout. Please check your internet connection.", "red")

    except Exception as e:
        log_error("register", e)
        loadSnackbar(page, f"Error: {e}", "red")

    finally:
        loader_overlay.visible = False
        page.update()


# -------------------------------
# Login
# -------------------------------
async def login(e, page: ft.Page):
    global email_field, password_field, loader_overlay

    loader_overlay.visible = True
    page.update()

    try:
        email, password = email_field.value, password_field.value

        if not validate_inputs(page, email=email, password=password):
            loader_overlay.visible = False
            page.update()
            return

        headers = HEADERS
        payload = {"email": email, "password": password}

        response = await request.post(
            f"{REQUEST_URL}/users/login",
            headers=headers,
            data=json.dumps(payload),
            timeout=10
        )

        data = response.json()

        if data.get("status") != 200:
            raise Exception(data.get("message", "Login failed."))

        if data.get("error"):
            raise Exception(data["error"])

        user_data = {
            "token": data["message"]["token"],
            "is_logged_in": True,
        }

        page.session.set("user", user_data)
        page.run_thread(lambda: page.client_storage.set("user", json.dumps(user_data)))

        for i in range(3):
            loadSnackbar(page, f"Loading your dashboard... ({(i+1)/3*100:.0f}%)", "blue")
            await asyncio.sleep(0.4)

        page.go("/menu")

    except asyncio.TimeoutError:
        loadSnackbar(page, "⏰ Request timed out. Please check your internet connection.", "red")

    except Exception as e:
        log_error("login", e)
        loadSnackbar(page, f"Error: {e}", "red")

    finally:
        loader_overlay.visible = False
        page.update()



# -------------------------------
# Renderización de vistas
# -------------------------------
def renderRegisterForm(page: ft.Page):
    global register_view
    try:
        register_view = renderRegisterView(
            page, username_field, email_field, password_field, register, toogle_view, loader_overlay
        )
    except Exception as e:
        log_error("renderRegisterForm", e)
        loadSnackbar(page, "❌ Error loading register form.", "red")


def renderLoginForm(page: ft.Page):
    global login_view
    try:
        login_view = renderLoginView(
            page, email_field, password_field, login, toogle_view, loader_overlay
        )
    except Exception as e:
        log_error("renderLoginForm", e)
        loadSnackbar(page, "❌ Error loading login form.", "red")


def toogle_view(page: ft.Page, switched: str):
    """Alterna entre login/register."""
    global login_view, register_view, email_field, password_field, username_field
    try:
        if login_view and register_view:
            login_view.visible = switched == "login"
            register_view.visible = switched == "register"
            clearInputsForm(page, [email_field, password_field, username_field])
            page.update()
        else:
            raise Exception("Views not initialized.")
    except Exception as e:
        log_error("toogle_view", e)
        loadSnackbar(page, "❌ Unable to switch views.", "red")


def renderTemplate(page: ft.Page):
    """Render principal que carga login y registro."""
    global login_view, register_view

    try:
        page.title = "Login / Register"
        page.window_width = 600
        page.window_height = 800
        page.window_resizable = False

        renderLoginForm(page)
        renderRegisterForm(page)

        return addElementsPage(
            page,
            [
                login_view or ft.Text("⚠️ Login view not loaded"),
                register_view or ft.Text("⚠️ Register view not loaded")
            ]
        )
    except Exception as e:
        log_error("renderTemplate", e)
        return addElementsPage(page, [ft.Text("❌ Critical error loading authentication module")])
