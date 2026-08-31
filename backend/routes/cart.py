from flask import Blueprint, jsonify, request

from database.db import get_db
from services.cart_service import validar_carrinho

bp = Blueprint("cart", __name__, url_prefix="/api/cart")


@bp.post("/validate")
def validate():
    """
    Corpo esperado: { "itens": [ {product_id, quantidade, variant_id, option_ids} ] }

    Recalcula cada item no servidor e devolve o total oficial. O front-end
    chama essa rota logo antes de montar a mensagem do WhatsApp, para
    garantir que o valor final é sempre o do backend — nunca o que estava
    guardado (e potencialmente alterado) no navegador.
    """
    dados = request.get_json(silent=True) or {}
    itens = dados.get("itens") or []

    with get_db() as conn:
        resultado = validar_carrinho(conn, itens)

    return jsonify(resultado)
