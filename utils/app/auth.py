import flet as ft
import json
import jwt
from jwt.exceptions import InvalidTokenError

def handle_logout(page: ft.Page):
    page.session.clear()
    page.client_storage.clear()
    page.go("/")

def getSession( data , decrypt=False ):

    data = json.loads( data )

    user_data = data
    
    if decrypt:
        # Aquí iría la lógica de desencriptación si se implementa
        if "token" in user_data:
            try:
                decoded = jwt.decode(user_data["token"], "secret", algorithms=["HS256"])
                return decoded
            except InvalidTokenError:
                return {}
        else:
            return {}
        
    return user_data

def isAuthenticated( page: ft.Page ) -> bool:
    if "user" in page.session:
        user_data = getSession( page.session["user"], decrypt=True )
        if user_data:
            return True
    return False

def getAuthenticatedUser( page: ft.Page ) -> dict:
    if "user" in page.session:
        user_data = getSession( page.session["user"], decrypt=True )
        return user_data
    return {}

def setAuthenticatedUser( page: ft.Page, user_data: dict, encrypt=False ):
    if encrypt:
        token = jwt.encode(user_data, "secret", algorithm="HS256")
        user_data = {"token": token}
    
    page.session["user"] = json.dumps(user_data)
    page.client_storage.set("user", page.session["user"])

def clearAuthenticatedUser( page: ft.Page ):
    if "user" in page.session:
        del page.session["user"]
    page.client_storage.remove("user")

def isAdmin( page: ft.Page ) -> bool:
    user = getAuthenticatedUser( page )
    return user.get("role") == "admin"

def isUser( page: ft.Page ) -> bool:
    user = getAuthenticatedUser( page )
    return user.get("role") == "user"

def isGuest( page: ft.Page ) -> bool:
    user = getAuthenticatedUser( page )
    return user.get("role") == "guest"

def getUserInfo( page: ft.Page, field: str = "name" ) -> str:
    try:
        user = getAuthenticatedUser(page)
        if not isinstance(user, dict):
            return "Guest User"
        return user.get(field) or "Guest User"
    except Exception as e:
        return "Guest User"