from werkzeug.utils import secure_filename

ALLOWED_MIME = {
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/webp",
        "application/pdf"
}

def validate_mime(file):
    if not file.mimetype:
        return True, None

    if file.mimetype.startswith("image/"):
        return True, None

    if file.mimetype == "application/pdf":
        return True, None

    return True, None
