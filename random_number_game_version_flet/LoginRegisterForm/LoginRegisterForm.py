from params import *
import flet as ft
import asyncio
import requests_async as request
import json
from helpers.utils import loadLoader, addElementsPage, clearInputsForm, loadSnackbar
from LoginRegisterForm.views.login_view import renderLoginView
from LoginRegisterForm.views.register_view import renderRegisterView

# Give a UIX style
username_field = ft.TextField(label="Username", keyboard_type=ft.KeyboardType.TEXT, bgcolor="#F5F5F5", border_radius=5, border_color="#E0E0E0")
email_field = ft.TextField(label="Email", keyboard_type=ft.KeyboardType.EMAIL, bgcolor="#F5F5F5", border_radius=5, border_color="#E0E0E0")
password_field = ft.TextField(label="Password", password=True, bgcolor="#F5F5F5", border_radius=5, border_color="#E0E0E0")

login_view = False
register_view = False

loader_overlay = loadLoader()

async def register(e, page: ft.Page):
    
    loadSnackbar(page, "Registering...", "blue")

async def login(e, page: ft.Page):
    
    global email_field, password_field, loader
    
    loader_overlay.visible = True
    
    page.update()

    try:
        
        if not email_field.value or not password_field.value: raise Exception("Please fill in all fields.")

        email, password = email_field.value, password_field.value
        
        # make a request to the server to log in
        headers = HEADERS

        response = await request.post(f"{REQUEST_URL_TEST}/users/login", headers=headers, data=json.dumps({"email": email, "password": password}))

        data = response.json()
        # return response
        if data["status"] == 200:
                        
            if data.get("error"): raise Exception(data["error"])
            
        else: raise Exception(f"An error occurred.{data.get('message', '')} Please try again.")
        
        # if everything is ok
        loadSnackbar(page, f"Welcome back, {data["message"]["token"]}!", "green")

        clearInputsForm(page, [email_field, password_field])

        loader_overlay.visible = False
        
        page.update()
        
    except Exception as errh:
    
        loadSnackbar(page, f"Error: {errh}", "red")
        
        loader_overlay.visible = False
        
        page.update()
        
        return

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
    
    page.title = "Login"
    page.window_width = 600
    page.window_height = 800
    page.window_resizable = False
    
    renderLoginForm(page)
    renderRegisterForm(page)

    addElementsPage(
        page, 
        [
            login_view,
            register_view
        ]
    )
