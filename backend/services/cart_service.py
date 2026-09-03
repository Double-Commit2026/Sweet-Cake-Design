"""
Serviço de validação do carrinho.

Recebe a lista de itens que o front-end guardou (via localStorage) e
recalcula CADA item do zero usando o pricing_service — nunca confia em
nenhum preço que tenha vindo do navegador. É essa revalidação que
impede que alguém altere valores no DevTools antes de finalizar o pedido.
"""
from services.pricing_service import (
    calcular_preco_item_fixo,
    calcular_preco_item_configuravel,
    ItemIndisponivelError,
    ProdutoNaoEncontradoError,
)


def validar_carrinho(conn, itens):
    """
    itens: lista de dicts no formato:
      { "product_id": int, "quantidade": int, "variant_id": int|None, "option_ids": [int]|None }

    Retorna: { "itens": [...], "total": float|None, "tem_item_sob_orcamento": bool, "erros": [...] }
    """
    itens_calculados = []
    erros = []
    total_centavos = 0
    tem_item_sob_orcamento = False

    for item in itens:
        product_id = item.get("product_id")
        quantidade = item.get("quantidade", 1)
        variant_id = item.get("variant_id")
        option_ids = item.get("option_ids") or []

        if not product_id or quantidade < 1:
            erros.append("Item inválido no carrinho.")
            continue

        try:
            if variant_id:
                resultado = calcular_preco_item_configuravel(conn, product_id, variant_id, option_ids, quantidade)
            else:
                resultado = calcular_preco_item_fixo(conn, product_id, quantidade)
        except (ItemIndisponivelError, ProdutoNaoEncontradoError) as e:
            erros.append(str(e))
            continue

        itens_calculados.append(resultado)
        if resultado["requer_orcamento"]:
            tem_item_sob_orcamento = True
        else:
            total_centavos += round(resultado["subtotal"] * 100)

    return {
        "itens": itens_calculados,
        # Soma apenas os itens com preço definido; itens sob orçamento entram
        # separadamente na mensagem do WhatsApp, sem valor.
        "total": round(total_centavos / 100, 2),
        "tem_item_sob_orcamento": tem_item_sob_orcamento,
        "erros": erros,
    }
