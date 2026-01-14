from api import api
from flask import request, jsonify
from flask_jwt_extended import jwt_required
from gradio_client import Client

HF_SPACE_NAME = "afniyuliana/chatbottttt"

# Inisiasi client harus dilakukan, atau akan error 'client' tidak didefinisikan
client = Client(HF_SPACE_NAME)

@api.route("/api/chatbot", methods=["POST"])
@jwt_required()
def api_chatbot():
    data = request.get_json()
    query = data.get("query")

    if not query:
        return jsonify({"status": "error", "message": "query kosong"}), 400

    try:
        answer = client.predict(
            question=query,
            api_name="//predict"
        )

        return jsonify({
            "status": "success",
            "data": { 
                "query": query,
                "answer": answer
            }
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 502