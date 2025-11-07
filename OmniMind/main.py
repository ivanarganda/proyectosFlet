import flet as ft
from helpers.utils import getSession, get_hostname
import json
from LoginRegisterForm.LoginRegisterForm import renderTemplate
from MainMenu.MainMenu import renderMainMenu
from Tasks.Tasks import RenderTasks
from Tasks.views.details_category import loadDetailsCategory
from Tasks.views.AddCategoryTasksForm import AddCategoryTasksForm
from Tasks.views.AddTaskForm import AddTaskForm
from Games.RandomNumber import renderGameRandomNumber
from Games.Tetris import render_tetris
from params import REQUEST_URL, HEADERS
import requests_async as request
import asyncio
import threading

token = None

async def load_scores( game_id:int ):

    headers = HEADERS
    headers["Authorization"] = f"Bearer {token}"

    response = await request.get( f"{REQUEST_URL}/games/scores?id={game_id}" , headers=headers  )
    return response.json()

def main(page: ft.Page):

    global token

    # handle session here    
    page.on_route_change = route_change
    
    user_data = getSession(page.client_storage.get("user") or "{}")

    token = user_data.get("token","")

    # Check if the user is logged in
    if not user_data or not user_data.get("is_logged_in"):
        page.go("/")       # Go to login page
    else:
        page.go("/menu")   # Go to main menu

def route_change(e: ft.RouteChangeEvent):
    page = e.page
    page.views.clear()
    if page.route == "/":
        page.views.append(ft.View("/", [renderTemplate(page)]))
    elif page.route == "/menu":
        page.views.append(ft.View("/menu", [renderMainMenu(page)]))
    elif page.route == "/games":
        page.views.append(ft.View("/games", [renderGame(page)]))
    elif page.route == "/games/random_number":
        scores = asyncio.run( load_scores(1) )
        page.views.append(ft.View("/games/random_number", [renderGameRandomNumber(page, scores)]))
    elif page.route == "/games/tetris":
        scores = asyncio.run( load_scores(2) )
        page.views.append(ft.View("/games/tetris", [render_tetris(page, scores )]))
    elif page.route == "/tasks":
        page.views.append(ft.View("/tasks", [RenderTasks(page)]))
    elif page.route.startswith("/category/create"):
        page.views.append(
            ft.View(
                f"/category/create",
                [AddCategoryTasksForm(page)]
            )
        )
    elif page.route.startswith("/tasks/create/"):
        id_category = page.route.split("/")[-1]  # "5", "12", etc.
        page.views.append(
            ft.View(
                f"/tasks/create/{id_category}",
                [AddTaskForm(page, id_category)]
            )
        )
    elif page.route.startswith("/category/details/"):
        category = page.route.split("/")[-1]  # "5", "12", etc.
        page.views.append(
            ft.View(
                f"/category/details/{category}",
                [loadDetailsCategory(page, category)]
            )
        )
    page.update()
    
ft.app(target=main)
