from flask import Flask, request, jsonify
from datetime import datetime
import json
import os
import requests

app = Flask(__name__)

# CONFIGURAÇÕES PLUGZAPI
PLUGZ_API_URL = "https://api.plugzapi.com.br/instances/3C0D21B917DCB0A98E224689DEFE84AF/token/4FB6B468AB4F478D13FC0070/send-text"
TELEFONE_DESTINO = "5511971102724"
CLIENT_TOKEN = "Fc0dd5429e2674e2e9cea2c0b5b29d000S"  # Token de autenticação para envio

# Função para salvar os dados no log
def salvar_log(dados):
    with open("log_webhook.txt", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} - Dados recebidos:\n")
        f.write(json.dumps(dados, ensure_ascii=False, indent=2))
        f.write("\n\n")

# Enviar mensagem via PlugzAPI
def enviar_whatsapp(mensagem):
    if not mensagem:
        print("❌ Mensagem vazia. Não enviada ao WhatsApp.")
        return False

    payload = {
        "number": TELEFONE_DESTINO,
        "text": mensagem
    }

    headers = {
        "Content-Type": "application/json",
        "Client-Token": CLIENT_TOKEN  # Cabeçalho exigido pela PlugzAPI
    }

    try:
        resposta = requests.post(PLUGZ_API_URL, headers=headers, json=payload)
        print(f"✅ Mensagem enviada ao WhatsApp. Status: {resposta.status_code}")
        print("🧾 Resposta da PlugzAPI:", resposta.text)
        return resposta.status_code == 200
    except Exception as e:
        print(f"❌ Erro ao enviar mensagem pelo PlugzAPI: {e}")
        return False

@app.route("/webhook", methods=["GET"])
def webhook_info():
    return jsonify({
        "mensagem": "Este endpoint é um webhook e aceita apenas requisições POST com JSON."
    }), 200

@app.route("/webhook", methods=["POST"])
def receber_webhook():
    try:
        dados = request.get_json(silent=True)

        if not dados:
            print("⚠️ Webhook recebido com corpo vazio ou JSON inválido.")
            return jsonify({
                "erro": "Corpo vazio ou JSON inválido",
                "dados": {}
            }), 400

        print("📨 Webhook recebido da Tecnospeed:")
        print(json.dumps(dados, indent=2, ensure_ascii=False))
        salvar_log(dados)

        mensagem = f"📬 Notificação recebida da Tecnospeed:\n\n{json.dumps(dados, indent=2, ensure_ascii=False)}"
        enviar_whatsapp(mensagem)

        return jsonify({
            "mensagem": "Recebido com sucesso",
            "dados": {}
        }), 200

    except Exception as e:
        print(f"❌ Erro ao processar webhook: {e}")
        return jsonify({
            "erro": "Falha ao processar",
            "dados": {}
        }), 400

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)