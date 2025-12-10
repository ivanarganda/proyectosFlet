import subprocess
import os
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def kill_backend():
    print("🛑 Matando todos los procesos uvicorn...")
    subprocess.call('taskkill /F /IM uvicorn.exe /T', shell=True)
    subprocess.call('taskkill /F /IM python.exe /FI "WINDOWTITLE eq uvicorn" /T', shell=True)
    print("✔ Servidor detenido.")


# ---- 1. Iniciar Backend ----
print("🚀 Lanzando backend...")
backend = subprocess.Popen(
    ["cmd", "/c", "start", "run.bat"],  # abre una ventana CMD que ejecuta el bat
    cwd=BASE_DIR,
    shell=True
)

time.sleep(1)


# ---- 2. Iniciar Frontend (Flet) ----
print("🎨 Lanzando frontend Flet...")
frontend = subprocess.Popen(
    ["python", os.path.join(BASE_DIR, "app.py")],
    cwd=BASE_DIR
)


# ---- 3. ESPERAR A QUE FLET SE CIERRE ----
frontend.wait()

print("❌ Flet se cerró. Procediendo a matar el servidor backend...")

# ---- 4. MATAR TODOS LOS UVICORN ----
kill_backend()

print("😴 Todo cerrado correctamente.")