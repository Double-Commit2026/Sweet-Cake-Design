"""
Funções de acesso a dados. Mantém as queries SQL num único lugar, para que
as rotas fiquem enxutas e o SQL não se espalhe pelo projeto.

Todos os preços são armazenados em centavos (inteiros) no banco e
convertidos para reais (float, 2 casas) somente na borda, ao montar a
resposta da API.
"""

def centavos_para_reais(centavos):
    if centavos is None:
        return None
    return round(centavos / 100, 2)


def list_categories(conn):
    rows = conn.execute(
        "SELECT id, slug, nome, tipo, descricao, ordem FROM categories ORDER BY ordem"
    ).fetchall()
    return [dict(r) for r in rows]


def list_products(conn, categoria_slug=None, apenas_destaque=False):
    query = """
        SELECT p.id, p.nome, p.descricao, p.tipo_preco, p.preco_base, p.preco_promocional,
               p.imagem_url, p.disponivel, p.destaque, p.ordem,
               c.slug AS categoria_slug, c.nome AS categoria_nome, c.tipo AS categoria_tipo
        FROM products p
        JOIN categories c ON c.id = p.categoria_id
        WHERE p.disponivel = TRUE
    """
    params = []
    if categoria_slug:
        query += " AND c.slug = %s"
        params.append(categoria_slug)
    if apenas_destaque:
        query += " AND p.destaque = TRUE"
    query += " ORDER BY c.ordem, p.ordem"

    rows = conn.execute(query, params).fetchall()
    produtos = []
    for r in rows:
        produtos.append({
            "id": r["id"],
            "nome": r["nome"],
            "descricao": r["descricao"],
            "tipo_preco": r["tipo_preco"],
            "preco": centavos_para_reais(r["preco_base"]) if r["tipo_preco"] == "fixo" else None,
            "preco_promocional": centavos_para_reais(r["preco_promocional"]),
            "imagem_url": r["imagem_url"],
            "destaque": bool(r["destaque"]),
            "categoria": {"slug": r["categoria_slug"], "nome": r["categoria_nome"], "tipo": r["categoria_tipo"]},
        })
    return produtos


def get_product_detail(conn, product_id):
    p = conn.execute(
        """SELECT p.*, c.slug AS categoria_slug, c.nome AS categoria_nome, c.tipo AS categoria_tipo
           FROM products p JOIN categories c ON c.id = p.categoria_id
           WHERE p.id = %s AND p.disponivel = TRUE""",
        (product_id,),
    ).fetchone()
    if not p:
        return None

    produto = {
        "id": p["id"],
        "nome": p["nome"],
        "descricao": p["descricao"],
        "tipo_preco": p["tipo_preco"],
        "preco": centavos_para_reais(p["preco_base"]) if p["tipo_preco"] == "fixo" else None,
        "preco_promocional": centavos_para_reais(p["preco_promocional"]),
        "imagem_url": p["imagem_url"],
        "categoria": {"slug": p["categoria_slug"], "nome": p["categoria_nome"], "tipo": p["categoria_tipo"]},
    }

    if p["tipo_preco"] == "configuravel":
        variantes = conn.execute(
            """SELECT id, nome, preco_base, serve_pessoas FROM product_variants
               WHERE product_id = %s AND disponivel = TRUE ORDER BY ordem""",
            (product_id,),
        ).fetchall()
        produto["variantes"] = [
            {"id": v["id"], "nome": v["nome"], "preco_base": centavos_para_reais(v["preco_base"]),
             "serve_pessoas": v["serve_pessoas"]}
            for v in variantes
        ]

        grupos = conn.execute(
            """SELECT id, nome, obrigatorio, tipo_selecoes, min_selecoes, max_selecoes FROM option_groups
               WHERE product_id = %s ORDER BY ordem""",
            (product_id,),
        ).fetchall()
        produto["grupos_opcoes"] = []
        for g in grupos:
            opcoes = conn.execute(
                """SELECT id, nome, preco_adicional, requer_orcamento FROM options
                   WHERE option_group_id = %s AND disponivel = TRUE ORDER BY ordem""",
                (g["id"],),
            ).fetchall()
            produto["grupos_opcoes"].append({
                "id": g["id"],
                "nome": g["nome"],
                "obrigatorio": bool(g["obrigatorio"]),
                "tipo_selecoes":g["tipo_selecoes"],
                "min_selecoes":g["min_selecoes"],
                "max_selecoes":g["max_selecoes"],
                "opcoes": [
                    {"id": o["id"], "nome": o["nome"], "preco_adicional": centavos_para_reais(o["preco_adicional"]),
                     "requer_orcamento": bool(o["requer_orcamento"])}
                    for o in opcoes
                ],
            })

    return produto


def get_store_info(conn):
    rows = conn.execute("SELECT chave, valor FROM store_info").fetchall()
    return {r["chave"]: r["valor"] for r in rows}
