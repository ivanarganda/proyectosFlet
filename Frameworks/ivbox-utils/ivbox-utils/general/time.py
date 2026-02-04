import flet as ft
from datetime import datetime, timezone, timedelta

def get_time_ago(date_str):
    """
    Devuelve tiempo transcurrido en formato legible.
    Admite fechas con o sin milisegundos y evita errores si date_str es None.
    """
    if not date_str or date_str.lower() == "none":
        return "No registered"

    try:
        # intentar con milisegundos
        start = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f")
    except ValueError:
        try:
            # intentar sin milisegundos
            start = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")
        except Exception:
            return "Invalid date"

    # Convertir UTC a hora local (España = UTC+1 invierno / +2 verano)
    start = start.replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=1)))

    now = datetime.now(timezone(timedelta(hours=1)))
    diff = (now - start).total_seconds()

    days = int(diff // 86400)
    hours = int((diff % 86400) // 3600)
    minutes = int((diff % 3600) // 60)
    seconds = int(diff % 60)

    # Formato legible
    if days > 0:
        return f"{days} d and {hours} h ago"
    elif hours > 0:
        return f"{hours} h and {minutes} min ago"
    elif minutes > 0:
        return f"{minutes} min ago"
    elif seconds >= 0:
        return f"{seconds} secs ago"
    else:
        return "Now"

# --- Tiempo y formato ---
def get_timestamp() -> str:
    """Devuelve la fecha/hora actual legible."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_day_name( lang = "EN" ) -> str:
    """Devuelve el día de la semana (Lunes, Martes...)."""
    by_default = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"] 
    days = {
        "ES": ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"],
        "EN": by_default,
        "FR": ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"],
        "DE": ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"],
        "IT": ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
    }.get(lang.upper(), by_default)
    
    return days[datetime.now().weekday()]

def get_time_diff(seconds: float) -> str:
    """Convierte segundos en formato mm:ss."""
    mins, secs = divmod(int(seconds), 60)
    return f"{mins:02d}:{secs:02d}"

def now_ts():
    return int(datetime.now().timestamp())

def age_from_timestamp(ts):
    fecha_nac = datetime.utcfromtimestamp(int(ts)).date()
    hoy = datetime.now().date()
    age = hoy.year - fecha_nac.year - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day))
    return age