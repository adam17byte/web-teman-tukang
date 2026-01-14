from flask import request
from flask_jwt_extended import jwt_required
from datetime import datetime
import os
from werkzeug.utils import secure_filename

from db import db, cursor
from . import api
from utils.response import success_response, error_response
from utils.auth import get_user_id, get_tukang_id
from utils.notifikasi import buat_notifikasi
from utils.pagination import get_pagination_params, build_pagination_meta
from utils.role import role_required

# =========================
# KONSTANTA STATUS
# =========================
PESANAN_MENUNGGU = "menunggu_konfirmasi"
PESANAN_DITERIMA = "diterima"
PESANAN_DITOLAK = "ditolak"
PESANAN_MENUJU = "menuju_lokasi"
PESANAN_PROSES = "dalam_pengerjaan"
PESANAN_SELESAI = "selesai"

ALUR_STATUS_PESANAN = {
    PESANAN_MENUNGGU: [PESANAN_DITERIMA, PESANAN_DITOLAK],
    PESANAN_DITERIMA: [PESANAN_MENUJU],
    PESANAN_MENUJU: [PESANAN_PROSES],
    PESANAN_PROSES: [PESANAN_SELESAI],
}

# =========================
# UPLOAD CONFIG
# =========================
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "pdf"}
MAX_FILE_SIZE = 5 * 1024 * 1024

def validate_upload(file):
    if not file or file.filename == "":
        return False, "File tidak ditemukan"

    ext = file.filename.rsplit(".", 1)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, "Format file tidak diizinkan"

    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)

    if size > MAX_FILE_SIZE:
        return False, "Ukuran file maksimal 5MB"

    return True, None

# ======================================================
# PESANAN - CUSTOMER
# ======================================================

@api.route("/api/pesanan", methods=["POST"])
@jwt_required()
@role_required("customer")
def buat_pesanan():
    user_id = get_user_id()
    data = request.get_json()

    metode = data.get("metode_pembayaran")
    if metode not in ("cash", "transfer"):
        return error_response("Metode pembayaran tidak valid")

    status_pembayaran = "dibayar" if metode == "cash" else "belum_bayar"


    cursor.execute("""
        INSERT INTO pesanan (
            user_id,
            tukang_id,
            nama_customer,
            alamat,
            tanggal_pengerjaan,
            harga_per_hari,
            metode_pembayaran,
            status_pembayaran,
            status
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        user_id,
        data["tukang_id"],
        data["nama_customer"],
        data["alamat"],
        data["tanggal_pengerjaan"],
        data["harga_per_hari"],
        metode,
        status_pembayaran,
        PESANAN_MENUNGGU
    ))
    db.commit()

    cursor.execute(
        "SELECT id_users FROM tukang WHERE id_tukang=%s",
        (data["tukang_id"],)
    )
    tukang = cursor.fetchone()
    if tukang:
        buat_notifikasi(
            tukang["id_users"],
            "Pesanan Baru",
            "Ada pesanan baru dari customer"
        )

    return success_response(
        message="Pesanan berhasil dibuat",
        code=201
    )

# ======================================================
# UPLOAD BUKTI PEMBAYARAN (TRANSFER ONLY)
# ======================================================

@api.route("/api/pesanan/upload-bukti/<int:id_pesanan>", methods=["POST"])
@jwt_required()
@role_required("customer")
def upload_bukti_pembayaran(id_pesanan):
    if "bukti_pembayaran" not in request.files:
        return error_response("File tidak ditemukan")

    file = request.files["bukti_pembayaran"]

    valid, msg = validate_upload(file)
    if not valid:
        return error_response(msg)

    cursor.execute("""
        SELECT
            status,
            metode_pembayaran,
            status_pembayaran
        FROM pesanan
        WHERE id_pesanan=%s AND user_id=%s
    """, (id_pesanan, get_user_id()))

    pesanan = cursor.fetchone()
    if not pesanan:
        return error_response("Pesanan tidak ditemukan", 404)

    if pesanan["metode_pembayaran"] != "transfer":
        return error_response(
            "Bukti pembayaran hanya untuk metode transfer", 400
        )

    if pesanan["status_pembayaran"] == "dibayar":
        return error_response(
            "Bukti pembayaran sudah diupload", 400
        )

    if pesanan["status"] not in (
        PESANAN_DITERIMA,
        PESANAN_MENUJU
    ):
        return error_response(
            "Upload hanya boleh sebelum pengerjaan dimulai", 403
        )

    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = secure_filename(
        f"{id_pesanan}_{int(datetime.utcnow().timestamp())}.{ext}"
    )

    file.save(os.path.join(UPLOAD_FOLDER, filename))

    cursor.execute("""
        UPDATE pesanan
        SET
            bukti_pembayaran=%s,
            status_pembayaran='dibayar'
        WHERE id_pesanan=%s
    """, (filename, id_pesanan))

    db.commit()

    return success_response(
        message="Bukti pembayaran berhasil diupload"
    )

# ======================================================
# RIWAYAT PESANAN CUSTOMER
# ======================================================

@api.route("/api/customer/pesanan", methods=["GET"])
@jwt_required()
@role_required("customer")
def riwayat_customer():
    user_id = get_user_id()
    page, limit, offset = get_pagination_params(request)

    # ================= TOTAL =================
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM pesanan
        WHERE user_id=%s
    """, (user_id,))
    total = cursor.fetchone()["total"]

    # ================= DATA =================
    cursor.execute("""
        SELECT
            p.id_pesanan,
            p.tukang_id,
            t.nama AS nama_tukang,
            p.tanggal_pengerjaan,
            p.alamat,
            p.harga_per_hari,
            p.status,
            p.metode_pembayaran,
            p.status_pembayaran,
            p.bukti_pembayaran,
            p.created_at,

            r.rating,
            r.review_text AS ulasan

        FROM pesanan p
        JOIN tukang t ON p.tukang_id = t.id_tukang
        LEFT JOIN review r ON r.pesanan_id = p.id_pesanan

        WHERE p.user_id=%s
        ORDER BY p.created_at DESC
        LIMIT %s OFFSET %s
    """, (user_id, limit, offset))

    data = cursor.fetchall()

    return success_response(
        data={
            "items": data,
            "meta": build_pagination_meta(page, limit, total)
        },
        message=None,
        code=200
    )


# ======================================================
# PESANAN MASUK - TUKANG
# ======================================================

@api.route("/api/tukang/pesanan-masuk", methods=["GET"])
@jwt_required()
@role_required("tukang")
def pesanan_masuk_tukang():
    tukang_id = get_tukang_id()

    cursor.execute("""
        SELECT *
        FROM pesanan
        WHERE tukang_id=%s
          AND status!='selesai'
        ORDER BY created_at DESC
    """, (tukang_id,))

    return success_response(cursor.fetchall())

# ======================================================
# KONFIRMASI PESANAN
# ======================================================

@api.route("/api/tukang/pesanan/konfirmasi", methods=["PUT"])
@jwt_required()
@role_required("tukang")
def konfirmasi_pesanan():
    tukang_id = get_tukang_id()
    data = request.get_json()

    cursor.execute("""
        UPDATE pesanan
        SET status=%s
        WHERE id_pesanan=%s
          AND tukang_id=%s
          AND status=%s
    """, (
        data["status"],
        data["id_pesanan"],
        tukang_id,
        PESANAN_MENUNGGU
    ))
    db.commit()

    return success_response(message="Pesanan dikonfirmasi")

# ======================================================
# UPDATE STATUS PENGERJAAN
# ======================================================

@api.route("/api/tukang/pesanan/status", methods=["PUT"])
@jwt_required()
@role_required("tukang")
def update_status():
    tukang_id = get_tukang_id()
    data = request.get_json()

    cursor.execute("""
        SELECT
            status,
            metode_pembayaran,
            status_pembayaran,
            user_id
        FROM pesanan
        WHERE id_pesanan=%s
          AND tukang_id=%s
    """, (data["id_pesanan"], tukang_id))

    p = cursor.fetchone()
    if not p:
        return error_response("Pesanan tidak ditemukan")

    if data["status"] not in ALUR_STATUS_PESANAN.get(p["status"], []):
        return error_response("Alur status tidak valid")

    # 🔒 BLOKIR JIKA TRANSFER BELUM BAYAR
    if (
        p["metode_pembayaran"] == "transfer"
        and p["status_pembayaran"] != "dibayar"
    ):
        return error_response("Customer belum melakukan pembayaran")

    cursor.execute("""
        UPDATE pesanan
        SET status=%s
        WHERE id_pesanan=%s
    """, (data["status"], data["id_pesanan"]))

    db.commit()

    buat_notifikasi(
        p["user_id"],
        "Update Pesanan",
        f"Status: {data['status']}"
    )

    return success_response(message="Status diperbarui")

@api.route("/api/customer/home", methods=["GET"])
@jwt_required()
def home_customer():
    user_id = get_user_id()
    cursor.execute(
        """
        SELECT
            p.id_pesanan,
            t.nama AS nama_tukang,
            p.tanggal_pengerjaan,
            p.status,
            p.harga_per_hari
        FROM pesanan p
        JOIN tukang t ON p.tukang_id = t.id_tukang
        WHERE p.user_id=%s
          AND p.status != %s
        ORDER BY p.created_at DESC
        """, (user_id, PESANAN_SELESAI)
    )
    return success_response(cursor.fetchall())