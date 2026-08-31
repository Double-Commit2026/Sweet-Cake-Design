/**
 * catalog.js
 * Busca categorias e produtos "delivery" (preço fixo, catálogo do iFood)
 * na API e renderiza os chips de navegação + a grade de produtos.
 */

const Catalog = {
  categorias: [],
  categoriaAtiva: "todas",
  produtosPorId: {}, // <- Novo: cache simples {id: produto}

  async init() {
    const grid = document.getElementById("catalog-grid");
    const chipsEl = document.getElementById("catalog-chips");

    try {
      const todas = await api.getCategories();
      this.categorias = todas.filter((c) => c.tipo === "delivery");
    } catch (erro) {
      grid.innerHTML = this._stateHTML(
        "Não foi possível carregar o catálogo.",
        "Verifique sua conexão e tente novamente."
      );
      return;
    }

    this._renderChips(chipsEl);
    await this._renderGrid(grid);
  },

  _renderChips(container) {
    const chips = [{ slug: "todas", nome: "Todas" }, ...this.categorias];
    container.innerHTML = chips
      .map(
        (c) => `
      <button type="button" class="chip" data-slug="${c.slug}" aria-pressed="${c.slug === this.categoriaAtiva}">
        ${c.nome}
      </button>`
      )
      .join("");

    container.querySelectorAll(".chip").forEach((chip) => {
      chip.addEventListener("click", async () => {
        this.categoriaAtiva = chip.dataset.slug;
        container.querySelectorAll(".chip").forEach((c) => c.setAttribute("aria-pressed", "false"));
        chip.setAttribute("aria-pressed", "true");
        await this._renderGrid(document.getElementById("catalog-grid"));
      });
    });
  },

  async _renderGrid(grid) {
    grid.innerHTML = this._skeletonHTML(6);

    try {
      const categoriasParaExibir =
        this.categoriaAtiva === "todas" ? this.categorias : this.categorias.filter((c) => c.slug === this.categoriaAtiva);

      const resultadosPorCategoria = await Promise.all(
        categoriasParaExibir.map((c) => api.getProducts({ categoria: c.slug }))
      );

      const secoes = categoriasParaExibir
        .map((cat, i) => ({ categoria: cat, produtos: resultadosPorCategoria[i] }))
        .filter((s) => s.produtos.length > 0);

      if (secoes.length === 0) {
        grid.innerHTML = this._stateHTML("Nenhum produto encontrado.", "Tente outra categoria.");
        return;
      }

      grid.innerHTML = secoes
        .map(
          (s) => `
        <div class="catalog-category">
          <div class="catalog-category__title"><h3>${s.categoria.nome}</h3></div>
          <div class="product-grid">
            ${s.produtos.map((p) => this._cardHTML(p)).join("")}
          </div>
        </div>`
        )
        .join("");

      // Guarda os produtos no caache e liga o clique de "ver detalhes" na imagem
      secoes.forEach((s) => s.produtos.forEach((p) => (this.produtosPorId[p.id] = p)));

      grid.querySelectorAll(".product-card__image[data-detail-id]").forEach((img) => {
        img.addEventListener("click", () => {
          const produto = this.produtosPorId[Number(img.dataset.detailId)];
          if (produto) productDetail.open(produto);
        });
      });

      grid.querySelectorAll(".product-card [data-add-fixed]").forEach((btn) => {
        btn.addEventListener("click", () => this._adicionarAoCarrinho(btn));
      });

      revealOnScroll(grid.querySelectorAll(".reveal"));
    } catch (erro) {
      grid.innerHTML = this._stateHTML("Não foi possível carregar o catálogo.", "Tente novamente em instantes.");
    }
  },

  _cardHTML(produto) {
    const precoAtual = CartUI.formatBRL(produto.preco);
    const precoAntigo = produto.preco_promocional ? CartUI.formatBRL(produto.preco_promocional) : null;
    return `
      <article class="product-card reveal" data-product-id="${produto.id}">
        <div class="product-card__image" data-detail-id="${produto.id}">
          ${produto.imagem_url ? `<img src="${produto.imagem_url}" alt="${produto.nome}" loading="lazy">` : "imagem em breve"}
        </div>
        <div class="product-card__body">
          ${produto.destaque ? `<span class="badge">Destaque</span>` : ""}
          <p class="product-card__title">${produto.nome}</p>
          <p class="product-card__desc">${produto.descricao || ""}</p>
          <div class="product-card__footer">
            <span class="price">
              ${precoAntigo ? `<span class="price-strike">${precoAntigo}</span>` : ""}${precoAtual}
            </span>
            <button type="button" class="btn btn--primary btn--sm" data-add-fixed
              data-id="${produto.id}" data-nome="${produto.nome}" data-preco="${produto.preco}">
              Adicionar
            </button>
          </div>
        </div>
      </article>`;
  },

  _adicionarAoCarrinho(btn) {
    const id = Number(btn.dataset.id);
    Cart.addItem({
      product_id: id,
      variant_id: null,
      option_ids: [],
      quantidade: 1,
      nome_exibido: btn.dataset.nome,
      detalhe_exibido: "",
      preco_exibido: Number(btn.dataset.preco),
      requer_orcamento: false,
    });
    CartUI.render();
    CartUI.bumpCounter();
    Toast.show(`${btn.dataset.nome} adicionado ao carrinho.`);

    const card = btn.closest(".product-card");
    card.classList.remove("is-added");
    void card.offsetWidth;
    card.classList.add("is-added");
  },

  _skeletonHTML(qtd) {
    return `<div class="product-grid">${Array.from({ length: qtd })
      .map(() => `<div class="skeleton" style="aspect-ratio:4/3.6"></div>`)
      .join("")}</div>`;
  },

  _stateHTML(titulo, subtitulo) {
    return `<div class="state-message"><strong>${titulo}</strong>${subtitulo}</div>`;
  },
};

/** Revela elementos com uma leve animação de entrada quando entram na viewport. */
function revealOnScroll(elements) {
  if (!("IntersectionObserver" in window)) {
    elements.forEach((el) => el.classList.add("is-visible"));
    return;
  }
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.1 }
  );
  elements.forEach((el) => observer.observe(el));
}

/**
 * ProductDetail
 * Painel com a descrição completa do produto, aberto ao clicar na imagem do card
 * — Para o cliente decidir com mais informação antes de comprar.
 */
const productDetail = {
  produtoAtual: null,

  open(produto) {
    this.produtoAtual = produto;
    document.getElementById("product-sheet-title").textContent = produto.nome;

    const precoAtual = CartUI.formatBRL(produto.preco);
    const precoAntigo = produto.preco_promocional ? CartUI.formatBRL(produto.preco_promocional) : null;

    document.getElementById("product-sheet-body").innerHTML = `
      <div class="product-detail__image">
        ${produto.imagem_url ? `<img src="${produto.imagem_url}" alt="${produto.nome}">` : ""}
      </div>
      ${produto.destaque ? `<span class="badge" style="margin-bottom:8px">Destaque</span>` : ""}
      <p class="product-detail__desc">${produto.descricao || "Sem descrição disponível."}</p>
    `;

    document.getElementById("product-sheet-footer").innerHTML = `
      <div class="wizard-footer">
        <div class="wizard-footer__price">
          <small>Preço</small>
          <strong>${precoAntigo ? `<span class="price-strike">${precoAntigo}</span>` : ""}${precoAtual}</strong>
        </div>
        <button type="button" id="product-detail-add-btn" class="btn btn--primary">Adicionar ao carrinho</button>
      </div>
    `;

    document.getElementById("product-detail-add-btn").addEventListener("click", () => {
      Cart.addItem({
        product_id: produto.id,
        variant_id: null,
        option_ids: [],
        quantidade: 1,
        nome_exibido: produto.nome,
        detalhe_exibido: "",
        preco_exibido: produto.preco,
        requer_orcamento: false,
      });
      CartUI.render();
      CartUI.bumpCounter();
      Toast.show(`${produto.nome} adicionado ao carrinho.`);
      this.close();
    });

    document.getElementById("overlay").classList.add("is-open");
    const sheet = document.getElementById("product-sheet");
    sheet.classList.add("is-open");
    sheet.setAttribute("aria-hidden", "false");
  },

  close() {
    const sheet = document.getElementById("product-sheet");
    sheet.classList.remove("is-open");
    sheet.setAttribute("aria-hidden", "true");
    if (!document.querySelector(".sheet.is-open")) document.getElementById("overlay").classList.remove("is-open");
  },
};

