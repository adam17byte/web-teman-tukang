from flask import request
from flask_jwt_extended import jwt_required

from db import db, cursor
from . import api
from utils.response import success_response, error_response
from utils.auth import get_user_id, get_tukang_id
from utils.pagination import get_pagination_params, build_pagination_meta
from utils.role import role_required
from flask_jwt_extended import get_jwt_identity
# ======================================
# PROFIL TUKANG (PRIBADI)
# ======================================

@api.route("/api/tukang/profile", methods=["GET"])
@jwt_required()
def get_tukang_profile():
    user_id = get_user_id()

    cursor.execute("""
        SELECT
            id_tukang,
            nama,
            keahlian,
            pengalaman,
            foto,
            rating,
            jumlah_ulasan
        FROM tukang
        WHERE id_users=%s
    """, (user_id,))

    tukang = cursor.fetchone()
    if not tukang:
        return error_response("Profil tukang tidak ditemukan", 404)

    return success_response(tukang)


@api.route("/api/tukang/profile", methods=["PUT"])
@jwt_required()
def update_tukang_profile():
    user_id = get_user_id()
    data = request.get_json()

    if not data:
        return error_response("Request tidak valid")

    cursor.execute(
        "SELECT id_tukang FROM tukang WHERE id_users=%s",
        (user_id,)
    )
    tukang = cursor.fetchone()

    if not tukang:
        return error_response("Profil tukang tidak ditemukan", 404)

    cursor.execute("""
        UPDATE tukang
        SET
            nama=%s,
            keahlian=%s,
            pengalaman=%s,
            foto=%s
        WHERE id_users=%s
    """, (
        data.get("nama"),
        data.get("keahlian"),
        data.get("pengalaman"),
        data.get("foto"),
        user_id
    ))

    db.commit()

    return success_response(message="Profil tukang berhasil diperbarui")


# ======================================
# PROFIL TUKANG (PUBLIC)
# ======================================

@api.route("/api/tukang/<int:id_tukang>", methods=["GET"])
@jwt_required()
def get_tukang_public(id_tukang):
    cursor.execute("""
        SELECT
            id_tukang,
            nama,
            keahlian,
            pengalaman,
            foto,
            rating,
            jumlah_ulasan
        FROM tukang
        WHERE id_tukang=%s
    """, (id_tukang,))

    tukang = cursor.fetchone()
    if not tukang:
        return error_response("Tukang tidak ditemukan", 404)

    cursor.execute("""
        SELECT
            review_text,
            rating,
            sentiment,
            tanggal
        FROM review
        WHERE tukang_id=%s
        ORDER BY tanggal DESC
    """, (id_tukang,))

    ulasan = cursor.fetchall()

    return success_response({
        "tukang": tukang,
        "ulasan": ulasan
    })

@api.route("/api/tukang/riwayat", methods=["GET"])
@jwt_required()
def riwayat_tukang():
    tukang_id = get_tukang_id()
    if not tukang_id:
        return error_response("Akun bukan tukang", 403)

    cursor.execute("""
        SELECT
            p.id_pesanan,
            u.username AS nama_customer,
            p.alamat,
            p.tanggal_pengerjaan,
            p.harga_per_hari,
            p.status,
            p.created_at
        FROM pesanan p
        JOIN users u ON p.user_id = u.id_users
        WHERE p.tukang_id = %s
        ORDER BY p.created_at DESC
    """, (tukang_id,))

    return success_response(cursor.fetchall())

# ======================================
# REKAP DATA TUKANG
# ======================================

@api.route("/api/tukang/rekap", methods=["GET"])
@jwt_required()
@role_required("tukang")
def rekap_tukang():
    tukang_id = get_tukang_id()

    if not tukang_id:
        return error_response("Akun bukan tukang", 403)

    cursor.execute("""
        SELECT
            SUM(CASE WHEN status='menunggu_konfirmasi' THEN 1 ELSE 0 END) AS masuk,
            SUM(CASE WHEN status='selesai' THEN 1 ELSE 0 END) AS selesai
        FROM pesanan
        WHERE tukang_id=%s
    """, (tukang_id,))

    data = cursor.fetchone()

    return success_response({
        "proyek_masuk": int(data["masuk"] or 0),
        "proyek_selesai": int(data["selesai"] or 0)
    })
