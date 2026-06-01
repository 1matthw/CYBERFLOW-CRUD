from wtforms import (
    BooleanField,
    DateField,
    DecimalField,
    Form,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    TextAreaField,
)
from wtforms.validators import DataRequired, InputRequired, Length, NumberRange, Optional, Regexp


def limpar_texto(valor):
    # Remove espaços extras antes da validação e persistência dos campos.
    if valor is None:
        return valor
    return valor.strip()


class ProductForm(Form):
    nome = StringField(
        "Nome",
        filters=[limpar_texto],
        validators=[DataRequired(message="Informe o nome."), Length(max=200)],
    )
    descricao = TextAreaField(
        "Descrição",
        filters=[limpar_texto],
        validators=[Optional(), Length(max=5000)],
    )
    ean = StringField(
        "Código EAN",
        filters=[limpar_texto],
        validators=[
            Optional(),
            Length(min=8, max=14, message="O EAN deve ter entre 8 e 14 dígitos."),
            Regexp(r"^\d+$", message="O EAN deve conter apenas números."),
        ],
    )
    preco = DecimalField(
        "Preço",
        places=2,
        validators=[
            InputRequired(message="Informe o preço."),
            NumberRange(min=0, message="O preço não pode ser negativo."),
        ],
    )
    estoque = IntegerField(
        "Estoque",
        validators=[
            InputRequired(message="Informe o estoque."),
            NumberRange(min=0, message="O estoque não pode ser negativo."),
        ],
    )
    categoria_id = SelectField(
        "Categoria",
        coerce=int,
        validators=[InputRequired(message="Escolha uma categoria.")],
    )

    data_producao = DateField(
        "Data de produção",
        format="%Y-%m-%d",
        validators=[Optional()],
    )
    data_validade = DateField(
        "Data de validade",
        format="%Y-%m-%d",
        validators=[Optional()],
    )

    imagem = StringField(
        "URL da imagem",
        filters=[limpar_texto],
        validators=[Optional(), Length(max=255)],
    )
    ativo = BooleanField("Produto ativo", default=True)


class CategoryForm(Form):
    nome = StringField(
        "Nome",
        filters=[limpar_texto],
        validators=[DataRequired(message="Informe o nome."), Length(max=100)],
    )


class LoginForm(Form):
    usuario = StringField(
        "Usuário",
        filters=[limpar_texto],
        validators=[DataRequired(message="Informe o usuário."), Length(max=80)],
    )
    senha = PasswordField(
        "Senha",
        validators=[DataRequired(message="Informe a senha."), Length(max=120)],
    )


def carregar_categorias(form, categorias):
    # Monta as opções exibidas no campo de categorias.
    form.categoria_id.choices = [(categoria.id, categoria.nome) for categoria in categorias]


class RegisterForm(Form):
    usuario = StringField(
        "Usuário",
        filters=[limpar_texto],
        validators=[DataRequired(message="Informe o usuário."), Length(min=3, max=80)],
    )
    email = StringField("Email", filters=[limpar_texto], validators=[Optional(), Length(max=150)])
    telefone = StringField("Telefone", filters=[limpar_texto], validators=[Optional(), Length(max=20)])
    endereco = StringField("Endereço", filters=[limpar_texto], validators=[Optional(), Length(max=255)])
    senha = PasswordField(
        "Senha",
        validators=[DataRequired(message="Informe a senha."), Length(min=6, max=120)],
    )
    confirmar_senha = PasswordField(
        "Confirmar senha",
        validators=[DataRequired(message="Confirme a senha.")],
    )
