# KENAPA WARNING?
# Jawaban:
# - Tidak ditemukan `import jsonify` dari flask, tapi digunakan pada beberapa tempat.
#   Flask tidak otomatis meng-import jsonify ke global scope; perlu di-import sendiri.
# - Beberapa linter/type checker akan memberi warning:
#   "Undefined name 'jsonify'"
# - Untuk memperbaiki, tambahkan: `from flask import jsonify`

from flask import request, jsonify
from flask_jwt_extended import jwt_required

from db import db, cursor
from . import api
from utils.response import success_response, error_response
from utils.auth import get_user_id


# =====================================
# GET CHAT BY PESANAN
# =====================================
@api.route("/api/chat/<int:pesanan_id>", methods=["GET"])
@jwt_required()
def get_chat(pesanan_id):
    user_id = get_user_id()
    cursor.execute(
        """
        SELECT id_pesanan
        FROM pesanan
        WHERE id_pesanan=%s
          AND (user_id=%s
               OR tukang_id IN (
                   SELECT id_tukang FROM tukang WHERE id_users=%s
               ))
        """, (pesanan_id, user_id, user_id)
    )
    if not cursor.fetchone():
        return jsonify({
            "status": "error",
            "message": "Akses ditolak"
        }), 403
    cursor.execute(
        """
        SELECT sender, message, created_at
        FROM chat
        WHERE pesanan_id=%s
        ORDER BY created_at ASC
        """, (pesanan_id,)
    )
    return jsonify({
        "status": "success",
        "data": cursor.fetchall()
    }), 200

@api.route("/api/chat", methods=["POST"])
@jwt_required()
def send_chat():
    user_id = get_user_id()
    data = request.get_json()
    if not data:
        return jsonify({
            "status": "error",
            "message": "Request tidak valid"
        }), 400
    pesanan_id = data.get("pesanan_id")
    message = data.get("message")
    if not pesanan_id or not message:
        return jsonify({
            "status": "error",
            "message": "Data tidak lengkap"
        }), 400
    cursor.execute("SELECT role FROM users WHERE id_users=%s", (user_id,))
    user = cursor.fetchone()
    if not user:
        return jsonify({
            "status": "error",
            "message": "User tidak valid"
        }), 401
    cursor.execute(
        """
        SELECT status
        FROM pesanan
        WHERE id_pesanan=%s
          AND (user_id=%s
               OR tukang_id IN (
                   SELECT id_tukang FROM tukang WHERE id_users=%s
               ))
        """, (pesanan_id, user_id, user_id)
    )
    pesanan = cursor.fetchone()
    if not pesanan or pesanan.get("status") == "selesai":
        return jsonify({
            "status": "error",
            "message": "Chat ditutup"
        }), 403
    cursor.execute(
        """
        INSERT INTO chat (pesanan_id, sender, message)
        VALUES (%s, %s, %s)
        """, (pesanan_id, user["role"], message)
    )
    db.commit()
    return jsonify({
        "status": "success",
        "message": "Pesan terkirim"
    }), 201
