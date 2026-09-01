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
from database.db import init_db
from routes import categories, products, pricing, cart, store_info

app = Flask(__name__)
CORS(app, origins=[settings.FRONTEND_ORIGIN] if settings.FRONTEND_ORIGIN != "*" else "*")

app.register_blueprint(categories.bp)
app.register_blueprint(products.bp)
app.register_blueprint(pricing.bp)
app.register_blueprint(cart.bp)
app.register_blueprint(store_info.bp)

@app.get("/")
def home():
    return jsonify({
        "status": "ok",
        "message": "Sweet Cake API está funcionando"
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
    init_db()  # garante que as tabelas existem antes de subir o servidor
    app.run(debug=settings.DEBUG, port=5000)
