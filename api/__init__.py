from flask import Blueprint
from flask_bcrypt import Bcrypt

api = Blueprint("api", __name__)
bcrypt = Bcrypt()

from . import auth
from . import pesanan
from . import tukang
from . import review
from . import chat
from . import rekomendasi
from . import ml
from . import notifikasi
from . import chatbot

