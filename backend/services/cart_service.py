"""
Serviço de validação do carrinho.

Recebe a lista de itens enviada pelo front-end e recalcula cada item
do zero utilizando o pricing_service.

O servidor NUNCA confia nos preços enviados pelo navegador.

Além da validação de preço, este serviço também valida:
- estrutura dos itens;
- quantidade;
- IDs dos produtos;
- variantes;
- opções;
- grupos obrigatórios;
- opções duplicadas dentro do mesmo grupo.
"""

from services.pricing_service import (
    calcular_preco_item_fixo,
    calcular_preco_item_configuravel,
    ItemIndisponivelError,
    ProdutoNaoEncontradoError,
    SelecaoInvalidaError,
)


def validar_carrinho(conn, itens):
    """
    Valida e recalcula todos os itens do carrinho.

    Formato esperado:

    {
        "itens": [
            {
                "product_id": 1,
                "quantidade": 2,
                "variant_id": null,
                "option_ids": []
            }
        ]
    }

    Retorna:

    {
        "itens": [...],
        "total": 0.0,
        "tem_item_sob_orcamento": false,
        "erros": [...]
    }
    """

    itens_calculados = []
    erros = []
    total_centavos = 0
    tem_item_sob_orcamento = False

    if len(itens) > 50:
        return {
            "itens": [],
            "total": 0.0,
            "tem_item_sob_orcamento": False,
            "erros": ["O carrinho não pode conter mais de 50 itens."],
        }

    # Validação se itens é lista
    if not isinstance(itens, list):
        return {
            "itens": [],
            "total": 0.0,
            "tem_item_sob_orcamento": False,
            "erros": ["O campo 'itens' deve ser uma lista."],
        }

    # ---------------------------------------------------------
    # 1. VALIDAÇÃO DA ESTRUTURA PRINCIPAL
    # ---------------------------------------------------------

    if not isinstance(itens, list):
        return {
            "itens": [],
            "total": 0.0,
            "tem_item_sob_orcamento": False,
            "erros": ["O carrinho deve conter uma lista de itens."],
        }

    # ---------------------------------------------------------
    # 2. PROCESSAMENTO DOS ITENS
    # ---------------------------------------------------------

    for indice, item in enumerate(itens, start=1):

        # -----------------------------------------------------
        # 2.1 O item precisa ser um objeto/dicionário
        # -----------------------------------------------------

        if not isinstance(item, dict):
            erros.append(
                f"Item {indice}: formato inválido."
            )
            continue

        product_id = item.get("product_id")
        quantidade = item.get("quantidade", 1)
        variant_id = item.get("variant_id")
        option_ids = item.get("option_ids") or []

        # -----------------------------------------------------
        # 2.2 VALIDAÇÃO DO PRODUCT_ID
        # -----------------------------------------------------

        if (
            isinstance(product_id, bool)
            or not isinstance(product_id, int)
            or product_id < 1
        ):
            erros.append(
                f"Item {indice}: product_id inválido."
            )
            continue

        # -----------------------------------------------------
        # 2.3 VALIDAÇÃO DA QUANTIDADE
        # -----------------------------------------------------

        if (
            isinstance(quantidade, bool)
            or not isinstance(quantidade, int)
            or quantidade < 1
            or quantidade > 30
        ):
            erros.append(
                f"Item {indice}: quantidade deve ser um número inteiro entre 1 e 30."
            )
            continue

        # -----------------------------------------------------
        # 2.4 VALIDAÇÃO DO VARIANT_ID
        # -----------------------------------------------------

        if variant_id is not None:

            if (
                isinstance(variant_id, bool)
                or not isinstance(variant_id, int)
                or variant_id < 1
            ):
                erros.append(
                    f"Item {indice}: variant_id inválido."
                )
                continue

        # -----------------------------------------------------
        # 2.5 VALIDAÇÃO DO OPTION_IDS
        # -----------------------------------------------------

        if not isinstance(option_ids, list):
            erros.append(f"Item {indice}: option_ids deve ser uma lista.")
            continue

        if any(
            not isinstance(option_id, int)
            or isinstance(option_id, bool)
            or option_id < 1
            for option_id in option_ids
        ):
            erros.append(
                f"Item {indice}: option_ids deve conter apenas números inteiros positivos."
            )
            continue

        if len(option_ids) != len(set(option_ids)):
            erros.append(
                f"Item {indice}: não é permitido selecionar a mesma opção mais de uma vez."
            )
            continue

        # -----------------------------------------------------
        # 2.6 IMPEDIR OPÇÕES DUPLICADAS
        # -----------------------------------------------------

        if len(option_ids) != len(set(option_ids)):
            erros.append(
                f"Item {indice}: existem opções duplicadas."
            )
            continue

        # -----------------------------------------------------
        # 2.7 PRODUTO FIXO NÃO PODE RECEBER OPÇÕES/VARIANTE
        # -----------------------------------------------------

        try:
            produto_info = conn.execute(
                """
                SELECT id, nome, tipo_preco, disponivel
                FROM products
                WHERE id = %s
                """,
                (product_id,),
            ).fetchone()

        except Exception:
            erros.append(
                f"Item {indice}: não foi possível validar o produto."
            )
            continue

        if not produto_info:
            erros.append(
                f"Item {indice}: produto {product_id} não encontrado."
            )
            continue

        if not produto_info["disponivel"]:
            erros.append(
                f"Item {indice}: '{produto_info['nome']}' está indisponível no momento."
            )
            continue

        # -----------------------------------------------------
        # 2.8 PRODUTO FIXO
        # -----------------------------------------------------

        if produto_info["tipo_preco"] == "fixo":

            if variant_id is not None:
                erros.append(
                    f"Item {indice}: o produto '{produto_info['nome']}' não possui variantes."
                )
                continue

            if option_ids:
                erros.append(
                    f"Item {indice}: o produto '{produto_info['nome']}' não aceita opções."
                )
                continue

        # -----------------------------------------------------
        # 2.9 PRODUTO CONFIGURÁVEL
        # -----------------------------------------------------

        elif produto_info["tipo_preco"] == "configuravel":

            if variant_id is None:
                erros.append(
                    f"Item {indice}: selecione uma variante para o produto '{produto_info['nome']}'."
                )
                continue

            # -------------------------------------------------
            # Buscar grupos de opções do produto
            # -------------------------------------------------

            grupos = conn.execute(
                """
                SELECT id, nome, obrigatorio
                FROM option_groups
                WHERE product_id = %s
                ORDER BY ordem
                """,
                (product_id,),
            ).fetchall()

            grupos_por_id = {
                grupo["id"]: grupo
                for grupo in grupos
            }

            # -------------------------------------------------
            # Buscar as opções enviadas
            # -------------------------------------------------

            opcoes = []

            if option_ids:

                opcoes = conn.execute(
                    """
                    SELECT
                        o.id,
                        o.nome,
                        o.option_group_id,
                        g.nome AS grupo_nome,
                        g.obrigatorio
                    FROM options o
                    JOIN option_groups g
                        ON g.id = o.option_group_id
                    WHERE o.id = ANY(%s)
                      AND g.product_id = %s
                      AND o.disponivel = TRUE
                    """,
                    (option_ids, product_id),
                ).fetchall()

            # -------------------------------------------------
            # Verificar se todas as opções enviadas existem
            # -------------------------------------------------

            ids_encontrados = {opcao["id"] for opcao in opcoes}

            if not all(option_id in ids_encontrados for option_id in option_ids):
                erros.append(
                    f"Item {indice}: uma ou mais opções são inválidas para o produto '{produto_info['nome']}'."
                )
                continue

            # -------------------------------------------------
            # Verificar se existe mais de uma opção no mesmo
            # grupo.
            # -------------------------------------------------

            grupos_selecionados = {}

            grupo_invalido = False

            for opcao in opcoes:

                grupo_id = opcao["option_group_id"]

                if grupo_id in grupos_selecionados:
                    erros.append(
                        f"Item {indice}: selecione apenas uma opção para o grupo "
                        f"'{opcao['grupo_nome']}'."
                    )
                    grupo_invalido = True
                    break

                grupos_selecionados[grupo_id] = opcao

            if grupo_invalido:
                continue

            # -------------------------------------------------
            # Verificar grupos obrigatórios
            # -------------------------------------------------

            grupo_obrigatorio_faltando = False

            for grupo in grupos:

                if (
                    grupo["obrigatorio"]
                    and grupo["id"] not in grupos_selecionados
                ):
                    erros.append(
                        f"Item {indice}: selecione uma opção para o grupo "
                        f"'{grupo['nome']}'."
                    )
                    grupo_obrigatorio_faltando = True

            if grupo_obrigatorio_faltando:
                continue

        # -----------------------------------------------------
        # 2.10 TIPO DE PREÇO DESCONHECIDO
        # -----------------------------------------------------

        else:
            erros.append(
                f"Item {indice}: tipo de preço inválido para o produto "
                f"'{produto_info['nome']}'."
            )
            continue

        # -----------------------------------------------------
        # 3. RECALCULAR O PREÇO NO BACKEND
        # -----------------------------------------------------

        try:

            if variant_id is not None:

                resultado = calcular_preco_item_configuravel(
                    conn,
                    product_id,
                    variant_id,
                    option_ids,
                    quantidade,
                )

            else:

                resultado = calcular_preco_item_fixo(
                    conn,
                    product_id,
                    quantidade,
                )

        except (
            ItemIndisponivelError,
            ProdutoNaoEncontradoError,
            SelecaoInvalidaError,
        ) as e:

            erros.append(
                f"Item {indice}: {str(e)}"
            )
            continue

        # -----------------------------------------------------
        # 4. ADICIONAR RESULTADO
        # -----------------------------------------------------

        itens_calculados.append(resultado)

        if resultado["requer_orcamento"]:

            tem_item_sob_orcamento = True

        else:

            # O pricing_service já retorna o subtotal calculado
            # pelo backend.
            #
            # Mantemos a conversão apenas na borda porque a
            # resposta da API utiliza reais.
            subtotal_centavos = round(
                resultado["subtotal"] * 100
            )

            total_centavos += subtotal_centavos

    # ---------------------------------------------------------
    # 5. RESPOSTA FINAL
    # ---------------------------------------------------------

    return {
        "itens": itens_calculados,
        "total": round(total_centavos / 100, 2),
        "tem_item_sob_orcamento": tem_item_sob_orcamento,
        "erros": erros,
    }
