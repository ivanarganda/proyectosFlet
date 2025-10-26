import flet as ft
import asyncio
import json
import requests_async as request
from params import *
from helpers.utils import (
    loadLoader, addElementsPage, clearInputsForm,
    loadSnackbar, setInputField, validate_inputs
)
from LoginRegisterForm.views.login_view import renderLoginView
from LoginRegisterForm.views.register_view import renderRegisterView
from LoginRegisterForm.views.change_password_view import renderChangePasswordView

# -------------------------------
# Campos UI base
# -------------------------------
username_field = setInputField("text", label="Username")
email_field = setInputField("text", label="Email")
password_field = setInputField("text", label="Password")
password_field_confirm = setInputField("text", label="Confirm Password")

login_view = None
register_view = None
change_password_view = None
forgot_password = None
loader_overlay = loadLoader()
attempts = 0

# -------------------------------
# Función auxiliar para logs
# -------------------------------
def log_error(context: str, error: Exception):
    print(f"❌ Error en {context}: {type(error).__name__} -> {error}")

# -------------------------------
# Validaciones previas
# -------------------------------
async def change_password( e, page: ft.Page ):
    global email_field, password_field, loader_overlay, toggle_view

    loader_overlay.visible = True
    page.update()

    try:
        email, new_password = email_field.value, password_field.value

        if not validate_inputs(page, email=email, password=new_password):
            loader_overlay.visible = False
            page.update()
            return
        
        if new_password != password_field_confirm.value:
            raise Exception("Passwords do not match.")

        headers = HEADERS
        payload = {"email": email, "new_password": new_password}

        response = await request.post(
            f"{REQUEST_URL}/users/change_password",
            headers=headers,
            data=json.dumps(payload),
            timeout=10
        )

        data = response.json()

        if data.get("status") != 200:
            raise Exception(data.get("message", "Change password failed."))

        if data.get("error"):
            raise Exception(data["error"])

        loadSnackbar(page, "✅ Password changed successfully! Redirecting to login...", "green")
        await asyncio.sleep(2)
        toggle_view(page, "login")

    except (asyncio.TimeoutError, OSError, ConnectionError):
        loadSnackbar(page, "⚠️ Network error or timeout. Please check your internet connection.", "red")

    except Exception as e:
        log_error("change_password", e)
        loadSnackbar(page, f"Error: {e}", "red")

    finally:
        loader_overlay.visible = False
        attempts = 0
        update_forgot_password_visibility(page)   # ✅ resetea el botón
        page.update()

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
    global email_field, password_field, loader_overlay, attempts

    loader_overlay.visible = True
    page.update()

    try:
        email, password = email_field.value, password_field.value

        if not validate_inputs(page, email=email, password=password):
            loader_overlay.visible = False
            attempts+=1
            update_forgot_password_visibility(page)   # ✅ actualiza el botón
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
def renderChangePasswordForm(page: ft.Page):
    global change_password_view
    try:
        change_password_view = renderChangePasswordView(
            page, email_field, password_field_confirm, password_field, change_password, toggle_view, loader_overlay
        )
    except Exception as e:
        log_error("renderChangePasswordForm", e)
        loadSnackbar(page, "❌ Error loading change password form.", "red")

# -------------------------------
# Renderización de vistas
# -------------------------------
def renderRegisterForm(page: ft.Page):
    global register_view
    try:
        register_view = renderRegisterView(
            page, username_field, email_field, password_field, register, toggle_view, loader_overlay
        )
    except Exception as e:
        log_error("renderRegisterForm", e)
        loadSnackbar(page, "❌ Error loading register form.", "red")

def update_forgot_password_visibility(page: ft.Page):
    global forgot_password
    if forgot_password:
        forgot_password.visible = attempts > 1
        page.update()

def renderForgetPasswordInput(page: ft.Page):
    global attempts
    return ft.Container(
        content=ft.Row(
            [
                ft.Text("Forgot your password?"),
                ft.TextButton("Change password", on_click=lambda _: toggle_view(page, "changePassword"))
            ]
        ),
        width=page.window_width,
        height=50,
        border_radius=ft.border_radius.all(10),
        visible=attempts > 1  # Se actualizará dinámicamente
    )



def renderLoginForm(page: ft.Page):
    global login_view, forgot_password
    
    try:
        forgot_password = renderForgetPasswordInput(page)
        login_view = renderLoginView(
            page, forgot_password, email_field, password_field, login, toggle_view, loader_overlay
        )
    except Exception as e:
        log_error("renderLoginForm", e)
        loadSnackbar(page, "❌ Error loading login form.", "red")


def toggle_view(page: ft.Page, switched: str):
    """Alterna entre login/register/changePassword."""
    global login_view, register_view, change_password_view
    try:
        if any(v is None for v in [login_view, register_view, change_password_view]):
            raise Exception("Views not initialized.")
        login_view.visible = switched == "login"
        register_view.visible = switched == "register"
        change_password_view.visible = switched == "changePassword"
        clearInputsForm(page, [email_field, password_field, username_field])
        page.update()
    except Exception as e:
        log_error("toggle_view", e)
        loadSnackbar(page, "❌ Unable to switch views.", "red")


def renderTemplate(page: ft.Page):
    """Render principal que carga login y registro."""
    global login_view, register_view

    try:
        page.title = "Login / Register"
        page.window_width = 600
        page.window_height = 800
        page.window_resizable = False

        renderChangePasswordForm(page)
        renderLoginForm(page)
        renderRegisterForm(page)

        return addElementsPage(
            page,
            [
                change_password_view or ft.Text("⚠️ Login view not loaded"),
                login_view or ft.Text("⚠️ Login view not loaded"),
                register_view or ft.Text("⚠️ Register view not loaded")
            ]
        )
    except Exception as e:
        log_error("renderTemplate", e)
        return addElementsPage(page, [ft.Text("❌ Critical error loading authentication module")])
