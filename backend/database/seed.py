"""
Popula o banco de dados com o catálogo real da Sweet Cake.

Fontes:
- Página oficial da Sweet Cake no iFood (Belém, Marambaia) — produtos de
  delivery com preço fixo.
- Cardápio 2026 (PDF fornecido pelo proprietário) — bolos personalizados
  por encomenda, com variantes de tamanho/camadas e opções de massa,
  recheio e decoração.

Nenhum produto, preço ou descrição aqui foi inventado. Rode com:
    python database/seed.py
Rodar de novo é seguro: o script limpa e recria os dados antes de inserir.
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from database.db import get_db, init_db  # noqa: E402


def reais(valor):
    """Converte um valor em reais (float) para centavos (int) — evita erros de ponto flutuante."""
    return round(valor * 100)


def seed():
    init_db()
    with get_db() as conn:
        cur = conn.cursor()

        # Limpa dados antigos (idempotente) respeitando FKs.
        for tabela in ["options", "option_groups", "product_variants", "products", "categories", "store_info"]:
            cur.execute(f"DELETE FROM {tabela}")

        # ------------------------------------------------------------------
        # Informações da loja (endereço, WhatsApp, horário, pagamento)
        # ------------------------------------------------------------------
        store_info = {
            "nome": "Sweet Cake",
            "endereco": "R. J, 62 - Marambaia, Belém - PA, 66620-810, Brasil",
            "whatsapp": "5591985396256",
            "horario": "Segunda a sábado, das 9h às 20h",
            "pagamento": "Cartão e Pix",
            "instagram": "https://www.instagram.com/sweetcakeedesign",
        }
        cur.executemany(
            "INSERT INTO store_info (chave, valor) VALUES (?, ?)",
            list(store_info.items()),
        )

        # ------------------------------------------------------------------
        # Categorias
        # ------------------------------------------------------------------
        categorias = [
            # slug, nome, tipo, ordem
            ("brownie", "Brownie", "delivery", 1),
            ("mini-vulcoes", "Mini Vulcões", "delivery", 2),
            ("bolo-vulcao", "Bolo Vulcão", "delivery", 3),
            ("bolos-caseiros", "Bolos Caseiros", "delivery", 4),
            ("pao-de-batata", "Pão de Batata", "delivery", 5),
            ("bento-cake", "Bentô Cake", "encomenda", 6),
            ("mini-cake", "Mini Cake", "encomenda", 7),
            ("bolo-redondo", "Bolo Redondo", "encomenda", 8),
            ("bolo-coracao", "Bolo Coração", "encomenda", 9),
        ]
        cat_ids = {}
        for slug, nome, tipo, ordem in categorias:
            cur.execute(
                "INSERT INTO categories (slug, nome, tipo, ordem) VALUES (?, ?, ?, ?)",
                (slug, nome, tipo, ordem),
            )
            cat_ids[slug] = cur.lastrowid

        # ------------------------------------------------------------------
        # Produtos de preço fixo (catálogo iFood)
        # ------------------------------------------------------------------
        def add_fixed_product(slug_categoria, nome, descricao, preco, preco_promo=None, destaque=False, ordem=0, imagem_url=None):
            cur.execute(
                """INSERT INTO products
                   (categoria_id, nome, descricao, tipo_preco, preco_base, preco_promocional, imagem_url, destaque, ordem)
                   VALUES (?, ?, ?, 'fixo', ?, ?, ?, ?, ?)""",
                (
                    cat_ids[slug_categoria], 
                    nome, 
                    descricao, 
                    reais(preco), 
                    reais(preco_promo) if preco_promo else None, 
                    imagem_url, 
                    1 if destaque else 0, 
                    ordem,
                ),
            )
            return cur.lastrowid

        # Brownie
        add_fixed_product(
            "brownie", 
            "Afogadinho de brownie",
            "O nosso delicioso brownie, cortado em cubos, com uma camada generosa de Ninho com Nutella.",
            28.00, 
            ordem=1,
            )

        add_fixed_product(
            "brownie", 
            "Brownie Supreme com Nutella",
            "7 quadradinhos de brownie artesanal, com muito chocolate, casquinha crocante por fora e "
            "textura macia e úmida por dentro. Acompanha um potinho de Nutella. A partir de R$ 27,00.",
            27.00, 
            ordem=2
            )
        
        add_fixed_product(
            "brownie", 
            "Sanduíche de Brownie Recheado",
            "Duas camadas de brownie macio com recheio generoso de chocolate e Ninho super cremoso.",
            17.50, 
            ordem=3
            )
        
        add_fixed_product(
            "brownie", 
            "Duo Bolo Casadinho Supremo com Brownies",
            "Bolo casadinho super macio, coberto com chocolate ao leite e creme especial, finalizado "
            "com granulado gourmet, acompanhado de 4 quadradinhos de brownie artesanal.",
            26.90, 
            ordem=4
            )
        
        add_fixed_product(
            "brownie", 
            "Fatia de Brownie",
            "Brownie super chocolatudo com a cobertura que você escolher.",
            25.00, 
            ordem=5
            )
        
        add_fixed_product(
            "brownie", 
            "Marmita de Brownie (180g)",
            "Brownie cremoso feito com chocolate 50% e cobertura com granulado.",
            22.00, 
            ordem=6
            )

        # Mini Vulcões
        add_fixed_product(
            "mini-vulcoes", 
            "Mini vulcão chocobrownie",
            "Mini bolo chocolate brownie: massa úmida e intensa de chocolate, com pedaços de brownie.",
            25.90, 
            ordem=1
            )

        # Bolo Vulcão (destaque no iFood)
        add_fixed_product(
            "bolo-vulcao",
            "Bolo Vulcão 20cm",
            "Delicioso bolo vulcão com uma irresistível cobertura, macio e com bastante recheio.",
            98.00, 
            preco_promo=150.00, 
            destaque=True, 
            ordem=1,
            imagem_url="assets/images/bolo-vulcao.jpeg"
            )

        # Bolos Caseiros
        add_fixed_product(
            "bolos-caseiros", 
            "Bolo de maracujá 20cm",
            "Massa fofa, calda artesanal de fruta fresca. Sem conservantes.", 
            34.00, 
            ordem=1,
            imagem_url="assets/images/bolo-caseiro.jpeg"
            )
        
        add_fixed_product(
            "bolos-caseiros", 
            "Bolo formigueiro 20cm",
            "Bolo caseiro, massa fofinha, pronta para aquele café.", 
            29.00, 
            ordem=2
            )
        
        add_fixed_product(
            "bolos-caseiros", 
            "Bolo mesclado 20cm",
            "Bolo caseiro, massa fofinha para acompanhar aquele café.", 
            29.00, 
            ordem=3
            )
        
        add_fixed_product(
            "bolos-caseiros", 
            "Fatias de Bolo com Cobertura",
            "3 fatias de bolo fofinho e macio, com uma porção generosa de cobertura cremosa de "
            "chocolate ou Ninho, servida à parte. Serve 1 pessoa.", 
            15.00, 
            ordem=4
            )
        
        add_fixed_product(
            "bolos-caseiros", 
            "Bolo amanteigado (20cm)",
            "Massa fofinha e amanteigada, com gostinho caseiro. Serve 4 pessoas.", 
            32.00,
            ordem=5
            )
        
        add_fixed_product(
            "bolos-caseiros", 
            "Romeu e Julieta (20cm)",
            "Bolo de massa de queijo com goiabada. Serve 4 pessoas.", 
            32.00, 
            ordem=6
            )
        
        add_fixed_product(
            "bolos-caseiros", 
            "Bolo Com Cobertura",
            "Bolo caseiro com 150g de cobertura.", 
            58.50, 
            preco_promo=78.00, 
            destaque=True, 
            ordem=7
            )
        

        # Pão de batata
        add_fixed_product("pao-de-batata", "Pão (20cm)",
                           "Receita caseira de pão de batata com creme de queijo. Serve 4 pessoas.",
                           65.00, preco_promo=85.00, destaque=True, ordem=1)

        # ------------------------------------------------------------------
        # Produtos configuráveis (cardápio de encomendas 2026)
        # ------------------------------------------------------------------
        def add_configurable_product(slug_categoria, nome, descricao, ordem=1):
            cur.execute(
                """INSERT INTO products
                   (categoria_id, nome, descricao, tipo_preco, destaque, ordem)
                   VALUES (?, ?, ?, 'configuravel', 0, ?)""",
                (cat_ids[slug_categoria], nome, descricao, ordem),
            )
            return cur.lastrowid

        def add_variant(product_id, nome, preco, serve=None, ordem=0):
            cur.execute(
                """INSERT INTO product_variants (product_id, nome, preco_base, serve_pessoas, ordem)
                   VALUES (?, ?, ?, ?, ?)""",
                (product_id, nome, reais(preco), serve, ordem),
            )

        def add_option_group(product_id, nome, obrigatorio=True, ordem=0):
            cur.execute(
                "INSERT INTO option_groups (product_id, nome, obrigatorio, ordem) VALUES (?, ?, ?, ?)",
                (product_id, nome, 1 if obrigatorio else 0, ordem),
            )
            return cur.lastrowid

        def add_option(group_id, nome, preco_adicional=0, requer_orcamento=False, ordem=0):
            cur.execute(
                """INSERT INTO options (option_group_id, nome, preco_adicional, requer_orcamento, ordem)
                   VALUES (?, ?, ?, ?, ?)""",
                (group_id, nome, reais(preco_adicional), 1 if requer_orcamento else 0, ordem),
            )

        MASSA = [("Amanteigada", 0), ("Cacau", 0)]

        RECHEIO_BENTO_MINI = [
            ("Brigadeiro", 0), ("Ninho", 0), ("Doce de leite", 0), ("Beijinho", 0),
            ("Ninho com Nutella", 10), ("Ninho com geleia de morango", 10),
        ]

        # Decoração compartilhada entre Bentô cake e Mini cake (mesma página do cardápio)
        DECORACAO_BENTO_MINI = [
            ("Simples", 0), ("Bordinha", 0),
            ("Topo (a partir de)", 15),
            ("Floral", 5), ("Polaroid", 10), ("Ilustração", 10),
            ("Vintage", 20), ("Flores naturais", 30), ("Papel de arroz", 30),
        ]

        RECHEIO_REDONDO_CORACAO = [
            ("Brigadeiro", 0), ("Ninho", 0), ("Beijinho", 0), ("Doce de leite", 0),
            ("Ninho com Nutella", 15), ("Creme de abacaxi", 15),
            ("Ninho com geleia de morango", 20), ("Ameixa", 20),
            ("Cupuaçu", 15), ("Caramelo", 20),
            ("Mousse de chocolate ou Ninho", 15), ("Trufado", 15),
        ]

        # Decoração compartilhada entre Bolo Redondo e Bolo Coração
        DECORACAO_REDONDO_CORACAO = [
            ("Topo simples", 0), ("Bordinha", 0), ("Simples", 0),
            ("Topo detalhado (a partir de)", 30),
            ("Vintage cake (a partir de)", 30),
            ("Ilustração (a partir de)", 10),
            ("Floral (a partir de)", 10),
            ("Flores naturais (a partir de)", 30),
            ("Papel Arroz", 30),
        ]

        def add_common_groups(product_id, recheio_list, decoracao_list, incluir_orcamento=True):
            g_massa = add_option_group(product_id, "Massa", ordem=1)
            for i, (nome, preco) in enumerate(MASSA):
                add_option(g_massa, nome, preco, ordem=i)

            g_recheio = add_option_group(product_id, "Recheio", ordem=2)
            for i, (nome, preco) in enumerate(recheio_list):
                add_option(g_recheio, nome, preco, ordem=i)

            g_decor = add_option_group(product_id, "Decoração", ordem=3)
            for i, (nome, preco) in enumerate(decoracao_list):
                add_option(g_decor, nome, preco, ordem=i)
            if incluir_orcamento:
                add_option(g_decor, "Decoração personalizada / mais detalhada (sob orçamento)",
                           0, requer_orcamento=True, ordem=len(decoracao_list))

        # --- Bentô cake ---
        p = add_configurable_product(
            "bento-cake", "Bentô Cake",
            "Bolo pequeno servido na caixa (10cm), a partir de R$ 60,00. Os valores alteram de acordo com a "
            "decoração — para decorações mais detalhadas, solicite orçamento.")
        add_variant(p, "Bolo na caixa (10cm)", 60.00, ordem=1)
        add_common_groups(p, RECHEIO_BENTO_MINI, DECORACAO_BENTO_MINI)

        # --- Mini cake ---
        p = add_configurable_product(
            "mini-cake", "Mini Cake",
            "Bolo pequeno com decoração mais sofisticada, com bordinha e lacinhos.")
        add_variant(p, "Redondo 10cm", 60.00, ordem=1)
        add_variant(p, "Redondo 12cm", 70.00, ordem=2)
        add_variant(p, "Coração 10cm", 60.00, ordem=3)
        add_variant(p, "Coração 13cm", 100.00, ordem=4)
        add_common_groups(p, RECHEIO_BENTO_MINI, DECORACAO_BENTO_MINI)

        # --- Bolo Redondo ---
        p = add_configurable_product(
            "bolo-redondo", "Bolo Redondo",
            "Bolo redondo clássico, em diversos tamanhos e números de camadas.")
        add_variant(p, "13cm · 2 camadas de bolo e 1 de recheio", 100.00, serve=5, ordem=1)
        add_variant(p, "15cm · 2 camadas de bolo e 1 de recheio", 150.00, serve=10, ordem=2)
        add_variant(p, "20cm · 2 camadas de bolo e 1 de recheio", 180.00, serve=20, ordem=3)
        add_variant(p, "13cm · 3 camadas de bolo e 2 de recheio", 165.00, serve=8, ordem=4)
        add_variant(p, "15cm · 3 camadas de bolo e 2 de recheio", 210.00, serve=15, ordem=5)
        add_variant(p, "20cm · 3 camadas de bolo e 2 de recheio", 280.00, serve=25, ordem=6)
        add_variant(p, "25cm · 3 camadas de bolo e 2 de recheio", 350.00, serve=35, ordem=7)
        add_variant(p, "30cm · 3 camadas de bolo e 2 de recheio", 460.00, serve=45, ordem=8)
        add_variant(p, "20cm · 4 camadas de bolo e 3 de recheio", 310.00, serve=30, ordem=9)
        add_variant(p, "25cm · 4 camadas de bolo e 3 de recheio", 400.00, serve=40, ordem=10)
        add_common_groups(p, RECHEIO_REDONDO_CORACAO, DECORACAO_REDONDO_CORACAO)

        # --- Bolo Coração ---
        p = add_configurable_product(
            "bolo-coracao", "Bolo Coração",
            "Bolo em formato de coração, em diversos tamanhos e números de camadas.")
        add_variant(p, "13cm · 3 camadas de bolo e 2 de recheio", 165.00, serve=6, ordem=1)
        add_variant(p, "20cm · 2 camadas de bolo e 1 de recheio", 200.00, serve=18, ordem=2)
        add_variant(p, "20cm · 3 camadas de bolo e 2 de recheio", 300.00, serve=25, ordem=3)
        add_common_groups(p, RECHEIO_REDONDO_CORACAO, DECORACAO_REDONDO_CORACAO)

        print("Banco populado com sucesso com o catálogo real da Sweet Cake.")


if __name__ == "__main__":
    seed()
