
/**
 * product-wizard.js
 * Fluxo de configuração dos bolos por encomenda (Bentô, Mini Cake, Bolo
 * Redondo, Bolo Coração): o cliente escolhe variante (tamanho/camadas) e
 * cada grupo de opção (massa, recheio, decoração) em passos sucessivos.
 *
 * O preço mostrado a cada passo vem sempre de POST /api/pricing/calculate
 * — este arquivo nunca soma valores localmente para fins de cobrança,
 * apenas exibe o número que o backend calculou para a combinação atual.
 */

const ProductWizard = {
  produto: null,
  steps: [],
  stepIndex: 0,
  selections: { variantId: null, optionsByGroup: {} },
  quantidade: 1,
  precoAtual: null,

  async open(productId) {
    const sheet = document.getElementById("wizard-sheet");
    const body = document.getElementById("wizard-sheet-body");
    body.innerHTML = `<div class="skeleton" style="height:220px"></div>`;
    document.getElementById("overlay").classList.add("is-open");
    sheet.classList.add("is-open");
    sheet.setAttribute("aria-hidden", "false");

    try {
      this.produto = await api.getProduct(productId);
    } catch (erro) {
      body.innerHTML = `<div class="state-message"><strong>Não foi possível carregar este produto.</strong>Tente novamente.</div>`;
      return;
    }

    this.steps = [
      { type: "variant" },
      ...this.produto.grupos_opcoes.map((g) => ({ type: "options", group: g })),
      { type: "review" },
    ];
    this.stepIndex = 0;
    this.selections = { variantId: null, optionsByGroup: {} };
    this.quantidade = 1;
    this.precoAtual = null;

    document.getElementById("wizard-sheet-title").textContent = this.produto.nome;
    this._renderStep();
  },

  close() {
    const sheet = document.getElementById("wizard-sheet");
    sheet.classList.remove("is-open");
    sheet.setAttribute("aria-hidden", "true");
    if (!document.querySelector(".sheet.is-open")) document.getElementById("overlay").classList.remove("is-open");
  },

  async _recalcularPreco() {
    const optionIds = Object.values(this.selections.optionsByGroup).filter(Boolean);
    if (!this.selections.variantId) {
      this.precoAtual = { preco_unitario: this.produto.variantes[0] ? null : null, requer_orcamento: false };
      return;
    }
    try {
      this.precoAtual = await api.calculatePrice({
        product_id: this.produto.id,
        variant_id: this.selections.variantId,
        option_ids: optionIds,
        quantidade: this.quantidade,
      });
    } catch (erro) {
      this.precoAtual = null;
    }
  },

  _currentStep() {
    return this.steps[this.stepIndex];
  },

  _canAdvance() {
    const step = this._currentStep();
    if (step.type === "variant") return !!this.selections.variantId;
    if (step.type === "options") {
      if (!step.group.obrigatorio) return true;
      return !!this.selections.optionsByGroup[step.group.id];
    }
    return true;
  },

  async _goNext() {
    if (!this._canAdvance()) return;
    if (this.stepIndex < this.steps.length - 1) {
      this.stepIndex += 1;
      await this._renderStep();
    }
  },

  async _goBack() {
    if (this.stepIndex > 0) {
      this.stepIndex -= 1;
      await this._renderStep();
    } else {
      this.close();
    }
  },

  async _selectVariant(variantId) {
    this.selections.variantId = variantId;
    await this._recalcularPreco();
    await this._renderStep();
  },

  async _selectOption(groupId, optionId) {
    this.selections.optionsByGroup[groupId] = optionId;
    await this._recalcularPreco();
    await this._renderStep();
  },

  async _renderStep() {
    const body = document.getElementById("wizard-sheet-body");
    const footer = document.getElementById("wizard-sheet-footer");
    const step = this._currentStep();

    const dots = this.steps
      .map((_, i) => `<span class="wizard-steps__dot ${i < this.stepIndex ? "is-done" : ""} ${i === this.stepIndex ? "is-active" : ""}"></span>`)
      .join("");

    let conteudo = "";

    if (step.type === "variant") {
      conteudo = `
        <span class="wizard-step__label">Escolha o tamanho</span>
        <div class="wizard-options">
          ${this.produto.variantes
            .map(
              (v) => `
            <button type="button" class="wizard-option ${this.selections.variantId === v.id ? "is-selected" : ""}" data-variant-id="${v.id}">
              <span class="wizard-option__name">
                <span class="wizard-option__radio"></span>
                <span>${v.nome}${v.serve_pessoas ? `<span class="wizard-option__meta">Serve ~${v.serve_pessoas} pessoas</span>` : ""}</span>
              </span>
              <span class="wizard-option__price">${CartUI.formatBRL(v.preco_base)}</span>
            </button>`
            )
            .join("")}
        </div>`;
    } else if (step.type === "options") {
      const g = step.group;
      conteudo = `
        <span class="wizard-step__label">${g.nome}${g.obrigatorio ? "" : " (opcional)"}</span>
        <div class="wizard-options">
          ${g.opcoes
            .map((o) => {
              const selecionado = this.selections.optionsByGroup[g.id] === o.id;
              let precoLabel = "incluso";
              let precoClass = "wizard-option__price--included";
              if (o.requer_orcamento) {
                precoLabel = "sob orçamento";
                precoClass = "wizard-option__price--budget";
              } else if (o.preco_adicional > 0) {
                precoLabel = `+ ${CartUI.formatBRL(o.preco_adicional)}`;
                precoClass = "";
              }
              return `
              <button type="button" class="wizard-option ${selecionado ? "is-selected" : ""}" data-group-id="${g.id}" data-option-id="${o.id}">
                <span class="wizard-option__name">
                  <span class="wizard-option__radio"></span>
                  <span>${o.nome}</span>
                </span>
                <span class="wizard-option__price ${precoClass}">${precoLabel}</span>
              </button>`;
            })
            .join("")}
        </div>`;
    } else if (step.type === "review") {
      const variante = this.produto.variantes.find((v) => v.id === this.selections.variantId);
      const opcoesEscolhidas = this.produto.grupos_opcoes
        .map((g) => {
          const optId = this.selections.optionsByGroup[g.id];
          if (!optId) return null;
          const opt = g.opcoes.find((o) => o.id === optId);
          return opt ? `${g.nome}: ${opt.nome}` : null;
        })
        .filter(Boolean);

      conteudo = `
        <span class="wizard-step__label">Revise seu bolo</span>
        <p style="font-weight:600;margin-bottom:4px">${this.produto.nome} — ${variante ? variante.nome : ""}</p>
        <ul style="margin:0 0 14px;padding:0;color:var(--color-text-secondary);font-size:0.85rem">
          ${opcoesEscolhidas.map((o) => `<li>${o}</li>`).join("")}
        </ul>
        <div class="wizard-quantity">
          <span class="wizard-step__label" style="margin:0">Quantidade</span>
          <div class="cart-item__qty">
            <button type="button" id="wizard-qty-dec" aria-label="Diminuir quantidade">−</button>
            <span id="wizard-qty-value">${this.quantidade}</span>
            <button type="button" id="wizard-qty-inc" aria-label="Aumentar quantidade">+</button>
          </div>
        </div>
        ${this.precoAtual && this.precoAtual.requer_orcamento
          ? `<p class="cart-budget-note">Essa combinação inclui uma opção sob orçamento. O valor final será combinado pelo WhatsApp.</p>`
          : ""}
      `;
    }

    body.innerHTML = `<div class="wizard-steps">${dots}</div>${conteudo}`;

    // Preço no rodapé
    const precoTexto = this.precoAtual
      ? this.precoAtual.requer_orcamento
        ? "Sob orçamento"
        : CartUI.formatBRL(this.precoAtual.subtotal ?? this.precoAtual.preco_unitario ?? 0)
      : "Selecione o tamanho";

    const isReview = step.type === "review";
    footer.innerHTML = `
      <div class="wizard-footer">
        <div class="wizard-footer__price">
          <small>${isReview ? "Total" : "Total parcial"}</small>
          <strong>${precoTexto}</strong>
        </div>
        ${isReview
          ? `<button type="button" id="wizard-add-btn" class="btn btn--primary">Adicionar ao carrinho</button>`
          : `<button type="button" id="wizard-next-btn" class="btn btn--primary" ${this._canAdvance() ? "" : "disabled"}>Próximo</button>`
        }
      </div>
      <div class="wizard-nav">
        <button type="button" id="wizard-back-btn" class="btn btn--outline btn--block btn--sm">Voltar</button>
      </div>
    `;

    this._bindStepEvents(step);
  },

  _bindStepEvents(step) {
    document.getElementById("wizard-back-btn").addEventListener("click", () => this._goBack());

    if (step.type === "variant") {
      document.querySelectorAll("[data-variant-id]").forEach((btn) => {
        btn.addEventListener("click", () => this._selectVariant(Number(btn.dataset.variantId)));
      });
      const nextBtn = document.getElementById("wizard-next-btn");
      if (nextBtn) nextBtn.addEventListener("click", () => this._goNext());
    } else if (step.type === "options") {
      document.querySelectorAll("[data-option-id]").forEach((btn) => {
        btn.addEventListener("click", () =>
          this._selectOption(Number(btn.dataset.groupId), Number(btn.dataset.optionId))
        );
      });
      const nextBtn = document.getElementById("wizard-next-btn");
      if (nextBtn) nextBtn.addEventListener("click", () => this._goNext());
    } else if (step.type === "review") {
      document.getElementById("wizard-qty-inc").addEventListener("click", async () => {
        this.quantidade += 1;
        await this._recalcularPreco();
        await this._renderStep();
      });
      document.getElementById("wizard-qty-dec").addEventListener("click", async () => {
        if (this.quantidade <= 1) return;
        this.quantidade -= 1;
        await this._recalcularPreco();
        await this._renderStep();
      });
      document.getElementById("wizard-add-btn").addEventListener("click", () => this._addToCart());
    }
  },

  _addToCart() {
    const variante = this.produto.variantes.find((v) => v.id === this.selections.variantId);
    const opcoesEscolhidas = this.produto.grupos_opcoes
      .map((g) => {
        const optId = this.selections.optionsByGroup[g.id];
        const opt = optId ? g.opcoes.find((o) => o.id === optId) : null;
        return opt ? opt.nome : null;
      })
      .filter(Boolean);

    const requerOrcamento = !!(this.precoAtual && this.precoAtual.requer_orcamento);

    Cart.addItem({
      product_id: this.produto.id,
      variant_id: this.selections.variantId,
      option_ids: Object.values(this.selections.optionsByGroup).filter(Boolean),
      quantidade: this.quantidade,
      nome_exibido: `${this.produto.nome} — ${variante ? variante.nome : ""}`,
      detalhe_exibido: opcoesEscolhidas.join(", "),
      preco_exibido: requerOrcamento ? 0 : (this.precoAtual ? this.precoAtual.preco_unitario : 0),
      requer_orcamento: requerOrcamento,
    });

    CartUI.render();
    CartUI.bumpCounter();
    Toast.show(`${this.produto.nome} adicionado ao carrinho.`);
    this.close();
  },
};
