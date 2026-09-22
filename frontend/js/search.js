/**
 * search.js
 * Etapa 4: os resultados agora aparecem de verdade no #searchResults,
 * e clicar num deles já abre o produto (pronta entrega) ou o
 * configurador (sob encomenda) — sem precisar rolar a página até achar
 * o card no catálogo.
 */
const Search = {
  produtos: [],
  produtosPorId: {},
  debounceTimer: null,

    async init() {
    this.container = document.getElementById("search");
    this.input = document.getElementById("searchInput");
    this.clearBtn = document.getElementById("searchClear");
    this.resultsEl = document.getElementById("searchResults");
    if (!this.input) return;

    try {
      this.produtos = await api.getProducts();
      this.produtos.forEach((p) => (this.produtosPorId[p.id] = p));
    } catch (erro) {
      this.produtos = [];
    }

    this.input.addEventListener("input", () => this._onInput());
    this.clearBtn.addEventListener("click", () => {
      this._limparInput();
      this._esconderResultados();
      this.input.focus();
    });

    this.input.addEventListener("focus", () => {
      if (this.input.value.trim()) this._renderResultados(this._buscar(this.input.value));
    });

    document.addEventListener("click", (e) => {
      if (!this.container.contains(e.target)) this._esconderResultados();
    });
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
      .slice(0, 6);
  },

  _renderResultados(resultados) {
    if (resultados.length === 0) {
      this.resultsEl.innerHTML = `
        <div class="search__empty">
          Nenhum produto encontrado.<br>Fale com a gente pelo WhatsApp se procura algo específico.
        </div>`;
      this.resultsEl.hidden = false;
      return;
    }

    this.resultsEl.innerHTML = resultados
      .map((p) => {
        const ehEncomenda = p.categoria.tipo === "encomenda";
        const tagOuPreco = ehEncomenda
          ? `<span class="search__tag">Sob encomenda</span>`
          : `<span class="search__price">${CartUI.formatBRL(p.preco)}</span>`;
        const thumb = p.imagem_url
          ? `<img class="search__item-thumb" src="${p.imagem_url}" alt="" loading="lazy">`
          : `<span class="search__item-thumb search__item-thumb--placeholder" aria-hidden="true">🍰</span>`;
        return `
        <button type="button" class="search__item" data-product-id="${p.id}">
          ${thumb}
          <span class="search__item-name">${p.nome}</span>
          ${tagOuPreco}
        </button>`;
      })
      .join("");

    this.resultsEl.querySelectorAll(".search__item").forEach((btn) => {
      btn.addEventListener("click", () => this._selecionar(Number(btn.dataset.productId)));
    });

    this.resultsEl.hidden = false;
  },

  _selecionar(id) {
    const produto = this.produtosPorId[id];
    if (!produto) return;

    this._esconderResultados();
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
};