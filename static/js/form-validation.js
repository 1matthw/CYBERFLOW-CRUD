document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".needs-validation").forEach(function (form) {
        form.addEventListener("submit", function (event) {
            const erros = validarFormulario(form);

            if (erros.length > 0) {
                event.preventDefault();
                event.stopPropagation();
                alert(erros.join("\n"));
            }

            form.classList.add("was-validated");
        });
    });
});

function validarFormulario(form) {
    const erros = [];

    if (!form.checkValidity()) {
        erros.push("Preencha corretamente os campos obrigatórios.");
    }

    if (form.dataset.validate === "product") {
        validarProduto(form, erros);
    }

    if (form.dataset.validate === "register") {
        validarCadastro(form, erros);
    }

    return erros;
}

function validarProduto(form, erros) {
    // Confere campos numéricos e textos especiais do produto.
    const preco = Number(form.querySelector("[name='preco']")?.value || 0);
    const estoque = Number(form.querySelector("[name='estoque']")?.value || 0);
    const imagem = form.querySelector("[name='imagem']")?.value.trim();
    const ean = form.querySelector("[name='ean']")?.value.trim();

    if (preco < 0) {
        erros.push("O preço não pode ser negativo.");
    }

    if (!Number.isInteger(estoque) || estoque < 0) {
        erros.push("O estoque deve ser um número inteiro maior ou igual a zero.");
    }

    if (imagem && !imagem.startsWith("http://") && !imagem.startsWith("https://")) {
        erros.push("A URL da imagem deve começar com http:// ou https://.");
    }

    if (ean && (!/^[0-9]+$/.test(ean) || ean.length < 8 || ean.length > 14)) {
        erros.push("O EAN deve conter de 8 a 14 números.");
    }
}

function validarCadastro(form, erros) {
    // Garante que as duas senhas digitadas sejam iguais.
    const senha = form.querySelector("[name='senha']")?.value || "";
    const confirmar = form.querySelector("[name='confirmar_senha']")?.value || "";

    if (senha && confirmar && senha !== confirmar) {
        erros.push("As senhas não coincidem.");
    }
}
