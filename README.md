# CYBERFLOW
Sistema CRUD web acadêmico desenvolvido para gerenciamento de pedidos e controle operacional de uma loja de equipamentos e serviços de tecnologia.

## Objetivo
Centralizar o gerenciamento de clientes, produtos, pedidos e usuários em uma única plataforma, oferecendo maior controle sobre o fluxo de vendas e acompanhamento das operações do negócio.

## Principais Funcionalidades

- Autenticação de usuários com controle de sessão.
- Cadastro e gerenciamento de clientes.
- Cadastro e manutenção de produtos.
- Controle de categorias de produtos.
- Registro e acompanhamento de pedidos.
- Carrinho de compras integrado ao fluxo de vendas.
- Painel administrativo para gerenciamento das informações do sistema.
- Proteção contra envio indevido de formulários através de CSRF.

## Tecnologias Utilizadas

**Backend**

- Python 3
- Flask
- SQLAlchemy
- Flask-Login
- Flask-WTF

**Banco de Dados**

- MySQL

**Frontend**

- HTML5
- CSS3
- JavaScript

## Como inicializar o projeto

**1.** Crie e ative o ambiente virtual.

**WINDOWS:**

```
python -m venv .venv
.\.venv\Scripts\activate
```

LINUX:

```
python3 -m venv venv
source venv/bin/activate
```

**2.** Crie o banco de dados

Crie o banco de dados utilizando o script SQL disponibilizado no arquivo "schema.sql".

«Importante: o banco de dados deve ser criado antes da execução da aplicação. Caso contrário, o sistema não será inicializado corretamente.»

**3.** Instalar as dependências

> pip install -r requirements.txt

**4.** Configurar as credenciais do MySQL
Configure as credenciais de acesso ao banco de dados no arquivo ".env".

Valores padrão:

- host: `localhost`
- porta: `3306`
- usuário: `SEU_USUARIO_SQL`
- senha: defina em `SUA_SENHA_SQL`
- banco: `ecommerce_db`

«Substitua os valores de usuário e senha pelas credenciais configuradas em sua instalação do MySQL.»

**5.** Executar a aplicação
   
```
python app.py
```

**6.** Acessar o sistema
Após a inicialização, acesse o endereço abaixo no navegador ou utilize a URL exibida no terminal:
   
```
http://localhost:5000
```

## Credenciais de teste
Na primeira execução da aplicação, serão criados automaticamente dois usuários para fins de teste.

**Administrador:**
- usuário: `admin`
- senha: `admin123`

**Cliente:**
- usuário: `cliente`
- senha: `cliente123`

## Possíveis Evoluções

- Controle de estoque em tempo real.
- Dashboard com indicadores gerenciais.
- Integração com meios de pagamento.
- Emissão de relatórios em PDF.
- Sistema de notificações para pedidos.

## Estrutura
- app.py - inicia o Flask.
- config.py - carrega configurações do MySQL e da sessão.
- forms.py - define formulários e validações.
- models.py - define tabelas, banco e dados iniciais.
- routes.py - concentra rotas e regras do sistema.
- templates/ - guarda as páginas HTML.
- static/css/ - guarda estilos organizados por módulo.
- static/js/ - guarda animações, validações e segurança da sessão.
- migrations/ - guarda o código SQL de referência.
