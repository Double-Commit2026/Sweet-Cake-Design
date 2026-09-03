"""
Serviço de precificação.

Esta é a ÚNICA função autorizada a calcular o preço final de um item.
Tanto o wizard (pré-visualização em tempo real) quanto a validação final
do carrinho passam por aqui — o front-end nunca soma preços por conta
própria para fins de cobrança, apenas exibe o que este serviço retorna.
"""
from database.db import get_db
from models.repository import centavos_para_reais


class ItemIndisponivelError(Exception):
    pass


class ProdutoNaoEncontradoError(Exception):
    pass


def calcular_preco_item_fixo(conn, product_id, quantidade):
    """Calcula o preço de um item de preço fixo (catálogo iFood)."""
    p = conn.execute(
        "SELECT id, nome, preco_base, disponivel FROM products WHERE id = ? AND tipo_preco = 'fixo'",
        (product_id,),
    ).fetchone()
    if not p:
        raise ProdutoNaoEncontradoError(f"Produto {product_id} não encontrado.")
    if not p["disponivel"]:
        raise ItemIndisponivelError(f"'{p['nome']}' está indisponível no momento.")

    preco_unitario = p["preco_base"]
    return {
        "nome": p["nome"],
        "preco_unitario": centavos_para_reais(preco_unitario),
        "quantidade": quantidade,
        "subtotal": centavos_para_reais(preco_unitario * quantidade),
        "requer_orcamento": False,
    }


def calcular_preco_item_configuravel(conn, product_id, variant_id, option_ids, quantidade):
    """
    Calcula o preço de um item configurável (bolo personalizado):
    preço da variante escolhida + soma dos adicionais das opções escolhidas.

    Se alguma opção selecionada exigir orçamento, o preço não é somado —
    o item retorna como "sob orçamento" para o front-end trocar o botão
    de finalização por "Solicitar orçamento no WhatsApp".
    """
    produto = conn.execute(
        "SELECT id, nome, disponivel FROM products WHERE id = ? AND tipo_preco = 'configuravel'",
        (product_id,),
    ).fetchone()
    if not produto:
        raise ProdutoNaoEncontradoError(f"Produto {product_id} não encontrado.")
    if not produto["disponivel"]:
        raise ItemIndisponivelError(f"'{produto['nome']}' está indisponível no momento.")

    variante = conn.execute(
        "SELECT id, nome, preco_base, disponivel FROM product_variants WHERE id = ? AND product_id = ?",
        (variant_id, product_id),
    ).fetchone()
    if not variante:
        raise ProdutoNaoEncontradoError(f"Variante {variant_id} não encontrada para o produto {product_id}.")
    if not variante["disponivel"]:
        raise ItemIndisponivelError(f"'{variante['nome']}' está indisponível no momento.")

    total_centavos = variante["preco_base"]
    opcoes_escolhidas = []
    requer_orcamento = False

    for option_id in option_ids:
        opcao = conn.execute(
            """SELECT o.id, o.nome, o.preco_adicional, o.requer_orcamento, o.disponivel, g.nome AS grupo_nome
               FROM options o JOIN option_groups g ON g.id = o.option_group_id
               WHERE o.id = ? AND g.product_id = ?""",
            (option_id, product_id),
        ).fetchone()
        if not opcao:
            raise ProdutoNaoEncontradoError(f"Opção {option_id} inválida para este produto.")
        if not opcao["disponivel"]:
            raise ItemIndisponivelError(f"'{opcao['nome']}' está indisponível no momento.")

        opcoes_escolhidas.append({"grupo": opcao["grupo_nome"], "nome": opcao["nome"]})
        if opcao["requer_orcamento"]:
            requer_orcamento = True
        else:
            total_centavos += opcao["preco_adicional"]

    descricao_completa = f"{produto['nome']} — {variante['nome']}"
    if opcoes_escolhidas:
        descricao_completa += " (" + ", ".join(o["nome"] for o in opcoes_escolhidas) + ")"

    if requer_orcamento:
        return {
            "nome": descricao_completa,
            "preco_unitario": None,
            "quantidade": quantidade,
            "subtotal": None,
            "requer_orcamento": True,
        }

    return {
        "nome": descricao_completa,
        "preco_unitario": centavos_para_reais(total_centavos),
        "quantidade": quantidade,
        "subtotal": centavos_para_reais(total_centavos * quantidade),
        "requer_orcamento": False,
    }
