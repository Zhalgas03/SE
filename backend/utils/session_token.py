from flask import request

def get_guest_token():
    return request.cookies.get("session_token")
