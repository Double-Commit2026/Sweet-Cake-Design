/**
 * main.js
 * Ponto de entrada: inicializa carrinho, catálogo, os cartões de bolos
 * personalizados (que abrem o wizard) e preenche as informações da loja
 * buscadas da API (endereço, horário, WhatsApp).
 */

document.addEventListener("DOMContentLoaded", async () => {
  Cart.load();
  CartUI.init();

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
  const grid = document.getElementById("custom-cake-grid");
  try {
    const categorias = (await api.getCategories()).filter((c) => c.tipo === "encomenda");
    const listas = await Promise.all(categorias.map((c) => api.getProducts({ categoria: c.slug })));
    const produtos = listas.flat();

    if (produtos.length === 0) {
      grid.innerHTML = `<div class="state-message"><strong>Cardápio de encomendas em atualização.</strong>Fale conosco pelo WhatsApp.</div>`;
      return;
    }

    grid.innerHTML = produtos
      .map(
        (p) => `
      <button type="button" class="custom-cake-card reveal" data-product-id="${p.id}">
        <span class="custom-cake-card__icon" aria-hidden="true">🎂</span>
        <h3>${p.nome}</h3>
        <p>${p.descricao || "Monte do seu jeito: tamanho, sabor e decoração."}</p>
        <span class="custom-cake-card__cta">Montar meu bolo →</span>
      </button>`
      )
      .join("");

    grid.querySelectorAll(".custom-cake-card").forEach((card) => {
      card.addEventListener("click", () => ProductWizard.open(Number(card.dataset.productId)));
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
