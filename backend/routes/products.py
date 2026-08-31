from flask import Blueprint, jsonify, request

from database.db import get_db
from models.repository import list_products, get_product_detail

bp = Blueprint("products", __name__, url_prefix="/api/products")


@bp.get("")
def get_products():
    categoria = request.args.get("categoria")
    destaque = request.args.get("destaque") == "true"
    with get_db() as conn:
        return jsonify(list_products(conn, categoria_slug=categoria, apenas_destaque=destaque))


@bp.get("/<int:product_id>")
def get_product(product_id):
    with get_db() as conn:
        produto = get_product_detail(conn, product_id)
    if not produto:
        return jsonify({"detail": "Produto não encontrado."}), 404
    return jsonify(produto)
