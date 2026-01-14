import tensorflow as tf
import numpy as np
from PIL import Image
from flask import request

from . import api
from utils.response import success_response, error_response

model = tf.keras.models.load_model("model/model_temantukang.keras")

@api.route("/api/deteksi", methods=["POST"])
def deteksi():
    if "file" not in request.files:
        return error_response("File tidak ditemukan")

    img = Image.open(request.files["file"]).resize((128,128))
    arr = np.expand_dims(np.array(img)/255.0, axis=0)
    pred = model.predict(arr)

    return success_response({
        "confidence": float(np.max(pred))
    })
