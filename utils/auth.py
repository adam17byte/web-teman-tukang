from flask_jwt_extended import get_jwt_identity
from db import cursor

def get_user_id():
    return int(get_jwt_identity())

def get_tukang_id():
    user_id = get_user_id()
    cursor.execute(
        "SELECT id_tukang FROM tukang WHERE id_users=%s",
        (user_id,)
    )
    row = cursor.fetchone()
    return row["id_tukang"] if row else None
