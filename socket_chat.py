from flask_socketio import emit, join_room
from flask_jwt_extended import decode_token
from db import db, cursor
from app import socketio

@socketio.on("join_chat")
def join_chat(data):
    try:
        token = data["token"]
        pesanan_id = data["pesanan_id"]

        user_id = decode_token(token)["sub"]

        cursor.execute("""
            SELECT id_pesanan FROM pesanan
            WHERE id_pesanan=%s
            AND (user_id=%s OR tukang_id=%s)
        """, (pesanan_id, user_id, user_id))

        if not cursor.fetchone():
            emit("error", {"message": "Akses ditolak"})
            return

        join_room(f"pesanan_{pesanan_id}")
        emit("joined", {"pesanan_id": pesanan_id})

    except Exception as e:
        emit("error", {"message": str(e)})


@socketio.on("send_message")
def send_message(data):
    try:
        token = data["token"]
        pesanan_id = data["pesanan_id"]
        message = data["message"]

        user_id = decode_token(token)["sub"]

        cursor.execute("SELECT role FROM users WHERE id_users=%s", (user_id,))
        row = cursor.fetchone()
        if not row:
            emit("error", {"message": "User tidak ditemukan"})
            return

        sender = row["role"]
        if sender not in ["customer", "tukang"]:
            emit("error", {"message": "Role tidak valid untuk chat"})
            return

        cursor.execute("""
            SELECT status FROM pesanan
            WHERE id_pesanan=%s
            AND (user_id=%s OR tukang_id=%s)
        """, (pesanan_id, user_id, user_id))

        pesanan = cursor.fetchone()
        if not pesanan or pesanan["status"] == "selesai":
            emit("chat_closed")
            return

        cursor.execute("""
            INSERT INTO chat (pesanan_id, sender, message)
            VALUES (%s,%s,%s)
        """, (pesanan_id, sender, message))
        db.commit()

        emit(
            "receive_message",
            {
                "sender": sender,
                "message": message
            },
            room=f"pesanan_{pesanan_id}"
        )

    except Exception as e:
        emit("error", {"message": str(e)})
