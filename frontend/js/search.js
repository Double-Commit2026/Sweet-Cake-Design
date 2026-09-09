/**
 * search.js
 * Busca unificada no header: cobre os dois catálogos (pronta entrega e sob
 * encomenda) porque o cliente que já sabe o que quer pode estar procurando
 * qualquer um dos dois — ex: "bentô" só existe no catálogo de encomenda.
 *
 * Não faz nenhuma chamada de preço além do que api.getProducts() já
 * devolve. Produtos configuráveis (sob encomenda) não têm preço fixo na
 * listagem — o mesmo já acontece hoje nos cards de "Monte seu bolo" em
 * main.js — então no resultado da busca eles aparecem com a tag "Sob
 * encomenda" em vez de um preço.
 *
 * Clicar num resultado já leva direto à ação (abrir o detalhe do produto
 * ou o configurador), sem precisar rolar a página até o catálogo.
 */
const Search = {
  produtos: [], // cache local de todos os produtos (delivery + encomenda)
  produtosPorId: {},
  debounceTimer: null,

  async init() {
    this.container = document.getElementById("site-search");
    this.toggleBtn = document.getElementById("site-search-toggle");
    this.input = document.getElementById("site-search-input");
    this.clearBtn = document.getElementById("site-search-clear");
    this.resultsEl = document.getElementById("site-search-results");

    if (!this.container || !this.input) return; // header sem busca — não trava o resto do site

    try {
      this.produtos = await api.getProducts(); // sem "categoria" = todos os produtos
      this.produtos.forEach((p) => (this.produtosPorId[p.id] = p));
    } catch (erro) {
      // A busca é um extra: se a API falhar aqui, o resto do site continua
      // funcionando normalmente, só a busca fica sem resultados.
      this.produtos = [];
    }

    this.toggleBtn.addEventListener("click", () => this._abrirMobile());

    this.input.addEventListener("input", () => this._onInput());
    this.input.addEventListener("focus", () => {
      if (this.input.value.trim()) this._renderResultados(this._buscar(this.input.value));
    });

    this.clearBtn.addEventListener("click", () => {
      this._limparInput();
      this.input.focus();
    });

    document.addEventListener("click", (e) => {
      if (!this.container.contains(e.target)) this._fechar();
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") this._fechar();
    });
  },

  _abrirMobile() {
    this.container.classList.add("is-open");
    this.toggleBtn.setAttribute("aria-expanded", "true");
    requestAnimationFrame(() => this.input.focus());
  },

  _onInput() {
    const valor = this.input.value;
    this.clearBtn.hidden = valor.trim() === "";

    clearTimeout(this.debounceTimer);
    this.debounceTimer = setTimeout(() => {
      if (!valor.trim()) {
        this._esconderResultados();
        return;
      }
      this._renderResultados(this._buscar(valor));
    }, 150);
  },

  /** Remove acentos e caixa para comparar "bolo vulcao" com "Bolo Vulcão". */
  _normalizar(texto) {
    return (texto || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .trim();
  },

  _buscar(termo) {
    const alvo = this._normalizar(termo);
    if (!alvo) return [];
    return this.produtos
      .filter((p) => {
        const nome = this._normalizar(p.nome);
        const desc = this._normalizar(p.descricao);
        return nome.includes(alvo) || desc.includes(alvo);
      })
      .slice(0, 6); // dropdown enxuto, não é uma segunda página de catálogo
  },

  _renderResultados(resultados) {
    if (resultados.length === 0) {
      this.resultsEl.innerHTML = `
        <div class="site-search__empty">
          Nenhum produto encontrado.<br>Fale com a gente pelo WhatsApp se procura algo específico.
        </div>`;
      this.resultsEl.hidden = false;
      return;
    }

    this.resultsEl.innerHTML = resultados
      .map((p) => {
        const ehEncomenda = p.categoria.tipo === "encomenda";
        const tagOuPreco = ehEncomenda
          ? `<span class="site-search__tag">Sob encomenda</span>`
          : `<span class="site-search__price">${CartUI.formatBRL(p.preco)}</span>`;
        return `
        <button type="button" class="site-search__item" data-product-id="${p.id}">
          <span class="site-search__item-name">${p.nome}</span>
          ${tagOuPreco}
        </button>`;
      })
      .join("");

    this.resultsEl.querySelectorAll(".site-search__item").forEach((btn) => {
      btn.addEventListener("click", () => this._selecionar(Number(btn.dataset.productId)));
    });

    this.resultsEl.hidden = false;
  },

  _selecionar(id) {
    const produto = this.produtosPorId[id];
    if (!produto) return;

    this._fechar();
    this._limparInput();

    if (produto.categoria.tipo === "encomenda") {
      ProductWizard.open(produto.id);
    } else {
      productDetail.open(produto);
    }
  },

  _limparInput() {
    this.input.value = "";
    this.clearBtn.hidden = true;
  },

  _esconderResultados() {
    this.resultsEl.hidden = true;
    this.resultsEl.innerHTML = "";
  },

  _fechar() {
    this._esconderResultados();
    this.container.classList.remove("is-open");
    this.toggleBtn.setAttribute("aria-expanded", "false");
  },
};