from flask import Blueprint, jsonify

from database.db import get_db
from models.repository import get_store_info

bp = Blueprint("store_info", __name__, url_prefix="/api/store-info")


@bp.get("")
def get_info():
    with get_db() as conn:
        return jsonify(get_store_info(conn))
