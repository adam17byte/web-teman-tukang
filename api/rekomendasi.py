from flask import request
from flask_jwt_extended import jwt_required
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from db import cursor
from . import api
from utils.response import success_response, error_response


def to_float(val):
    try:
        return float(val)
    except Exception:
        return 0.0


@api.route("/api/rekomendasi", methods=["POST"])
@jwt_required()
def api_rekomendasi():
    data = request.get_json()
    jenis_kerusakan = data.get("jenis_kerusakan") if data else None

    if not jenis_kerusakan:
        return error_response("jenis_kerusakan wajib diisi", 422)

    cursor.execute("""
        SELECT
            id_tukang,
            nama,
            keahlian,
            pengalaman,
            rating,
            foto
        FROM tukang
    """)
    tukang_data = cursor.fetchall()

    if not tukang_data:
        return success_response([])

    # Gabungkan teks keahlian + pengalaman
    dokumen = [
        f"{t['keahlian']} {t['pengalaman'] or ''}"
        for t in tukang_data
    ]

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(dokumen)

    query_vec = vectorizer.transform([jenis_kerusakan])
    sim_scores = cosine_similarity(query_vec, tfidf_matrix).flatten()

    # Normalisasi rating (PAKSA FLOAT)
    ratings = [to_float(t["rating"]) for t in tukang_data]
    max_rating = max(ratings) if max(ratings) > 0 else 1.0

    rekomendasi = []
    for i, t in enumerate(tukang_data):
        sim = float(sim_scores[i])
        if sim < 0.1:
            continue

        rating_norm = to_float(t["rating"]) / max_rating
        score = (0.7 * sim) + (0.3 * rating_norm)

        rekomendasi.append({
            "id_tukang": t["id_tukang"],
            "nama": t["nama"],
            "keahlian": t["keahlian"],
            "pengalaman": t["pengalaman"],
            "rating": to_float(t["rating"]),
            "foto": t["foto"],
            "score": round(score, 4)
        })

    rekomendasi.sort(key=lambda x: x["score"], reverse=True)

    return success_response(rekomendasi)
