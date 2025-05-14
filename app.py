from flask import Flask, request, jsonify
import requests
import json

app = Flask(__name__)

# Configurações da instância PlugZAPI
PLUGZAPI_ID_INSTANCIA = "3C0D21B917DCB0A98E224689DEFE84AF"
PLUGZAPI_TOKEN = "4FB6B468AB4F478D13FC0070"
TOKEN_SEGURANCA = "Fc0dd5429e2674e2e9cea2c0b5b29d000S"

# Endpoint da API do PlugZAPI
PLUGZAPI_URL = "https://api.plugzapi.com.br/instances/3C0D21B917DCB0A98E224689DEFE84AF/token/4FB6B468AB4F478D13FC0070/send-text"

# Número fixo de destino (ou modifique para ser dinâmico)
NUMERO_DESTINO = "5511988314240"

@app.route("/webhook", methods=["POST"])
def receber_webhook():
    # Verifica o token de segurança via header
    client_token = request.headers.get("Client-Token")
    if client_token != TOKEN_SEGURANCA:
        return jsonify({"erro": "Token inválido"}), 403

    try:
        # Recebe o JSON da Tecnospeed
        dados = request.get_json()

        # Converte o JSON para uma string formatada
        mensagem = f"📩 Webhook recebido:\n\n{json.dumps(dados, indent=2, ensure_ascii=False)}"

        # Prepara o corpo da requisição para PlugZAPI
        payload = {
            "phone": NUMERO_DESTINO,
            "message": mensagem
        }

        # Envia para a API PlugZAPI
        response = requests.post(PLUGZAPI_URL, json=payload)

        if response.status_code == 200:
            return jsonify({"status": "Mensagem enviada com sucesso"}), 200
        else:
            return jsonify({
                "erro": "Falha ao enviar mensagem para o WhatsApp",
                "resposta_plugzapi": response.text
            }), 500

    except Exception as e:
        return jsonify({"erro": f"Erro ao processar o webhook: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(port=5000, debug=True)