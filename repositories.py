
import datetime
from database import get_db_connection


class RepositoryBase:
    def get_columns(self, cursor):
        return [desc[0] for desc in cursor.description]
    
    @staticmethod
    def insert_new(self, data: dict):
        raise NotImplementedError("This method should be implemented in subclasses.")

class BalanceteReposotory(RepositoryBase):
    def __init__(self):
        self.connection = get_db_connection()

    def get_all(self):
        cursor = self.connection.cursor()
        query = "SELECT id, type, value, reference_id, to_char(date, 'yyyy-mm-dd') as data, category FROM balancete;"
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        return results
    
    def insert_new(self, balancete_data: dict):
        cursor = self.connection.cursor()
        query = """
        INSERT INTO balancete (type, value, reference_id, date, category)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;"""
        
        cursor.execute(query, (
            balancete_data['type'], balancete_data['value'], balancete_data['reference_id'],
            balancete_data['date'], balancete_data['category']
        ))
        
        new_id = cursor.fetchone()[0]
        self.connection.commit()
        cursor.close()
        return new_id
    
    def get_balance(self):
        cursor = self.connection.cursor()
        query = """
        SELECT sum(value) as total,
        FROM public.balancete
        WHERE TYPE LIKE 'entrada'"""
        
        cursor.execute(query)
        result = cursor.fetchone()
        cursor.close()
        
        return result[0]

class ComprasRepository(RepositoryBase):
    def __init__(self):
        self.connection = get_db_connection()

    def get_all(self):
        cursor = self.connection.cursor()
        query = "SELECT id, item, fornecedor, valor, to_char(data, 'yyyy-mm-dd') as data, observacao, \"timestamp\" from compras;"
        cursor.execute(query)
        columns = self.get_columns(cursor)
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        cursor.close()
        return results
    
    def get_by_id(self, compra_id):
        cursor = self.connection.cursor()
        query = "SELECT id, item, fornecedor, valor, to_char(data, 'yyyy-mm-dd') as data, observacao, \"timestamp\" FROM compras WHERE id = %s;"
        cursor.execute(query, (compra_id,))
        columns = self.get_columns(cursor)
        result = cursor.fetchone()
        cursor.close()
        return dict(zip(columns, result)) if result else None

    def insert_new(self, compra_data: dict):
        cursor = self.connection.cursor()
        query = """
        INSERT INTO compras (item, fornecedor, valor, data, observacao, \"timestamp\")
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id;"""
        
        cursor.execute(query, (
            compra_data.get('item', 'null')
            , compra_data.get('fornecedor', 'null')
            , compra_data.get('valor', 'null')
            , compra_data.get('data', 'null')
            , compra_data.get('observacao', 'null')
            , compra_data.get('timestamp', datetime.datetime.now().isoformat())
        ))
        
        new_id = cursor.fetchone()[0]
        self.connection.commit()
        cursor.close()
        return new_id   
    
    def update_compra(self, compra_id, compra_data: dict):
        cursor = self.connection.cursor()
        query = """
        UPDATE compras SET
            item = %s,
            fornecedor = %s,
            valor = %s,
            data = %s,
            observacao = %s
        WHERE id = %s;"""
        
        cursor.execute(query, (
              compra_data.get('item', 'null')
            , compra_data.get('fornecedor', 'null')
            , compra_data.get('valor', 'null')
            , compra_data.get('data', 'null')
            , compra_data.get('observacao', 'null')
            , compra_id
        ))
        
        self.connection.commit()
        cursor.close()

class ContasPagarRepository(RepositoryBase):
    def __init__(self):
        self.connection = get_db_connection()

    def get_all(self):
        cursor = self.connection.cursor()
        query = "SELECT  id, descricao, valor, vencimento, status, compra_id, \"timestamp\" FROM contas_pagar;"
        cursor.execute(query)
        columns = self.get_columns(cursor)
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        cursor.close()
        return results
    
    def get_by_id(self, conta_id):
        cursor = self.connection.cursor()
        query = "SELECT id, descricao, valor, vencimento, status, compra_id, \"timestamp\" FROM contas_pagar WHERE id = %s;"
        cursor.execute(query, (conta_id,))
        columns = self.get_columns(cursor)
        result = cursor.fetchone()
        cursor.close()
        return dict(zip(columns, result)) if result else None
    
    def insert_new(self, conta_data: dict):
        cursor = self.connection.cursor()
        query = """
        INSERT INTO contas_pagar (descricao, valor, vencimento, status, compra_id, "timestamp")
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id;"""
        
        cursor.execute(query, (
            conta_data['descricao'], conta_data['valor'], conta_data['vencimento'],
            conta_data['status'], conta_data['compra_id'], conta_data['timestamp']
        ))
        
        new_id = cursor.fetchone()[0]
        self.connection.commit()
        cursor.close()
        return new_id
    
    def update_conta(self, conta_id, conta_data: dict):
        cursor = self.connection.cursor()
        query = """
        UPDATE contas_pagar SET
            descricao = %s,
            valor = %s,
            vencimento = %s,
            status = %s,
            compra_id = %s,
            "timestamp" = %s
        WHERE id = %s;"""
        
        cursor.execute(query, (
            conta_data['descricao'], conta_data['valor'], conta_data['vencimento'],
            conta_data['status'], conta_data['compra_id'], conta_data['timestamp'],
            conta_id
        ))
        
        self.connection.commit()
        cursor.close()

    def delete(self, conta_id):
        cursor = self.connection.cursor()
        query = "DELETE FROM contas_pagar WHERE id = %s;"
        cursor.execute(query, (conta_id,))
        self.connection.commit()
        cursor.close()

class FechamentoRepository(RepositoryBase):
    def __init__(self):
        self.connection = get_db_connection()

    def get_all(self):
        cursor = self.connection.cursor()
        query = """SELECT id, mes, ano, data_fechamento, total_receitas, total_custos, ordens_transferidas, "timestamp" FROM fechamento;"""
        cursor.execute(query)
        columns = self.get_columns(cursor)
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        cursor.close()
        return results
    
    def insert_new(self, fechamento_data: dict):
        cursor = self.connection.cursor()
        query = """
        INSERT INTO fechamento (mes, ano, data_fechamento, total_receitas, total_custos, ordens_transferidas, "timestamp")
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id;"""
        
        cursor.execute(query, (
            fechamento_data['mes']
            , fechamento_data['ano']
            , fechamento_data['data_fechamento']
            , fechamento_data['total_receitas']
            , fechamento_data['total_custos']
            , fechamento_data['ordens_transferidas']
            , fechamento_data.get('timestamp', datetime.datetime.now().isoformat())
        ))
        
        new_id = cursor.fetchone()[0]
        self.connection.commit()
        cursor.close()
        return new_id

class FinancialRepository(RepositoryBase):
    def __init__(self):
        self.connection = get_db_connection()

    def get_all(self):
        cursor = self.connection.cursor()
        query = "SELECT id, type, value, description, to_char(date, 'yyyy-mm-dd') as data, order_id FROM financial;"
        cursor.execute(query)
        columns = self.get_columns(cursor)
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        cursor.close()
        return results
    
    def get_by_id(self, financial_id):
        cursor = self.connection.cursor()
        query = "SELECT id, type, value, description, to_char(date, 'yyyy-mm-dd') as data, order_id FROM financial WHERE id = %s;"
        cursor.execute(query, (financial_id,))
        columns = self.get_columns(cursor)
        result = cursor.fetchone()
        cursor.close()
        return dict(zip(columns, result)) if result else None
    
    def get_by_conta_id(self, conta_id):
        cursor = self.connection.cursor()
        query = "SELECT id, type, value, description, to_char(date, 'yyyy-mm-dd') as data, order_id FROM financial WHERE conta_id = %s;"
        cursor.execute(query, (conta_id,))
        columns = self.get_columns(cursor)
        result = cursor.fetchall()
        cursor.close()
        return [dict(zip(columns, row)) for row in result]
    
    def insert_new(self, financial_data: dict):
        cursor = self.connection.cursor()
        query = """
        INSERT INTO financial (type, value, description, date, order_id, compra_id, conta_id, "timestamp")
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;"""
        
        cursor.execute(query, (
            financial_data['type']
            , financial_data['value']
            , financial_data['description']
            , financial_data['date']
            , financial_data.get('order_id', None)
            , financial_data.get('compra_id', None)
            , financial_data.get('conta_id', None)
            , financial_data.get('timestamp', datetime.datetime.now().isoformat())
        ))
        
        new_id = cursor.fetchone()[0]
        self.connection.commit()
        cursor.close()
        return new_id
    
    def get_balance(self):
        cursor = self.connection.cursor()
        query = """
        SELECT sum(value) as total,
        FROM public.financial
        WHERE TYPE LIKE 'entrada'"""
        
        cursor.execute(query)
        result = cursor.fetchone()
        cursor.close()
        
        return result[0]

class OrdersRepository(RepositoryBase):
    def __init__(self):
        self.connection = get_db_connection()

    def get_all(self):
        cursor = self.connection.cursor()
        query = """SELECT 
         id
            , cliente
            , vendedor
            , material
            , fornecedor
            , valor_total
            , custo
            , valor_entrada
            , valor_restante
            , valor_estimado_lucro
            , forma_pagamento
            , to_char(data, 'yyyy-mm-dd') as data
            , status
            , status_class 
              FROM orders;"""
        cursor.execute(query)
        columns = self.get_columns(cursor)
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        cursor.close()
        return results

    def get_order_by_id(self, order_id):
        cursor = self.connection.cursor()
        query = """
        SELECT id
            , cliente
            , vendedor
            , material
            , fornecedor
            , valor_total
            , custo
            , valor_entrada
            , valor_restante
            , valor_estimado_lucro
            , forma_pagamento
            , to_char(data, 'yyyy-mm-dd') as data
            , status
            , status_class 
        FROM orders WHERE id = %s;"""

        cursor.execute(query, (order_id,))
        columns = self.get_columns(cursor)
        result = cursor.fetchone()
        cursor.close()
        return dict(zip(columns, result))

    def insert_new(self, order_data: dict):
        cursor = self.connection.cursor()
        query = """
        INSERT INTO orders (
            cliente, vendedor, material, fornecedor, valor_total, custo,
            valor_entrada, valor_restante, valor_estimado_lucro, forma_pagamento,
            data, status, status_class
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, to_date(%s, 'yyyy-mm-dd'), %s, %s)
        RETURNING id;"""
        
        cursor.execute(query, (
            order_data['cliente'], order_data['vendedor'], order_data['material'],
            order_data['fornecedor'], order_data['valor_total'], order_data['custo'],
            order_data['valor_entrada'], order_data['valor_restante'],
            order_data['valor_estimado_lucro'], order_data['forma_pagamento'],
            order_data['data'], order_data['status'], order_data['status_class']
        ))
        
        new_id = cursor.fetchone()[0]
        self.connection.commit()
        cursor.close()
        return new_id

    def update_order(self, order_id, order_data: dict):
        cursor = self.connection.cursor()
        query = """
        UPDATE orders SET
            cliente = %s,
            vendedor = %s,
            material = %s,
            fornecedor = %s,
            valor_total = %s,
            custo = %s,
            valor_entrada = %s,
            valor_restante = %s,
            valor_estimado_lucro = %s,
            forma_pagamento = %s,
            data = %s,
            status = %s,
            status_class = %s
        WHERE id = %s;"""
        
        cursor.execute(query, (
            order_data['cliente'], order_data['vendedor'], order_data['material'],
            order_data['fornecedor'], order_data['valor_total'], order_data['custo'],
            order_data['valor_entrada'], order_data['valor_restante'],
            order_data['valor_estimado_lucro'], order_data['forma_pagamento'],
            order_data['data'], order_data['status'], order_data['status_class'],
            order_id
        ))
        
        self.connection.commit()
        cursor.close()

class UsersRepository(RepositoryBase):
    def __init__(self):
        self.connection = get_db_connection()

    def get_all(self):
        cursor = self.connection.cursor()
        query = "SELECT id, username, password_hash, role FROM users;"
        cursor.execute(query)
        columns = self.get_columns(cursor)
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        cursor.close()
        return results

    def get_by_id(self, user_id):
        cursor = self.connection.cursor()
        query = "SELECT id, username, password_hash, role FROM users WHERE id = %s;"
        cursor.execute(query, (user_id,))
        columns = self.get_columns(cursor)
        result = cursor.fetchone()
        cursor.close()
        return dict(zip(columns, result)) if result else None

    def insert_new(self, user_data: dict):
        cursor = self.connection.cursor()
        query = """
        INSERT INTO users (username, password_hash, role)
        VALUES (%s, %s, %s)
        RETURNING id;"""
        
        cursor.execute(query, (
            user_data['username'], user_data['password_hash'], user_data['role']
        ))
        
        new_id = cursor.fetchone()[0]
        self.connection.commit()
        cursor.close()
        return new_id


if __name__ == "__main__":
    print("Repository module is not meant to be run directly.")
    # Example usage