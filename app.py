from flask import Flask, jsonify, render_template, request, redirect, url_for, session
from flask_cors import CORS
import datetime
import logging
from werkzeug.security import check_password_hash, generate_password_hash
from flask_session import Session
from repositories import BalanceteReposotory, ComprasRepository, ContasPagarRepository, FechamentoRepository, FinancialRepository, OrdersRepository, UsersRepository

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Habilita CORS para todas as rotas
app.secret_key = "cubograf_secret_key"
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
Session(app)


#ok
def load_users():
    try:
        users_repository = UsersRepository()
        return users_repository.get_all()
    except Exception as e:
        logger.error(f"Erro ao carregar usuários: {e}")
        return []
    
def save_user(user):
    try:
        users_repository = UsersRepository()
        return users_repository.insert_new(user)
    except Exception as e:
        logger.error(f"Erro ao salvar usuário: {e}")
        return False

@app.route("/")
def index():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return render_template("index.html")
#ok
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        logger.info(f"Tentativa de login para usuário: {username}")

        users = load_users()
        logger.info(f"Usuários carregados: {len(users)} usuários encontrados")

        for user in users:
            if user.get("username") == username:
                logger.info("Usuário encontrado, verificando senha")
                stored_hash = user.get("password_hash", "")
                logger.info(f"Hash armazenado: {stored_hash}")

                if check_password_hash(stored_hash, password):
                    logger.info("Senha correta, autenticando usuário")
                    session["logged_in"] = True
                    session["username"] = username
                    session["user_role"] = user.get("role", "vendedor")
                    return redirect(url_for("index"))
                else:
                    logger.warning("Senha incorreta")
                    return render_template("login.html", error="Usuário ou senha incorretos")

        logger.warning("Usuário não encontrado")
        return render_template("login.html", error="Usuário ou senha incorretos")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))
#ok
@app.route("/api/orders", methods=["GET"])
def get_orders():
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401
    _repository = OrdersRepository()
    orders = _repository.get_all()
    # orders = load_data(ORDERS_FILE)

    # Adiciona classes CSS para status
    for order in orders:
        if isinstance(order, dict):
            status = order.get("status", "")
            if status == "Aguardando Aprovação":
                order["status_class"] = "status-aprovacao"
            elif status == "Aguardando Pagamento":
                order["status_class"] = "status-pagamento"
            elif status == "Em Produção":
                order["status_class"] = "status-producao"
            elif status == "Disponível para Retirada":
                order["status_class"] = "status-retirada"
            elif status == "Finalizada":
                order["status_class"] = "status-finalizada"
            elif status == "Cancelada":
                order["status_class"] = "status-cancelada"

            # Garante que o campo material seja uma lista
            if "material" in order and not isinstance(order["material"], list):
                order["material"] = [order["material"]]

    return jsonify(orders)
#ok
@app.route("/api/orders", methods=["POST"])
def create_order():
    order_repository = OrdersRepository()
    try:

        data = request.get_json()
        if not data:
            return jsonify({"error": "Dados inválidos", "details": ["Nenhum dado recebido"]}), 400

        validation_errors = validate_order_data(data)
        if validation_errors:
            return jsonify({"error": "Dados inválidos", "details": validation_errors}), 400

        valor_total = float(data.get("valor_total", 0))
        custo = float(data.get("custo", 0))
        valor_estimado_lucro = valor_total - custo

        new_order = {
            "cliente": data.get("cliente", "").strip(),
            "vendedor": data.get("vendedor", "").strip(),
            "material": data.get("material"),
            "fornecedor": data.get("fornecedor", "").strip(),
            "valor_total": float(data.get("valor_total", 0)),
            "custo": custo,
            "valor_entrada": float(data.get("valor_entrada", 0)),
            "valor_restante": float(data.get("valor_restante", 0)),
            "valor_estimado_lucro": valor_estimado_lucro,
            "forma_pagamento": data.get("forma_pagamento", "PIX"),
            "data": data.get("data", datetime.datetime.now().strftime("%Y-%m-%d")),
            "status": data.get("status", "Aguardando Aprovação"),
            "status_class": f"status-{data.get('status', 'aguardando-aprovacao').lower().replace(' ', '-')}"
        }

        order_repository.insert_new(new_order)

        update_financial_data(new_order)
        return jsonify({"success": True, "order": new_order})
        
    except Exception as e:
        logger.error(f"Erro ao criar ordem: {e}")
        return jsonify({"error": "Erro ao processar dados", "details": [str(e)]}), 400
#ok
def validate_order_data(data):
    """Valida os dados da ordem de serviço"""
    errors = []

    # Validação de campos obrigatórios
    required_fields = {
        "cliente": "Nome do cliente",
        "vendedor": "Nome do vendedor",
        "material": "Material",
        "valor_total": "Valor total"
    }

    for field, name in required_fields.items():
        if not data.get(field):
            errors.append(f"Campo '{name}' é obrigatório")

    # Validação de valores numéricos
    try:
        # Converter valor_total para float, removendo formatação monetária
        valor_total_str = str(data.get("valor_total", "0"))
        valor_total_str = valor_total_str.replace("R$", "").replace(".", "").replace(",", ".").strip()
        valor_total = float(valor_total_str)

        if valor_total <= 0:
            errors.append("Valor total deve ser maior que zero")

        # Converter custo para float, removendo formatação monetária
        custo_str = str(data.get("custo", "0"))
        custo_str = custo_str.replace("R$", "").replace(".", "").replace(",", ".").strip()
        custo = float(custo_str)

        if custo < 0:
            errors.append("Custo não pode ser negativo")

        # Atualizar os valores no dicionário de dados
        data["valor_total"] = valor_total
        data["custo"] = custo

    except ValueError:
        errors.append("Valor total ou custo inválido")

    # Validação do material
    material = data.get("material", [])
    if isinstance(material, str):
        material = [item.strip() for item in material.split(",") if item.strip()]
    if not material:
        errors.append("Pelo menos um material deve ser informado")

    return errors
#ok
def update_financial_data(order):
    try:
        financial_repository = FinancialRepository()
        entry = {
            "type": "entrada",
            "value": float(order["valor_total"]),
            "description": f"Ordem de Serviço #{order['numero']} - {order['cliente']}",
            "date": datetime.datetime.now().isoformat(),
            "order_id": order["numero"]
        }

        financial_repository.insert_new(entry)

        update_balancete(order["valor_total"], "entrada", order["numero"])
        
        return True

    except Exception as e:
        logger.error(f"Erro ao atualizar dados financeiros: {str(e)}")
        return False

def update_balancete(value, entry_type, reference_id):
    try:
        balancete_repository = BalanceteReposotory()
        entry = {
            "type": entry_type,
            "value": float(value),
            "reference_id": reference_id,
            "date": datetime.datetime.now().isoformat(),
            "category": "servico" if entry_type == "entrada" else "custo"
        }

        balancete_repository.insert_new(entry)
        return True

    except Exception as e:
        logger.error(f"Erro ao atualizar balancete: {str(e)}")
        return False
#ok
@app.route("/api/orders/<order_id>", methods=["PUT"])
def update_order(order_id):
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = request.json
        if not data:
            return jsonify({"error": "Dados inválidos"}), 400

        orders_repository = OrdersRepository()

        required_fields = ["cliente", "vendedor", "material", "valor_total"]
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return jsonify({"error": f"Campos obrigatórios faltando: {', '.join(missing_fields)}"}), 400

        try:
            valor_total = float(data["valor_total"])
            custo = float(data["custo"])
            if valor_total < 0 or custo < 0:
                return jsonify({"error": "Valores não podem ser negativos"}), 400
        except ValueError:
            return jsonify({"error": "Valores numéricos inválidos"}), 400

        valor_entrada = valor_total * 0.5 
        valor_restante = valor_total - valor_entrada
        valor_estimado_lucro = valor_total - custo
        order = {
            "cliente": data.get("cliente", "").strip(),
            "vendedor": data.get("vendedor", "").strip(),
            "material": data.get("material", ""),
            "fornecedor": data.get("fornecedor", "").strip(),
            "valor_total": valor_total,
            "custo": custo,
            "valor_entrada": valor_entrada,
            "valor_restante": valor_restante,
            "valor_estimado_lucro": valor_estimado_lucro,
            "forma_pagamento": data.get("forma_pagamento", "PIX"),
            "data": data.get("data", ""),
            "status": data.get("status",  "Aguardando Aprovação")
        }

        orders_repository.update_order(order_id, order)

        return jsonify({"success": True, "order": order})

    except Exception as e:
        logger.error(f"Erro ao atualizar ordem: {e}")
        return jsonify({"error": f"Erro ao processar dados: {str(e)}"}), 400
#ok
@app.route("/api/compras", methods=["GET"])
def get_compras():
    if not session.get("logged_in") or session.get("user_role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401

    compras_repository = ComprasRepository()
    compras = compras_repository.get_all()
    return jsonify(compras)
#ok
@app.route("/api/compras", methods=["POST"])
def create_compra():
    if not session.get("logged_in") or session.get("user_role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = request.json
        if not data:
            return jsonify({"error": "Dados inválidos", "details": ["Nenhum dado recebido"]}), 400

        required_fields = {
            "item": "Item",
            "fornecedor": "Fornecedor",
            "valor": "Valor",
            "data": "Data"
        }

        errors = []
        for field, name in required_fields.items():
            if not data.get(field):
                errors.append(f"Campo '{name}' é obrigatório")

        if errors:
            return jsonify({"error": "Dados inválidos", "details": errors}), 400

        try:
            valor = float(data["valor"])
            if valor <= 0:
                return jsonify({"error": "Dados inválidos", "details": ["Valor deve ser maior que zero"]}), 400
        except ValueError:
            return jsonify({"error": "Dados inválidos", "details": ["Valor inválido"]}), 400

        compras_repository = ComprasRepository()

        new_compra = {
            "item": data["item"].strip(),
            "fornecedor": data["fornecedor"].strip(),
            "valor": valor,
            "data": data["data"],
            "observacao": data.get("observacao", "").strip(),
            "timestamp": datetime.datetime.now().isoformat()
        }

        compra_id = compras_repository.insert_new(new_compra)

        try:
            contas_repository = ContasPagarRepository()
            financial_repository = FinancialRepository()

            new_conta = {
                "descricao": f"Compra #{compra_id} - {new_compra['item']}",
                "valor": new_compra["valor"],
                "vencimento": new_compra["data"],
                "status": "Pendente",
                "compra_id": compra_id,
                "timestamp": datetime.datetime.now().isoformat()
            }

            conta_id = contas_repository.insert_new(new_conta)

            expense_entry = {
                "type": "expense",
                "description": f"Compra #{conta_id} - {new_compra['item']}",
                "value": new_compra["valor"],
                "date": new_compra["data"],
                "status": "Pendente",
                "compra_id": compra_id,
                "conta_id": conta_id,
                "timestamp": datetime.datetime.now().isoformat()
            }

            financial_repository.insert_new(expense_entry)

            return jsonify({
                "success": True,
                "compra": new_compra,
                "conta": new_conta,
                "financial_entry": expense_entry
            })

        except Exception as e:
            logger.error(f"Erro ao criar conta a pagar: {e}")
            # Retornar sucesso da compra, mas com aviso
            return jsonify({
                "success": True,
                "compra": new_compra,
                "warning": "Erro ao criar conta a pagar automaticamente"
            })

    except Exception as e:
        logger.error(f"Erro ao criar compra: {e}")
        return jsonify({"error": "Erro ao processar dados", "details": [str(e)]}), 400
#ok
@app.route("/api/compras/<compra_id>", methods=["PUT"])
def update_compra(compra_id):
    if not session.get("logged_in") or session.get("user_role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = request.json
        if not data:
            return jsonify({"error": "Dados inválidos"}), 400

        compras_repository = ComprasRepository()
        compra = {
            "item": data.get("item", ""),
            "fornecedor": data.get("fornecedor",  ""),
            "valor": float(data.get("valor",  0)),
            "data": data.get("data", ""),
            "observacao": data.get("observacao", "")
        }

        compras_repository.update_compra(compra_id, compra)

        return jsonify({"success": True, "compra": compra})
        

    except Exception as e:
        logger.error(f"Erro ao atualizar compra: {e}")
        return jsonify({"error": f"Erro ao processar dados: {str(e)}"}), 400
#ok
@app.route("/api/contas_pagar", methods=["GET"])
def get_contas_pagar():
    if not session.get("logged_in") or session.get("user_role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401

    try:
        contas_repository = ContasPagarRepository()
        contas = contas_repository.get_all()
        return jsonify(contas)
    except Exception as e:
        logger.error(f"Erro ao buscar contas a pagar: {e}")
        return jsonify({"error": "Erro ao buscar dados"}), 500
#ok
@app.route("/api/contas_pagar", methods=["POST"])
def criar_conta_pagar():
    if not session.get("logged_in") or session.get("user_role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = request.json
        if not data:
            return jsonify({"error": "Dados inválidos"}), 400

        required_fields = {
            "descricao": "Descrição",
            "valor": "Valor",
            "vencimento": "Data de Vencimento",
            "categoria": "Categoria",
            "forma_pagamento": "Forma de Pagamento"
        }

        missing_fields = []
        for field, name in required_fields.items():
            if not data.get(field):
                missing_fields.append(name)

        if missing_fields:
            return jsonify({
                "error": "Campos obrigatórios faltando",
                "fields": missing_fields
            }), 400

        # Carregar contas existentes
        contas_repository = ContasPagarRepository()
        balancete_repository = BalanceteReposotory()

        # Criar nova conta
        nova_conta = {
            "descricao": data["descricao"],
            "valor": float(data["valor"]),
            "vencimento": data["vencimento"],
            "categoria": data["categoria"],
            "forma_pagamento": data["forma_pagamento"],
            "status": "Pendente",
            "observacao": data.get("observacao", ""),
            "compra_id": data.get("compra_id"),
            "data_criacao": datetime.datetime.now().isoformat(),
            "criado_por": session.get("username")
        }

        conta_id = contas_repository.insert_new(nova_conta)
        
        balancete = {
            "tipo": "saida",
            "valor": nova_conta["valor"],
            "descricao": nova_conta["descricao"],
            "data": nova_conta["vencimento"],
            "categoria": nova_conta["categoria"],
            "referencia": conta_id
        }
        balancete_repository.insert_new(balancete)

        return jsonify({"success": True, "conta": nova_conta})
        
    except Exception as e:
        logger.error(f"Erro ao criar conta a pagar: {e}")
        return jsonify({"error": str(e)}), 500
#ok
@app.route("/api/contas_pagar/<conta_id>", methods=["PUT"])
def atualizar_conta_pagar(conta_id):
    if not session.get("logged_in") or session.get("user_role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = request.json
        if not data:
            return jsonify({"error": "Dados inválidos"}), 400

        contas_repository = ContasPagarRepository()

        data = {
            "descricao": data.get("descricao", None),
            "valor": float(data.get("valor", None)),
            "vencimento": data.get("vencimento", None),
            "categoria": data.get("categoria", None),
            "forma_pagamento": data.get("forma_pagamento", None),
            "status": data.get("status", None),
            "observacao": data.get("observacao", None),
            "atualizado_em": datetime.datetime.now().isoformat(),
            "atualizado_por": session.get("username")
        }

        contas_repository.update_conta(conta_id, data)

        return jsonify({"success": True, "conta": data})
        
    except Exception as e:
        logger.error(f"Erro ao atualizar conta a pagar: {e}")
        return jsonify({"error": str(e)}), 500
#ok
@app.route("/api/contas_pagar/<conta_id>", methods=["DELETE"])
def excluir_conta_pagar(conta_id):
    if not session.get("logged_in") or session.get("user_role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401

    try:
        contas_repository = ContasPagarRepository()
        contas_repository.delete_conta(conta_id)

        return jsonify({"success": True, "message": "Conta excluída com sucesso"})
        
    except Exception as e:
        logger.error(f"Erro ao excluir conta a pagar: {e}")
        return jsonify({"error": str(e)}), 500
#ok
@app.route("/api/contas_pagar/<conta_id>/pagar", methods=["POST"])
def pagar_conta(conta_id):
    if not session.get("logged_in") or session.get("user_role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401

    try:
        contas_repository = ContasPagarRepository()
        financial_repository = FinancialRepository()

        conta = contas_repository.get_by_id(conta_id)
        
        if conta["status"] == "Pago":
            return jsonify({"error": "Conta já está paga"}), 400

        conta["status"] = "Pago"
        conta["data_pagamento"] = datetime.datetime.now().isoformat()
        conta["pago_por"] = session.get("username")

        contas_repository.update_conta(conta_id, conta)
        
        financial = {
            "type": "saida",
            "value": conta["valor"],
            "description": f"Pagamento: {conta['descricao']}",
            "date": conta["data_pagamento"],
            "conta_id": conta["id"]
        }

        financial_repository.insert_new(financial)
        
        return jsonify({"success": True, "conta": conta})
        
    except Exception as e:
        logger.error(f"Erro ao pagar conta: {e}")
        return jsonify({"error": str(e)}), 500
#ok
@app.route("/api/financeiro/dados", methods=["GET"])
def get_dados_financeiros():
    if not session.get("logged_in") or session.get("user_role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401

    try:
        mes = request.args.get("mes", datetime.datetime.now().month)
        ano = request.args.get("ano", datetime.datetime.now().year)

        try:
            mes = int(mes)
            ano = int(ano)
            if mes < 1 or mes > 12:
                raise ValueError("Mês inválido")
        except ValueError as e:
            return jsonify({"error": f"Parâmetros inválidos: {str(e)}"}), 400

        orders_repository = OrdersRepository()
        compras_repository = ComprasRepository()
        contas_repository = ContasPagarRepository()

        orders = orders_repository.get_all()
        compras = compras_repository.get_all()
        contas = contas_repository.get_all()

        # Filtrar por período
        periodo = f"{ano}-{mes:02d}"

        # Calcular receita total (apenas ordens finalizadas)
        receita_total = sum(
            float(order.get("valor_total", 0))
            for order in orders
            if isinstance(order, dict)
            and order.get("status") == "Finalizada"
            and order.get("data", "").startswith(periodo)
        )

        # Calcular custos totais (ordens finalizadas)
        custos_total = sum(
            float(order.get("custo", 0))
            for order in orders
            if isinstance(order, dict)
            and order.get("status") == "Finalizada"
            and order.get("data", "").startswith(periodo)
        )

        # Calcular valores a receber (ordens não finalizadas/canceladas)
        valores_receber = sum(
            float(order.get("valor_restante", 0))
            for order in orders
            if isinstance(order, dict)
            and order.get("status") not in ["Finalizada", "Cancelada"]
            and order.get("data", "").startswith(periodo)
        )

        # Calcular saídas (compras não canceladas + contas pendentes)
        saidas_compras = sum(
            float(compra.get("valor", 0))
            for compra in compras
            if isinstance(compra, dict)
            and compra.get("status") != "Cancelada"
            and compra.get("data", "").startswith(periodo)
        )

        saidas_contas = sum(
            float(conta.get("valor", 0))
            for conta in contas
            if isinstance(conta, dict)
            and conta.get("status") == "Pendente"
            and conta.get("data_vencimento", "").startswith(periodo)
        )

        saidas_total = saidas_compras + saidas_contas

        # Calcular lucro líquido (receita - custos - saídas)
        lucro_liquido = receita_total - (custos_total + saidas_total)

        return jsonify({
            "receita_total": receita_total,
            "custos_total": custos_total,
            "saidas_total": saidas_total,
            "saidas_compras": saidas_compras,
            "saidas_contas": saidas_contas,
            "lucro_liquido": lucro_liquido,
            "valores_receber": valores_receber,
            "periodo": {
                "mes": mes,
                "ano": ano
            }
        })

    except Exception as e:
        logger.error(f"Erro ao buscar dados financeiros: {e}")
        return jsonify({"error": "Erro ao processar dados"}), 500
#ok
@app.route("/api/financeiro/transferir", methods=["POST"])
def transferir_pedidos():
    if not session.get("logged_in") or session.get("user_role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = request.json
        if not data:
            return jsonify({"error": "Dados inválidos"}), 400

        mes_origem = data.get("mes_origem")
        ano_origem = data.get("ano_origem")
        mes_destino = data.get("mes_destino")
        ano_destino = data.get("ano_destino")

        if not all([mes_origem, ano_origem, mes_destino, ano_destino]):
            return jsonify({"error": "Todos os campos de período são obrigatórios"}), 400

        orders_repository = OrdersRepository()
        orders = orders_repository.get_all()
        # Identificar pedidos a serem transferidos
        periodo_origem = f"{ano_origem}-{mes_origem.zfill(2)}"
        pedidos_transferir = [
            order for order in orders
            if isinstance(order, dict)
               and order.get("data", "").startswith(periodo_origem)
               and order.get("status") not in ["Finalizada", "Cancelada"]
        ]

        # Atualizar data dos pedidos
        periodo_destino = f"{ano_destino}-{mes_destino.zfill(2)}-01"
        for order in orders:
            if isinstance(order, dict) and order in pedidos_transferir:
                order["data"] = periodo_destino
                orders_repository.update_order(order["id"], order)

        return jsonify({
            "success": True,
            "message": f"Transferidos {len(pedidos_transferir)} pedidos",
            "pedidos": pedidos_transferir
        })
        

    except Exception as e:
        logger.error(f"Erro ao transferir pedidos: {e}")
        return jsonify({"error": f"Erro ao processar dados: {str(e)}"}), 400
#ok
@app.route("/api/financeiro/pagamentos", methods=["GET"])
def get_pagamentos():
    if not session.get("logged_in") or session.get("user_role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401

    try:
        # Obter parâmetros de período
        mes = request.args.get("mes")
        ano = request.args.get("ano")

        if not mes or not ano:
            return jsonify({"error": "Mês e ano são obrigatórios"}), 400

        financial_repository = FinancialRepository()
        pagamentos = financial_repository.get_all()

        # Filtrar por período
        periodo = f"{ano}-{mes.zfill(2)}"
        pagamentos_periodo = [
            pagamento for pagamento in pagamentos
            if isinstance(pagamento, dict) and pagamento.get("date", "").startswith(periodo)
        ]

        return jsonify(pagamentos_periodo)

    except Exception as e:
        logger.error(f"Erro ao buscar pagamentos: {e}")
        return jsonify({"error": f"Erro ao processar dados: {str(e)}"}), 400
#ok
@app.route("/api/financeiro/pagamentos", methods=["POST"])
def create_pagamento():
    if not session.get("logged_in") or session.get("user_role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = request.json
        if not data:
            return jsonify({"error": "Dados inválidos"}), 400

        # Validar campos obrigatórios
        required_fields = ["data", "cliente", "valor", "status"]
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return jsonify({"error": f"Campos obrigatórios faltando: {', '.join(missing_fields)}"}), 400

        financial_repository = FinancialRepository()

        new_pagamento = {
            "date": data.get("data"),
            "cliente": data.get("cliente"),
            "valor": float(data.get("valor")),
            "status": data.get("status"),
            "observacao": data.get("observacao", "")
        }

        financial_repository.insert_new(new_pagamento)

        return jsonify({"success": True, "pagamento": new_pagamento})
        

    except Exception as e:
        logger.error(f"Erro ao criar pagamento: {e}")
        return jsonify({"error": f"Erro ao processar dados: {str(e)}"}), 400
#ok
@app.route("/api/financeiro/pagamentos/<pagamento_id>", methods=["PUT"])
def update_pagamento(pagamento_id):
    if not session.get("logged_in") or session.get("user_role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = request.json
        if not data:
            return jsonify({"error": "Dados inválidos"}), 400

        financial_repository = FinancialRepository()
        pagamento = financial_repository.get_by_id(pagamento_id)

        if pagamento is None:
            return jsonify({"error": "Pagamento não encontrado"}), 404

        
        pagamento["date"] = data.get("date", None)
        pagamento["cliente"] = data.get("cliente", None)
        pagamento["valor"] = float(data.get("valor", None))
        pagamento["status"]  = data.get("status", None)
        pagamento["observacao"] = data.get("observacao", None)

        financial_repository.update_entry(pagamento_id, pagamento)

        return jsonify({"success": True, "pagamento": pagamento})

    except Exception as e:
        logger.error(f"Erro ao atualizar pagamento: {e}")
        return jsonify({"error": f"Erro ao processar dados: {str(e)}"}), 400

@app.route("/login.html")
def login_page():
    return render_template("login.html")
#ok
def update_payment_status(conta_id, new_status):
    """Atualiza o status de pagamento e propaga as alterações"""
    try:
        
        contas_repository = ContasPagarRepository()
        financial_repository = FinancialRepository()

        conta = contas_repository.get_by_id(conta_id)
        conta["status"] = new_status
        conta["updated_at"] = datetime.datetime.now().isoformat()

        for entry in financial_repository.get_by_conta_id(conta_id):
            if entry.get("conta_id") == conta_id:
                entry["status"] = new_status
                entry["updated_at"] = datetime.datetime.now().isoformat()
                financial_repository.update_entry(entry["id"], entry)

        contas_repository.update_conta(conta_id, conta)

        return True, None

    except Exception as e:
        logger.error(f"Erro ao atualizar status de pagamento: {e}")
        return False, str(e)
#ok
def init_admin_user():
    """Inicializa o usuário admin se não existir"""
    try:
        
        users = load_users()
        admin_exists = any(user.get("username") == "admin" for user in users if isinstance(user, dict))

        if not admin_exists:
            logger.info("Criando novo usuário admin")

            admin_user = {
                "username": "admin",
                "password_hash": generate_password_hash("Cubo2509&Sorocaba$"),
                "role": "admin"
            }

            save_user(admin_user)

            logger.info("Usuário admin criado com sucesso")
        else:
            logger.info("Usuário admin já existe")

    except Exception as e:
        logger.error(f"Erro ao criar usuário admin: {e}")
        raise
#ok
init_admin_user()
#ok
@app.route("/api/dashboard/stats", methods=["GET"])
def get_dashboard_stats():
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401

    try:
        # Obter parâmetros de período
        mes = request.args.get("mes", datetime.datetime.now().month)
        ano = request.args.get("ano", datetime.datetime.now().year)

        try:
            mes = int(mes)
            ano = int(ano)
            if mes < 1 or mes > 12:
                raise ValueError("Mês inválido")
        except ValueError as e:
            return jsonify({"error": f"Parâmetros inválidos: {str(e)}"}), 400

        orders_repository = OrdersRepository()
        contas_repository = ContasPagarRepository()

        # Carregar dados
        orders = orders_repository.get_all()
        contas = contas_repository.get_all()

        # Filtrar por período
        periodo = f"{ano}-{mes:02d}"
        orders_periodo = [
            order for order in orders
            if isinstance(order, dict) and order.get("data", "").startswith(periodo)
        ]

        # Calcular estatísticas
        total_orders = len(orders_periodo)
        orders_em_producao = sum(1 for order in orders_periodo if order.get("status") == "Em Produção")
        orders_aguardando = sum(
            1 for order in orders_periodo if order.get("status") in ["Aguardando Aprovação", "Aguardando Pagamento"])
        orders_finalizados = sum(1 for order in orders_periodo if order.get("status") == "Finalizada")
        orders_retirada = sum(1 for order in orders_periodo if order.get("status") == "Disponível para Retirada")

        # Calcular valores financeiros
        receita_total = sum(
            float(order.get("valor_total", 0)) for order in orders_periodo if order.get("status") == "Finalizada")
        custos_total = sum(
            float(order.get("custo", 0)) for order in orders_periodo if order.get("status") == "Finalizada")
        lucro_total = receita_total - custos_total

        # Valores a receber e a pagar
        valores_receber = sum(float(order.get("valor_restante", 0)) for order in orders_periodo
                              if order.get("status") not in ["Finalizada", "Cancelada"])

        valores_pagar = sum(float(conta.get("valor", 0)) for conta in contas
                            if isinstance(conta, dict)
                            and conta.get("status") == "Pendente"
                            and conta.get("vencimento", "").startswith(periodo))

        return jsonify({
            "total_orders": total_orders,
            "orders_em_producao": orders_em_producao,
            "orders_aguardando": orders_aguardando,
            "orders_finalizados": orders_finalizados,
            "orders_retirada": orders_retirada,
            "receita_total": receita_total,
            "custos_total": custos_total,
            "lucro_total": lucro_total,
            "valores_receber": valores_receber,
            "valores_pagar": valores_pagar,
            "periodo": {
                "mes": mes,
                "ano": ano
            }
        })

    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas do dashboard: {e}")
        return jsonify({"error": "Erro ao processar dados"}), 500

@app.route("/api/encerrar_mes", methods=["POST"])
def encerrar_mes():
    if not session.get("logged_in") or session.get("user_role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = request.json
        mes_atual = data.get("mes")
        ano_atual = data.get("ano")

        if not mes_atual or not ano_atual:
            return jsonify({"error": "Mês e ano são obrigatórios"}), 400

        proximo_mes = mes_atual + 1 if mes_atual < 12 else 1
        proximo_ano = ano_atual + 1 if mes_atual == 12 else ano_atual

        orders_repository = OrdersRepository()
        fechamento_repository = FechamentoRepository()
        orders = orders_repository.get_all()

        for order in orders:
            if isinstance(order, dict) and order.get("status") not in ["Finalizada", "Cancelada"]:
                order["data"] = f"{proximo_ano}-{proximo_mes:02d}-01"

        mes_fechamento = {
            "mes": mes_atual,
            "ano": ano_atual,
            "data_fechamento": datetime.datetime.now().isoformat(),
            "total_receitas": sum(float(order.get("valor_total", 0)) for order in orders
                                  if isinstance(order, dict) and order.get("status") == "Finalizada"),
            "total_custos": sum(float(order.get("custo", 0)) for order in orders
                                if isinstance(order, dict) and order.get("status") == "Finalizada"),
            "ordens_transferidas": len([order for order in orders
                                        if isinstance(order, dict) and order.get("status") not in ["Finalizada",
                                                                                                   "Cancelada"]])
        }

        fechamento_repository.insert_new(mes_fechamento)
        
        return jsonify({
            "success": True,
            "message": "Mês encerrado com sucesso",
            "fechamento": mes_fechamento
        })

    except Exception as e:
        logger.error(f"Erro ao encerrar mês: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/balancete/export", methods=["GET"])
def export_balancete():
    if not session.get("logged_in") or session.get("user_role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401

    try:
        mes = request.args.get("mes")
        ano = request.args.get("ano")

        if not mes or not ano:
            return jsonify({"error": "Mês e ano são obrigatórios"}), 400

        orders_repository = OrdersRepository()
        compras_repository = ComprasRepository()
        contas_repository = ContasPagarRepository()

        # Carregar dados
        orders = orders_repository.get_all()
        compras = compras_repository.get_all()
        contas = contas_repository.get_all()

        # Filtrar por período
        periodo = f"{ano}-{int(mes):02d}"

        # Calcular entradas
        entradas = []
        for order in orders:
            if isinstance(order, dict) and order.get("status") in ["Finalizada", "Disponível para Retirada"]:
                data = order.get("data", "")
                if data.startswith(periodo):
                    entradas.append({
                        "data": data,
                        "descricao": f"Ordem #{order['numero']} - {order['cliente']}",
                        "valor": float(order.get("valor_total", 0))
                    })

        # Calcular saídas
        saidas = []
        # Compras
        for compra in compras:
            if isinstance(compra, dict):
                data = compra.get("data", "")
                if data.startswith(periodo):
                    saidas.append({
                        "data": data,
                        "descricao": f"Compra: {compra['item']}",
                        "valor": float(compra.get("valor", 0))
                    })

        # Contas pagas
        for conta in contas:
            if isinstance(conta, dict) and conta.get("status") == "Pago":
                data = conta.get("data_pagamento", "")
                if data.startswith(periodo):
                    saidas.append({
                        "data": data,
                        "descricao": f"Conta: {conta['descricao']}",
                        "valor": float(conta.get("valor", 0))
                    })

        # Ordenar por data
        entradas.sort(key=lambda x: x["data"])
        saidas.sort(key=lambda x: x["data"])

        # Calcular totais
        total_entradas = sum(entrada["valor"] for entrada in entradas)
        total_saidas = sum(saida["valor"] for saida in saidas)
        saldo = total_entradas - total_saidas

        # Preparar dados para exportação
        export_data = {
            "periodo": {
                "mes": mes,
                "ano": ano
            },
            "entradas": entradas,
            "saidas": saidas,
            "totais": {
                "entradas": total_entradas,
                "saidas": total_saidas,
                "saldo": saldo
            },
            "gerado_em": datetime.datetime.now().isoformat(),
            "gerado_por": session.get("username")
        }

        return jsonify(export_data)

    except Exception as e:
        logger.error(f"Erro ao exportar balancete: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=True)
