from flask import Blueprint, jsonify, request

from database.db import get_db
from services.pricing_service import (
    calcular_preco_item_configuravel,
    calcular_preco_item_fixo,
    ItemIndisponivelError,
    ProdutoNaoEncontradoError,
)

bp = Blueprint("pricing", __name__, url_prefix="/api/pricing")


@bp.post("/calculate")
def calculate():
    """
    Corpo esperado:
      { "product_id": int, "quantidade": int,
        "variant_id": int|null, "option_ids": [int]|null }

    Usado pelo wizard para mostrar o preço somando em tempo real a cada
    escolha do cliente — o cálculo em si sempre acontece aqui, nunca no JS.
    """
    dados = request.get_json(silent=True) or {}
    product_id = dados.get("product_id")
    quantidade = dados.get("quantidade", 1)
    variant_id = dados.get("variant_id")
    option_ids = dados.get("option_ids") or []

    if not product_id:
        return jsonify({"detail": "product_id é obrigatório."}), 400

    try:
        with get_db() as conn:
            if variant_id:
                resultado = calcular_preco_item_configuravel(conn, product_id, variant_id, option_ids, quantidade)
            else:
                resultado = calcular_preco_item_fixo(conn, product_id, quantidade)
    except ProdutoNaoEncontradoError as e:
        return jsonify({"detail": str(e)}), 404
    except ItemIndisponivelError as e:
        return jsonify({"detail": str(e)}), 409

    return jsonify(resultado)
