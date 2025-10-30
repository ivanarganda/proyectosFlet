from helpers.utils import getSession, handle_logout, log_error
def middleware_auth( page )-> dict:
    try:
        # Sesión
        session = page.client_storage.get("user") or "{}"
        token_session = getSession( session ).get("token",None)
        user_session = getSession( session, True ) or None

        if token_session == None or user_session == None:
            handle_logout(page)

        # Optional object to get whatever necessary items 
        return {
            "token": token_session,
            "session": user_session
        }
    except Exception as e:
        log_error("⚠️ middleware_auth error:", e)
        handle_logout(page)