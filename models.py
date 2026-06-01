from datetime import datetime, timedelta, timezone
from decimal import Decimal
from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, create_engine, event, inspect, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash


engine = None
SessionLocal = scoped_session(sessionmaker(autoflush=False, autocommit=False))
BRASILIA_TZ = timezone(timedelta(hours=-3))
MYSQL_BRASILIA_TIME_ZONE = "-03:00"


def horario_brasilia():
    return datetime.now(BRASILIA_TZ).replace(tzinfo=None)


class Base(DeclarativeBase):
    # Base declarativa compartilhada por todos os modelos do SQLAlchemy.
    pass


class Category(Base):
    __tablename__ = "categorias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    criado_em: Mapped[datetime] = mapped_column("criado_em", DateTime, default=horario_brasilia)
    atualizado_em: Mapped[datetime] = mapped_column(
        "atualizado_em",
        DateTime,
        default=horario_brasilia,
        onupdate=horario_brasilia,
    )

    produtos: Mapped[list["Product"]] = relationship("Product", back_populates="categoria")


class ClientType(Base):
    __tablename__ = "tipos_cliente"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)

    clientes: Mapped[list["User"]] = relationship("User", back_populates="tipo_cliente")


class User(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(150))
    telefone: Mapped[str | None] = mapped_column(String(20))
    endereco: Mapped[str | None] = mapped_column(String(255))
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    criado_em: Mapped[datetime] = mapped_column("criado_em", DateTime, default=horario_brasilia)
    atualizado_em: Mapped[datetime] = mapped_column(
        "atualizado_em",
        DateTime,
        default=horario_brasilia,
        onupdate=horario_brasilia,
    )

    tipo_cliente_id: Mapped[int] = mapped_column(ForeignKey("tipos_cliente.id"), nullable=False)
    tipo_cliente: Mapped[ClientType] = relationship("ClientType", back_populates="clientes")
    pedidos: Mapped[list["Order"]] = relationship("Order", back_populates="cliente")

    def definir_senha(self, senha):
        # Persiste somente o hash da senha do usuário.
        self.senha_hash = generate_password_hash(senha)

    def senha_confere(self, senha):
        # Compara a senha informada com o hash armazenado.
        return password_matches(self.senha_hash, senha)


class Product(Base):
    __tablename__ = "produtos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    descricao: Mapped[str | None] = mapped_column(Text)
    ean: Mapped[str | None] = mapped_column(String(14), unique=True)
    preco: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    estoque: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    data_producao: Mapped[datetime | None] = mapped_column(Date)
    data_validade: Mapped[datetime | None] = mapped_column(Date)
    imagem: Mapped[str | None] = mapped_column(String(255))
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    criado_em: Mapped[datetime] = mapped_column("criado_em", DateTime, default=horario_brasilia)
    atualizado_em: Mapped[datetime] = mapped_column(
        "atualizado_em",
        DateTime,
        default=horario_brasilia,
        onupdate=horario_brasilia,
    )

    categoria_id: Mapped[int | None] = mapped_column(ForeignKey("categorias.id"))
    categoria: Mapped[Category | None] = relationship("Category", back_populates="produtos")
    itens_pedido: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="produto")


class Order(Base):
    __tablename__ = "pedidos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("carrinho", "pendente", "confirmado", "enviado", "entregue", "cancelado"),
        nullable=False,
        default="carrinho",
    )
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    observacoes: Mapped[str | None] = mapped_column(Text)
    criado_em: Mapped[datetime] = mapped_column("criado_em", DateTime, default=horario_brasilia)
    atualizado_em: Mapped[datetime] = mapped_column(
        "atualizado_em",
        DateTime,
        default=horario_brasilia,
        onupdate=horario_brasilia,
    )

    cliente: Mapped[User] = relationship("User", back_populates="pedidos")
    itens: Mapped[list["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="pedido",
        cascade="all, delete-orphan",
    )


class OrderItem(Base):
    __tablename__ = "itens_pedido"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pedido_id: Mapped[int] = mapped_column(ForeignKey("pedidos.id"), nullable=False)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), nullable=False)
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    preco_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    valor_total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    criado_em: Mapped[datetime] = mapped_column("criado_em", DateTime, default=horario_brasilia)
    atualizado_em: Mapped[datetime] = mapped_column(
        "atualizado_em",
        DateTime,
        default=horario_brasilia,
        onupdate=horario_brasilia,
    )

    pedido: Mapped[Order] = relationship("Order", back_populates="itens")
    produto: Mapped[Product] = relationship("Product", back_populates="itens_pedido")

    @property
    def subtotal(self):
        return self.valor_total or ((self.preco_unitario or Decimal("0.00")) * self.quantidade)


def init_database(config):
    configure_engine(config["DATABASE_URL"])
    seed_initial_data()


def create_database_if_needed(config):
    server_engine = create_engine(config["MYSQL_SERVER_URL"], pool_pre_ping=True)

    with server_engine.begin() as connection:
        connection.execute(
            text(
                f"CREATE DATABASE IF NOT EXISTS `{config['MYSQL_DATABASE']}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        )

    server_engine.dispose()


def configure_engine(database_url):
    global engine

    engine = create_engine(database_url, pool_pre_ping=True)

    if database_url.startswith("mysql"):
        event.listen(engine, "connect", set_mysql_time_zone)

    SessionLocal.configure(bind=engine)


def set_mysql_time_zone(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute(f"SET time_zone = '{MYSQL_BRASILIA_TIME_ZONE}'")
    cursor.close()


def get_db():
    # Entrega uma sessão do banco para a requisição atual.
    return SessionLocal()


def close_db(exception=None):
    SessionLocal.remove()


def ensure_optional_columns():
    inspector = inspect(engine)

    with engine.begin() as connection:
        ensure_product_columns(connection, inspector)
        ensure_audit_columns(connection, inspector)
        ensure_order_columns(connection, inspector)


def ensure_product_columns(connection, inspector):
    if not inspector.has_table("produtos"):
        return

    columns = {column["name"] for column in inspector.get_columns("produtos")}

    if "imagem" not in columns:
        connection.execute(text("ALTER TABLE produtos ADD COLUMN imagem VARCHAR(255)"))

    if "ean" not in columns:
        connection.execute(text("ALTER TABLE produtos ADD COLUMN ean VARCHAR(14) UNIQUE"))

    if "data_producao" not in columns:
        connection.execute(text("ALTER TABLE produtos ADD COLUMN data_producao DATE NULL"))

    if "data_validade" not in columns:
        connection.execute(text("ALTER TABLE produtos ADD COLUMN data_validade DATE NULL"))


def ensure_order_columns(connection, inspector):
    if not inspector.has_table("itens_pedido"):
        return

    columns = {column["name"] for column in inspector.get_columns("itens_pedido")}

    if "valor_total" not in columns:
        connection.execute(
            text(
                "ALTER TABLE itens_pedido "
                "ADD COLUMN valor_total DECIMAL(10,2) NOT NULL DEFAULT 0 AFTER preco_unitario"
            )
        )

    connection.execute(
        text(
            "UPDATE itens_pedido "
            "SET valor_total = quantidade * preco_unitario "
            "WHERE valor_total IS NULL OR valor_total <> quantidade * preco_unitario"
        )
    )


def ensure_audit_columns(connection, inspector):
    for table_name in ("clientes", "categorias", "produtos", "pedidos", "itens_pedido"):
        ensure_brazilian_audit_columns(connection, inspector, table_name)


def ensure_brazilian_audit_columns(connection, inspector, table_name):
    if not inspector.has_table(table_name):
        return

    columns = {column["name"] for column in inspector.get_columns(table_name)}
    renamed_created_at = False
    renamed_updated_at = False

    if "criado_em" not in columns:
        if "created_at" in columns:
            connection.execute(
                text(
                    f"ALTER TABLE {table_name} "
                    "CHANGE COLUMN created_at criado_em DATETIME DEFAULT CURRENT_TIMESTAMP"
                )
            )
            renamed_created_at = True
        else:
            connection.execute(
                text(f"ALTER TABLE {table_name} ADD COLUMN criado_em DATETIME DEFAULT CURRENT_TIMESTAMP")
            )
    else:
        connection.execute(
            text(f"ALTER TABLE {table_name} MODIFY COLUMN criado_em DATETIME DEFAULT CURRENT_TIMESTAMP")
        )

    if "atualizado_em" not in columns:
        if "updated_at" in columns:
            connection.execute(
                text(
                    f"ALTER TABLE {table_name} "
                    "CHANGE COLUMN updated_at atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
                )
            )
            renamed_updated_at = True
        else:
            connection.execute(
                text(
                    f"ALTER TABLE {table_name} "
                    "ADD COLUMN atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
                )
            )
    else:
        connection.execute(
            text(
                f"ALTER TABLE {table_name} "
                "MODIFY COLUMN atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
            )
        )

    if renamed_created_at and renamed_updated_at:
        connection.execute(
            text(
                f"UPDATE {table_name} "
                "SET criado_em = DATE_SUB(criado_em, INTERVAL 3 HOUR), "
                "atualizado_em = DATE_SUB(atualizado_em, INTERVAL 3 HOUR) "
                "WHERE criado_em IS NOT NULL OR atualizado_em IS NOT NULL"
            )
        )
    elif renamed_created_at:
        connection.execute(
            text(
                f"UPDATE {table_name} "
                "SET criado_em = DATE_SUB(criado_em, INTERVAL 3 HOUR), "
                "atualizado_em = atualizado_em "
                "WHERE criado_em IS NOT NULL"
            )
        )
    elif renamed_updated_at:
        connection.execute(
            text(
                f"UPDATE {table_name} "
                "SET atualizado_em = DATE_SUB(atualizado_em, INTERVAL 3 HOUR) "
                "WHERE atualizado_em IS NOT NULL"
            )
        )


def seed_initial_data():
    db = get_db()

    try:
        admin_type = get_or_create_client_type(db, "admin")
        user_type = get_or_create_client_type(db, "user")

        ensure_user(db, usuario="admin", senha="admin123", tipo=admin_type)
        ensure_user(db, usuario="cliente", senha="cliente123", tipo=user_type)

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
        SessionLocal.remove()


def get_or_create_client_type(db, nome):
    tipo = db.query(ClientType).filter_by(nome=nome).first()

    if tipo is None:
        tipo = ClientType(nome=nome)
        db.add(tipo)
        db.commit()

    return tipo


def ensure_user(db, usuario, senha, tipo):
    user = db.query(User).filter_by(usuario=usuario).first()

    if user is None:
        db.add(
            User(
                usuario=usuario,
                senha_hash=generate_password_hash(senha),
                tipo_cliente=tipo,
                ativo=True,
            )
        )
        db.commit()
        return

    if not password_matches(user.senha_hash, senha):
        user.senha_hash = generate_password_hash(senha)
        user.tipo_cliente = tipo
        user.ativo = True
        db.commit()


def password_matches(senha_hash, senha):
    try:
        return check_password_hash(senha_hash, senha)
    except ValueError:
        return False
