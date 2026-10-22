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
Rodar de novo é seguro: o script limpa e recria os dados antes de inserir
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from database.db import get_db

def reais(valor):
    """Converte um valor em reais (float) para centavos (int) — evita erros de ponto flutuante."""
    return round(valor * 100)

# ----------------------------------------------------------------------
# BANNERS DE DESTAQUE (produtos sazonais)
#
# Para adicionar, trocar ou remover um banner: edite esta lista e rode
#     python database/seed.py banners
# A ordem da lista é a ordem de exibição. Lista vazia (BANNERS = []) faz
# o banner sumir do site.
# ----------------------------------------------------------------------
BANNERS = [
    {
        "chamada": "Novidade do momento",                       # opcional: linha manuscrita acima do título
        "titulo": "Morango Cravejado",
        "descricao": "Morango coberto com brigadeiro de ninho e chocolate branco, com pequenos pedaços de caramelo!",
        "imagem_url": "assets/images/banner/morango_cravejado.png",   # define imagem destaque 723 x 519
        "botao_texto": "Fazer meu pedido",               # opcional (padrão: "Fazer meu pedido")
        "mensagem_whatsapp": "Olá! Gostaria de pedir um morango cravejado",  # opcional
        "data_inicio": "2026-10-22",                                                # opcional: aparece a partir deste dia -> "data_inicio": "2026-10-22"                     
        "data_fim": "2026-12-31",                                                # opcional: some depois deste dia -> "data_fim": "2026-12-31"
        "ativo": True,                                  # opcional: False deixa o banner guardado, mas escondido
    },
]


def seed_banners(cur):
    """Recria a tabela de banners a partir da lista BANNERS."""
    cur.execute("TRUNCATE TABLE banners RESTART IDENTITY")
    for ordem, b in enumerate(BANNERS, start=1):
        cur.execute(
            """
            INSERT INTO banners
                (chamada, titulo, descricao, imagem_url, botao_texto,
                 mensagem_whatsapp, ativo, data_inicio, data_fim, ordem)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s::date, %s::date, %s)
            """,
            (
                b.get("chamada"),
                b["titulo"],
                b.get("descricao"),
                b["imagem_url"],
                b.get("botao_texto", "Fazer meu pedido"),
                b.get("mensagem_whatsapp"),
                b.get("ativo", True),
                b.get("data_inicio"),
                b.get("data_fim"),
                ordem,
            ),
        )

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
            ("vulcoes", "Vulcões", "delivery", 2),
            ("bolos-caseiros", "Bolos Caseiros", "delivery", 3),
            ("pao-de-batata", "Pão de Batata", "delivery", 4),
            ("doces", "Doces", "delivery", 5),
            ("bolos", "Bolos", "encomenda", 6),
            ("cento_docinhos", "Cento de docinhos", "encomenda", 7),
            ("linha-especial", "Linha Especial", "encomenda", 8),
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
        # Produtos de preço fixo
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
            imagem_url="assets/images/sand-brownie.webp"
            )
        
        add_fixed_product(
            "brownie", 
            "Duo Bolo Casadinho Supremo com Brownies",
            "Bolo casadinho super macio, coberto com chocolate ao leite e creme especial, finalizado "
            "com granulado gourmet, acompanhado de 4 quadradinhos de brownie artesanal.",
            26.90, 
            ordem=4,
            imagem_url="assets/images/duo-brownie.webp"
            )
        
        add_fixed_product(
            "brownie", 
            "Fatia de Brownie",
            "Brownie super chocolatudo com a cobertura que você escolher.",
            22.00, 
            ordem=5,
            imagem_url="assets/images/fatia-brownie.webp"
            )
        
        add_fixed_product(
            "brownie", 
            "Marmita de Brownie (180g)",
            "Brownie cremoso feito com chocolate 50% e cobertura com granulado.",
            18.00, 
            ordem=6,
            imagem_url="assets/images/marmita-brownie.webp"
            )

        # Mini Vulcões
        add_fixed_product(
            "vulcoes", 
            "Mini vulcão chocobrownie",
            "Mini bolo chocolate brownie: massa úmida e intensa de chocolate, com pedaços de brownie.",
            20.00, 
            ordem=1,
            imagem_url="assets/images/chocobrownie.webp"
            )

        # Bolo Vulcão
        add_fixed_product(
            "vulcoes",
            "Bolo Vulcão 20cm",
            "Delicioso bolo vulcão com uma irresistível cobertura, macio e com bastante recheio.",
            80.00, 
            ordem=2,
            imagem_url="assets/images/bolo-vulcao-choca.webp"
            )

        # Bolos Caseiros
        add_fixed_product(
            "bolos-caseiros", 
            "Bolo de maracujá 20cm",
            "Massa fofa, calda artesanal de fruta fresca. Sem conservantes.", 
            27.00, 
            ordem=1,
            imagem_url="assets/images/bolo-maracuja.webp"
            )
        
        add_fixed_product(
            "bolos-caseiros", 
            "Bolo formigueiro 20cm",
            "Bolo caseiro, massa fofinha, pronta para aquele café.", 
            25.00, 
            ordem=2,
            imagem_url="assets/images/caseiro-formiga.webp"
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
            imagem_url="assets/images/romeu-julieta.webp"
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
            imagem_url="assets/images/pao-de-batata.webp"
            )

        #Cupcakes
        add_fixed_product(
            "doces",
            "Cupcakes",
            "Preço por unidade, dependendo da decoração, o valor tem alteração. Sob orçamento!",
            12.00,
            ordem=1,
            imagem_url="assets/images/cupcake-p.webp"
        )

        #Pirulitos
        add_fixed_product(
            "doces",
            "Pirulitos",
            "Preço por unidade, dependendo da decoração, o valor tem alteração. Sob orçamento!",
            10.00,
            ordem=2,
            imagem_url="assets/images/pirulito-p.webp"
        )

        # ------------------------------------------------------------------
        # Produtos configuráveis (cardápio de encomendas 2026)
        # ------------------------------------------------------------------
        def add_configurable_product(slug_categoria, nome, descricao, ordem=1, imagem_url=None):
            cur.execute(
                """
                INSERT INTO products
                (categoria_id, nome, descricao, tipo_preco, imagem_url, destaque, ordem)
                VALUES (%s, %s, %s, 'configuravel', %s, FALSE, %s)
                RETURNING id
                """,
                (
                    cat_ids[slug_categoria], 
                    nome, 
                    descricao, 
                    imagem_url,
                    ordem,
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
            imagem_url="assets/images/doce-tradicional.jpeg"
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
            imagem_url="assets/images/doce-gourmet.jpeg"
        )
        add_variant(doce_gourmet, "Cento (100 unidades)", 230.00, ordem=1)
        g = add_option_group(doce_gourmet, "Sabores", obrigatorio=True, tipo_selecoes="multipla", min_selecoes=3, max_selecoes=3, ordem=1)
        for i, nome in enumerate(["Churros", "Ninho c/ Nutella", "Casadinho", "Três Amores", "Queijo c/ Goiaba", "Cajuzinho", "Maracujá", "Oreo"]):
            add_option(g, nome, 0, ordem=i)

        # Linha Especial — R$250 o cento, cliente escolhe 3 sabores
        doce_especial = add_configurable_product(
            "linha-especial", "Cento Linha Especial",
            "Cento de docinhos linha especial. Escolha 3 sabores — o valor não muda.",
            ordem=1,
            imagem_url="assets/images/linha-especial.jpeg"
        )
        add_variant(doce_especial, "Cento (100 unidades)", 250.00, ordem=1)
        g = add_option_group(doce_especial, "Sabores", obrigatorio=True, tipo_selecoes="multipla", min_selecoes=3, max_selecoes=3, ordem=1)
        for i, nome in enumerate(["Brigadeiro Colorido", "Coco queimado", "Surpresa de uva", "Café", "Olho de sogra", "Ferrero Rocher"]):
            add_option(g, nome, 0, ordem=i)

        # Linha Especial 2.0 — 1 produto, escolha o sabor (preço vem da opção)
        doce_especial2 = add_configurable_product(
            "linha-especial", "Linha Especial 2.0",
            "Doces finos avulsos. Escolha o sabor.",
            ordem=2,
            imagem_url="assets/images/linha-especial-2.0.webp"
        )
        add_variant(doce_especial2, "Unidade", 0, ordem=1)
        g = add_option_group(doce_especial2, "Sabor", obrigatorio=True, ordem=1)
        add_option(g, "Doce formato de flor ou coração", 5.00, ordem=1)
        add_option(g, "Bombom cereja", 5.00, ordem=2)
        add_option(g, "Brigadeiro de pistache", 5.00, ordem=3)
        add_option(g, "Camafeu de morango", 19.90, ordem=4)
        add_option(g, "Bombom prestígio", 3.00, ordem=5)

        # doces Finos
        p_docefinos = add_configurable_product(
        "cento_docinhos", "Doce Finos",
        "Cento de docinhos trufados. Escolha 3 sabores — o valor não muda.",
        ordem=4,
        imagem_url="assets/images/doces-finos.jpeg"
        )
        add_variant(p_docefinos, "Cento (100 unidades)", 300.00, ordem=1)
        g = add_option_group(p_docefinos, "Sabores", obrigatorio=True, tipo_selecoes="multipla", min_selecoes=3, max_selecoes=3, ordem=1)
        for i, nome in enumerate(["Cupuaçu", "Morango", "Cereja", "Nutella", "Ganache de chocolate", "Caramelo", "Castanha do Pará"]):
            add_option(g, nome, 0, ordem=i)

        # Doces festivos
        doces_festivos = add_configurable_product(
            "linha-especial","Doces Fetivos",
            "Doces Festivos para adoçar ainda mais sua comemoração. — Preço unitário",
            ordem=4,
            imagem_url="assets/images/doce-festivo-mini-bolo.webp"
        )
        add_variant(doces_festivos, "Mini Bolo", 13.90, ordem=1)
        add_variant(doces_festivos, "Bem Casado", 5.00, ordem=2)
        g = add_option_group(doces_festivos, "Personalização", obrigatorio=False, ordem=1)
        add_option(g, "Chocolate", 1.00, ordem=1)
        add_option(g, "Pasta americana", 2.00, ordem=2)

        # Cento de biscoitos
        biscoito = add_configurable_product(
            "linha-especial", "Biscoitos",
            "Biscoitos artesanais. Escolha o sabor por 1 cento - o valor não muda.",
            ordem = 3,
            imagem_url="assets/images/biscoitos.webp"
        )
        add_variant (biscoito,"Pacote", 120.00, ordem=1)
        g = add_option_group(biscoito, "Sabor", obrigatorio=True, ordem=1)
        for i, nome in enumerate(["Monteiro Lopes", "Castanha do Pará"]):
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
            "bolos", "Bentô Cake",
            "Bolo pequeno servido na caixa (10cm), a partir de R$ 60,00. Os valores alteram de acordo com a "
            "decoração — para decorações mais detalhadas, solicite orçamento.", ordem=1, imagem_url="assets/images/bento-cake.webp")
        add_variant(p, "Bolo na caixa (10cm)", 60.00, ordem=1)
        add_common_groups(p, RECHEIO_BENTO_MINI, DECORACAO_BENTO_MINI)

        # --- Mini cake ---
        p = add_configurable_product(
            "bolos", "Mini Cake",
            "Bolo pequeno com decoração mais sofisticada, com bordinha e lacinhos.", ordem=2, imagem_url="assets/images/mini-cake.jpeg")
        add_variant(p, "Redondo 10cm", 60.00, ordem=1)
        add_variant(p, "Redondo 12cm", 70.00, ordem=2)
        add_variant(p, "Coração 10cm", 60.00, ordem=3)
        add_variant(p, "Coração 13cm", 100.00, ordem=4)
        add_common_groups(p, RECHEIO_BENTO_MINI, DECORACAO_BENTO_MINI)

        # --- Bolo Redondo ---
        p = add_configurable_product(
            "bolos", "Bolo Redondo",
            "Bolo redondo clássico, em diversos tamanhos e números de camadas.", ordem=3, imagem_url="assets/images/bolo-redondo.webp")
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
            "bolos", "Bolo Coração",
            "Bolo em formato de coração, em diversos tamanhos e números de camadas.", ordem=4, imagem_url="assets/images/bolo-coracao.jpeg")
        add_variant(p, "13cm · 3 camadas de bolo e 2 de recheio", 165.00, serve=6, ordem=1)
        add_variant(p, "20cm · 2 camadas de bolo e 1 de recheio", 200.00, serve=18, ordem=2)
        add_variant(p, "20cm · 3 camadas de bolo e 2 de recheio", 300.00, serve=25, ordem=3)
        add_common_groups(p, RECHEIO_REDONDO_CORACAO, DECORACAO_REDONDO_CORACAO)

        seed_banners(cur)

        print("Banco populado com sucesso com o catálogo real da Sweet Cake.")


def seed_only_banners():
    with get_db() as conn:
        seed_banners(conn.cursor())
    print("Banners atualizados.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "banners":
        seed_only_banners()
    else:
        seed()
