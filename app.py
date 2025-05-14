from flask import Flask, request, jsonify
from datetime import datetime
import json
import os
import requests
from collections.abc import MutableMapping

app = Flask(__name__)

# CONFIGURAÇÕES
PLUGZ_API_URL = "https://api.plugzapi.com.br/instances/3C0D21B917DCB0A98E224689DEFE84AF/token/4FB6B468AB4F478D13FC0070/send-text"
TELEFONE_DESTINO = "5511988314240"

# Função para salvar os dados no log
def salvar_log(dados):
    with open("log_webhook.txt", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} - Dados recebidos:\n")
        f.write(json.dumps(dados, ensure_ascii=False, indent=2))
        f.write("\n\n")

# Função para achatar dicionários aninhados
def flatten_dict(d, parent_key='', sep='.'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, MutableMapping):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

# Enviar mensagem via PlugzAPI
def enviar_whatsapp(mensagem):
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

# Endpoint informativo
@app.route("/webhook", methods=["GET"])
def webhook_info():
    return jsonify({
        "mensagem": "Este endpoint é um webhook e aceita apenas requisições POST com JSON."
    }), 200

# Endpoint principal do webhook
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

        # Achatar JSON para gerar mensagem legível
        flat = flatten_dict(dados)
        corpo = "\n".join([f"{k}: {v}" for k, v in flat.items() if v is not None])
        mensagem = f"📩 Webhook recebido:\n\n{corpo}"

        enviado = enviar_whatsapp(mensagem)
        if not enviado:
            return jsonify({"erro": "Falha ao enviar mensagem para o WhatsApp"}), 500

        return jsonify({"mensagem": "Recebido com sucesso"}), 200

    except Exception as e:
        print(f"❌ Erro ao processar webhook: {e}")
        return jsonify({"erro": f"Erro interno: {str(e)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)