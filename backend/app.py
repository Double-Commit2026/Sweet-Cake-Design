"""
Ponto de entrada do backend da Sweet Cake.

Para rodar:
    cd backend
    pip install -r ../requirements.txt
    python database/seed.py     # popula o banco com o catálogo real (1x)
    python app.py

O front-end (arquivos estáticos em ../frontend) consome esta API via
fetch() — ver frontend/js/api.js.
"""
from flask import Flask, jsonify
from flask_cors import CORS

from config.settings import settings
from routes import categories, products, pricing, cart, store_info


app = Flask(__name__)

raw_origins = settings.FRONTEND_ORIGIN or "*"
origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()] if raw_origins != "*" else ["*"]

CORS(
    app,
    resources={r"/api/*": {"origins": origins}},
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
)

app.register_blueprint(categories.bp)
app.register_blueprint(products.bp)
app.register_blueprint(pricing.bp)
app.register_blueprint(cart.bp)
app.register_blueprint(store_info.bp)

# Teste da API

@app.get("/")
def home():
    return jsonify({
        "status": "online",
        "message": "Sweet Cake Design API"
    })

@app.get("/api/health")
def health_check():
    return jsonify({"status": "ok"})

# Tratamento genérico de erros: nunca expõe detalhes técnicos (stack trace,
# nomes de tabela, etc.) ao usuário final — só uma mensagem amigável.
@app.errorhandler(Exception)
def erro_generico(e):
    if settings.DEBUG:
        raise e
    return jsonify({"detail": "Não foi possível processar sua solicitação. Tente novamente."}), 500


if __name__ == "__main__":
    app.run(
        debug=settings.DEBUG, 
        port=5000
    )
