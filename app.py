from flask import Flask, request, jsonify
from datetime import datetime
import json
import os

app = Flask(__name__)

# Função para salvar os dados no log
def salvar_log(dados):
    with open("log_webhook.txt", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} - Dados recebidos:\n")
        f.write(json.dumps(dados, ensure_ascii=False, indent=2))
        f.write("\n\n")

# Rota do webhook
@app.route("/webhook", methods=["POST"])
def receber_webhook():
    try:
        dados = request.get_json(silent=True)

        if not dados:
            print("⚠️ Webhook recebido com corpo vazio ou JSON inválido.")
            return jsonify({"erro": "Corpo vazio ou JSON inválido"}), 400

        print("📨 Webhook recebido da TecnoSpeed:")
        print(json.dumps(dados, indent=2, ensure_ascii=False))
        salvar_log(dados)
        return jsonify({"mensagem": "Recebido com sucesso"}), 200

    except Exception as e:
        print(f"❌ Erro ao processar webhook: {e}")
        return jsonify({"erro": "Falha ao processar"}), 400

# Inicialização do Flask
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)