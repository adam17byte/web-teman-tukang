from datetime import datetime
from db import db, cursor
from socket_chat import emit_notifikasi

def buat_notifikasi(user_id, judul, isi):
    cursor.execute("""
        INSERT INTO notifikasi (user_id, judul, isi, created_at)
        VALUES (%s,%s,%s,%s)
    """, (user_id, judul, isi, datetime.utcnow()))
    db.commit()
    emit_notifikasi(user_id, {
        "judul": judul,
        "isi": isi
    })
