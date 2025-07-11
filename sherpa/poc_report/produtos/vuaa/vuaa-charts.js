// Configurar gráficos específicos do VUAA
document.addEventListener('DOMContentLoaded', function() {
    // Gráfico TER
    const terCtx = document.getElementById('terChart').getContext('2d');
    new Chart(terCtx, {
        type: 'bar',
        data: {
            labels: ['SPLG', 'SPYL', 'IVV', 'VOO', 'VUAA', 'CSPX', 'VUSA', 'SPY'],
            datasets: [{
                label: 'Taxa de Despesa Total (%)',
                data: [0.02, 0.03, 0.03, 0.03, 0.07, 0.07, 0.07, 0.0945],
                backgroundColor: ['#4b5563', '#4b5563', '#4b5563', '#4b5563', '#1a365d', '#1a365d', '#1a365d', '#9ca3af'],
                borderColor: ['#374151', '#374151', '#374151', '#374151', '#1e3a8a', '#1e3a8a', '#1e3a8a', '#6b7280'],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + context.raw.toFixed(2) + '%';
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 0.11,
                    ticks: {
                        callback: function(value) {
                            return value.toFixed(2) + '%';
                        }
                    },
                    title: {
                        display: true,
                        text: 'TER (%)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'ETFs S&P 500'
                    }
                }
            }
        }
    });
    
    // Gráfico Alocação Setorial
    const sectorCtx = document.getElementById('sectorChart').getContext('2d');
    new Chart(sectorCtx, {
        type: 'pie',
        data: {
            labels: ['Tecnologia', 'Financeiro', 'Saúde', 'Consumo Cíclico', 'Comunicação', 'Industriais', 'Consumo Defensivo', 'Energia', 'Utilitários', 'Imobiliário', 'Materiais Básicos'],
            datasets: [{
                data: [31.00, 14.21, 11.19, 10.35, 9.33, 7.46, 6.03, 3.66, 2.72, 2.27, 1.79],
                backgroundColor: [
                    '#1a365d', '#2d3748', '#4a5568', '#718096', '#a0aec0',
                    '#cbd5e0', '#e2e8f0', '#edf2f7', '#f7fafc', '#4b5563', '#6b7280'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        boxWidth: 15,
                        font: {
                            size: 10
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.label + ': ' + context.raw + '%';
                        }
                    }
                }
            }
        }
    });

    // Gráfico Concentração por Tamanho
    const sizeCtx = document.getElementById('sizeChart').getContext('2d');
    new Chart(sizeCtx, {
        type: 'doughnut',
        data: {
            labels: ['Top 10 Holdings', 'Outras 490 empresas'],
            datasets: [{
                data: [33.57, 66.43],
                backgroundColor: ['#1a365d', '#e2e8f0'],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.label + ': ' + context.raw + '%';
                        }
                    }
                }
            }
        }
    });
    
    // Gráfico de Desempenho
    const performanceCtx = document.getElementById('performanceChart').getContext('2d');
    const startDateSelector = document.getElementById('startDateSelector');
    const resetButton = document.getElementById('resetChart');

    // Dados originais
    const performanceLabels = [
        '05/2019', '06/2019', '07/2019', '08/2019', '09/2019', '10/2019', '11/2019', '12/2019',
        '01/2020', '02/2020', '03/2020', '04/2020', '05/2020', '06/2020', '07/2020', '08/2020', 
        '09/2020', '10/2020', '11/2020', '12/2020', '01/2021', '02/2021', '03/2021', '04/2021', 
        '05/2021', '06/2021', '07/2021', '08/2021', '09/2021', '10/2021', '11/2021', '12/2021', 
        '01/2022', '02/2022', '03/2022', '04/2022', '05/2022', '06/2022', '07/2022', '08/2022', 
        '09/2022', '10/2022', '11/2022', '12/2022', '01/2023', '02/2023', '03/2023', '04/2023', 
        '05/2023', '06/2023', '07/2023', '08/2023', '09/2023', '10/2023', '11/2023', '12/2023', 
        '01/2024', '02/2024', '03/2024', '04/2024', '05/2024', '06/2024', '07/2024', '08/2024', 
        '09/2024', '10/2024', '11/2024', '12/2024', '01/2025', '02/2025', '03/2025', '04/2025'
    ];

    const originalVUAA = [
        0.0096, 0.0366, 0.0681, 0.0343, 0.0575, 0.0764, 0.1202, 0.1482,
        0.1550, 0.0397, -0.0409, 0.0598, 0.0976, 0.1215, 0.1834, 0.2771,
        0.2351, 0.1959, 0.3199, 0.3704, 0.3714, 0.4068, 0.4664, 0.5411,
        0.5548, 0.5861, 0.6264, 0.6766, 0.6108, 0.7039, 0.7027, 0.7725,
        0.6603, 0.6313, 0.7106, 0.5757, 0.5380, 0.4148, 0.5317, 0.4915,
        0.3755, 0.4542, 0.4881, 0.4422, 0.5240, 0.5027, 0.5429, 0.5688,
        0.5782, 0.6835, 0.7388, 0.7175, 0.6402, 0.5883, 0.7332, 0.8271,
        0.8652, 0.9411, 1.0091, 0.9464, 0.9977, 1.1111, 1.1245, 1.1509,
        1.2077, 1.2057, 1.3266, 1.2949, 1.3653, 1.2790, 1.1533, 1.0939
    ];

    const originalSP500 = [
        -0.0347, 0.0318, 0.0454, 0.0265, 0.0441, 0.0655, 0.1017, 0.1332,
        0.1314, 0.0362, -0.0934, 0.0216, 0.0678, 0.0875, 0.1474, 0.2278,
        0.1796, 0.1470, 0.2703, 0.3175, 0.3028, 0.3368, 0.3935, 0.4666,
        0.4746, 0.5074, 0.5417, 0.5864, 0.5109, 0.6154, 0.6019, 0.6718,
        0.5839, 0.5342, 0.5891, 0.4493, 0.4494, 0.3278, 0.4487, 0.3873,
        0.2577, 0.3581, 0.4311, 0.3467, 0.4299, 0.3926, 0.4414, 0.4625,
        0.4661, 0.5610, 0.6096, 0.5811, 0.5041, 0.4710, 0.6022, 0.6731,
        0.6997, 0.7876, 0.8430, 0.7663, 0.8511, 0.9153, 0.9370, 0.9812,
        1.0212, 1.0012, 1.1159, 1.0630, 1.1188, 1.0886, 0.9684, 0.8547
    ];

    const originalSP500TR = [
        0.05879999610331166, 0.13342073405364596, 0.14971151392710103, 0.1314985239419646, 0.15266962490253566, 0.17763531343799155, 0.22038235879282042, 0.2572169290124551,
        0.2567239417400131, 0.15327201919268818, 0.01082736059691225, 0.14040938832109995, 0.19472416505022716, 0.2184850650053778, 0.2871895810048428, 0.37971251058007005,
        0.32728734666625137, 0.29199121896278335, 0.43341730571730275, 0.48853015418521095, 0.47350158284228105, 0.5141327077150297, 0.5804450692467729, 0.6647918849967374,
        0.6760325193626058, 0.7155558045106405, 0.756307670518517, 0.8097093482676401, 0.7255408809438069, 0.8464345114695637, 0.83364100934718, 0.9158182314805192,
        0.8166806735125973, 0.7622853402464569, 0.8277189798320141, 0.6683389953962866, 0.6713986450765146, 0.5334353653688564, 0.6748249206705441, 0.6065232810265366,
        0.45856330975711934, 0.5766504816718883, 0.664761161108202, 0.5688465203135475, 0.667423835667661, 0.6267390376603674, 0.6864636542018843, 0.7127874697491459,
        0.7202327671769944, 0.833898040902487, 0.8928110971687926, 0.8626754586945409, 0.7738665601571855, 0.7365675721346312, 0.8951610999601702, 0.9812595520382101,
        1.0145528194225917, 1.1221216493632458, 1.1904002460908516, 1.1009332193801775, 1.205108371023175, 1.284231563699799, 1.3120363081426154, 1.3681178958033025,
        1.4186939125111029, 1.3967611775941906, 1.537452420124445, 1.4769643898891411, 1.545941205717789, 1.5127226873061241, 1.3711451355279416, 1.2334426529253433
    ];

    // Preencher o seletor de datas
    performanceLabels.forEach((label, index) => {
        const option = document.createElement('option');
        option.value = index;
        option.textContent = label;
        startDateSelector.appendChild(option);
    });

    let chartInstance;

    function createChart(startIndex = 0) {
        // Destruir o gráfico existente se houver
        if (chartInstance) {
            chartInstance.destroy();
        }

        // Normalizar os dados a partir do índice selecionado
        const baseValueVUAA = originalVUAA[startIndex];
        const baseValueSP500 = originalSP500[startIndex];
        const baseValueSP500TR = originalSP500TR[startIndex];
        
        const normalizedVUAA = originalVUAA.slice(startIndex).map(value => 
            ((value - baseValueVUAA) * 100)
        );
        
        const normalizedSP500 = originalSP500.slice(startIndex).map(value => 
            ((value - baseValueSP500) * 100)
        );
        
        const normalizedSP500TR = originalSP500TR.slice(startIndex).map(value => 
            ((value - baseValueSP500TR) * 100)
        );
        
        const normalizedLabels = performanceLabels.slice(startIndex);

        chartInstance = new Chart(performanceCtx, {
            type: 'line',
            data: {
                labels: normalizedLabels,
                datasets: [
                    {
                        label: 'VUAA LN',
                        data: normalizedVUAA,
                        backgroundColor: 'rgba(26, 54, 93, 0.5)',
                        borderColor: 'rgba(26, 54, 93, 1)',
                        borderWidth: 2,
                        pointRadius: 0,
                        tension: 0.1
                    },
                    {
                        label: 'S&P 500',
                        data: normalizedSP500,
                        backgroundColor: 'rgba(153, 27, 27, 0.5)',
                        borderColor: 'rgba(153, 27, 27, 1)',
                        borderWidth: 2,
                        pointRadius: 0,
                        tension: 0.1
                    },
                    {
                        label: 'S&P 500 TR',
                        data: normalizedSP500TR,
                        backgroundColor: 'rgba(37, 99, 235, 0.5)',
                        borderColor: 'rgba(37, 99, 235, 1)',
                        borderWidth: 2,
                        pointRadius: 0,
                        tension: 0.1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ' + context.raw.toFixed(2) + '%';
                            }
                        }
                    },
                    title: {
                        display: true,
                        text: `Retorno Acumulado desde ${performanceLabels[startIndex]}`
                    }
                },
                scales: {
                    y: {
                        ticks: {
                            callback: function(value) {
                                return value.toFixed(1) + '%';
                            }
                        },
                        title: {
                            display: true,
                            text: 'Retorno Acumulado (%)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Período'
                        }
                    }
                }
            }
        });
    }

    // Criar o gráfico inicial
    createChart(0);

    // Event listener para o seletor de data
    startDateSelector.addEventListener('change', function() {
        createChart(parseInt(this.value));
    });

    // Event listener para o botão de reset
    resetButton.addEventListener('click', function() {
        startDateSelector.value = '0';
        createChart(0);
    });
});

// Função para download dos dados do VUAA
function downloadData() {
    let csvContent = "data:text/csv;charset=utf-8,";
    csvContent += "ETF,Domicílio,Método,Dividendos,TER (%),AUM ($B),Lançamento\n";
    
    // Dados do VUAA e concorrentes
    csvContent += "VUAA,Irlanda,Física,Acumulação,0.07,62.51,2019\n";
    csvContent += "CSPX,Irlanda,Física,Acumulação,0.07,60.00,2010\n";
    csvContent += "SPYL,Irlanda,Física,Acumulação,0.03,4.00,2023\n";
    csvContent += "SPLG,EUA,Física,Distribuição,0.02,15.37,2019\n";
    csvContent += "VUSA,Irlanda,Física,Distribuição,0.07,35.33,2012\n";
    csvContent += "SPY,EUA,Física,Distribuição,0.0945,598.19,1993\n";
    csvContent += "IVV,EUA,Física,Distribuição,0.03,556.38,2000\n";
    csvContent += "VOO,EUA,Física,Distribuição,0.03,594.75,2010\n";
    
    // Criação do elemento para download
    var encodedUri = encodeURI(csvContent);
    var link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "comparativo_etf_sp500.csv");
    document.body.appendChild(link);
    
    // Download
    link.click();
    document.body.removeChild(link);
}