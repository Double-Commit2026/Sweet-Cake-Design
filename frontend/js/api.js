/**
 * api.js
 * Única camada que fala com o backend. Nenhum outro arquivo deve montar
 * uma URL de fetch diretamente — assim, se o endpoint mudar, só este
 * arquivo precisa ser tocado.
 *
 * Importante: os preços que chegam aqui vêm sempre do servidor. Este
 * arquivo nunca calcula nem arredonda preço, apenas repassa o que a API
 * retornou.
 */

const API_BASE_URL = window.SWEET_CAKE_API_BASE_URL || "https://sweet-cake-design-eh5j.onrender.com";

async function apiRequest(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
  } catch (erroDeRede) {
    throw new ApiError("Não foi possível conectar ao servidor. Verifique sua internet e tente novamente.");
  }

  if (!response.ok) {
    let detail = "Não foi possível processar sua solicitação. Tente novamente.";
    try {
      const corpo = await response.json();
      if (corpo && corpo.detail) detail = corpo.detail;
    } catch (_) { /* resposta sem corpo JSON */ }
    throw new ApiError(detail, response.status);
  }

  return response.json();
}

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

const api = {
  getCategories() {
    return apiRequest("/categories");
  },
  getProducts({ categoria, destaque } = {}) {
    const params = new URLSearchParams();
    if (categoria) params.set("categoria", categoria);
    if (destaque) params.set("destaque", "true");
    const query = params.toString() ? `?${params.toString()}` : "";
    return apiRequest(`/products${query}`);
  },
  getProduct(id) {
    return apiRequest(`/products/${id}`);
  },
  calculatePrice({ product_id, variant_id, option_ids, quantidade }) {
    return apiRequest("/pricing/calculate", {
      method: "POST",
      body: JSON.stringify({ product_id, variant_id, option_ids, quantidade }),
    });
  },
  validateCart(itens) {
    return apiRequest("/cart/validate", {
      method: "POST",
      body: JSON.stringify({ itens }),
    });
  },
  getStoreInfo() {
    return apiRequest("/store-info");
  },
};
