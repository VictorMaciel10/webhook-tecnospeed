from flask import Flask, request, jsonify
from datetime import datetime
import json
import os
import requests
from collections.abc import MutableMapping

app = Flask(__name__)

# CONFIGURAÇÕES PLUGZAPI
PLUGZ_API_URL = "https://api.plugzapi.com.br/instances/3C0D21B917DCB0A98E224689DEFE84AF/token/4FB6B468AB4F478D13FC0070/send-text"

# Mapeamento CNPJ -> número de WhatsApp
DESTINOS_WHATSAPP = {
    "45784346000166": "5511988314240",
    "35255716000114": "5511971102724",
    "13279813000104": "5511971102724"
}

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
def enviar_whatsapp(mensagem, telefone_destino):
    payload = {
        "phone": telefone_destino,
        "message": mensagem
    }
    headers = {
        "Content-Type": "application/json",
        "Client-Token": "Fc0dd5429e2674e2e9cea2c0b5b29d000S"
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

        print("📨 Webhook recebido da TecnoSpeed:")
        print(json.dumps(dados, indent=2, ensure_ascii=False))
        salvar_log(dados)

        # Obter o CNPJ do cedente
        cnpj = dados.get("CpfCnpjCedente")
        if not cnpj:
            return jsonify({
                "erro": "Campo 'CpfCnpjCedente' ausente no JSON recebido.",
                "dados": {}
            }), 400

        telefone_destino = DESTINOS_WHATSAPP.get(cnpj)
        if not telefone_destino:
            return jsonify({
                "erro": f"CNPJ '{cnpj}' não autorizado ou não mapeado.",
                "dados": {}
            }), 403

        # Achatar JSON para texto plano
        flat = flatten_dict(dados)
        mensagem = "\n".join([f"{k}: {v}" for k, v in flat.items() if v is not None])

        # Enviar mensagem para WhatsApp
        enviar_whatsapp(mensagem, telefone_destino)

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