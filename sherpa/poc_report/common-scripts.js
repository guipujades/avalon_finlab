// Funções comuns para todas as páginas de análise

// Inicialização do seletor de produtos
function initializeProductSelector() {
    const productSelector = document.getElementById('productSelector');
    if (productSelector) {
        productSelector.addEventListener('change', function(e) {
            const selectedProduct = e.target.value;
            
            // Se não selecionou nada, não faz nada
            if (!selectedProduct) return;
            
            // Se selecionou "Voltar ao Início"
            if (selectedProduct === 'inicio') {
                window.location.href = '../../index.html';
                return;
            }
            
            // Mapeamento fixo de produtos para suas páginas
            const productPages = {
                'vuaa': 'vuaa.html',
                'harris': 'harris.html',
                'vontobel': 'vontobel.html',
                'private-equity': 'private-equity.html',
                'hedge-funds': 'hedge-funds.html'
            };
            
            // Se a página existe no mapeamento, redireciona
            if (productPages[selectedProduct]) {
                // Obtém o caminho base até a pasta 'poc_report'
                const pathParts = window.location.pathname.split('/');
                const pocReportIndex = pathParts.indexOf('poc_report');
                const basePath = pathParts.slice(0, pocReportIndex + 1).join('/');
                
                // Constrói o caminho completo
                const targetPath = `${basePath}/produtos/${selectedProduct}/${productPages[selectedProduct]}`;
                window.location.href = targetPath;
            }
        });
    }
}

// Inicialização da navegação
function initializeNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    const sections = document.querySelectorAll('section');
    
    function setActiveLink() {
        let currentSection = '';
        
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;
            
            if (window.scrollY >= (sectionTop - 100)) {
                currentSection = section.getAttribute('id');
            }
        });
        
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${currentSection}`) {
                link.classList.add('active');
            }
        });
    }
    
    window.addEventListener('scroll', setActiveLink);
    setActiveLink();
}

// Inicialização do botão de impressão
function initializePrintButton() {
    const printBtn = document.getElementById('printBtn');
    if (printBtn) {
        printBtn.addEventListener('click', function() {
            window.print();
        });
    }
}

// Inicialização do download de dados
function initializeDownloadButton() {
    const downloadBtn = document.getElementById('downloadBtn');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', function() {
            // Esta função deve ser personalizada para cada página
            if (typeof downloadData === 'function') {
                downloadData();
            }
        });
    }
}

// Inicialização geral
document.addEventListener('DOMContentLoaded', function() {
    initializeProductSelector();
    initializeNavigation();
    initializePrintButton();
    initializeDownloadButton();
});