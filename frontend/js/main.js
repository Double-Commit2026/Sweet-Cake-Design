/**
 * main.js
 * Ponto de entrada: inicializa carrinho, catálogo, os cartões de bolos
 * personalizados (que abrem o wizard) e preenche as informações da loja
 * buscadas da API (endereço, horário, WhatsApp).
 */

document.addEventListener("DOMContentLoaded", async () => {
  Cart.load();
  CartUI.init();
  Search.init();

  document.getElementById("overlay").addEventListener("click", () => ProductWizard.close());
  document.getElementById("wizard-sheet-close").addEventListener("click", () => ProductWizard.close());
  document.getElementById("product-sheet-close").addEventListener("click", () => productDetail.close());

  await Catalog.init();
  await initCustomCakeCards();
  await initStoreInfo();

  revealOnScroll(document.querySelectorAll(".section .reveal"));
});

/**
 * Busca os produtos "encomenda" (Bentô, Mini Cake, Bolo Redondo, Bolo
 * Coração) e monta um cartão de entrada para o wizard de cada um.
 */

async function initCustomCakeCards() {
const CUSTOM_ICONS = {
  cake: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 21h16"/><path d="M5 21v-6a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v6"/><path d="M5 17c1.5 1.2 2.5 1.2 3.5 0s2.5-1.2 3.5 0 2.5 1.2 3.5 0 2-1.2 3.5 0"/><path d="M12 13V9"/><path d="M12 9c-.9-1-.9-1.8 0-2.8.9 1 .9 1.8 0 2.8z"/></svg>`,
  candy: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4.5"/><path d="M7.7 9.8 3.5 7.5v9l4.2-2.3"/><path d="M16.3 9.8l4.2-2.3v9l-4.2-2.3"/></svg>`,
};

const CUSTOM_CATEGORY_ICON = {
  "bento-cake": "cake",
  "mini-cake-e": "cake",
  "bolo-redondo": "cake",
  "bolo-coracao": "cake",
  cento_docinhos: "candy",
  "linha-especial": "candy",
};

function customCardHTML(p, slug) {
  const icone = CUSTOM_ICONS[CUSTOM_CATEGORY_ICON[slug]] || CUSTOM_ICONS.cake;
  const imagem = p.imagem_url ? `<img src="${p.imagem_url}" alt="${p.nome}" loading="lazy">` : "";
  return `
    <button type="button" class="custom-card reveal" data-product-id="${p.id}">
      <span class="custom-card__media">
        ${imagem}
        <span class="custom-card__title">
          <span class="custom-card__icon" aria-hidden="true">${icone}</span>
          <span>${p.nome}</span>
        </span>
      </span>
      <span class="custom-card__body">
        <span class="custom-card__desc">${p.descricao || "Monte do seu jeito."}</span>
        <span class="custom-card__cta">Personalizar <span aria-hidden="true">→</span></span>
      </span>
    </button>`;
}

  const grid = document.getElementById("custom-cake-grid");
  try {
    const categorias = (await api.getCategories()).filter((c) => c.tipo === "encomenda");
    const resultadosPorCategoria = await Promise.all(categorias.map((c) => api.getProducts({ categoria: c.slug })));

    const secoes = categorias
      .map((cat, i) => ({ categoria: cat, produtos: resultadosPorCategoria[i] }))
      .filter((s) => s.produtos.length > 0);

    if (secoes.length === 0) {
      grid.innerHTML = `<div class="state-message"><strong>Cardápio de encomendas em atualização.</strong>Fale conosco pelo WhatsApp.</div>`;
      return;
    }

    grid.innerHTML = secoes
      .map(
        (s) => `
      <div class="catalog-category">
        <div class="catalog-category__title"><h3>${s.categoria.nome}</h3></div>
        <div class="custom-cake-grid__cards">
          ${s.produtos
            .map((p) =>
              p.tipo_preco === "fixo"
                ? Catalog._cardHTML(p)
                : customCardHTML(p,s.categoria.slug)
            )
            .join("")}
        </div>
      </div>`
      )
      .join("");

    secoes.forEach((s) => s.produtos.filter((p) => p.tipo_preco === "fixo").forEach((p) => (Catalog.produtosPorId[p.id] = p)));

    grid.querySelectorAll(".custom-card").forEach((card) => {
      card.addEventListener("click", () => ProductWizard.open(Number(card.dataset.productId)));
    });

    grid.querySelectorAll(".product-card__image[data-detail-id]").forEach((img) => {
      img.addEventListener("click", () => {
        const produto = Catalog.produtosPorId[Number(img.dataset.detailId)];
        if (produto) productDetail.open(produto);
      });
    });

    grid.querySelectorAll(".product-card [data-add-fixed]").forEach((btn) => {
      btn.addEventListener("click", () => Catalog._adicionarAoCarrinho(btn));
    });

    revealOnScroll(grid.querySelectorAll(".reveal"));
  } catch (erro) {
    grid.innerHTML = `<div class="state-message"><strong>Não foi possível carregar o cardápio de encomendas.</strong>Tente novamente.</div>`;
  }
}

/** Preenche endereço, horário, formas de pagamento e link do WhatsApp na seção de contato. */
async function initStoreInfo() {
  try {
    const info = await api.getStoreInfo();
    window.SWEET_CAKE_WHATSAPP_NUMBER = info.whatsapp || "";

    const setText = (id, value) => {
      const el = document.getElementById(id);
      if (el && value) el.textContent = value;
    };
    setText("store-endereco", info.endereco);
    setText("store-horario", info.horario);
    setText("store-pagamento", info.pagamento);

    const whatsappLinks = document.querySelectorAll("[data-whatsapp-link]");
    if (info.whatsapp) {
      const link = `https://wa.me/${info.whatsapp}`;
      whatsappLinks.forEach((a) => (a.href = link));
    }

    const instagramLink = document.getElementById("store-instagram-link");
    if (instagramLink && info.instagram) instagramLink.href = info.instagram;
  } catch (erro) {
    // Seção de contato mantém os placeholders estáticos do HTML se a API falhar.
  }
}
