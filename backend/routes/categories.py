from flask import Blueprint, jsonify

from database.db import get_db
from models.repository import list_categories

bp = Blueprint("categories", __name__, url_prefix="/api/categories")


@bp.get("")
def get_categories():
    with get_db() as conn:
        return jsonify(list_categories(conn))
