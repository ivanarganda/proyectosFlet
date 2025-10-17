from params import *
import flet as ft
import asyncio
import requests_async as request
import json
from helpers.utils import loadLoader, addElementsPage, clearInputsForm, loadSnackbar, setInputField
from LoginRegisterForm.views.login_view import renderLoginView
from LoginRegisterForm.views.register_view import renderRegisterView

# Give a UIX style
username_field = setInputField("text", label="Username")
email_field = setInputField("text", label="Email")
password_field = setInputField("text", label="Password")

login_view = False
register_view = False

loader_overlay = loadLoader()

async def register(e, page: ft.Page):
    
    global email_field, password_field, loader
    
    loader_overlay.visible = True
    
    page.update()
    
    try:
        
        if not email_field.value or not password_field.value or not username_field.value: raise Exception("Please fill in all fields.")

        username, email, password = username_field.value, email_field.value, password_field.value
        
        # make a request to the server to register
        headers = HEADERS

        response = await request.post(f"{REQUEST_URL_TEST}/users/register", headers=headers, data=json.dumps({"username": username, "email": email, "password": password}))

        data = response.json()
        # return response
        if data["status"] == 200:
                        
            if data.get("error"): raise Exception(data["error"])
            
        else: raise Exception(f"An error occurred.{data.get('message', '')} Please try again.")
        
        # if everything is ok
        loadSnackbar(page, f"Account created successfully! Going to login...It might takes a few seconds.", "green")
        
        await asyncio.sleep(3)
        
        loader_overlay.visible = False
        
        toogle_view(page, "login")
        
    except Exception as errh:
    
        loadSnackbar(page, f"Error: {errh}", "red")
        
        loader_overlay.visible = False
        
        page.update()
        
        return

async def login(e, page: ft.Page):
    global email_field, password_field, loader_overlay

    try:
        # Mostrar loader al iniciar el proceso
        loader_overlay.visible = True
        page.update()

        if not email_field.value or not password_field.value:
            raise Exception("Please fill in all fields.")

        email, password = email_field.value, password_field.value

        # Simular pequeña carga de red
        await asyncio.sleep(0.3)

        # Petición al servidor
        headers = HEADERS
        response = await request.post(
            f"{REQUEST_URL_TEST}/users/login",
            headers=headers,
            data=json.dumps({"email": email, "password": password})
        )

        data = response.json()

        # Validar respuesta
        if data["status"] != 200:
            raise Exception(f"An error occurred. {data.get('message', '')}")

        if data.get("error"):
            raise Exception(data["error"])

        # Crear objeto de sesión
        user_data = {
            "token": data["message"]["token"],
            "is_logged_in": True,
        }

        # Guardar sesión en memoria (sin bloquear la interfaz)
        page.session.set("user", user_data)

        def persist_user():
            page.client_storage.set("user", json.dumps(user_data))

        page.run_thread(persist_user)

        # Simula un tiempo de carga mientras muestra el loader
        for i in range(3):
            loadSnackbar(page, f"Loading your dashboard... ({(i+1)/3*100:.2f}%)", "blue")
            await asyncio.sleep(0.5)

        # Ocultar loader y navegar al menú
        loader_overlay.visible = False
        page.update()
        page.go("/menu")

    except Exception as errh:
        loadSnackbar(page, f"Error: {errh}", "red")
        loader_overlay.visible = False
        page.update()


def renderRegisterForm(page: ft.Page):
    
    global register_view
    register_view = renderRegisterView(page, username_field, email_field, password_field, register, toogle_view, loader_overlay)
    
def renderLoginForm(page: ft.Page):
    
    global login_view
    login_view = renderLoginView(page, email_field, password_field, login, toogle_view, loader_overlay)

def toogle_view( page: ft.Page, switched: str ):
    
    global login_view, register_view, email_field, password_field, username_field
    login_view.visible = switched == "login"
    register_view.visible = switched == "register"
    clearInputsForm(page, [email_field, password_field, username_field])
    page.update()
    

def renderTemplate(page: ft.Page):
    
    global login_view, register_view, email_field, password_field, username_field, loader_overlay
    
    page.title = "Login / Register"
    page.window_width = 600
    page.window_height = 800
    page.window_resizable = False
    
    renderLoginForm(page)
    renderRegisterForm(page)

    return addElementsPage(
        page, 
        [
            login_view,
            register_view
        ]
    )
