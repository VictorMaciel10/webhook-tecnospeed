from flask import Flask, request, jsonify
from datetime import datetime
import json
import os
import requests
import pymysql
from collections.abc import MutableMapping

app = Flask(__name__)

# CONFIGURAÇÕES PLUGZAPI
PLUGZ_API_URL = "https://api.plugzapi.com.br/instances/3C0D21B917DCB0A98E224689DEFE84AF/token/4FB6B468AB4F478D13FC0070/send-text"

# CONFIGURAÇÃO DO BANCO DE DADOS MYSQL AZURE
DB_CONFIG = {
    'host': 'bddevelop1.mysql.database.azure.com',
    'user': 'bddevelop',
    'password': 'E130581.rik',
    'database': 'develop_1_lic',
    'port': 3306,
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def conectar_banco():
    return pymysql.connect(**DB_CONFIG)

DESTINOS_WHATSAPP = {
    "45784346000166": "5511978554235",
    "35255716000114": "5511971102724",
    "13279813000104": "5511971102724",
    "06555039000151": "553188356564",
    "06269409000194": "553188356564"
}

def salvar_log(dados):
    os.makedirs("logs", exist_ok=True)
    with open("logs/log_webhook.txt", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} - Dados recebidos:\n")
        f.write(json.dumps(dados, ensure_ascii=False, indent=2))
        f.write("\n\n")

def flatten_dict(d, parent_key='', sep='.'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, MutableMapping):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def gerar_mensagem_personalizada(dados, schema_cliente):
    tipo = dados.get("tipoWH")
    titulo = dados.get("titulo", {})
    nosso_numero = titulo.get("TituloNossoNumero", "N/A")
    id_integracao = titulo.get("idintegracao", "N/A")
    data_envio = dados.get("dataHoraEnvio", "N/A")
    mensagem = ""
    nome_empresa = "Desconhecida"

    if id_integracao and id_integracao != "N/A":
        try:
            conn = conectar_banco()
            with conn.cursor() as cursor:
                cursor.execute(f"""
                    SELECT cadastro.razaosocial
                    FROM `{schema_cliente}`.receber
                    INNER JOIN `{schema_cliente}`.cadastro
                        ON receber.coddestinatario = cadastro.codcadastro
                    WHERE receber.numeroboleto = %s
                    LIMIT 1
                """, (id_integracao,))
                resultado = cursor.fetchone()
                if resultado:
                    nome_empresa = resultado["razaosocial"]
        except Exception as e:
            print(f"⚠️ Erro ao buscar razão social da empresa: {e}")
        finally:
            if 'conn' in locals():
                conn.close()

    empresa_info = f"🏢 Empresa: {nome_empresa}"

    if tipo == "notifica_registrou":
        mensagem = (
            f"{empresa_info}\n"
            f"📄 REGISTRO EFETUADO\n"
            f"Nosso Número: {nosso_numero}\n"
            f"ID Integração: {id_integracao}\n"
            f"Data de Envio: {data_envio}\n"
            f"Situação: {titulo.get('situacao', 'N/A')}"
        )
        if id_integracao != "N/A":
            url_boleto = f"https://plugboleto.com.br/api/v1/boletos/impressao/{id_integracao}"
            mensagem += f"\n\n🔗 Boleto: {url_boleto}"

    elif tipo == "notifica_liquidou":
        mensagem = (
            f"{empresa_info}\n"
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
            f"{empresa_info}\n"
            f"🗑️ TÍTULO BAIXADO\n"
            f"Nosso Número: {nosso_numero}\n"
            f"ID Integração: {id_integracao}\n"
            f"Situação: {titulo.get('situacao', 'N/A')}\n"
            f"Data de Envio: {data_envio}"
        )

    elif tipo == "notifica_rejeitou":
        mensagem = (
            f"{empresa_info}\n"
            f"❌ TÍTULO REJEITADO\n"
            f"Nosso Número: {nosso_numero}\n"
            f"ID Integração: {id_integracao}\n"
            f"Situação: {titulo.get('situacao', 'N/A')}\n"
            f"Data de Envio: {data_envio}"
        )

    elif tipo == "notifica_alterou":
        mensagem = (
            f"{empresa_info}\n"
            f"✏️ ALTERAÇÃO EFETUADA\n"
            f"Nosso Número: {nosso_numero}\n"
            f"ID Integração: {id_integracao}\n"
            f"Novo Valor: {titulo.get('TituloValor', 'N/A')}\n"
            f"Nova Data de Vencimento: {titulo.get('TituloDataVencimento', 'N/A')}\n"
            f"Data de Envio: {data_envio}"
        )

    elif tipo == "notifica_protestou":
        mensagem = (
            f"{empresa_info}\n"
            f"📣 TÍTULO ENVIADO A PROTESTO\n"
            f"Nosso Número: {nosso_numero}\n"
            f"ID Integração: {id_integracao}\n"
            f"Situação: {titulo.get('situacao', 'N/A')}\n"
            f"Data de Envio: {data_envio}"
        )

    else:
        flat = flatten_dict(dados)
        mensagem = f"{empresa_info}\n📦 Dados do título:\n" + "\n".join([f"{k}: {v}" for k, v in flat.items() if v is not None])

    return mensagem

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
            return jsonify({"erro": "Corpo vazio ou JSON inválido", "dados": {}}), 400

        print("📨 Webhook recebido da TecnoSpeed:")
        print(json.dumps(dados, indent=2, ensure_ascii=False))
        salvar_log(dados)

        cnpj = dados.get("CpfCnpjCedente")
        if not cnpj:
            return jsonify({"erro": "Campo 'CpfCnpjCedente' ausente no JSON recebido."}), 400

        # Redirecionamento especial
        cnpj_original = cnpj
        if cnpj == "13279813000104":
            cnpj = "35255716000114"
        elif cnpj == "06269409000194":
            cnpj = "06555039000151"

        conn = conectar_banco()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT CODIGOEMPRESA, ESQUEMA
                FROM develop_1_lic.autenticacao
                WHERE REPLACE(REPLACE(REPLACE(REPLACE(RAZAOEMPRESA, '.', ''), '/', ''), '-', ''), ' ', '') = %s
                LIMIT 1
            """, (cnpj,))
            empresa = cursor.fetchone()

            if not empresa:
                return jsonify({
                    "erro": f"CNPJ {cnpj} não encontrado na tabela develop_1_lic.autenticacao."
                }), 404

            schema_cliente = empresa["ESQUEMA"].lower()
            if not schema_cliente.isidentifier():
                return jsonify({
                    "erro": f"Nome de schema inválido: {schema_cliente}"
                }), 500

            sql_insert = f"""
                INSERT INTO `{schema_cliente}`.webhooks_recebidos 
                (cnpj, tipo_wh, data_envio, json_completo, codigoempresa)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql_insert, (
                cnpj_original,
                dados.get("tipoWH"),
                dados.get("dataHoraEnvio"),
                json.dumps(dados, ensure_ascii=False),
                empresa["CODIGOEMPRESA"]
            ))
            conn.commit()

        mensagem = gerar_mensagem_personalizada(dados, schema_cliente)

        telefone_principal = DESTINOS_WHATSAPP.get(cnpj_original)
        if telefone_principal:
            enviar_whatsapp(mensagem, telefone_principal)

        if cnpj_original in {"35255716000114", "13279813000104"}:
            enviar_whatsapp(mensagem, "5511989704515")

        return jsonify({"mensagem": "Recebido com sucesso", "dados": {}}), 200

    except Exception as e:
        print(f"❌ Erro ao processar webhook: {e}")
        return jsonify({"erro": "Falha ao processar", "dados": {}}), 400
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)