/**
 * cart.js
 * Estado do carrinho + persistência em localStorage + renderização do
 * carrinho flutuante e do bottom sheet.
 *
 * Cada item guardado localmente contém APENAS os dados necessários para
 * recalcular o preço no servidor (product_id, variant_id, option_ids,
 * quantidade) — mais um "preco_exibido" só para não deixar a tela em
 * branco enquanto a validação final não roda. O valor que efetivamente
 * conta é sempre o que /api/cart/validate devolve.
 */

const CART_STORAGE_KEY = "sweetcake_cart_v1";

const Cart = {
  itens: [],

  load() {
    try {
      const raw = localStorage.getItem(CART_STORAGE_KEY);
      this.itens = raw ? JSON.parse(raw) : [];
    } catch (_) {
      this.itens = [];
    }
  },

  save() {
    try {
      localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(this.itens));
    } catch (_) { /* localStorage indisponível — carrinho segue funcionando na sessão atual */ }
  },

  /** Adiciona um item. Itens configuráveis idênticos (mesma variante+opções) somam quantidade. */
  addItem(item) {
    const chave = Cart._chaveItem(item);
    const existente = this.itens.find((i) => Cart._chaveItem(i) === chave);
    if (existente) {
      existente.quantidade += item.quantidade;
    } else {
      this.itens.push(item);
    }
    this.save();
  },

  updateQuantity(index, delta) {
    const item = this.itens[index];
    if (!item) return;
    item.quantidade += delta;
    if (item.quantidade <= 0) {
      this.itens.splice(index, 1);
    }
    this.save();
  },

  removeItem(index) {
    this.itens.splice(index, 1);
    this.save();
  },

  clear() {
    this.itens = [];
    this.save();
  },

  totalItens() {
    return this.itens.reduce((soma, i) => soma + i.quantidade, 0);
  },

  _chaveItem(item) {
    return [item.product_id, item.variant_id || "", (item.option_ids || []).slice().sort().join(",")].join("|");
  },
};

// ---------------------------------------------------------------------------
// UI
// ---------------------------------------------------------------------------

const CartUI = {
  elFloating: null,
  elSheet: null,
  elOverlay: null,

  init() {
    this.elFloating = document.getElementById("floating-cart");
    this.elSheet = document.getElementById("cart-sheet");
    this.elOverlay = document.getElementById("overlay");

    document.getElementById("header-cart-btn").addEventListener("click", () => this.open());
    this.elFloating.addEventListener("click", () => this.open());
    document.getElementById("cart-sheet-close").addEventListener("click", () => this.close());
    this.elOverlay.addEventListener("click", () => this.closeAll());

    this.render();
  },

  open() {
    this.elOverlay.classList.add("is-open");
    this.elSheet.classList.add("is-open");
    this.elSheet.setAttribute("aria-hidden", "false");
  },

  close() {
    this.elSheet.classList.remove("is-open");
    this.elSheet.setAttribute("aria-hidden", "true");
    if (!document.querySelector(".sheet.is-open")) this.elOverlay.classList.remove("is-open");
  },

  closeAll() {
    document.querySelectorAll(".sheet.is-open").forEach((s) => {
      s.classList.remove("is-open");
      s.setAttribute("aria-hidden", "true");
    });
    this.elOverlay.classList.remove("is-open");
  },

  bumpCounter() {
    const badge = document.getElementById("cart-count");
    badge.classList.remove("is-bumped");
    // força reflow para reiniciar a animação
    void badge.offsetWidth;
    badge.classList.add("is-bumped");
  },

  formatBRL(valor) {
    return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
  },

  render() {
    const total = Cart.itens.reduce((soma, i) => soma + (i.preco_exibido || 0) * i.quantidade, 0);
    const totalItens = Cart.totalItens();
    const temOrcamento = Cart.itens.some((i) => i.requer_orcamento);

    // Badge do header
    const badge = document.getElementById("cart-count");
    badge.textContent = totalItens;
    badge.hidden = totalItens === 0;

    // Carrinho flutuante
    if (totalItens > 0) {
      this.elFloating.classList.add("is-visible");
      document.getElementById("floating-cart-count").textContent =
        `${totalItens} ${totalItens === 1 ? "item" : "itens"}`;
      document.getElementById("floating-cart-total").textContent =
        temOrcamento ? `${this.formatBRL(total)} + orçamento` : this.formatBRL(total);
    } else {
      this.elFloating.classList.remove("is-visible");
    }

    // Corpo do sheet
    const body = document.getElementById("cart-sheet-body");
    if (Cart.itens.length === 0) {
      body.innerHTML = `<p class="state-message">Seu carrinho está vazio.</p>`;
    } else {
      body.innerHTML = Cart.itens.map((item, index) => `
        <div class="cart-item">
          <div>
            <p class="cart-item__name">${item.nome_exibido}</p>
            ${item.detalhe_exibido ? `<p class="cart-item__detail">${item.detalhe_exibido}</p>` : ""}
            <div class="cart-item__qty">
              <button type="button" data-action="dec" data-index="${index}" aria-label="Diminuir quantidade">−</button>
              <span>${item.quantidade}</span>
              <button type="button" data-action="inc" data-index="${index}" aria-label="Aumentar quantidade">+</button>
            </div>
          </div>
          <div class="cart-item__right">
            ${item.requer_orcamento
              ? `<span class="cart-item__subtotal--budget">Sob orçamento</span>`
              : `<span class="cart-item__subtotal">${this.formatBRL((item.preco_exibido || 0) * item.quantidade)}</span>`
            }
            <button type="button" class="cart-item__remove" data-action="remove" data-index="${index}">Remover</button>
          </div>
        </div>
      `).join("");
    }

    // Rodapé / total
    const footer = document.getElementById("cart-sheet-footer");
    if (Cart.itens.length === 0) {
      footer.innerHTML = "";
    } else {
      footer.innerHTML = `
        ${temOrcamento ? `<p class="cart-budget-note">Um ou mais itens têm decoração personalizada e dependem de orçamento — o valor final desses itens será combinado pelo WhatsApp.</p>` : ""}
        <div class="cart-total-row">
          <span>Total${temOrcamento ? " (itens com preço fixo)" : ""}</span>
          <strong>${this.formatBRL(total)}</strong>
        </div>
        <button type="button" id="whatsapp-checkout-btn" class="btn btn--whatsapp btn--block">
          Finalizar pedido pelo WhatsApp
        </button>
        <button type="button" id="cart-clear-btn" class="btn btn--sm" style="margin-top:8px;color:var(--color-text-secondary)">
          Esvaziar carrinho
        </button>
      `;
      // Os botões foram recriados no innerHTML acima — precisam de listeners de novo.
      document.getElementById("whatsapp-checkout-btn").addEventListener("click", () => Checkout.finalizar());
      document.getElementById("cart-clear-btn").addEventListener("click", () => {
        Cart.clear();
        this.render();
      });
    }

    // Listeners de quantidade/remoção (delegação simples, recriados a cada render)
    body.querySelectorAll("[data-action]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const index = Number(btn.dataset.index);
        const action = btn.dataset.action;
        if (action === "inc") Cart.updateQuantity(index, 1);
        if (action === "dec") Cart.updateQuantity(index, -1);
        if (action === "remove") Cart.removeItem(index);
        this.render();
      });
    });
  },
};
