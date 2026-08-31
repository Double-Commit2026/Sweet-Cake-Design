# Sweet Cake — Site oficial

Site comercial da **Sweet Cake** (bolos decorados, Belém — Marambaia): landing page + catálogo de produtos + carrinho de compras, com pedidos finalizados via WhatsApp.

Todas as informações de produto, preço, contato e identidade visual usadas neste projeto vêm de fontes reais fornecidas pela proprietária do negócio (Instagram @sweetcakeedesign, página oficial no iFood e o Cardápio 2026 em PDF). Nenhum produto, preço ou dado de contato foi inventado.

---

## Tecnologias

- **Front-end:** HTML5, CSS3 e JavaScript puro (sem frameworks) — arquivos separados por responsabilidade.
- **Backend:** Python (Flask) + SQLite.
- **Integração:** WhatsApp (link `wa.me` com mensagem pré-formatada).

---

## Estrutura de pastas

```
sweet-cake-design/
├── frontend/
│   ├── index.html
│   ├── css/
│   │   ├── style.css          # variáveis de design, layout, componentes
│   │   ├── responsive.css     # ajustes por breakpoint
│   │   └── animations.css     # animações leves (respeita prefers-reduced-motion)
│   ├── js/
│   │   ├── api.js             # única camada que fala com o backend
│   │   ├── catalog.js         # catálogo de preço fixo (iFood)
│   │   ├── product-wizard.js  # configurador de bolos personalizados
│   │   ├── cart.js            # estado do carrinho + localStorage + UI
│   │   ├── whatsapp.js        # revalidação final + geração da mensagem
│   │   └── main.js            # inicialização geral
│   └── assets/
│       └── images/            # fotos reais fornecidas pela Sweet Cake
│
├── backend/
│   ├── app.py                 # ponto de entrada Flask
│   ├── routes/                # endpoints da API
│   ├── models/                # acesso a dados (repository)
│   ├── services/               # regras de precificação e validação do carrinho
│   ├── database/
│   │   ├── db.py              # conexão + schema
│   │   └── seed.py            # popula o banco com o catálogo REAL
│   └── config/
│       └── settings.py        # configurações via variáveis de ambiente
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Como rodar localmente

### 1. Backend

```bash
cd backend
pip install -r ../requirements.txt --break-system-packages   # ou use um virtualenv
cp ../.env.example ../.env      # depois edite o .env com os valores reais
python database/seed.py         # popula o banco com o catálogo (rodar 1x, ou de novo se precisar resetar)
python app.py
```

O servidor sobe em `http://localhost:5000`.

### 2. Front-end

Em outro terminal:

```bash
cd frontend
python -m http.server 8080
```

Abra `http://localhost:8080` no navegador.

> Se a API rodar em outro endereço (produção, outra porta, etc.), atualize a constante `window.SWEET_CAKE_API_BASE_URL` no início do `frontend/index.html`.

---

## Variáveis de ambiente (`.env`)

Veja `.env.example` para a lista completa. As principais:

| Variável | Descrição |
|---|---|
| `WHATSAPP_NUMBER` | Número oficial da Sweet Cake, só dígitos com DDI+DDD (ex: `5591985396256`) |
| `DATABASE_PATH` | Caminho do arquivo SQLite (opcional — usa `backend/database/sweetcake.db` por padrão) |
| `FRONTEND_ORIGIN` | Origem autorizada a consumir a API (CORS) |
| `FLASK_ENV` | `development` ou `production` |

**O `.env` nunca deve ser commitado no Git** (já está no `.gitignore`).

---

## Banco de dados e catálogo

O banco é criado e populado por `backend/database/seed.py`, que contém o catálogo **real**:

- **Catálogo de pronta entrega** (iFood): Brownie, Mini Vulcões, Bolo Vulcão, Bolos Caseiros, Pão de Batata — preço fixo por produto.
- **Catálogo de encomendas** (Cardápio 2026): Bentô Cake, Mini Cake, Bolo Redondo, Bolo Coração — produtos **configuráveis**, com variantes de tamanho/camadas e grupos de opção (massa, recheio, decoração), cada um com seu próprio adicional de preço.

### Como atualizar produtos ou preços

Toda alteração de catálogo é feita editando `backend/database/seed.py` (adicionando, removendo ou alterando as chamadas `add_fixed_product`, `add_configurable_product`, `add_variant`, `add_option_group`, `add_option`) e rodando de novo:

```bash
python database/seed.py
```

O script limpa e recria os dados a cada execução — é seguro rodar quantas vezes precisar. **Nunca edite preços diretamente no HTML ou no JavaScript do front-end**: o front-end sempre busca produtos e preços através da API.

---

## Arquitetura de preços (importante)

Por exigência do projeto, os preços **nunca** ficam fixos no front-end:

```
BANCO DE DADOS → BACKEND → API → JAVASCRIPT → INTERFACE → USUÁRIO
```

- O catálogo (`GET /api/products`) devolve os preços vindos do banco.
- O configurador de bolos personalizados (`POST /api/pricing/calculate`) recalcula o preço a cada escolha do cliente (tamanho, sabor, decoração) — sempre no servidor.
- Antes de gerar a mensagem do WhatsApp, o carrinho inteiro é revalidado em `POST /api/cart/validate`, que recalcula cada item do zero. Isso impede que um preço alterado no DevTools do navegador chegue à mensagem final — o valor que conta é sempre o que o backend confirma nesse momento.

Decorações marcadas como "sob orçamento" não têm preço somado: o item entra no carrinho e na mensagem do WhatsApp como "a combinar".

---

## API

| Rota | Descrição |
|---|---|
| `GET /api/categories` | Lista categorias (delivery e encomenda) |
| `GET /api/products?categoria=<slug>` | Lista produtos de uma categoria |
| `GET /api/products/:id` | Detalhe de um produto (inclui variantes e opções, se configurável) |
| `POST /api/pricing/calculate` | Calcula o preço de uma combinação (usado pelo wizard) |
| `POST /api/cart/validate` | Revalida todo o carrinho antes da finalização |
| `GET /api/store-info` | Endereço, horário, WhatsApp e forma de pagamento |
| `GET /api/health` | Health check |

---

## Carrinho e WhatsApp

- O carrinho persiste em `localStorage` (chave `sweetcake_cart_v1`) — sobrevive a atualizações de página e fechamento da aba, dentro da mesma sessão do navegador.
- Nenhum dado sensível é salvo no `localStorage`, apenas IDs de produto/variante/opção e quantidades.
- Ao clicar em **"Finalizar pedido pelo WhatsApp"**, o front-end chama `/api/cart/validate`, monta a mensagem com os valores oficiais devolvidos pela API e abre `https://wa.me/<numero>?text=...` numa nova aba.

---

## Imagens

As fotos usadas na galeria e nos destaques são fotos reais fornecidas pela proprietária da Sweet Cake (extraídas do material enviado durante o desenvolvimento). Produtos do catálogo de pronta entrega que ainda não têm foto exibem o placeholder "imagem em breve" — para adicionar uma foto, preencha o campo `imagem_url` do produto correspondente em `seed.py` com o caminho do arquivo (ex: `assets/images/brownie-supremo.jpg`) e rode o seed novamente.

O logotipo atual (`frontend/assets/images/logo-sweetcake.jpg`) foi extraído de um print de tela do Instagram e está em baixa resolução. **Recomenda-se fortemente substituir esse arquivo pelo logo original em alta resolução**, assim que a proprietária puder fornecê-lo — isso vai melhorar bastante a nitidez do cabeçalho e da seção "Sobre".

---

## Acessibilidade e performance

- HTML semântico, `alt` descritivo em todas as imagens, navegação por teclado nos botões e modais, foco visível.
- `prefers-reduced-motion` é respeitado — animações são desativadas automaticamente para quem prefere.
- Imagens da galeria estão em JPEG otimizado (e versão `.webp` disponível) com `loading="lazy"`, exceto a imagem do hero (`loading="eager"`).

---

## Próximos passos sugeridos

- Substituir o logo por um arquivo em alta resolução.
- Adicionar fotos reais dos produtos do catálogo de pronta entrega (iFood) conforme forem sendo fotografados.
- Avaliar hospedagem: backend (Flask) pode ir para qualquer serviço com suporte a Python (Render, Railway, etc.); front-end é estático e pode ser hospedado separadamente (Netlify, Vercel, GitHub Pages) — nesse caso, lembre de atualizar `SWEET_CAKE_API_BASE_URL` no `index.html` para a URL pública da API.
- Se o volume de pedidos crescer, considerar implementar `POST /api/orders` para registrar pedidos no banco (hoje o pedido só é formalizado via mensagem de WhatsApp).
