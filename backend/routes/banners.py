from flask import Blueprint, jsonify

from database.db import get_db
from models.repository import list_banners_ativos

bp = Blueprint("banners", __name__, url_prefix="/api/banners")


@bp.get("")
def listar():
    with get_db() as conn:
        return jsonify(list_banners_ativos(conn))
