from decimal import Decimal
from functools import wraps
from hmac import compare_digest
from secrets import token_urlsafe
from time import time
from flask import abort, current_app, flash, redirect, render_template, request, session, url_for
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from forms import CategoryForm, LoginForm, ProductForm, RegisterForm, carregar_categorias
from models import Category, ClientType, Order, OrderItem, Product, User, get_db


def login_required(view):
    # Exige autenticação antes de liberar rotas protegidas.
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "usuario_id" not in session:
            return redirecionar_para_login()
        return view(*args, **kwargs)

    return wrapped_view


def admin_required(view):
    # Restringe alterações de cadastro aos administradores.
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "usuario_id" not in session:
            return redirecionar_para_login()

        if session.get("tipo") != "admin":
            flash("Apenas administradores podem alterar cadastros.", "error")
            return redirect(url_for("listar_produtos"))

        return view(*args, **kwargs)

    return wrapped_view


def register_routes(app):
    app.template_filter("brl")(formatar_brl)

    @app.before_request
    def validar_csrf():
        # Protege formulários POST contra envios externos.
        if request.method != "POST":
            return None

        token_sessao = session.get("_csrf_token", "")
        token_formulario = request.form.get("csrf_token", "")

        if token_sessao and compare_digest(token_sessao, token_formulario):
            return None

        flash("Formulário expirado. Tente novamente.", "error")
        return redirect(request.referrer or url_for("login"))

    @app.before_request
    def controlar_timeout():
        # Encerra a sessão quando o usuário passa do limite de inatividade.
        if request.endpoint in {"login", "register", "logout", "static"} or request.endpoint is None:
            return None

        if "usuario_id" not in session:
            return None

        agora = time()
        ultimo_acesso = session.get("ultimo_acesso")
        limite = current_app.config["INACTIVITY_TIMEOUT_SECONDS"]

        if ultimo_acesso and agora - ultimo_acesso > limite:
            session.clear()
            flash("Sessão expirada por inatividade. Entre novamente.", "error")
            return redirect(url_for("login"))

        session["ultimo_acesso"] = agora
        return None

    @app.context_processor
    def inject_template_data():
        usuario_id = session.get("usuario_id")
        total = contar_itens_carrinho(usuario_id) if usuario_id else 0
        return {"cart_count": total, "csrf_token": gerar_csrf_token}

    @app.route("/")
    def home():
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if "usuario_id" in session:
            return redirect(url_for("listar_produtos"))

        form = LoginForm(request.form if request.method == "POST" else None)
        proximo = request.args.get("next") or request.form.get("next")

        if request.method == "POST" and form.validate():
            db = get_db()
            usuario = db.query(User).filter_by(usuario=form.usuario.data).first()

            if usuario and usuario.ativo and usuario.senha_confere(form.senha.data):
                iniciar_sessao(usuario)
                flash(f"Bem-vindo, {usuario.usuario}!", "success")
                return redirect(destino_seguro(proximo))

            flash("Usuário ou senha inválidos.", "error")

        return render_template("auth/login.html", form=form, next_url=proximo or "")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        form = RegisterForm(request.form if request.method == "POST" else None)

        if request.method == "POST" and form.validate():
            if form.senha.data != form.confirmar_senha.data:
                flash("As senhas não coincidem.", "error")
                return render_template("auth/register.html", form=form)

            db = get_db()
            existente = db.query(User).filter_by(usuario=form.usuario.data).first()

            if existente:
                flash("Usuário já cadastrado.", "error")
            else:
                tipo_usuario = db.query(ClientType).filter_by(nome="user").first()

                if tipo_usuario is None:
                    flash("Tipo de cliente padrão não encontrado.", "error")
                else:
                    usuario = User(
                        usuario=form.usuario.data,
                        email=form.email.data or None,
                        telefone=form.telefone.data or None,
                        endereco=form.endereco.data or None,
                        tipo_cliente=tipo_usuario,
                        ativo=True,
                    )
                    usuario.definir_senha(form.senha.data)
                    db.add(usuario)

                    try:
                        db.commit()
                        flash("Conta criada com sucesso.", "success")
                        return redirect(url_for("login"))
                    except IntegrityError:
                        db.rollback()
                        flash("Não foi possível criar a conta com esses dados.", "error")

        return render_template("auth/register.html", form=form)

    @app.route("/logout")
    def logout():
        timeout = request.args.get("timeout") == "1"
        duplicada = request.args.get("duplicada") == "1"
        session.clear()

        if duplicada:
            flash("Acesso em nova aba encerrado. Faça login novamente.", "error")
        elif timeout:
            flash("Sessão encerrada por inatividade.", "error")
        else:
            flash("Você saiu do sistema.", "success")

        return redirect(url_for("login"))

    @app.route("/produtos")
    @login_required
    def listar_produtos():
        db = get_db()
        busca = request.args.get("q", "").strip()
        categoria_filtro = request.args.get("categoria", type=int)

        consulta = db.query(Product).outerjoin(Category).filter(Product.ativo.is_(True))

        if busca:
            termo = f"%{busca}%"
            consulta = consulta.filter(
                or_(
                    Product.nome.like(termo),
                    Product.descricao.like(termo),
                    Product.ean.like(termo),
                )
            )

        if categoria_filtro:
            consulta = consulta.filter(Product.categoria_id == categoria_filtro)

        produtos = consulta.order_by(Product.nome).all()
        categorias = listar_categorias(db)
        produtos_ativos = db.query(Product).filter(Product.ativo.is_(True)).all()
        total_inativos = db.query(Product).filter(Product.ativo.is_(False)).count()

        return render_template(
            "produtos/lista.html",
            produtos=produtos,
            categorias=categorias,
            stats=calcular_estatisticas(produtos_ativos),
            search=busca,
            busca=busca,
            categoria_filtro=categoria_filtro or "",
            total_inativos=total_inativos,
            modo_inativos=False,
        )

    @app.route("/produtos/inativos")
    @admin_required
    def listar_produtos_inativos():
        db = get_db()
        busca = request.args.get("q", "").strip()
        categoria_filtro = request.args.get("categoria", type=int)

        consulta = db.query(Product).outerjoin(Category).filter(Product.ativo.is_(False))

        if busca:
            termo = f"%{busca}%"
            consulta = consulta.filter(
                or_(
                    Product.nome.like(termo),
                    Product.descricao.like(termo),
                    Product.ean.like(termo),
                )
            )

        if categoria_filtro:
            consulta = consulta.filter(Product.categoria_id == categoria_filtro)

        produtos = consulta.order_by(Product.nome).all()
        categorias = listar_categorias(db)
        produtos_inativos = db.query(Product).filter(Product.ativo.is_(False)).all()
        total_inativos = len(produtos_inativos)

        return render_template(
            "produtos/lista.html",
            produtos=produtos,
            categorias=categorias,
            stats=calcular_estatisticas(produtos_inativos),
            search=busca,
            busca=busca,
            categoria_filtro=categoria_filtro or "",
            total_inativos=total_inativos,
            modo_inativos=True,
        )

    @app.route("/produtos/novo", methods=["GET", "POST"])
    @admin_required
    def criar_produto():
        db = get_db()
        form = ProductForm(request.form if request.method == "POST" else None)
        carregar_categorias(form, listar_categorias(db))

        if request.method == "POST" and form.validate():
            produto = Product()
            preencher_produto(produto, form)
            db.add(produto)

            try:
                db.commit()
                flash("Produto cadastrado com sucesso.", "success")
                return redirect(url_for("listar_produtos"))
            except IntegrityError:
                db.rollback()
                flash("Já existe um produto com este nome ou EAN.", "error")

        return render_template("produtos/form.html", form=form, titulo="Criar Produto", produto=None)

    @app.route("/produtos/<int:produto_id>")
    def detalhar_produto(produto_id):
        return render_template("produtos/detalhe.html", produto=buscar_produto(produto_id))

    @app.route("/produtos/<int:produto_id>/editar", methods=["GET", "POST"])
    @admin_required
    def editar_produto(produto_id):
        db = get_db()
        produto = buscar_produto(produto_id, incluir_inativo=True)
        form = ProductForm(request.form if request.method == "POST" else None, obj=produto)
        carregar_categorias(form, listar_categorias(db))

        if request.method == "POST" and form.validate():
            preencher_produto(produto, form)

            try:
                db.commit()
                flash("Produto atualizado com sucesso.", "success")
                return redirect(url_for("listar_produtos"))
            except IntegrityError:
                db.rollback()
                flash("Já existe um produto com este nome ou EAN.", "error")

        return render_template("produtos/form.html", form=form, titulo="Editar Produto", produto=produto)

    @app.route("/produtos/<int:produto_id>/ativar", methods=["POST"])
    @admin_required
    def ativar_produto(produto_id):
        db = get_db()
        produto = buscar_produto(produto_id, incluir_inativo=True)
        produto.ativo = True
        db.commit()
        flash("Produto ativado com sucesso.", "success")
        return redirect(url_for("listar_produtos_inativos"))

    @app.route("/produtos/<int:produto_id>/excluir", methods=["POST"])
    @admin_required
    def excluir_produto(produto_id):
        db = get_db()
        produto = buscar_produto(produto_id, incluir_inativo=True)

        try:
            excluir_produto_do_banco(db, produto)
            db.commit()
            flash("Produto excluído do banco de dados com sucesso.", "success")
        except IntegrityError:
            db.rollback()
            flash("Não foi possível excluir este produto.", "error")

        return redirect(url_for("listar_produtos"))

    @app.route("/categorias")
    def listar_categorias_view():
        db = get_db()
        return render_template("categorias/lista.html", categorias=listar_categorias(db))

    @app.route("/categorias/nova", methods=["GET", "POST"])
    @admin_required
    def criar_categoria():
        db = get_db()
        form = CategoryForm(request.form if request.method == "POST" else None)

        if request.method == "POST" and form.validate():
            db.add(Category(nome=form.nome.data))

            try:
                db.commit()
                flash("Categoria cadastrada com sucesso.", "success")
                return redirect(url_for("listar_categorias_view"))
            except IntegrityError:
                db.rollback()
                flash("Já existe uma categoria com este nome.", "error")

        return render_template("categorias/form.html", form=form, titulo="Nova categoria")

    @app.route("/categorias/<int:categoria_id>/editar", methods=["GET", "POST"])
    @admin_required
    def editar_categoria(categoria_id):
        db = get_db()
        categoria = buscar_categoria(categoria_id)
        form = CategoryForm(request.form if request.method == "POST" else None, obj=categoria)

        if request.method == "POST" and form.validate():
            categoria.nome = form.nome.data

            try:
                db.commit()
                flash("Categoria atualizada com sucesso.", "success")
                return redirect(url_for("listar_categorias_view"))
            except IntegrityError:
                db.rollback()
                flash("Já existe uma categoria com este nome.", "error")

        return render_template("categorias/form.html", form=form, titulo="Editar categoria")

    @app.route("/categorias/<int:categoria_id>/excluir", methods=["POST"])
    @admin_required
    def excluir_categoria(categoria_id):
        db = get_db()
        categoria = buscar_categoria(categoria_id)

        if categoria.produtos:
            flash("Não é possível excluir uma categoria com produtos.", "error")
            return redirect(url_for("listar_categorias_view"))

        db.delete(categoria)
        db.commit()
        flash("Categoria excluída com sucesso.", "success")
        return redirect(url_for("listar_categorias_view"))

    @app.route("/usuarios")
    @admin_required
    def listar_usuarios():
        db = get_db()
        usuarios = (
            db.query(User)
            .join(ClientType)
            .order_by(ClientType.nome, User.usuario)
            .all()
        )
        return render_template("usuarios/lista.html", usuarios=usuarios)

    @app.route("/usuarios/<int:usuario_id>/tornar-admin", methods=["POST"])
    @admin_required
    def tornar_usuario_admin(usuario_id):
        db = get_db()
        usuario = db.get(User, usuario_id)

        if usuario is None:
            abort(404)

        tipo_admin = db.query(ClientType).filter_by(nome="admin").first()

        if tipo_admin is None:
            tipo_admin = ClientType(nome="admin")
            db.add(tipo_admin)
            db.flush()

        if usuario.tipo_cliente_id == tipo_admin.id:
            flash("Este usuário já possui acesso de administrador.", "info")
            return redirect(url_for("listar_usuarios"))

        usuario.tipo_cliente = tipo_admin
        db.commit()
        flash(f"{usuario.usuario} agora possui acesso de administrador.", "success")
        return redirect(url_for("listar_usuarios"))

    @app.route("/usuarios/<int:usuario_id>/remover-admin", methods=["POST"])
    @admin_required
    def remover_usuario_admin(usuario_id):
        db = get_db()
        usuario = db.get(User, usuario_id)

        if usuario is None:
            abort(404)

        tipo_admin = db.query(ClientType).filter_by(nome="admin").first()

        if tipo_admin is None or usuario.tipo_cliente_id != tipo_admin.id:
            flash("Este usuário não possui acesso de administrador.", "info")
            return redirect(url_for("listar_usuarios"))

        total_admins = (
            db.query(User)
            .filter(User.tipo_cliente_id == tipo_admin.id, User.ativo.is_(True))
            .count()
        )

        if total_admins <= 1:
            flash("Não é possível remover o último administrador ativo.", "error")
            return redirect(url_for("listar_usuarios"))

        tipo_usuario = db.query(ClientType).filter_by(nome="user").first()

        if tipo_usuario is None:
            tipo_usuario = ClientType(nome="user")
            db.add(tipo_usuario)
            db.flush()

        usuario.tipo_cliente = tipo_usuario
        db.commit()
        flash(f"{usuario.usuario} deixou de possuir acesso de administrador.", "success")

        if usuario.id == session.get("usuario_id"):
            session["tipo"] = "user"
            return redirect(url_for("listar_produtos"))

        return redirect(url_for("listar_usuarios"))

    @app.route("/carrinho")
    @login_required
    def ver_carrinho():
        db = get_db()
        pedido = buscar_carrinho_ativo(db, session["usuario_id"])
        itens = pedido.itens if pedido else []
        return render_template("carrinho/index.html", itens=itens, total=calcular_total_itens(itens))

    @app.route("/carrinho/adicionar", methods=["POST"])
    @login_required
    def adicionar_carrinho():
        db = get_db()
        produto_id = request.form.get("produto_id", type=int)
        quantidade = request.form.get("quantidade", 1, type=int)

        if not produto_id or quantidade < 1:
            flash("Dados inválidos para o carrinho.", "error")
            return redirect(url_for("listar_produtos"))

        produto = db.get(Product, produto_id)
        if produto is None or not produto.ativo:
            flash("Produto não encontrado.", "error")
            return redirect(url_for("listar_produtos"))

        if produto.estoque < quantidade:
            flash(f"Estoque insuficiente. Disponível: {produto.estoque} un.", "error")
            return redirect(request.referrer or url_for("listar_produtos"))

        pedido = buscar_carrinho_ativo(db, session["usuario_id"], criar=True)
        item = encontrar_item_carrinho(pedido, produto.id)

        if item:
            nova_quantidade = item.quantidade + quantidade
            if nova_quantidade > produto.estoque:
                flash(f"Estoque insuficiente. Disponível: {produto.estoque} un.", "error")
                return redirect(request.referrer or url_for("listar_produtos"))
            item.quantidade = nova_quantidade
        else:
            pedido.itens.append(
                OrderItem(produto=produto, quantidade=quantidade, preco_unitario=produto.preco)
            )

        atualizar_total_pedido(db, pedido)
        db.commit()
        flash(f'"{produto.nome}" adicionado ao carrinho.', "success")
        return redirect(request.referrer or url_for("listar_produtos"))

    @app.route("/carrinho/atualizar", methods=["POST"])
    @login_required
    def atualizar_carrinho():
        db = get_db()
        item_id = request.form.get("item_id", type=int)
        quantidade = request.form.get("quantidade", type=int)
        pedido = buscar_carrinho_ativo(db, session["usuario_id"])

        if pedido is None or item_id is None or quantidade is None:
            flash("Dados inválidos para atualizar o carrinho.", "error")
            return redirect(url_for("ver_carrinho"))

        item = db.get(OrderItem, item_id)
        if item is None or item.pedido_id != pedido.id:
            flash("Item não encontrado no carrinho.", "error")
            return redirect(url_for("ver_carrinho"))

        if quantidade <= 0:
            db.delete(item)
            flash("Item removido do carrinho.", "success")
        elif quantidade > item.produto.estoque:
            flash(f"Estoque insuficiente. Disponível: {item.produto.estoque} un.", "error")
            return redirect(url_for("ver_carrinho"))
        else:
            item.quantidade = quantidade
            flash("Carrinho atualizado.", "success")

        atualizar_total_pedido(db, pedido)
        db.commit()
        return redirect(url_for("ver_carrinho"))

    @app.route("/carrinho/remover", methods=["POST"])
    @login_required
    def remover_carrinho():
        db = get_db()
        item_id = request.form.get("item_id", type=int)
        pedido = buscar_carrinho_ativo(db, session["usuario_id"])

        if pedido is None or item_id is None:
            flash("Item não encontrado.", "error")
            return redirect(url_for("ver_carrinho"))

        item = db.get(OrderItem, item_id)
        if item is None or item.pedido_id != pedido.id:
            flash("Item não encontrado.", "error")
            return redirect(url_for("ver_carrinho"))

        db.delete(item)
        atualizar_total_pedido(db, pedido)
        db.commit()
        flash("Item removido do carrinho.", "success")
        return redirect(url_for("ver_carrinho"))

    @app.route("/carrinho/finalizar", methods=["POST"])
    @login_required
    def finalizar_carrinho():
        db = get_db()
        pedido = buscar_carrinho_ativo(db, session["usuario_id"])

        if pedido is None or not pedido.itens:
            flash("Seu carrinho está vazio.", "error")
            return redirect(url_for("ver_carrinho"))

        for item in pedido.itens:
            if not item.produto.ativo:
                flash(f'O produto "{item.produto.nome}" não está mais disponível.', "error")
                return redirect(url_for("ver_carrinho"))
            if item.quantidade > item.produto.estoque:
                flash(f'Estoque insuficiente para "{item.produto.nome}".', "error")
                return redirect(url_for("ver_carrinho"))

        for item in pedido.itens:
            item.produto.estoque -= item.quantidade

        pedido.status = "pendente"
        pedido.observacoes = (request.form.get("observacoes") or "").strip() or None
        atualizar_total_pedido(db, pedido)
        db.commit()

        flash("Pedido realizado com sucesso.", "success")
        return redirect(url_for("meus_pedidos"))

    @app.route("/meus_pedidos")
    @app.route("/pedidos/meus-pedidos")
    @login_required
    def meus_pedidos():
        db = get_db()
        pedidos = (
            db.query(Order)
            .filter(Order.cliente_id == session["usuario_id"], Order.status != "carrinho")
            .order_by(Order.criado_em.desc(), Order.id.desc())
            .all()
        )
        return render_template("pedidos/meus_pedidos.html", pedidos=pedidos)

    @app.errorhandler(404)
    def pagina_nao_encontrada(error):
        return render_template("404.html"), 404


def redirecionar_para_login():
    proximo = request.full_path if request.query_string else request.path
    flash("Faça login para continuar.", "error")
    return redirect(url_for("login", next=proximo))


def iniciar_sessao(usuario):
    # Guarda somente os dados necessários para identificar o usuário logado.
    session.clear()
    session.permanent = False
    session["usuario_id"] = usuario.id
    session["usuario"] = usuario.usuario
    session["tipo"] = usuario.tipo_cliente.nome
    session["ultimo_acesso"] = time()
    session["_csrf_token"] = token_urlsafe(32)


def gerar_csrf_token():
    # Cria ou reutiliza o token CSRF da sessão atual.
    if "_csrf_token" not in session:
        session["_csrf_token"] = token_urlsafe(32)
    return session["_csrf_token"]


def destino_seguro(proximo):
    if proximo and proximo.startswith("/") and not proximo.startswith("//"):
        return proximo
    return url_for("listar_produtos")


def formatar_brl(valor):
    try:
        numero = Decimal(str(valor or 0)).quantize(Decimal("0.01"))
    except Exception:
        numero = Decimal("0.00")

    sinal = "-" if numero < 0 else ""
    inteiro, centavos = f"{abs(numero):.2f}".split(".")
    grupos = []

    while inteiro:
        grupos.append(inteiro[-3:])
        inteiro = inteiro[:-3]

    return f"R$ {sinal}{'.'.join(reversed(grupos))},{centavos}"


def listar_categorias(db):
    return db.query(Category).order_by(Category.nome).all()


def buscar_produto(produto_id, incluir_inativo=False):
    produto = get_db().get(Product, produto_id)

    if produto is None or (not incluir_inativo and not produto.ativo):
        abort(404)

    return produto


def buscar_categoria(categoria_id):
    categoria = get_db().get(Category, categoria_id)

    if categoria is None:
        abort(404)

    return categoria


def preencher_produto(produto, form):
    # Copia dados validados do formulário para o modelo.
    produto.nome = form.nome.data
    produto.descricao = form.descricao.data
    produto.ean = form.ean.data or None
    produto.data_producao = form.data_producao.data
    produto.data_validade = form.data_validade.data
    produto.imagem = form.imagem.data or None
    produto.preco = form.preco.data
    produto.estoque = form.estoque.data
    produto.categoria_id = form.categoria_id.data
    produto.ativo = form.ativo.data


def excluir_produto_do_banco(db, produto):
    # Remove vínculos de pedido antes de apagar o produto.
    pedidos_afetados = {item.pedido for item in produto.itens_pedido}

    for item in list(produto.itens_pedido):
        db.delete(item)

    db.flush()

    for pedido in pedidos_afetados:
        atualizar_total_pedido(db, pedido)

    db.delete(produto)


def calcular_estatisticas(produtos):
    valor_total = sum(float(produto.preco or 0) * produto.estoque for produto in produtos)

    return {
        "total": len(produtos),
        "em_estoque": sum(1 for produto in produtos if produto.estoque > 0),
        "valor_total": valor_total,
    }


def buscar_carrinho_ativo(db, usuario_id, criar=False):
    pedido = (
        db.query(Order)
        .filter(Order.cliente_id == usuario_id, Order.status == "carrinho")
        .order_by(Order.id.desc())
        .first()
    )

    if pedido is None and criar:
        pedido = Order(cliente_id=usuario_id, status="carrinho", total=Decimal("0.00"))
        db.add(pedido)
        db.flush()

    return pedido


def encontrar_item_carrinho(pedido, produto_id):
    for item in pedido.itens:
        if item.produto_id == produto_id:
            return item
    return None


def calcular_total_itens(itens):
    return sum((item.subtotal for item in itens), Decimal("0.00"))


def atualizar_valor_total_item(item):
    item.valor_total = (item.preco_unitario or Decimal("0.00")) * (item.quantidade or 0)


def atualizar_total_pedido(db, pedido):
    for item in list(pedido.itens):
        if item in db.deleted:
            continue
        atualizar_valor_total_item(item)

    db.flush()
    total = (
        db.query(func.coalesce(func.sum(OrderItem.valor_total), 0))
        .filter(OrderItem.pedido_id == pedido.id)
        .scalar()
    )
    pedido.total = total or Decimal("0.00")


def contar_itens_carrinho(usuario_id):
    db = get_db()
    pedido = buscar_carrinho_ativo(db, usuario_id)

    if pedido is None:
        return 0

    total = (
        db.query(func.coalesce(func.sum(OrderItem.quantidade), 0))
        .filter(OrderItem.pedido_id == pedido.id)
        .scalar()
    )
    return int(total or 0)
