# CRUD Flask simples
Projeto CRUD acadêmico de e-commerce com login, cadastro, catálogo, categorias, carrinho e pedidos.

## Tecnologias
- Flask
- MySQL
- SQLAlchemy
- WTForms

## Como inicializar o projeto
1. Crie e ative o ambiente virtual.

WINDOWS:
> python -m venv .venv
> .\.venv\Scripts\activate

LINUX:
> python3 -m venv venv
> source venv/bin/activate

2. Crie o banco de dados utilizando o código SQL disponivel no arquivo `schema.sql`
OBS: Caso o banco de dados não seja criado, o projeto não será inicializado e retornará um erro, então certifique-se de criar o banco antes de executá-lo.

3. Instale as dependências.

> pip install -r requirements.txt

4. Configure as credenciais do seu MySQL no arquivo `.env`.

Valores padrão:

- host: `localhost`
- porta: `3306`
- usuário: `SEU_USUARIO_SQL`
- senha: defina em `SUA_SENHA_SQL`
- banco: `ecommerce_db`

5. Rode o sistema.
> python app.py

6. Acesse no navegador o seguinte endereço:
> http://localhost:5000


## Acessos de teste
Ao inicializar o arquivo `app.py`, serão criados 2 usuários padrão para testes, sendo eles:

Administrador:
- usuário: `admin`
- senha: `admin123`

Cliente:
- usuário: `cliente`
- senha: `cliente123`

## Estrutura
app.py              inicia o Flask
config.py           carrega configurações do MySQL e da sessão
forms.py            define formulários e validações
models.py           define tabelas, banco e dados iniciais
routes.py           concentra rotas e regras do sistema
templates/          guarda páginas HTML
static/css/         guarda estilos organizados por módulo
static/js/          guarda animações, validações e segurança da sessão
migrations/         guarda SQL de referência


## Funcionalidades
- Login e cadastro de usuários.
- Sessão por navegador, com timeout por inatividade.
- Bloqueio simples para evitar duas abas logadas ao mesmo tempo.
- Listagem, busca e filtro de produtos.
- Cadastro, edição e exclusão lógica de produtos.
- Listagem de produtos inativos para reativação pelo administrador.
- Listagem, cadastro, edição e exclusão de categorias.
- Carrinho com adicionar, atualizar, remover e finalizar pedido.
- Histórico em "Meus Pedidos".
- Permissão de administrador para alterar cadastros.
