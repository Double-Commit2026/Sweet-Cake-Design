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
  initHeroCarousel();
  initFeaturedBanner();
  
  document.getElementById("overlay").addEventListener("click", () => ProductWizard.close());
  document.getElementById("wizard-sheet-close").addEventListener("click", () => ProductWizard.close());
  document.getElementById("product-sheet-close").addEventListener("click", () => productDetail.close());

  await Catalog.init();
  await initCustomCakeCards();
  await initStoreInfo();

  revealOnScroll(document.querySelectorAll(".section .reveal"));
});

function initHeroCarousel() {
  const root = document.getElementById("hero-carousel");
  if (!root) return;

  const slides = Array.from(root.querySelectorAll(".hero-carousel__slide"));
  if (slides.length < 2) return;

  const INTERVALO = 5000; // ms entre fotos
  const reduzMovimento = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  let atual = 0;
  let timer = null;

  const dotsWrap = document.createElement("div");
  dotsWrap.className = "hero-carousel__dots";
  const dots = slides.map((_, i) => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "hero-carousel__dot";
    b.setAttribute("aria-label", `Ver foto ${i + 1} de ${slides.length}`);
    b.addEventListener("click", () => {
      mostrar(i);
      parar();
      iniciar();
    });
    dotsWrap.appendChild(b);
    return b;
  });
  root.appendChild(dotsWrap);

  function mostrar(i) {
    atual = (i + slides.length) % slides.length;
    slides.forEach((slide, idx) => {
      const ativo = idx === atual;
      slide.classList.toggle("is-active", ativo);
      slide.setAttribute("aria-hidden", ativo ? "false" : "true");
      dots[idx].classList.toggle("is-active", ativo);
      dots[idx].setAttribute("aria-current", ativo ? "true" : "false");
    });
  }

  function iniciar() {
    if (reduzMovimento || timer) return;
    timer = setInterval(() => mostrar(atual + 1), INTERVALO);
  }

  function parar() {
    clearInterval(timer);
    timer = null;
  }

  // pausa quando o mouse está em cima (só mouse, para não travar no toque do celular)
  root.addEventListener("pointerenter", (e) => { if (e.pointerType === "mouse") parar(); });
  root.addEventListener("pointerleave", (e) => { if (e.pointerType === "mouse") iniciar(); });
  // pausa para quem navega pelo teclado
  root.addEventListener("focusin", parar);
  root.addEventListener("focusout", iniciar);
  // não gasta processamento com a aba em segundo plano
  document.addEventListener("visibilitychange", () => (document.hidden ? parar() : iniciar()));

  mostrar(0);
  iniciar();
}

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

function escapeHTML(texto) {
  return String(texto ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

async function initFeaturedBanner() {
  const section = document.getElementById("destaques");
  const root = document.getElementById("featured-root");
  if (!section || !root) return;

  let banners = [];
  let numeroWhatsapp = "";
  try {
    const [lista, info] = await Promise.all([
      api.getBanners(),
      api.getStoreInfo().catch(() => ({})),
    ]);
    banners = lista;
    numeroWhatsapp = info.whatsapp || "";
  } catch (erro) {
    banners = [];
  }

  // Sem banner ativo (ou API fora do ar): a seção some e o hero fica no topo.
  if (!banners.length) {
    section.remove();
    return;
  }

  const nomeDe = (b) => [b.chamada, b.titulo].filter(Boolean).join(" ");
  const linkWhatsapp = (b) => {
    const mensagem = b.mensagem_whatsapp || `Olá! Gostaria de fazer um pedido: ${nomeDe(b)}.`;
    return `https://wa.me/${numeroWhatsapp}?text=${encodeURIComponent(mensagem)}`;
  };

  root.innerHTML = `
    <div class="featured__track">
      ${banners
        .map(
          (b, i) => `
        <article class="featured-slide ${i === 0 ? "is-active" : ""}">
          <div class="featured-slide__text">
            ${b.chamada ? `<span class="featured-slide__lead">${escapeHTML(b.chamada)}</span>` : ""}
            <h2 class="featured-slide__title">${escapeHTML(b.titulo)}</h2>
            ${b.descricao ? `<p class="featured-slide__desc">${escapeHTML(b.descricao)}</p>` : ""}
            ${
              numeroWhatsapp
                ? `<a class="btn btn--primary" href="${escapeHTML(linkWhatsapp(b))}" target="_blank" rel="noopener">${escapeHTML(b.botao_texto)} <span aria-hidden="true">→</span></a>`
                : ""
            }
          </div>
          <div class="featured-slide__media">
            <img src="${escapeHTML(b.imagem_url)}" alt="${escapeHTML(nomeDe(b))}" ${i === 0 ? 'fetchpriority="high"' : 'loading="lazy"'}>
          </div>
        </article>`
        )
        .join("")}
    </div>`;

  const slides = Array.from(root.querySelectorAll(".featured-slide"));

  if (slides.length > 1) {
    root.insertAdjacentHTML(
      "beforeend",
      `
      <button type="button" class="featured__arrow featured__arrow--prev" aria-label="Destaque anterior">
        <svg viewBox="0 0 24 24" aria-hidden="true"><polyline points="15 18 9 12 15 6"/></svg>
      </button>
      <button type="button" class="featured__arrow featured__arrow--next" aria-label="Próximo destaque">
        <svg viewBox="0 0 24 24" aria-hidden="true"><polyline points="9 18 15 12 9 6"/></svg>
      </button>
      <div class="featured__dots">
        ${slides.map((_, i) => `<button type="button" class="featured__dot" aria-label="Ver destaque ${i + 1} de ${slides.length}"></button>`).join("")}
      </div>`
    );

    const INTERVALO = 7000;
    const reduzMovimento = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const dots = Array.from(root.querySelectorAll(".featured__dot"));
    const track = root.querySelector(".featured__track");
    let atual = 0;
    let timer = null;

    const mostrar = (i) => {
      atual = (i + slides.length) % slides.length;
      slides.forEach((s, idx) => s.classList.toggle("is-active", idx === atual));
      dots.forEach((d, idx) => {
        d.classList.toggle("is-active", idx === atual);
        d.setAttribute("aria-current", idx === atual ? "true" : "false");
      });
    };
    const iniciar = () => {
      if (reduzMovimento || timer) return;
      timer = setInterval(() => mostrar(atual + 1), INTERVALO);
    };
    const parar = () => {
      clearInterval(timer);
      timer = null;
    };
    const reiniciar = () => {
      parar();
      iniciar();
    };

    root.querySelector(".featured__arrow--prev").addEventListener("click", () => { mostrar(atual - 1); reiniciar(); });
    root.querySelector(".featured__arrow--next").addEventListener("click", () => { mostrar(atual + 1); reiniciar(); });
    dots.forEach((d, i) => d.addEventListener("click", () => { mostrar(i); reiniciar(); }));

    // pausa: mouse em cima, foco do teclado e aba em segundo plano
    root.addEventListener("pointerenter", (e) => { if (e.pointerType === "mouse") parar(); });
    root.addEventListener("pointerleave", (e) => { if (e.pointerType === "mouse") iniciar(); });
    root.addEventListener("focusin", parar);
    root.addEventListener("focusout", iniciar);
    document.addEventListener("visibilitychange", () => (document.hidden ? parar() : iniciar()));

    // arrastar o dedo no celular
    let inicioX = null;
    track.addEventListener("pointerdown", (e) => { if (e.pointerType !== "mouse") inicioX = e.clientX; });
    track.addEventListener("pointerup", (e) => {
      if (inicioX === null) return;
      const dx = e.clientX - inicioX;
      inicioX = null;
      if (Math.abs(dx) > 50) { mostrar(atual + (dx < 0 ? 1 : -1)); reiniciar(); }
    });
    track.addEventListener("pointercancel", () => { inicioX = null; });

    mostrar(0);
    iniciar();
  }

  // abre com uma animação de altura em vez de empurrar a página de uma vez
  void section.offsetHeight;
  section.classList.add("is-open");
}
