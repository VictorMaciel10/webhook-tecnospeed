from flask import Flask, request, jsonify
from datetime import datetime
import json
import os
import requests

app = Flask(__name__)

# CONFIGURAÇÕES PLUGZAPI
PLUGZ_API_URL = "https://api.plugzapi.com.br/instances/3C0D21B917DCB0A98E224689DEFE84AF/token/4FB6B468AB4F478D13FC0070/send-text"
TELEFONE_DESTINO = "5511971102724"

# TOKEN DE SEGURANÇA DO HEADER (enviado pela Tecnospeed)
CLIENT_TOKEN_HEADER = "Fc0dd5429e2674e2e9cea2c0b5b29d000S"

# Função para salvar os dados no log
def salvar_log(dados):
    caminho_log = os.path.abspath("log_webhook.txt")
    print(f"📝 Salvando log em: {caminho_log}")
    with open(caminho_log, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} - Dados recebidos:\n")
        f.write(json.dumps(dados, ensure_ascii=False, indent=2))
        f.write("\n\n")

# Enviar mensagem via PlugzAPI
def enviar_whatsapp(mensagem):
    if not mensagem:
        print("❌ Mensagem vazia. Abortando envio.")
        return False

    if not TELEFONE_DESTINO:
        print("❌ Número de telefone não definido.")
        return False

    payload = {
        "phone": TELEFONE_DESTINO,
        "message": mensagem
    }

    headers = {
        "Content-Type": "application/json"
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
        token_recebido = request.headers.get("Client-Token")
        if token_recebido != CLIENT_TOKEN_HEADER:
            print(f"❌ Token inválido recebido: {token_recebido}")
            return jsonify({"erro": "Token de segurança inválido"}), 403

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
