CREATE DATABASE IF NOT EXISTS ecommerce_db;

USE ecommerce_db;

SET time_zone = '-03:00';

-- Armazena os perfis de acesso usados no login.
CREATE TABLE tipos_cliente (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(50) NOT NULL UNIQUE
);

INSERT INTO tipos_cliente (nome) VALUES
('admin'),
('user');

-- Armazena os dados dos usuários cadastrados.
CREATE TABLE clientes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario VARCHAR(80) NOT NULL UNIQUE,
    senha_hash VARCHAR(255) NOT NULL,
    email VARCHAR(150),
    telefone VARCHAR(20),
    endereco VARCHAR(255),
    tipo_cliente_id INT NOT NULL,
    ativo BOOLEAN NOT NULL DEFAULT 1,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (tipo_cliente_id) REFERENCES tipos_cliente(id)
);

-- Armazena as categorias exibidas no catálogo.
CREATE TABLE categorias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL UNIQUE,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

INSERT INTO categorias (nome) VALUES
('Computadores'),
('Periféricos'),
('Acessórios'),
('Outros');

-- Armazena os produtos vendidos na loja.
CREATE TABLE produtos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(200) NOT NULL UNIQUE,
    descricao TEXT,
    ean VARCHAR(14) UNIQUE,
    preco DECIMAL(10,2) NOT NULL,
    estoque INT NOT NULL DEFAULT 0,
    categoria_id INT,
    data_producao DATE,
    data_validade DATE,
    imagem VARCHAR(255),
    ativo BOOLEAN NOT NULL DEFAULT 1,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id)
);

-- Insere um produto inicial para teste.
INSERT INTO produtos (
    nome,
    descricao,
    ean,
    preco,
    estoque,
    categoria_id,
    imagem
)
VALUES (
    'Notebook Acer Nitro V15',
    'Processador Intel Core i5 de 13ª geração e 16GB RAM DDR5 para jogos e multitarefas sem limites.',
    '4711121539909',
    5999.90,
    10,
    1,
    'https://t.ctcdn.com.br/M2rhXO2LbJjce5hsvVhU6Ys8les=/640x360/smart/i754568.png'
);

-- Armazena carrinhos e pedidos finalizados.
CREATE TABLE pedidos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cliente_id INT NOT NULL,
    status ENUM(
        'carrinho',
        'pendente',
        'confirmado',
        'enviado',
        'entregue',
        'cancelado'
    ) NOT NULL DEFAULT 'carrinho',
    total DECIMAL(10,2) NOT NULL DEFAULT 0,
    observacoes TEXT,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
);

-- Armazena os produtos adicionados em cada pedido.
CREATE TABLE itens_pedido (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pedido_id INT NOT NULL,
    produto_id INT NOT NULL,
    quantidade INT NOT NULL DEFAULT 1,
    preco_unitario DECIMAL(10,2) NOT NULL,
    valor_total DECIMAL(10,2) NOT NULL DEFAULT 0,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (pedido_id) REFERENCES pedidos(id),
    FOREIGN KEY (produto_id) REFERENCES produtos(id)
);
