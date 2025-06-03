from flask import Blueprint

trip_bp = Blueprint('trip', __name__)

from . import routes
