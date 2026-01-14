from flask import jsonify

def success_response(data=None, message="success", code=200):
    payload = {
        "status": "success",
        "message": message,
        "data": data
    }
    return jsonify(payload), code


def error_response(message="error", code=400):
    payload = {
        "status": "error",
        "message": message
    }
    return jsonify(payload), code
