from functools import wraps
from flask_jwt_extended import get_jwt_identity
from utils.response import error_response
from db import cursor

def role_required(*allowed_roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user_id = get_jwt_identity()
            if not user_id:
                return error_response("Unauthorized", 401)

            cursor.execute(
                "SELECT role FROM users WHERE id_users=%s",
                (user_id,)
            )
            user = cursor.fetchone()

            if not user or user["role"] not in allowed_roles:
                return error_response("Akses ditolak", 403)

            return fn(*args, **kwargs)
        return wrapper
    return decorator
