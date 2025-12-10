@echo off
cd /d C:\Users\ivana\Desktop\curso-inserta-big-data\ProyectosPython\webscrapping\sofascore\Server
uvicorn app:app --host 0.0.0.0 --port 5000 --reload