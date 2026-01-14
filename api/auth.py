from flask import request
from flask_jwt_extended import create_access_token
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from db import db, cursor
from . import api, bcrypt
from utils.response import success_response, error_response
from flask_jwt_extended import jwt_required
from extensions import limiter

GOOGLE_CLIENT_ID = "152566724840-itl7926ncrk5pi4lhqtmqtpoaioe5cgr.apps.googleusercontent.com"

@api.route("/api/auth/check", methods=["GET"])
@jwt_required()
def check_token():
    return success_response({"valid": True})

@api.route("/api/register", methods=["POST"])
@limiter.limit("3 per minute")
def register():
    data = request.get_json()
    nama = data.get("nama")
    email = data.get("email")
    password = data.get("password")

    if not nama or not email or not password:
        return error_response("Data tidak lengkap")

    cursor.execute("SELECT id_users FROM users WHERE email=%s", (email,))
    if cursor.fetchone():
        return error_response("Email sudah terdaftar")

    hashed = bcrypt.generate_password_hash(password).decode("utf-8")

    cursor.execute("""
        INSERT INTO users (username, email, password, role, auth_provider)
        VALUES (%s, %s, %s, 'customer', 'local')
    """, (nama, email, hashed))

    db.commit()
    return success_response(message="Registrasi berhasil", code=201)

@api.route("/api/login", methods=["POST"])
@limiter.limit("5/minute")
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()


    if not user or not bcrypt.check_password_hash(user["password"], password):
        return error_response("Email atau password salah", 401)

    token = create_access_token(identity=str(user["id_users"]))
    return success_response({
        "access_token": token,
        "user": {
            "id_users": user["id_users"],
            "username": user["username"],
            "email": user["email"],   
            "role": user["role"]
        }
    })

@api.route("/api/auth/google", methods=["POST"])
def api_login_google():
    token = request.json.get("id_token")
    if not token:
        return error_response("id_token wajib")
    try:
        idinfo = id_token.verify_oauth2_token(
            token, google_requests.Request(), GOOGLE_CLIENT_ID
        )
    except ValueError:
        return error_response("Token Google tidak valid", 401)
    google_id = idinfo["sub"]
    email = idinfo["email"]
    username = idinfo.get("name", email.split("@")[0])
    cursor.execute("SELECT * FROM users WHERE google_id=%s", (google_id,))
    user = cursor.fetchone()
    if not user:
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        if cursor.fetchone():
            return error_response("Email sudah terdaftar dengan metode lain", 409)
        cursor.execute(
            """
            INSERT INTO users (username, email, role, auth_provider, google_id)
            VALUES (%s, %s, 'customer', 'google', %s)
            """,
            (username, email, google_id)
        )
        db.commit()
        cursor.execute("SELECT * FROM users WHERE google_id=%s", (google_id,))
        user = cursor.fetchone()
    token = create_access_token(identity=str(user["id_users"]))
    return success_response({
        "access_token": token,
        "user": {
            "id_users": user["id_users"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"],
            "auth_provider": user["auth_provider"]
        }
    })