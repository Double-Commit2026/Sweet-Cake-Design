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

from database.db import get_db

def reais(valor):
    """Converte um valor em reais (float) para centavos (int) — evita erros de ponto flutuante."""
    return round(valor * 100)


def seed():
    with get_db() as conn:
        cur = conn.cursor()

        # Limpa dados antigos (idempotente) respeitando FKs. <-- tomar cuidado ao executar esse bloco, executar apenas se for necessário em ambiente de produção.
        for tabela in ["options", "option_groups", "product_variants", "products", "categories", "store_info"]:
            cur.execute(
                """
                TRUNCATE TABLE
                    options,
                    option_groups,
                    product_variants,
                    products,
                    categories,
                    store_info
                RESTART IDENTITY CASCADE
                """
            )

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
            "INSERT INTO store_info (chave, valor) VALUES (%s, %s)",
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
            ("Cupcake", "Cupcakes", "delivery", 6),
            ("Pirulito", "Pirulito", "delivery", 7),
            ("bento-cake", "Bentô Cake", "encomenda", 8),
            ("mini-cake-e", "Mini Cake", "encomenda", 9),
            ("bolo-redondo", "Bolo Redondo", "encomenda", 10),
            ("bolo-coracao", "Bolo Coração", "encomenda", 11),
            ("cento_docinhos", "Cento de docinhos", "encomenda", 12),
        ]
        cat_ids = {}
        for slug, nome, tipo, ordem in categorias:
            cur.execute(
                """
                INSERT INTO categories (slug, nome, tipo, ordem) 
                VALUES (%s, %s, %s, %s) 
                RETURNING id
                """,
                (slug, nome, tipo, ordem),
            )
            cat_ids[slug] = cur.fetchone()["id"]

        # ------------------------------------------------------------------
        # Produtos de preço fixo (catálogo iFood)
        # ------------------------------------------------------------------
        def add_fixed_product(slug_categoria, nome, descricao, preco, preco_promo=None, destaque=False, ordem=0, imagem_url=None):
            cur.execute(
                """INSERT INTO products
                   (categoria_id, nome, descricao, tipo_preco, preco_base, preco_promocional, imagem_url, destaque, ordem)
                   VALUES (%s, %s, %s, 'fixo', %s, %s, %s, %s, %s)
                   RETURNING id
                   """,
                (
                    cat_ids[slug_categoria], 
                    nome, 
                    descricao, 
                    reais(preco), 
                    reais(preco_promo) if preco_promo is not None else None, 
                    imagem_url, 
                    destaque, 
                    ordem,
                ),
            )
            return cur.fetchone()["id"]

        # Brownie
        add_fixed_product(
            "brownie", 
            "Afogadinho de brownie",
            "O nosso delicioso brownie, cortado em cubos, com uma camada generosa de Ninho com Nutella.",
            28.00, 
            ordem=1,
            imagem_url="assets/images/afogado-brownie.jpeg"
            )

        add_fixed_product(
            "brownie", 
            "Brownie Supreme com Nutella",
            "7 quadradinhos de brownie artesanal, com muito chocolate, casquinha crocante por fora e "
            "textura macia e úmida por dentro. Acompanha um potinho de Nutella. A partir de R$ 27,00.",
            24.00, 
            ordem=2,
            imagem_url="assets/images/supreme_nutella.webp"
            )
        
        add_fixed_product(
            "brownie", 
            "Sanduíche de Brownie Recheado",
            "Duas camadas de brownie macio com recheio generoso de chocolate e Ninho super cremoso.",
            17.50, 
            ordem=3,
            imagem_url="assets/images/sand-brownie.jpeg"
            )
        
        add_fixed_product(
            "brownie", 
            "Duo Bolo Casadinho Supremo com Brownies",
            "Bolo casadinho super macio, coberto com chocolate ao leite e creme especial, finalizado "
            "com granulado gourmet, acompanhado de 4 quadradinhos de brownie artesanal.",
            26.90, 
            ordem=4,
            imagem_url="assets/images/duo-brownie.jpeg"
            )
        
        add_fixed_product(
            "brownie", 
            "Fatia de Brownie",
            "Brownie super chocolatudo com a cobertura que você escolher.",
            22.00, 
            ordem=5,
            imagem_url="assets/images/fatia-brownie.jpeg"
            )
        
        add_fixed_product(
            "brownie", 
            "Marmita de Brownie (180g)",
            "Brownie cremoso feito com chocolate 50% e cobertura com granulado.",
            18.00, 
            ordem=6,
            imagem_url="assets/images/marmita_brownie.webp"
            )

        # Mini Vulcões
        add_fixed_product(
            "mini-vulcoes", 
            "Mini vulcão chocobrownie",
            "Mini bolo chocolate brownie: massa úmida e intensa de chocolate, com pedaços de brownie.",
            20.00, 
            ordem=1,
            imagem_url="assets/images/chocobrownie.jpeg"
            )

        # Bolo Vulcão (destaque no iFood)
        add_fixed_product(
            "bolo-vulcao",
            "Bolo Vulcão 20cm",
            "Delicioso bolo vulcão com uma irresistível cobertura, macio e com bastante recheio.",
            80.00, 
            ordem=1,
            imagem_url="assets/images/bolo-vulcao-choca.jpeg"
            )

        # Bolos Caseiros
        add_fixed_product(
            "bolos-caseiros", 
            "Bolo de maracujá 20cm",
            "Massa fofa, calda artesanal de fruta fresca. Sem conservantes.", 
            27.00, 
            ordem=1,
            imagem_url="assets/images/bolo-maracuja.jpeg"
            )
        
        add_fixed_product(
            "bolos-caseiros", 
            "Bolo formigueiro 20cm",
            "Bolo caseiro, massa fofinha, pronta para aquele café.", 
            25.00, 
            ordem=2,
            imagem_url="assets/images/caseiro-formiga.jpeg"
            )
        
        add_fixed_product(
            "bolos-caseiros", 
            "Bolo mesclado 20cm",
            "Bolo caseiro, massa fofinha para acompanhar aquele café.", 
            25.00, 
            ordem=3,            
            imagem_url="assets/images/bolo-mesclado.jpeg"
            )
        
        add_fixed_product(
            "bolos-caseiros", 
            "Fatias de Bolo com Cobertura",
            "3 fatias de bolo fofinho e macio, com uma porção generosa de cobertura cremosa de "
            "chocolate ou Ninho, servida à parte. Serve 1 pessoa.", 
            15.00, 
            ordem=4,
            imagem_url="assets/images/fatias_cobertura.webp"
            )
        
        add_fixed_product(
            "bolos-caseiros", 
            "Bolo amanteigado (20cm)",
            "Massa fofinha e amanteigada, com gostinho caseiro. Serve 4 pessoas.", 
            32.00,
            ordem=5,
            imagem_url="assets/images/bolo-caseiro-manteiga.jpeg"
            )
        
        add_fixed_product(
            "bolos-caseiros", 
            "Romeu e Julieta (20cm)",
            "Bolo de massa de queijo com goiabada. Serve 4 pessoas.", 
            27.00, 
            ordem=6,
            imagem_url="assets/images/romeu-julieta.jpeg"
            )
        
        add_fixed_product(
            "bolos-caseiros", 
            "Bolo Com Cobertura",
            "Bolo caseiro com 150g de cobertura.", 
            50.00,  
            ordem=7,
            imagem_url="assets/images/bolo_cobertura.webp"
            )
        

        # Pão de batata
        add_fixed_product(
            "pao-de-batata", 
            "Pão (20cm)",
            "Receita caseira de pão de batata com creme de queijo. Serve 4 pessoas.",
            65.00, 
            preco_promo=85.00, 
            ordem=1,
            imagem_url="assets/images/pao-de-batata.jpeg"
            )

        #Cupcakes
        add_fixed_product(
            "Cupcake",
            "Cupcakes",
            "Preço por unidade, dependendo da decoração, o valor tem alteração. Sob orçamento!",
            12.00,
            ordem=1,
            imagem_url="assets/images/cupcake_P.png"
        )

        #Pirulitos
        add_fixed_product(
            "Pirulito",
            "Pirulitos",
            "Preço por unidade, dependendo da decoração, o valor tem alteração. Sob orçamento!",
            10.00,
            ordem=1,
            imagem_url="assets/images/pirulito_P.png"
        )

        # ------------------------------------------------------------------
        # Produtos configuráveis (cardápio de encomendas 2026)
        # ------------------------------------------------------------------
        def add_configurable_product(slug_categoria, nome, descricao, ordem=1):
            cur.execute(
                """
                INSERT INTO products
                (categoria_id, nome, descricao, tipo_preco, destaque, ordem)
                VALUES (%s, %s, %s, 'configuravel', FALSE, %s)
                RETURNING id
                """,
                (
                    cat_ids[slug_categoria], 
                    nome, 
                    descricao, 
                    ordem
                ),
            )
            return cur.fetchone()["id"]

        def add_variant(product_id, nome, preco, serve=None, ordem=0):
            cur.execute(
                """
                INSERT INTO product_variants (product_id, nome, preco_base, serve_pessoas, ordem)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (product_id, nome, reais(preco), serve, ordem),
            )

        def add_option_group(product_id, nome, obrigatorio=True, ordem=0, tipo_selecoes="unica", min_selecoes=1, max_selecoes=1):
            cur.execute(
                "INSERT INTO option_groups (product_id, nome, obrigatorio, tipo_selecoes, min_selecoes, max_selecoes, ordem) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
                (
                    product_id, 
                    nome, 
                    obrigatorio,
                    tipo_selecoes,
                    min_selecoes,
                    max_selecoes, 
                    ordem
                ),
            )
            return cur.fetchone()["id"]

        def add_option(group_id, nome, preco_adicional=0, requer_orcamento=False, ordem=0):
            cur.execute(
                """INSERT INTO options (option_group_id, nome, preco_adicional, requer_orcamento, ordem)
                   VALUES (%s, %s, %s, %s, %s)""",
                (
                    group_id, nome, 
                    reais(preco_adicional), 
                    requer_orcamento, 
                    ordem
                ),
            )

        # Doces Tradicionais — R$150 o cento, cliente escolhe 3 sabores
        doce_trad = add_configurable_product(
            "cento_docinhos", "Doces Tradicionais",
            "Cento de docinhos tradicionais. Escolha 3 sabores — o valor não muda.",
            ordem=1,
        )
        add_variant(doce_trad, "Cento (100 unidades)", 150.00, ordem=1)
        g = add_option_group(doce_trad, "Sabores", obrigatorio=True, tipo_selecoes="multipla", min_selecoes=3, max_selecoes=3, ordem=1)
        for i, nome in enumerate(["Brigadeiro", "Beijinho", "Bicho de pé", "Leite Ninho", "Queijo"]):
            add_option(g, nome, 0, ordem=i)

        # Doces Gourmet — R$230 o cento, cliente escolhe 3 sabores
        doce_gourmet = add_configurable_product(
            "cento_docinhos", "Doces Gourmet",
            "Cento de docinhos gourmet. Escolha 3 sabores — o valor não muda.",
            ordem=2,
        )
        add_variant(doce_gourmet, "Cento (100 unidades)", 230.00, ordem=1)
        g = add_option_group(doce_gourmet, "Sabores", obrigatorio=True, tipo_selecoes="multipla", min_selecoes=3, max_selecoes=3, ordem=1)
        for i, nome in enumerate(["Churros", "Ninho c/ Nutella", "Casadinho", "Três Amores", "Queijo c/ Goiaba", "Cajuzinho", "Maracujá", "Oreo"]):
            add_option(g, nome, 0, ordem=i)

        # Linha Especial — R$250 o cento, cliente escolhe 3 sabores
        doce_especial = add_configurable_product(
            "cento_docinhos", "Linha Especial",
            "Cento de docinhos linha especial. Escolha 3 sabores — o valor não muda.",
            ordem=3,
        )
        add_variant(doce_especial, "Cento (100 unidades)", 250.00, ordem=1)
        g = add_option_group(doce_especial, "Sabores", obrigatorio=True, tipo_selecoes="multipla", min_selecoes=3, max_selecoes=3, ordem=1)
        for i, nome in enumerate(["Brigadeiro Colorido", "Coco queimado", "Surpresa de uva", "Café", "Olho de sogra", "Ferrero Rocher"]):
            add_option(g, nome, 0, ordem=i)

        MASSA = [("Amanteigada", 0), ("Cacau", 0)]

        # Decoração compartilhada entre Bentô cake e Mini cake (mesma página do cardápio)
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

        # Decoração compartilhada entre Bolo Redondo e Bolo Coração
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
            "mini-cake-e", "Mini Cake",
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
