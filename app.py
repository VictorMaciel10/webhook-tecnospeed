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
    "45784346000166": "5511978554235",
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

# Função para gerar mensagem personalizada por tipoWH
def gerar_mensagem_personalizada(dados):
    tipo = dados.get("tipoWH")
    titulo = dados.get("titulo", {})
    nosso_numero = titulo.get("TituloNossoNumero", "N/A")
    id_integracao = titulo.get("idintegracao", "N/A")
    data_envio = dados.get("dataHoraEnvio", "N/A")
    mensagem = ""

    if tipo == "notifica_registrou":
        mensagem = (
            f"📄 REGISTRO EFETUADO\n"
            f"Nosso Número: {nosso_numero}\n"
            f"ID Integração: {id_integracao}\n"
            f"Data de Envio: {data_envio}\n"  
            f"Situação: {titulo.get('situacao', 'N/A')}"
        )
        if id_integracao and id_integracao != "N/A":
            url_boleto = f"https://plugboleto.com.br/api/v1/boletos/impressao/{id_integracao}"
            mensagem += f"\n\n🔗 Boleto: {url_boleto}"

    elif tipo == "notifica_liquidou":
        mensagem = (
            f"✅ LIQUIDAÇÃO CONFIRMADA\n"
            f"Nosso Número: {nosso_numero}\n"
            f"ID Integração: {id_integracao}\n"
            f"Valor Pago: {titulo.get('PagamentoValorPago', 'N/A')}\n"
            f"Data do Pagamento: {titulo.get('PagamentoData', 'N/A')}\n"
            f"Data do Crédito: {titulo.get('PagamentoDataCredito', 'N/A')}\n"
            f"Data de Envio: {data_envio}"
        )

    elif tipo == "notifica_baixou":
        mensagem = (
            f"🗑️ TÍTULO BAIXADO\n"
            f"Nosso Número: {nosso_numero}\n"
            f"ID Integração: {id_integracao}\n"
            f"Situação: {titulo.get('situacao', 'N/A')}\n"
            f"Data de Envio: {data_envio}"
        )

    elif tipo == "notifica_rejeitou":
        mensagem = (
            f"❌ TÍTULO REJEITADO\n"
            f"Nosso Número: {nosso_numero}\n"
            f"ID Integração: {id_integracao}\n"
            f"Situação: {titulo.get('situacao', 'N/A')}\n"
            f"Data de Envio: {data_envio}"
        )

    elif tipo == "notifica_alterou":
        mensagem = (
            f"✏️ ALTERAÇÃO EFETUADA\n"
            f"Nosso Número: {nosso_numero}\n"
            f"ID Integração: {id_integracao}\n"
            f"Novo Valor: {titulo.get('TituloValor', 'N/A')}\n"
            f"Nova Data de Vencimento: {titulo.get('TituloDataVencimento', 'N/A')}\n"
            f"Data de Envio: {data_envio}"
        )

    elif tipo == "notifica_protestou":
        mensagem = (
            f"📣 TÍTULO ENVIADO A PROTESTO\n"
            f"Nosso Número: {nosso_numero}\n"
            f"ID Integração: {id_integracao}\n"
            f"Situação: {titulo.get('situacao', 'N/A')}\n"
            f"Data de Envio: {data_envio}"
        )

    else:
        flat = flatten_dict(dados)
        mensagem = "📦 Dados do título:\n" + "\n".join([f"{k}: {v}" for k, v in flat.items() if v is not None])

    return mensagem

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
        print("📟 Resposta da PlugzAPI:", resposta.text)
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

        cnpj = dados.get("CpfCnpjCedente")
        if not cnpj:
            return jsonify({
                "erro": "Campo 'CpfCnpjCedente' ausente no JSON recebido.",
                "dados": {}
            }), 400

        telefone_principal = DESTINOS_WHATSAPP.get(cnpj)
        if not telefone_principal:
            return jsonify({
                "erro": f"CNPJ '{cnpj}' não autorizado ou não mapeado.",
                "dados": {}
            }), 403

        mensagem = gerar_mensagem_personalizada(dados)

        # Enviar para o número principal
        enviar_whatsapp(mensagem, telefone_principal)

        # Enviar para o número adicional se o CNPJ for especial
        if cnpj in {"35255716000114", "13279813000104"}:
            enviar_whatsapp(mensagem, "5511989704515")

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