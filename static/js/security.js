// Controla confirmações, inatividade e uso de sessão em uma única aba.
(function () {
    const body = document.body;
    const usuarioLogado = body.dataset.logged === "1";
    const tempoLimite = Number(body.dataset.timeout || 0);

    configurarConfirmacoes();

    if (!usuarioLogado) {
        limparAbaAtiva();
        return;
    }

    controlarAbaUnica();
    controlarInatividade(tempoLimite);
})();

function configurarConfirmacoes() {
    // Confirma exclusões antes de enviar formulários sensíveis.
    document.querySelectorAll("[data-confirm]").forEach(function (form) {
        form.addEventListener("submit", function (event) {
            if (!confirm(form.dataset.confirm)) {
                event.preventDefault();
            }
        });
    });
}

function controlarInatividade(tempoLimite) {
    // Encerra a sessão quando o usuário passa do tempo permitido sem ação.
    if (tempoLimite <= 0) {
        return;
    }

    let timer;

    function reiniciarTimer() {
        clearTimeout(timer);
        timer = setTimeout(function () {
            alert("Sessão encerrada por inatividade.");
            window.location.href = "/logout?timeout=1";
        }, tempoLimite * 1000);
    }

    ["click", "mousemove", "keydown", "scroll", "touchstart"].forEach(function (evento) {
        document.addEventListener(evento, reiniciarTimer, { passive: true });
    });

    reiniciarTimer();
}

function controlarAbaUnica() {
    // Mantém apenas uma aba logada por vez no mesmo navegador.
    const chaveAba = "ecommerce_aba_ativa";
    const chaveSessao = "ecommerce_aba_id";
    const limiteMs = 5000;
    const agora = Date.now();
    const abaAtual = obterIdAba(chaveSessao);
    const abaAtiva = lerAbaAtiva(chaveAba);

    if (abaAtiva && abaAtiva.id !== abaAtual && agora - abaAtiva.atualizadoEm < limiteMs) {
        window.location.replace("/logout?duplicada=1");
        return;
    }

    function renovarAba() {
        localStorage.setItem(
            chaveAba,
            JSON.stringify({ id: abaAtual, atualizadoEm: Date.now() })
        );
    }

    renovarAba();
    setInterval(renovarAba, 2000);

    window.addEventListener("beforeunload", function () {
        const abaSalva = lerAbaAtiva(chaveAba);

        if (abaSalva && abaSalva.id === abaAtual) {
            localStorage.removeItem(chaveAba);
        }
    });
}

function obterIdAba(chaveSessao) {
    // Cria um identificador simples preso somente à aba atual.
    let id = sessionStorage.getItem(chaveSessao);

    if (!id) {
        id = "aba-" + Date.now() + "-" + Math.random().toString(16).slice(2);
        sessionStorage.setItem(chaveSessao, id);
    }

    return id;
}

function lerAbaAtiva(chaveAba) {
    // Lê a aba salva sem quebrar a página se o valor estiver inválido.
    try {
        return JSON.parse(localStorage.getItem(chaveAba) || "null");
    } catch (error) {
        localStorage.removeItem(chaveAba);
        return null;
    }
}

function limparAbaAtiva() {
    // Limpa marcas locais quando a tela atual não está autenticada.
    sessionStorage.removeItem("ecommerce_aba_id");
    localStorage.removeItem("ecommerce_aba_ativa");
}
