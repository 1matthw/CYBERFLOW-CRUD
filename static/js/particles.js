// Gerencia o fundo animado, microinterações e efeitos visuais da interface.
const canvas = document.getElementById("particles");
const ctx = canvas.getContext("2d");
const mouse = { x: null, y: null, radius: 160 };
let particles = [];

function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
}

function initParticles() {
    // Cria partículas leves para o fundo animado.
    const total = Math.min(90, Math.floor((canvas.width * canvas.height) / 14000));
    particles = [];

    for (let i = 0; i < total; i += 1) {
        particles.push({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            r: Math.random() * 2 + 0.5,
            dx: (Math.random() - 0.5) * 0.3,
            dy: (Math.random() - 0.5) * 0.3,
            alpha: Math.random() * 0.5 + 0.2,
            pulse: Math.random() * Math.PI * 2,
            hue: Math.random() > 0.5 ? 250 : 270
        });
    }
}

function drawParticles() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    particles.forEach(function (particle) {
        moverParticle(particle);
        desenharParticle(particle);
    });

    desenharLinhas();
    requestAnimationFrame(drawParticles);
}

function moverParticle(particle) {
    // Move a partícula e aplica uma repulsão suave perto do mouse.
    particle.x += particle.dx;
    particle.y += particle.dy;
    particle.pulse += 0.015;

    if (particle.x < 0 || particle.x > canvas.width) {
        particle.dx *= -1;
    }

    if (particle.y < 0 || particle.y > canvas.height) {
        particle.dy *= -1;
    }

    if (mouse.x === null) {
        return;
    }

    const dx = particle.x - mouse.x;
    const dy = particle.y - mouse.y;
    const distancia = Math.sqrt(dx * dx + dy * dy) || 1;

    if (distancia < mouse.radius) {
        const forca = ((mouse.radius - distancia) / mouse.radius) * 1.2;
        particle.x += (dx / distancia) * forca;
        particle.y += (dy / distancia) * forca;
    }
}

function desenharParticle(particle) {
    // Desenha a partícula com brilho discreto.
    const alpha = particle.alpha + Math.sin(particle.pulse) * 0.1;

    ctx.beginPath();
    ctx.arc(particle.x, particle.y, particle.r * 4, 0, Math.PI * 2);
    ctx.fillStyle = `hsla(${particle.hue}, 80%, 72%, ${alpha * 0.07})`;
    ctx.fill();

    ctx.beginPath();
    ctx.arc(particle.x, particle.y, particle.r, 0, Math.PI * 2);
    ctx.fillStyle = `hsla(${particle.hue}, 80%, 82%, ${alpha})`;
    ctx.fill();
}

function desenharLinhas() {
    // Liga partículas próximas para dar profundidade ao fundo.
    for (let i = 0; i < particles.length; i += 1) {
        for (let j = i + 1; j < particles.length; j += 1) {
            const dx = particles[i].x - particles[j].x;
            const dy = particles[i].y - particles[j].y;
            const distancia = Math.sqrt(dx * dx + dy * dy);

            if (distancia < 135) {
                ctx.beginPath();
                ctx.moveTo(particles[i].x, particles[i].y);
                ctx.lineTo(particles[j].x, particles[j].y);
                ctx.strokeStyle = `rgba(167, 139, 250, ${0.12 * (1 - distancia / 135)})`;
                ctx.lineWidth = 0.5;
                ctx.stroke();
            }
        }
    }
}

function togglePassword(inputId, iconEl) {
    const input = document.getElementById(inputId);

    if (!input) {
        return;
    }

    const visivel = input.type === "password";
    input.type = visivel ? "text" : "password";
    iconEl.classList.toggle("bi-eye", !visivel);
    iconEl.classList.toggle("bi-eye-slash", visivel);
}

function changeQty(delta) {
    const input = document.getElementById("qty-input");

    if (!input) {
        return;
    }

    const max = parseInt(input.max, 10) || 999;
    const atual = parseInt(input.value, 10) || 1;
    input.value = Math.max(1, Math.min(max, atual + delta));
}

function iniciarAnimacoes() {
    // Mostra elementos com entrada suave.
    document.querySelectorAll(".stagger, .stagger-scale").forEach(function (el, index) {
        setTimeout(function () {
            el.classList.add("show");
        }, index * 70);
    });
}

function iniciarPreviewImagem() {
    // Atualiza a prévia da imagem no formulário do produto.
    const input = document.querySelector('input[name="imagem"]');
    const previewBox = document.getElementById("img-preview");

    if (!input || !previewBox) {
        return;
    }

    function mostrarPreview(src) {
        previewBox.innerHTML = src ? `<img src="${src}" alt="Preview">` : "";
        previewBox.style.display = src ? "block" : "none";
    }

    input.addEventListener("input", function () {
        mostrarPreview(input.value);
    });

    if (input.value) {
        mostrarPreview(input.value);
    }
}

function iniciarBotoes() {
    // Cria efeito visual simples nos botões principais.
    document.querySelectorAll(".btn-modern, .btn-buy, .btn-create").forEach(function (button) {
        button.addEventListener("click", function (event) {
            const rect = button.getBoundingClientRect();
            const ripple = document.createElement("span");

            ripple.className = "ripple";
            ripple.style.left = event.clientX - rect.left + "px";
            ripple.style.top = event.clientY - rect.top + "px";
            button.appendChild(ripple);

            setTimeout(function () {
                ripple.remove();
            }, 600);
        });
    });
}

function iniciarContadores() {
    // Anima os números exibidos nos cards de resumo.
    document.querySelectorAll("[data-count]").forEach(function (el) {
        const total = parseInt(el.dataset.count, 10) || 0;
        const passo = Math.max(1, Math.ceil(total / 40));
        let atual = 0;

        const intervalo = setInterval(function () {
            atual += passo;

            if (atual >= total) {
                atual = total;
                clearInterval(intervalo);
            }

            el.textContent = atual.toLocaleString("pt-BR");
        }, 25);
    });
}

function fecharFlashMessages() {
    // Remove mensagens automaticamente depois de alguns segundos.
    document.querySelectorAll(".flash-banner").forEach(function (el, index) {
        setTimeout(function () {
            el.style.animation = "flashSlideOut 0.5s ease forwards";
            setTimeout(function () {
                el.remove();
            }, 500);
        }, 3200 + index * 200);
    });
}

window.addEventListener("resize", function () {
    resizeCanvas();
    initParticles();
});

window.addEventListener("mousemove", function (event) {
    mouse.x = event.clientX;
    mouse.y = event.clientY;
});

window.addEventListener("mouseout", function () {
    mouse.x = null;
    mouse.y = null;
});

window.addEventListener("scroll", function () {
    const header = document.querySelector(".dashboard-header");

    if (header) {
        header.classList.toggle("scrolled", window.scrollY > 20);
    }
});

document.addEventListener("DOMContentLoaded", function () {
    iniciarAnimacoes();
    iniciarPreviewImagem();
    iniciarBotoes();
});

window.addEventListener("load", function () {
    iniciarContadores();
    fecharFlashMessages();
});

resizeCanvas();
initParticles();
drawParticles();
