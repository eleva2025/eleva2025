document.addEventListener('DOMContentLoaded', function() {
    // Quadros expansíveis
    document.querySelectorAll('.info-card').forEach(card => {
        card.addEventListener('click', function() {
            toggleCard(this);
        });
    });

    // Inicializa os cards com transição suave
    document.querySelectorAll('.card-content').forEach(content => {
        content.style.transition = 'opacity 0.3s ease';
    });

    document.querySelector('.hamburger').addEventListener('click', function() {
        this.classList.toggle('active');
        document.querySelector('.nav-links').classList.toggle('active');
    });

    // Controle da tela de etapas
    const abrirBtn = document.querySelector('.abrir-etapas-btn');
    const fecharBtn = document.querySelector('.fechar-etapas');
    const etapasFlutuante = document.querySelector('.etapas-flutuante');
    const etapaBtns = document.querySelectorAll('.etapa-btn');
    
    abrirBtn.addEventListener('click', () => {
        etapasFlutuante.classList.add('mostrar');
    });
    
    fecharBtn.addEventListener('click', () => {
        etapasFlutuante.classList.remove('mostrar');
    });
    
    etapaBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active de todos
            document.querySelectorAll('.etapa-btn.active').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.etapa-conteudo.active').forEach(el => el.classList.remove('active'));
            
            // Adiciona active no selecionado
            btn.classList.add('active');
            const etapa = btn.dataset.etapa;
            document.querySelector(`.etapa-conteudo[data-etapa="${etapa}"]`).classList.add('active');
        });
    });
    
    // Fechar ao clicar fora
    etapasFlutuante.addEventListener('click', (e) => {
        if (e.target === etapasFlutuante) {
            etapasFlutuante.classList.remove('mostrar');
        }
    });

    // Inicializa o carrossel de depoimentos
    new Glide('.glide', {
        type: 'carousel',
        perView: 1,
        gap: 30,
        autoplay: 5000,
        hoverpause: true
    }).mount();
});

// Função para alternar cards expansíveis
function toggleCard(card) {
    card.classList.toggle('active');
    const icon = card.querySelector('i');
    icon.classList.toggle('fa-plus');
    icon.classList.toggle('fa-minus');
    
    const content = card.querySelector('.card-content');
    if (content.style.display === 'block') {
        content.style.opacity = 0;
        setTimeout(() => {
            content.style.display = 'none';
        }, 300);
    } else {
        content.style.display = 'block';
        setTimeout(() => {
            content.style.opacity = 1;
        }, 10);
    }

}