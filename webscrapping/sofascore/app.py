import os
import sys
import flet as ft

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(BASE_DIR, "App")
sys.path.insert(0, APP_DIR)

from main import main

ft.app(target=main)