from flask_jwt_extended import jwt_required
from . import api
from utils.response import success_response
from utils.auth import get_user_id
from db import cursor

@api.route("/api/notifikasi", methods=["GET"])
@jwt_required()
def get_notifikasi():
    user_id = get_user_id()
    cursor.execute("""
        SELECT id, judul, isi, is_read, created_at
        FROM notifikasi
        WHERE user_id=%s
        ORDER BY created_at DESC
    """, (user_id,))
    return success_response(cursor.fetchall())
