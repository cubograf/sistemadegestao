from flask import Flask, jsonify, render_template, request, redirect, url_for, session, send_from_directory
from flask_cors import CORS
import json
import os
import datetime
import logging
from werkzeug.security import check_password_hash, generate_password_hash
from flask_session import Session

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Habilita CORS para todas as rotas
app.secret_key = "cubograf_secret_key"
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
Session(app)

# Caminhos para arquivos de dados
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
ORDERS_FILE = os.path.join(DATA_DIR, "sample_data.json")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
COMPRAS_FILE = os.path.join(DATA_DIR, "compras.json")
CONTAS_FILE = os.path.join(DATA_DIR, "contas_pagar.json")
FINANCIAL_FILE = os.path.join(DATA_DIR, "financial.json")
BALANCETE_FILE = os.path.join(DATA_DIR, "balancete.json")

# Garantir que os arquivos existam
for file_path in [ORDERS_FILE, COMPRAS_FILE, CONTAS_FILE, FINANCIAL_FILE, BALANCETE_FILE]:
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    if not os.path.exists(file_path):
        initial_data = [] if file_path != FINANCIAL_FILE and file_path != BALANCETE_FILE else {
            "entries": [],
            "balance": 0,
            "last_update": datetime.datetime.now().isoformat()
        }
        with open(file_path, 'w') as f:
            json.dump(initial_data, f, indent=2)


# Funções auxiliares para manipulação de dados
def load_data(file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        return [] if file_path != FINANCIAL_FILE and file_path != BALANCETE_FILE else {
            "entries": [],
            "balance": 0,
            "last_update": datetime.datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erro ao carregar dados de {file_path}: {e}")
        return [] if file_path != FINANCIAL_FILE and file_path != BALANCETE_FILE else {
            "entries": [],
            "balance": 0,
            "last_update": datetime.datetime.now().isoformat()
        }


def save_data(data, file_path):
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar dados em {file_path}: {e}")
        return False


def load_users():
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"Erro ao carregar usuários: {e}")
        return []


# Rotas de autenticação
@app.route("/")
def index():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return render_template("index.html")


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


# API para ordens de serviço
@app.route("/api/orders", methods=["GET"])
def get_orders():
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401

    orders = load_data(ORDERS_FILE)

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


@app.route("/api/orders", methods=["POST"])
def create_order():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Dados inválidos", "details": ["Nenhum dado recebido"]}), 400

        # Validação dos dados
        validation_errors = validate_order_data(data)
        if validation_errors:
            return jsonify({"error": "Dados inválidos", "details": validation_errors}), 400

        orders = load_data(ORDERS_FILE)

        # Gera um número sequencial para a ordem
        next_number = "01"
        if orders:
            valid_numbers = [int(order.get("numero", "0")) for order in orders if
                             isinstance(order, dict) and order.get("numero", "").isdigit()]
            if valid_numbers:
                next_number = str(max(valid_numbers) + 1).zfill(2)

        # Processa o campo material
        material_list = []
        if isinstance(data.get("material"), str):
            material_list = [item.strip() for item in data["material"].split(",") if item.strip()]
        elif isinstance(data.get("material"), list):
            material_list = data["material"]

        # Calcular valores automáticos
        valor_total = float(data.get("valor_total", 0))
        custo = float(data.get("custo", 0))
        valor_entrada = valor_total * 0.5  # 50% do valor total
        valor_restante = valor_total - valor_entrada
        valor_estimado_lucro = valor_total - custo

        # Cria a nova ordem
        new_order = {
            "numero": next_number,
            "cliente": data.get("cliente", "").strip(),
            "vendedor": data.get("vendedor", "").strip(),
            "material": material_list,
            "fornecedor": data.get("fornecedor", "").strip(),
            "valor_total": valor_total,
            "custo": custo,
            "valor_entrada": valor_entrada,
            "valor_restante": valor_restante,
            "valor_estimado_lucro": valor_estimado_lucro,
            "forma_pagamento": data.get("forma_pagamento", "PIX"),
            "data": data.get("data", datetime.datetime.now().strftime("%Y-%m-%d")),
            "status": data.get("status", "Aguardando Aprovação"),
            "status_class": f"status-{data.get('status', 'aguardando-aprovacao').lower().replace(' ', '-')}"
        }

        orders.append(new_order)

        if save_data(orders, ORDERS_FILE):
            # Atualizar dados financeiros
            update_financial_data(new_order)
            return jsonify({"success": True, "order": new_order})
        else:
            return jsonify({"error": "Erro ao salvar ordem", "details": ["Erro ao salvar no arquivo"]}), 500

    except Exception as e:
        logger.error(f"Erro ao criar ordem: {e}")
        return jsonify({"error": "Erro ao processar dados", "details": [str(e)]}), 400


def update_financial_data(order):
    try:
        # Carrega os dados financeiros
        financial_data = load_data(FINANCIAL_FILE)

        # Cria novo registro de entrada
        entry = {
            "id": len(financial_data["entries"]) + 1,
            "type": "entrada",
            "value": float(order["valor_total"]),
            "description": f"Ordem de Serviço #{order['numero']} - {order['cliente']}",
            "date": datetime.datetime.now().isoformat(),
            "order_id": order["numero"]
        }

        # Adiciona a entrada
        financial_data["entries"].append(entry)

        # Atualiza o saldo
        financial_data["balance"] = sum(
            entry["value"] if entry["type"] == "entrada" else -entry["value"]
            for entry in financial_data["entries"]
        )

        # Atualiza o balancete
        update_balancete(order["valor_total"], "entrada", order["numero"])

        # Salva os dados atualizados
        save_data(financial_data, FINANCIAL_FILE)
        return True

    except Exception as e:
        logger.error(f"Erro ao atualizar dados financeiros: {str(e)}")
        return False


def update_balancete(value, entry_type, reference_id):
    try:
        # Carrega os dados do balancete
        balancete = load_data(BALANCETE_FILE)

        # Cria novo registro
        entry = {
            "id": len(balancete["entries"]) + 1,
            "type": entry_type,
            "value": float(value),
            "reference_id": reference_id,
            "date": datetime.datetime.now().isoformat(),
            "category": "servico" if entry_type == "entrada" else "custo"
        }

        # Adiciona a entrada
        balancete["entries"].append(entry)

        # Atualiza o saldo
        balancete["balance"] = sum(
            entry["value"] if entry["type"] == "entrada" else -entry["value"]
            for entry in balancete["entries"]
        )

        # Salva os dados atualizados
        save_data(balancete, BALANCETE_FILE)
        return True

    except Exception as e:
        logger.error(f"Erro ao atualizar balancete: {str(e)}")
        return False


@app.route("/api/orders/<order_id>", methods=["PUT"])
def update_order(order_id):
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = request.json
        if not data:
            return jsonify({"error": "Dados inválidos"}), 400

        orders = load_data(ORDERS_FILE)

        # Encontra a ordem pelo número
        order_index = None
        for i, order in enumerate(orders):
            if isinstance(order, dict) and order.get("numero") == order_id:
                order_index = i
                break

        if order_index is None:
            return jsonify({"error": "Ordem não encontrada"}), 404

        # Validação dos campos obrigatórios
        required_fields = ["cliente", "vendedor", "material", "valor_total"]
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return jsonify({"error": f"Campos obrigatórios faltando: {', '.join(missing_fields)}"}), 400

        # Validação dos valores numéricos
        try:
            valor_total = float(data.get("valor_total", orders[order_index].get("valor_total", 0)))
            custo = float(data.get("custo", orders[order_index].get("custo", 0)))
            if valor_total < 0 or custo < 0:
                return jsonify({"error": "Valores não podem ser negativos"}), 400
        except ValueError:
            return jsonify({"error": "Valores numéricos inválidos"}), 400

        # Processa o campo material
        material_list = []
        if isinstance(data["material"], str):
            material_list = [item.strip() for item in data["material"].split(",") if item.strip()]
        elif isinstance(data["material"], list):
            material_list = [item.strip() for item in data["material"] if item.strip()]

        if not material_list:
            return jsonify({"error": "Lista de materiais inválida"}), 400

        # Calcular valores automáticos
        valor_entrada = valor_total * 0.5  # 50% do valor total
        valor_restante = valor_total - valor_entrada
        valor_estimado_lucro = valor_total - custo

        # Atualiza a ordem
        updated_order = orders[order_index].copy()
        updated_order.update({
            "cliente": data.get("cliente", "").strip(),
            "vendedor": data.get("vendedor", "").strip(),
            "material": material_list,
            "fornecedor": data.get("fornecedor", "").strip(),
            "valor_total": valor_total,
            "custo": custo,
            "valor_entrada": valor_entrada,
            "valor_restante": valor_restante,
            "valor_estimado_lucro": valor_estimado_lucro,
            "forma_pagamento": data.get("forma_pagamento", updated_order.get("forma_pagamento", "PIX")),
            "data": data.get("data", updated_order.get("data", "")),
            "status": data.get("status", updated_order.get("status", "Aguardando Aprovação"))
        })

        orders[order_index] = updated_order

        if save_data(orders, ORDERS_FILE):
            return jsonify({"success": True, "order": updated_order})
        else:
            return jsonify({"error": "Erro ao salvar ordem"}), 500

    except Exception as e:
        logger.error(f"Erro ao atualizar ordem: {e}")
        return jsonify({"error": f"Erro ao processar dados: {str(e)}"}), 400


# API para compras
@app.route("/api/compras", methods=["GET"])
def get_compras():
    if not session.get("logged_in") or session.get("user_role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401

    compras = load_data(COMPRAS_FILE)
    return jsonify(compras)


@app.route("/api/compras", methods=["POST"])
def create_compra():
    if not session.get("logged_in") or session.get("user_role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = request.json
        if not data:
            return jsonify({"error": "Dados inválidos", "details": ["Nenhum dado recebido"]}), 400

        # Validação básica
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

        compras = load_data(COMPRAS_FILE)

        # Gera um ID sequencial para a compra
        next_id = "1"
        if compras:
            valid_ids = [int(compra.get("id", "0")) for compra in compras if
                         isinstance(compra, dict) and compra.get("id", "").isdigit()]
            if valid_ids:
                next_id = str(max(valid_ids) + 1)

        # Cria a nova compra
        new_compra = {
            "id": next_id,
            "item": data["item"].strip(),
            "fornecedor": data["fornecedor"].strip(),
            "valor": valor,
            "data": data["data"],
            "observacao": data.get("observacao", "").strip(),
            "timestamp": datetime.datetime.now().isoformat()
        }

        compras.append(new_compra)

        # Salvar a compra
        if not save_data(compras, COMPRAS_FILE):
            return jsonify({"error": "Erro ao salvar compra"}), 500

        # Criar conta a pagar
        try:
            contas = load_data(CONTAS_FILE)
            next_conta_id = "1"
            if contas:
                valid_conta_ids = [int(conta.get("id", "0")) for conta in contas if
                                   isinstance(conta, dict) and conta.get("id", "").isdigit()]
                if valid_conta_ids:
                    next_conta_id = str(max(valid_conta_ids) + 1)

            new_conta = {
                "id": next_conta_id,
                "descricao": f"Compra #{new_compra['id']} - {new_compra['item']}",
                "valor": new_compra["valor"],
                "vencimento": new_compra["data"],
                "status": "Pendente",
                "compra_id": new_compra["id"],
                "timestamp": datetime.datetime.now().isoformat()
            }

            contas.append(new_conta)
            save_data(contas, CONTAS_FILE)

            # Atualizar dados financeiros
            financial_data = load_data(FINANCIAL_FILE)

            # Registrar despesa
            expense_entry = {
                "id": str(len(financial_data["entries"]) + 1),
                "type": "expense",
                "description": f"Compra #{new_compra['id']} - {new_compra['item']}",
                "value": new_compra["valor"],
                "date": new_compra["data"],
                "status": "Pendente",
                "compra_id": new_compra["id"],
                "conta_id": new_conta["id"],
                "timestamp": datetime.datetime.now().isoformat()
            }

            financial_data["entries"].append(expense_entry)
            save_data(financial_data, FINANCIAL_FILE)

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


@app.route("/api/compras/<compra_id>", methods=["PUT"])
def update_compra(compra_id):
    if not session.get("logged_in") or session.get("user_role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = request.json
        if not data:
            return jsonify({"error": "Dados inválidos"}), 400

        compras = load_data(COMPRAS_FILE)

        # Encontra a compra pelo ID
        compra_index = None
        for i, compra in enumerate(compras):
            if isinstance(compra, dict) and compra.get("id") == compra_id:
                compra_index = i
                break

        if compra_index is None:
            return jsonify({"error": "Compra não encontrada"}), 404

        # Atualiza a compra
        updated_compra = compras[compra_index].copy()
        updated_compra.update({
            "item": data.get("item", updated_compra.get("item", "")),
            "fornecedor": data.get("fornecedor", updated_compra.get("fornecedor", "")),
            "valor": float(data.get("valor", updated_compra.get("valor", 0))),
            "data": data.get("data", updated_compra.get("data", "")),
            "observacao": data.get("observacao", updated_compra.get("observacao", ""))
        })

        compras[compra_index] = updated_compra

        if save_data(compras, COMPRAS_FILE):
            return jsonify({"success": True, "compra": updated_compra})
        else:
            return jsonify({"error": "Erro ao salvar compra"}), 500

    except Exception as e:
        logger.error(f"Erro ao atualizar compra: {e}")
        return jsonify({"error": f"Erro ao processar dados: {str(e)}"}), 400


# API para contas a pagar
@app.route("/api/contas_pagar", methods=["GET"])
def get_contas_pagar():
    if not session.get("logged_in") or session.get("user_role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401

    try:
        contas = load_data(CONTAS_FILE)
        return jsonify(contas)
    except Exception as e:
        logger.error(f"Erro ao buscar contas a pagar: {e}")
        return jsonify({"error": "Erro ao buscar dados"}), 500


@app.route("/api/contas_pagar", methods=["POST"])
def criar_conta_pagar():
    if not session.get("logged_in") or session.get("user_role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = request.json
        if not data:
            return jsonify({"error": "Dados inválidos"}), 400

        # Validar campos obrigatórios
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
        contas = load_data(CONTAS_FILE)

        # Gerar ID único
        next_id = str(len(contas) + 1)

        # Criar nova conta
        nova_conta = {
            "id": next_id,
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

        # Adicionar à lista e salvar
        contas.append(nova_conta)
        if save_data(contas, CONTAS_FILE):
            # Atualizar balancete
            balancete = load_data(BALANCETE_FILE)
            balancete["entries"].append({
                "tipo": "saida",
                "valor": nova_conta["valor"],
                "descricao": nova_conta["descricao"],
                "data": nova_conta["vencimento"],
                "categoria": nova_conta["categoria"],
                "referencia": nova_conta["id"]
            })
            save_data(balancete, BALANCETE_FILE)

            return jsonify({"success": True, "conta": nova_conta})
        else:
            return jsonify({"error": "Erro ao salvar conta"}), 500

    except Exception as e:
        logger.error(f"Erro ao criar conta a pagar: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/contas_pagar/<conta_id>", methods=["PUT"])
def atualizar_conta_pagar(conta_id):
    if not session.get("logged_in") or session.get("user_role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = request.json
        if not data:
            return jsonify({"error": "Dados inválidos"}), 400

        # Carregar contas
        contas = load_data(CONTAS_FILE)

        # Encontrar conta
        conta_index = None
        for i, conta in enumerate(contas):
            if isinstance(conta, dict) and str(conta.get("id")) == str(conta_id):
                conta_index = i
                break

        if conta_index is None:
            return jsonify({"error": "Conta não encontrada"}), 404

        # Atualizar conta
        conta_atual = contas[conta_index]
        conta_atualizada = conta_atual.copy()
        conta_atualizada.update({
            "descricao": data.get("descricao", conta_atual["descricao"]),
            "valor": float(data.get("valor", conta_atual["valor"])),
            "vencimento": data.get("vencimento", conta_atual["vencimento"]),
            "categoria": data.get("categoria", conta_atual.get("categoria")),
            "forma_pagamento": data.get("forma_pagamento", conta_atual.get("forma_pagamento")),
            "status": data.get("status", conta_atual["status"]),
            "observacao": data.get("observacao", conta_atual.get("observacao", "")),
            "atualizado_em": datetime.datetime.now().isoformat(),
            "atualizado_por": session.get("username")
        })

        contas[conta_index] = conta_atualizada

        if save_data(contas, CONTAS_FILE):
            # Atualizar balancete se necessário
            if conta_atualizada["valor"] != conta_atual["valor"]:
                balancete = load_data(BALANCETE_FILE)
                for entry in balancete["entries"]:
                    if entry.get("referencia") == conta_id:
                        entry["valor"] = conta_atualizada["valor"]
                        break
                save_data(balancete, BALANCETE_FILE)

            return jsonify({"success": True, "conta": conta_atualizada})
        else:
            return jsonify({"error": "Erro ao salvar alterações"}), 500

    except Exception as e:
        logger.error(f"Erro ao atualizar conta a pagar: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/contas_pagar/<conta_id>", methods=["DELETE"])
def excluir_conta_pagar(conta_id):
    if not session.get("logged_in") or session.get("user_role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401

    try:
        # Carregar contas
        contas = load_data(CONTAS_FILE)

        # Encontrar e remover conta
        conta = None
        contas_atualizadas = []
        for c in contas:
            if isinstance(c, dict) and str(c.get("id")) == str(conta_id):
                conta = c
            else:
                contas_atualizadas.append(c)

        if not conta:
            return jsonify({"error": "Conta não encontrada"}), 404

        if save_data(contas_atualizadas, CONTAS_FILE):
            # Remover do balancete
            balancete = load_data(BALANCETE_FILE)
            balancete["entries"] = [
                entry for entry in balancete["entries"]
                if entry.get("referencia") != conta_id
            ]
            save_data(balancete, BALANCETE_FILE)

            return jsonify({"success": True, "message": "Conta excluída com sucesso"})
        else:
            return jsonify({"error": "Erro ao excluir conta"}), 500

    except Exception as e:
        logger.error(f"Erro ao excluir conta a pagar: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/contas_pagar/<conta_id>/pagar", methods=["POST"])
def pagar_conta(conta_id):
    if not session.get("logged_in") or session.get("user_role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401

    try:
        # Carregar contas
        contas = load_data(CONTAS_FILE)

        # Encontrar conta
        conta = None
        for c in contas:
            if isinstance(c, dict) and str(c.get("id")) == str(conta_id):
                if c["status"] == "Pago":
                    return jsonify({"error": "Conta já está paga"}), 400

                c["status"] = "Pago"
                c["data_pagamento"] = datetime.datetime.now().isoformat()
                c["pago_por"] = session.get("username")
                conta = c
                break

        if not conta:
            return jsonify({"error": "Conta não encontrada"}), 404

        if save_data(contas, CONTAS_FILE):
            # Atualizar financeiro
            financial_data = load_data(FINANCIAL_FILE)
            financial_data["entries"].append({
                "tipo": "saida",
                "valor": conta["valor"],
                "descricao": f"Pagamento: {conta['descricao']}",
                "data": conta["data_pagamento"],
                "referencia": conta["id"]
            })
            save_data(financial_data, FINANCIAL_FILE)

            return jsonify({"success": True, "conta": conta})
        else:
            return jsonify({"error": "Erro ao salvar alterações"}), 500

    except Exception as e:
        logger.error(f"Erro ao pagar conta: {e}")
        return jsonify({"error": str(e)}), 500


# API para dados financeiros
@app.route("/api/financeiro/dados", methods=["GET"])
def get_dados_financeiros():
    if not session.get("logged_in") or session.get("user_role") != "admin":
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

        # Carregar dados
        orders = load_data(ORDERS_FILE)
        compras = load_data(COMPRAS_FILE)
        contas = load_data(CONTAS_FILE)

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

        # Log para debug
        logger.info(f"""
        Dados financeiros calculados para {periodo}:
        - Receita Total: {receita_total}
        - Custos Total: {custos_total}
        - Saídas Compras: {saidas_compras}
        - Saídas Contas: {saidas_contas}
        - Saídas Total: {saidas_total}
        - Lucro Líquido: {lucro_liquido}
        - Valores a Receber: {valores_receber}
        """)

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

        # Carregar pedidos
        orders = load_data(ORDERS_FILE)

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

        # Salvar alterações
        if save_data(orders, ORDERS_FILE):
            return jsonify({
                "success": True,
                "message": f"Transferidos {len(pedidos_transferir)} pedidos",
                "pedidos": pedidos_transferir
            })
        else:
            return jsonify({"error": "Erro ao salvar alterações"}), 500

    except Exception as e:
        logger.error(f"Erro ao transferir pedidos: {e}")
        return jsonify({"error": f"Erro ao processar dados: {str(e)}"}), 400


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

        # Carregar pagamentos
        pagamentos = load_data(FINANCIAL_FILE)

        # Filtrar por período
        periodo = f"{ano}-{mes.zfill(2)}"
        pagamentos_periodo = [
            pagamento for pagamento in pagamentos.get("entries", [])
            if isinstance(pagamento, dict) and pagamento.get("date", "").startswith(periodo)
        ]

        return jsonify(pagamentos_periodo)

    except Exception as e:
        logger.error(f"Erro ao buscar pagamentos: {e}")
        return jsonify({"error": f"Erro ao processar dados: {str(e)}"}), 400


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

        # Carregar pagamentos existentes
        pagamentos = load_data(FINANCIAL_FILE)

        # Gerar ID sequencial
        next_id = "1"
        if pagamentos.get("entries", []):
            valid_ids = [int(pag.get("id", "0")) for pag in pagamentos.get("entries", []) if
                         isinstance(pag, dict) and pag.get("id", "").isdigit()]
            if valid_ids:
                next_id = str(max(valid_ids) + 1)

        # Criar novo pagamento
        new_pagamento = {
            "id": next_id,
            "date": data.get("data"),
            "cliente": data.get("cliente"),
            "valor": float(data.get("valor")),
            "status": data.get("status"),
            "observacao": data.get("observacao", "")
        }

        pagamentos.get("entries", []).append(new_pagamento)

        if save_data(pagamentos, FINANCIAL_FILE):
            return jsonify({"success": True, "pagamento": new_pagamento})
        else:
            return jsonify({"error": "Erro ao salvar pagamento"}), 500

    except Exception as e:
        logger.error(f"Erro ao criar pagamento: {e}")
        return jsonify({"error": f"Erro ao processar dados: {str(e)}"}), 400


@app.route("/api/financeiro/pagamentos/<pagamento_id>", methods=["PUT"])
def update_pagamento(pagamento_id):
    if not session.get("logged_in") or session.get("user_role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = request.json
        if not data:
            return jsonify({"error": "Dados inválidos"}), 400

        # Carregar pagamentos
        pagamentos = load_data(FINANCIAL_FILE)

        # Encontrar pagamento
        pagamento_index = None
        for i, pagamento in enumerate(pagamentos.get("entries", [])):
            if isinstance(pagamento, dict) and pagamento.get("id") == pagamento_id:
                pagamento_index = i
                break

        if pagamento_index is None:
            return jsonify({"error": "Pagamento não encontrado"}), 404

        # Atualizar pagamento
        updated_pagamento = pagamentos.get("entries", [])[pagamento_index].copy()
        updated_pagamento.update({
            "date": data.get("date", updated_pagamento.get("date")),
            "cliente": data.get("cliente", updated_pagamento.get("cliente")),
            "valor": float(data.get("valor", updated_pagamento.get("valor"))),
            "status": data.get("status", updated_pagamento.get("status")),
            "observacao": data.get("observacao", updated_pagamento.get("observacao", ""))
        })

        pagamentos.get("entries", [])[pagamento_index] = updated_pagamento

        if save_data(pagamentos, FINANCIAL_FILE):
            return jsonify({"success": True, "pagamento": updated_pagamento})
        else:
            return jsonify({"error": "Erro ao salvar pagamento"}), 500

    except Exception as e:
        logger.error(f"Erro ao atualizar pagamento: {e}")
        return jsonify({"error": f"Erro ao processar dados: {str(e)}"}), 400


# Rota para login
@app.route("/login.html")
def login_page():
    return render_template("login.html")


def update_payment_status(conta_id, new_status):
    """Atualiza o status de pagamento e propaga as alterações"""
    try:
        # Carregar dados
        contas = load_data(CONTAS_FILE)
        financial_data = load_data(FINANCIAL_FILE)

        # Encontrar a conta
        conta = None
        for c in contas:
            if c.get("id") == conta_id:
                conta = c
                break

        if not conta:
            raise ValueError("Conta não encontrada")

        # Atualizar status da conta
        old_status = conta["status"]
        conta["status"] = new_status
        conta["updated_at"] = datetime.datetime.now().isoformat()

        # Atualizar entrada financeira correspondente
        for entry in financial_data.get("entries", []):
            if entry.get("conta_id") == conta_id:
                entry["status"] = new_status
                entry["updated_at"] = datetime.datetime.now().isoformat()

                # Atualizar saldo se necessário
                if old_status != "Pago" and new_status == "Pago":
                    financial_data["balance"] -= entry["value"]
                elif old_status == "Pago" and new_status != "Pago":
                    financial_data["balance"] += entry["value"]

        # Salvar alterações
        save_data(contas, CONTAS_FILE)
        save_data(financial_data, FINANCIAL_FILE)

        return True, None

    except Exception as e:
        logger.error(f"Erro ao atualizar status de pagamento: {e}")
        return False, str(e)


def init_admin_user():
    """Inicializa o usuário admin se não existir"""
    try:
        # Garante que o diretório data existe
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
            logger.info("Diretório de dados criado")

        # Cria arquivo de usuários se não existir
        if not os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'w') as f:
                json.dump([], f)
            logger.info("Arquivo de usuários criado")

        users = load_users()
        admin_exists = any(user.get("username") == "admin" for user in users if isinstance(user, dict))

        if not admin_exists:
            logger.info("Criando novo usuário admin")
            # Criar senha hash
            password = "admin123"
            password_hash = generate_password_hash(password)

            admin_user = {
                "username": "admin",
                "password_hash": password_hash,
                "role": "admin"
            }

            users = [admin_user]  # Substitui a lista existente

            # Salva no arquivo
            with open(USERS_FILE, 'w') as f:
                json.dump(users, f, indent=2)

            logger.info("Usuário admin criado com sucesso")
            logger.info(f"Credenciais - Usuário: admin, Senha: {password}")
        else:
            logger.info("Usuário admin já existe")

    except Exception as e:
        logger.error(f"Erro ao criar usuário admin: {e}")
        raise


# Adiciona a chamada para inicializar o usuário admin logo após a definição do app
init_admin_user()


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

        # Carregar dados
        orders = load_data(ORDERS_FILE)
        financial_data = load_data(FINANCIAL_FILE)
        contas = load_data(CONTAS_FILE)

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

        # Calcular próximo mês e ano
        proximo_mes = mes_atual + 1 if mes_atual < 12 else 1
        proximo_ano = ano_atual + 1 if mes_atual == 12 else ano_atual

        # Carregar dados
        orders = load_data(ORDERS_FILE)
        financial_data = load_data(FINANCIAL_FILE)

        # Transferir ordens não finalizadas para o próximo mês
        for order in orders:
            if isinstance(order, dict) and order.get("status") not in ["Finalizada", "Cancelada"]:
                order["data"] = f"{proximo_ano}-{proximo_mes:02d}-01"

        # Registrar fechamento no financeiro
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

        if "fechamentos" not in financial_data:
            financial_data["fechamentos"] = []
        financial_data["fechamentos"].append(mes_fechamento)

        # Salvar alterações
        if save_data(orders, ORDERS_FILE) and save_data(financial_data, FINANCIAL_FILE):
            return jsonify({
                "success": True,
                "message": "Mês encerrado com sucesso",
                "fechamento": mes_fechamento
            })
        else:
            return jsonify({"error": "Erro ao salvar dados"}), 500

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

        # Carregar dados
        balancete = load_data(BALANCETE_FILE)
        orders = load_data(ORDERS_FILE)
        compras = load_data(COMPRAS_FILE)
        contas = load_data(CONTAS_FILE)

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
