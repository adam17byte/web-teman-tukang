from flask import request
from flask_jwt_extended import jwt_required

from db import db, cursor
from . import api
from utils.response import success_response, error_response
from utils.auth import get_user_id
from utils.sentiment import predict_sentiment
from utils.pagination import get_pagination_params, build_pagination_meta


# ======================================================
# TAMBAH REVIEW (HANYA JIKA PESANAN SELESAI)
# ======================================================
@api.route("/api/review", methods=["POST"])
@jwt_required()
def add_review():
    user_id = get_user_id()
    data = request.get_json()

    if not data:
        return error_response("Request tidak valid")

    pesanan_id = data.get("pesanan_id")
    tukang_id = data.get("tukang_id")
    review_text = data.get("review_text")
    rating = data.get("rating")

    if not pesanan_id or not tukang_id or not review_text or rating is None:
        return error_response("Data tidak lengkap")

    try:
        rating = int(rating)
    except ValueError:
        return error_response("Rating harus berupa angka")

    if rating < 1 or rating > 5:
        return error_response("Rating harus antara 1 sampai 5")

    # ================= VALIDASI PESANAN =================
    cursor.execute("""
        SELECT id_pesanan
        FROM pesanan
        WHERE id_pesanan=%s
          AND user_id=%s
          AND tukang_id=%s
          AND status='selesai'
    """, (pesanan_id, user_id, tukang_id))

    if not cursor.fetchone():
        return error_response(
            "Pesanan tidak valid atau belum selesai", 403
        )

    # ================= CEGAH REVIEW GANDA =================
    cursor.execute("""
        SELECT id_review
        FROM review
        WHERE pesanan_id=%s
    """, (pesanan_id,))

    if cursor.fetchone():
        return error_response(
            "Pesanan ini sudah direview", 409
        )

    sentiment = predict_sentiment(review_text)

    try:
        cursor.execute("""
            INSERT INTO review
            (user_id, tukang_id, pesanan_id, review_text, sentiment, rating)
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (
            user_id,
            tukang_id,
            pesanan_id,
            review_text,
            sentiment,
            rating
        ))

        # ================= UPDATE RATING TUKANG =================
        cursor.execute("""
            UPDATE tukang
            SET
                rating = (
                    SELECT ROUND(IFNULL(AVG(rating), 0), 2)
                    FROM review
                    WHERE tukang_id=%s
                ),
                jumlah_ulasan = (
                    SELECT COUNT(*)
                    FROM review
                    WHERE tukang_id=%s
                )
            WHERE id_tukang=%s
        """, (tukang_id, tukang_id, tukang_id))

        db.commit()

        return success_response(
            data={
                "sentiment": sentiment,
                "rating": rating
            },
            message="Review berhasil ditambahkan",
            code=201
        )

    except Exception as e:
        db.rollback()
        print("ERROR ADD REVIEW:", e)
        return error_response("Gagal menyimpan review", 500)


# ======================================================
# GET REVIEW BY TUKANG (PUBLIC + PAGINATION)
# ======================================================
@api.route("/api/tukang/<int:id_tukang>/review", methods=["GET"])
def get_review_tukang(id_tukang):
    page, limit, offset = get_pagination_params(request)

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM review
        WHERE tukang_id=%s
    """, (id_tukang,))
    total = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT
            r.review_text,
            r.rating,
            r.sentiment,
            r.tanggal,
            u.username AS customer
        FROM review r
        JOIN users u ON r.user_id=u.id_users
        WHERE r.tukang_id=%s
        ORDER BY r.tanggal DESC
        LIMIT %s OFFSET %s
    """, (id_tukang, limit, offset))

    data = cursor.fetchall()

    return success_response(
        data=data,
        meta=build_pagination_meta(page, limit, total)
    )
