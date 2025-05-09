@app.route("/webhook", methods=["POST"])
def receber_webhook():
    try:
        dados = request.get_json(silent=True)

        if not dados:
            print("! Webhook recebido com corpo vazio ou JSON inválido.")
            return jsonify({"erro": "Corpo vazio ou JSON inválido", "dados": {}}), 400

        print(" Webhook recebido da TecnoSpeed:")
        print(json.dumps(dados, indent=2, ensure_ascii=False))
        salvar_log(dados)
        return jsonify({"mensagem": "Recebido com sucesso", "dados": {}}), 200

    except Exception as e:
        print(f" Erro ao processar webhook: {e}")
        return jsonify({"erro": "Falha ao processar", "dados": {}}), 400
