import logging
from fastapi import FastAPI, Request, Depends, HTTPException, BackgroundTasks
from dotenv import load_dotenv
from ivbox.SQLiteORM import *
from init_data import init_tables
from params import DB,INITTED_FOLDER
from scrapping_state import SCRAPING_STATUS
from scrap import run_scrapping
import glob
from pathlib import Path
# --------------------------------------------------------------------
# CONFIG
# --------------------------------------------------------------------

logging.basicConfig(
    filename="process.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

load_dotenv()

app = FastAPI(
    title="SofaScore Backend",
    version="1.0.0",
    description="Backend API for SofaScore Scraping + DB"
)

db: SQLiteORM | None = None

# --------------------------------------------------------------------
# STARTUP EVENT  (equivalente a handle_server)
# --------------------------------------------------------------------

@app.on_event("startup")
def startup_event():

    try:

        logging.info("✅ Server started and DB initialized")

    except Exception as e:
        logging.error(str(e))
        raise


# --------------------------------------------------------------------
# HELPERS
# --------------------------------------------------------------------

def parse_json_response(message, status: int = 200):
    return {
        "message": message,
        "status": status
    }

def progress_callback(step, current=None, total=None):

    SCRAPING_STATUS["running"] = True
    SCRAPING_STATUS["step"] = step

    if current is not None:
        SCRAPING_STATUS["current"] = current
    if total is not None:
        SCRAPING_STATUS["total"] = total

    # ✅ FIN
    if current is not None and total is not None and current >= total:
        SCRAPING_STATUS["running"] = False
        SCRAPING_STATUS["finished"] = True


# --------------------------------------------------------------------
# AUTHORIZATION DEPENDENCY
# --------------------------------------------------------------------

def check_authorization(request: Request):
    auth_header = request.headers.get("Authorization")

    if not auth_header or "Bearer " not in auth_header:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        token = auth_header.split(" ")[1]
    except IndexError:
        raise HTTPException(status_code=401, detail="Invalid token format")

    result = db.execute_query(
        "SELECT * FROM usuarios WHERE token = ?",
        (token,)
    ).json

    if not result:
        raise HTTPException(status_code=401, detail="Invalid token")

    return True


# --------------------------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/init_data")
def init_data():
    if init_tables() is False:
        raise RuntimeError("❌ Unable initializing database tables")
    return parse_json_response("Scrapped ✅",200)

# --------------------------------------------------------------------
# PROTECTED TEST ENDPOINT
# --------------------------------------------------------------------

@app.get("/protected")
def protected_route(auth: bool = Depends(check_authorization)):
    return parse_json_response("Authorized ✅")

@app.get("/scrapping/status")
def scrapping_status():
    return SCRAPING_STATUS

@app.post("/scrapping/start")
def start_scrapping(background_tasks: BackgroundTasks):

    init_data()

    if SCRAPING_STATUS["running"]:
        return parse_json_response("Scraping already running", 409)

    SCRAPING_STATUS.update({
        "running": True,
        "finished": False,
        "current": 0,
        "total": 0,
        "step": "Inicializando",
        "error": None
    })

    background_tasks.add_task(run_scrapping, progress_callback) # permite ejecutar en segundo plano scrap.py para que vaya llamando al callback que es progress_cb

    return parse_json_response("Scraping started ✅")

@app.get("/files/db")
def list_db_files():
    pattern = f"{INITTED_FOLDER}*_db.*"
    files = glob.glob(pattern)
    return {
        "files": [Path(f).name for f in files]
    }

# ===================
# USERS
# ===================
@app.route("/users/login", methods=["POST"])
def login():

    try:

        handle_server()

        json_data = request.json

        # logging.debug(json_data) 

        email = json_data.get("email", None )
        password = json_data.get("password", None )

        if email == None or password == None:
            return parse_json_response( "Incorrect credentials" , 400 )

        result = db.execute_query(
            """ 
                SELECT id_usuario, username, email,password from users where email = ?
            """,
            ( email, )
        ).json

        # logging.debug(db.get_query())

        # logging.debug(result) 

        if not result:
            return parse_json_response( f"User {email} does not exist" , 402 )

        password_db = result[0]["password"]
        
        if password_db != password:
            return parse_json_response( "Incorrect password" , 401 )
        
        # To set payload for JWT token
        result = db.execute_query(
            """ 
               SELECT
                    u.id_usuario,
                    u.username,
                    u.email,
                    u.rol as role
                from usuarios u
                where u.email = ?
            """,
            ( email, )
        ).json

        # logging.debug(db.get_query())

        import jwt

        # Define a secret key
        secret_key = "secret"

        payload = result[0]
        
        payload["exp"] =  datetime.datetime.utcnow() + datetime.timedelta(hours=1)

        logging.debug(payload)

        encoded_jwt = jwt.encode(payload, secret_key, algorithm="HS256")
        
        db.execute_query(
            """ 
                UPDATE usuarios SET token = ? where email = ?
            """,
            ( encoded_jwt , email )
        )

        return parse_json_response( 
            {
                "token": encoded_jwt
            } 
        )

    except Exception as e:

        logging.debug(e)
        
        return parse_json_response( str(e) , 400 )