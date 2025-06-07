CREATE TABLE balancete (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50),
    value DOUBLE PRECISION,
    reference_id INT,
    date DATE,
    category VARCHAR(50)
);

CREATE TABLE compras (
    id SERIAL PRIMARY KEY,
    item VARCHAR(500),
    fornecedor VARCHAR(500),
    valor DOUBLE PRECISION,
    data DATE,
    observacao TEXT,
    timestamp TIMESTAMP
);

CREATE TABLE contas_pagar (
    id SERIAL PRIMARY KEY,
    descricao TEXT,
    valor DOUBLE PRECISION,
    vencimento DATE,
    status VARCHAR(50),
    compra_id INTEGER,
    updated_at TIMESTAMP,
    timestamp TIMESTAMP,
    pago_por VARCHAR(500),
    data_pagamento TIMESTAMP
);

CREATE TABLE financial (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50),
    value DOUBLE PRECISION,
    description TEXT,
    date TIMESTAMP,
    order_id INTEGER,
    compra_id integer, 
	conta_id integer,
    updated_at TIMESTAMP,
    timestamp TIMESTAMP
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    cliente VARCHAR(500),
    vendedor VARCHAR(500),
    material TEXT,
    fornecedor VARCHAR(500),
    valor_total DOUBLE PRECISION,
    custo DOUBLE PRECISION,
    valor_entrada DOUBLE PRECISION,
    valor_restante DOUBLE PRECISION,
    valor_estimado_lucro DOUBLE PRECISION,
    forma_pagamento VARCHAR(50),
    data DATE,
    status VARCHAR(50),
    status_class VARCHAR(100)
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(500),
    password_hash VARCHAR(500),
    role VARCHAR(100)
);

CREATE TABLE fechamento (
    id SERIAL PRIMARY KEY,
    mes integer,
    ano integer,
    data_fechamento DATE,
    total_receitas DOUBLE PRECISION,
    total_custos DOUBLE PRECISION,
    ordens_transferidas integer,
    timestamp TIMESTAMP
)