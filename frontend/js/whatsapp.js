/**
 * whatsapp.js
 * Fluxo de finalização: revalida o carrinho inteiro contra o backend
 * (fonte de verdade), monta a mensagem com os valores OFICIAIS retornados
 * pela API, e abre o WhatsApp com a mensagem pronta.
 *
 * O front-end nunca envia para o WhatsApp um preço que não tenha acabado
 * de vir do /api/cart/validate — mesmo que o carrinho local tenha sido
 * adulterado no navegador, a mensagem final reflete apenas o que o
 * servidor confirmou.
 */

const Checkout = {
  async finalizar() {
    if (Cart.itens.length === 0) return;

    const btn = document.getElementById("whatsapp-checkout-btn");
    const textoOriginal = btn.textContent;
    btn.disabled = true;
    btn.textContent = "Verificando disponibilidade...";

    try {
      const payload = Cart.itens.map((item) => ({
        product_id: item.product_id,
        variant_id: item.variant_id || null,
        option_ids: item.option_ids || [],
        quantidade: item.quantidade,
      }));

      const resultado = await api.validateCart(payload);

      if (resultado.erros && resultado.erros.length > 0) {
        Toast.show(resultado.erros[0]);
        // Remove do carrinho local os itens que a validação rejeitou seria ideal,
        // mas sem um identificador de volta por item, orientamos a revisar o carrinho.
      }

      if (!resultado.itens || resultado.itens.length === 0) {
        Toast.show("Não foi possível confirmar os itens do carrinho. Revise e tente novamente.");
        return;
      }

      const mensagem = this._montarMensagem(resultado);
      const numero = window.SWEET_CAKE_WHATSAPP_NUMBER || "";

      if (!numero) {
        Toast.show("Número de WhatsApp não configurado. Fale com a Sweet Cake por outro canal.");
        return;
      }

      const url = `https://wa.me/${numero}?text=${encodeURIComponent(mensagem)}`;
      window.open(url, "_blank", "noopener");
    } catch (erro) {
      Toast.show(erro.message || "Não foi possível finalizar o pedido agora. Tente novamente.");
    } finally {
      btn.disabled = false;
      btn.textContent = textoOriginal;
    }
  },

  _montarMensagem(resultado) {
    const linhas = ["Olá! Gostaria de fazer um pedido:", ""];

    resultado.itens.forEach((item) => {
      linhas.push(`• ${item.nome}`);
      linhas.push(`  Quantidade: ${item.quantidade}`);
      if (item.requer_orcamento) {
        linhas.push(`  Valor: a combinar (decoração sob orçamento)`);
      } else {
        linhas.push(`  Subtotal: ${this._formatBRL(item.subtotal)}`);
      }
      linhas.push("");
    });

    linhas.push("---------------------");
    linhas.push(`Total: ${this._formatBRL(resultado.total)}${resultado.tem_item_sob_orcamento ? " + itens sob orçamento" : ""}`);
    linhas.push("");
    linhas.push("Gostaria de confirmar a disponibilidade e finalizar o pedido.");

    return linhas.join("\n");
  },

  _formatBRL(valor) {
    return (valor || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
  },
};

const Toast = {
  show(mensagem, duracaoMs = 3200) {
    const el = document.getElementById("toast");
    el.textContent = mensagem;
    el.classList.add("is-visible");
    clearTimeout(this._timer);
    this._timer = setTimeout(() => el.classList.remove("is-visible"), duracaoMs);
  },
};
