// Configurar gráficos específicos do Harris Fund
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded');
    
    // Gráfico Alocação Setorial
    try {
        const sectorChart = document.getElementById('sectorChart');
        console.log('Sector Chart element:', sectorChart);
        
        if (sectorChart) {
            const sectorCtx = sectorChart.getContext('2d');
            console.log('Creating sector chart');
            new Chart(sectorCtx, {
                type: 'pie',
                data: {
                    labels: ['Financeiro', 'Consumo Cíclico', 'Saúde', 'Tecnologia', 'Industriais', 'Comunicação', 'Materiais', 'Energia', 'Outros'],
                    datasets: [{
                        data: [22.5, 18.3, 15.7, 14.8, 11.2, 7.9, 4.1, 3.2, 2.3],
                        backgroundColor: [
                            '#1a365d', '#2d3748', '#4a5568', '#718096', '#a0aec0',
                            '#cbd5e0', '#e2e8f0', '#edf2f7', '#f7fafc'
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
            console.log('Sector chart created successfully');
        }
    } catch (error) {
        console.error('Error creating sector chart:', error);
    }

    // Gráfico Características do Portfólio
    try {
        const sizeChart = document.getElementById('sizeChart');
        console.log('Size Chart element:', sizeChart);
        
        if (sizeChart) {
            const sizeCtx = sizeChart.getContext('2d');
            console.log('Creating size chart');
            new Chart(sizeCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Large Cap Value', 'Large Cap Core', 'Mid Cap Value', 'Outros'],
                    datasets: [{
                        data: [68, 22, 7, 3],
                        backgroundColor: ['#1a365d', '#4a5568', '#a0aec0', '#e2e8f0'],
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
            console.log('Size chart created successfully');
        }
    } catch (error) {
        console.error('Error creating size chart:', error);
    }

    // Gráfico de Taxas
    try {
        const terChart = document.getElementById('terChart');
        console.log('TER Chart element:', terChart);
        
        if (terChart) {
            const terCtx = terChart.getContext('2d');
            console.log('Creating TER chart');
            new Chart(terCtx, {
                type: 'bar',
                data: {
                    labels: ['VUAA (ETF)', 'Dodge & Cox US Stock', 'T. Rowe Price US Large Cap Value', 'JPMorgan US Value', 'American Funds US Value', 'Wellington US Value', 'Harris US Value Equity'],
                    datasets: [{
                        label: 'Taxa de Administração (%)',
                        data: [0.07, 0.63, 0.72, 1.02, 1.25, 1.66, 2.00],
                        backgroundColor: ['#4b5563', '#4b5563', '#4b5563', '#4b5563', '#4b5563', '#4b5563', '#1a365d'],
                        borderColor: ['#374151', '#374151', '#374151', '#374151', '#374151', '#374151', '#1e3a8a'],
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
                            max: 2.5,
                            ticks: {
                                callback: function(value) {
                                    return value.toFixed(2) + '%';
                                }
                            },
                            title: {
                                display: true,
                                text: 'Taxa de Administração (%)'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Fundos de Investimento'
                            }
                        }
                    }
                }
            });
            console.log('TER chart created successfully');
        }
    } catch (error) {
        console.error('Error creating TER chart:', error);
    }
    
    // Gráfico de Desempenho
    const performanceCtx = document.getElementById('performanceChart').getContext('2d');
    const startDateSelector = document.getElementById('startDateSelector');
    const resetButton = document.getElementById('resetChart');

    // Dados originais
    const performanceLabels = [
        '01/2011', '02/2011', '03/2011', '04/2011', '05/2011', '06/2011', '07/2011', '08/2011', '09/2011', '10/2011', '11/2011', '12/2011',
        '01/2012', '02/2012', '03/2012', '04/2012', '05/2012', '06/2012', '07/2012', '08/2012', '09/2012', '10/2012', '11/2012', '12/2012',
        '01/2013', '02/2013', '03/2013', '04/2013', '05/2013', '06/2013', '07/2013', '08/2013', '09/2013', '10/2013', '11/2013', '12/2013',
        '01/2014', '02/2014', '03/2014', '04/2014', '05/2014', '06/2014', '07/2014', '08/2014', '09/2014', '10/2014', '11/2014', '12/2014',
        '01/2015', '02/2015', '03/2015', '04/2015', '05/2015', '06/2015', '07/2015', '08/2015', '09/2015', '10/2015', '11/2015', '12/2015',
        '01/2016', '02/2016', '03/2016', '04/2016', '05/2016', '06/2016', '07/2016', '08/2016', '09/2016', '10/2016', '11/2016', '12/2016',
        '01/2017', '02/2017', '03/2017', '04/2017', '05/2017', '06/2017', '07/2017', '08/2017', '09/2017', '10/2017', '11/2017', '12/2017',
        '01/2018', '02/2018', '03/2018', '04/2018', '05/2018', '06/2018', '07/2018', '08/2018', '09/2018', '10/2018', '11/2018', '12/2018',
        '01/2019', '02/2019', '03/2019', '04/2019', '05/2019', '06/2019', '07/2019', '08/2019', '09/2019', '10/2019', '11/2019', '12/2019',
        '01/2020', '02/2020', '03/2020', '04/2020', '05/2020', '06/2020', '07/2020', '08/2020', '09/2020', '10/2020', '11/2020', '12/2020',
        '01/2021', '02/2021', '03/2021', '04/2021', '05/2021', '06/2021', '07/2021', '08/2021', '09/2021', '10/2021', '11/2021', '12/2021',
        '01/2022', '02/2022', '03/2022', '04/2022', '05/2022', '06/2022', '07/2022', '08/2022', '09/2022', '10/2022', '11/2022', '12/2022',
        '01/2023', '02/2023', '03/2023', '04/2023', '05/2023', '06/2023', '07/2023', '08/2023', '09/2023', '10/2023', '11/2023', '12/2023',
        '01/2024', '02/2024', '03/2024', '04/2024', '05/2024', '06/2024', '07/2024', '08/2024', '09/2024', '10/2024', '11/2024', '12/2024',
        '01/2025', '02/2025', '03/2025', '04/2025'
    ];

    const originalSP500TR = [
        0.000000, -0.002545, -0.028284, -0.029543, -0.024558, -0.026257, -0.028052, 0.013656, 0.010952, -0.029393, -0.025775, -0.016896,
        0.034401, -0.011302, -0.003699, -0.003299, -0.000368, -0.002527, 0.052592, 0.055246, -0.000245, 0.008652, 0.009061, 0.011452,
        0.209112, 0.167236, 0.164800, 0.170467, 0.207776, 0.208590, 0.166818, 0.163428, 0.166541, 0.175402, 0.175480, 0.215052,
        0.544853, 0.493583, 0.493124, 0.432348, 0.429872, 0.489398, 0.498473, 0.498605, 0.499118, 0.502581, 0.486335, 0.486667,
        0.722604, 0.712616, 0.707463, 0.700873, 0.681419, 0.666473, 0.686377, 0.716579, 0.702159, 0.724404, 0.724949, 0.688386,
        0.649804, 0.618930, 0.627569, 0.710485, 0.713929, 0.692057, 0.651999, 0.634103, 0.577113, 0.577358, 0.635494, 0.648259,
        0.982286, 0.952643, 0.960919, 0.972584, 0.971084, 0.978628, 0.994451, 0.996469, 0.971616, 0.971625, 0.977387, 0.973193,
        1.503340, 1.388632, 1.403919, 1.414103, 1.431080, 1.391240, 1.379343, 1.435166, 1.439065, 1.436370, 1.453698, 1.470266,
        1.449031, 1.267880, 1.212320, 1.288279, 1.477301, 1.472029, 1.304325, 1.326720, 1.336999, 1.347556, 1.347219, 1.485290,
        1.288820, 2.003485, 1.982595, 2.043567, 2.077872, 1.993147, 1.985058, 1.999786, 2.020549, 2.011929, 2.100871, 2.121016,
        2.546543, 2.595876, 2.599503, 2.474270, 2.499295, 2.519332, 2.572350, 2.592427, 2.677143, 2.675966, 2.568874, 2.570360,
        3.333005, 3.373876, 3.567247, 3.564675, 3.476492, 3.472502, 3.455202, 3.310283, 3.373399, 3.448781, 3.489530, 3.502249,
        2.991188, 2.709003, 2.701637, 2.729730, 2.686890, 2.771170, 3.035332, 2.990743, 2.768984, 2.795286, 2.844138, 2.857726,
        3.832059, 3.666896, 3.629677, 3.614413, 3.622842, 3.879788, 3.920069, 3.688176, 3.681910, 3.708512, 3.705522, 3.709457,
        4.638279, 4.854736, 4.928945, 5.028725, 5.052346, 4.962236, 4.896094, 4.905428, 4.860498, 4.815568, 5.060785, 5.044925
    ];

    const harrisReturns = [
        0.000000, -0.001030, -0.035079, -0.035814, -0.028901, -0.030593, -0.031990, 0.015002, 0.007501, -0.034785, -0.029048, -0.018606,
        -0.000735, -0.071408, -0.054787, -0.054420, -0.049272, -0.052361, 0.028607, 0.034932, -0.047875, -0.038609, -0.038976, -0.031622,
        0.148551, 0.105677, 0.104207, 0.111046, 0.148992, 0.148845, 0.105898, 0.100824, 0.109281, 0.116635, 0.115017, 0.156714,
        0.480880, 0.452934, 0.452714, 0.380129, 0.379615, 0.448448, 0.456538, 0.457420, 0.458156, 0.462568, 0.429916, 0.432637,
        0.618106, 0.654434, 0.613987, 0.603545, 0.615532, 0.596411, 0.615385, 0.641418, 0.623327, 0.632299, 0.634873, 0.605163,
        0.393587, 0.363656, 0.370716, 0.490293, 0.483453, 0.451243, 0.406898, 0.391602, 0.336594, 0.331225, 0.390940, 0.402339,
        0.787469, 0.742242, 0.755552, 0.775188, 0.769378, 0.776364, 0.798059, 0.796294, 0.772540, 0.780850, 0.789087, 0.782394,
        1.149654, 1.033608, 1.052875, 1.071481, 1.087513, 1.044418, 1.035226, 1.088469, 1.089351, 1.087586, 1.111046, 1.122297,
        0.960141, 0.742168, 0.706574, 0.778056, 0.981468, 0.975217, 0.796882, 0.811222, 0.828210, 0.836667, 0.845124, 0.982350,
        0.570231, 1.295558, 1.276291, 1.279673, 1.313281, 1.281659, 1.272761, 1.289013, 1.300485, 1.288719, 1.322695, 1.346227,
        1.637741, 1.691278, 1.712825, 1.630387, 1.646492, 1.696058, 1.729151, 1.732166, 1.793499, 1.790925, 1.721209, 1.722533,
        2.310707, 2.333064, 2.391602, 2.427342, 2.370054, 2.372408, 2.367995, 2.305633, 2.344315, 2.358435, 2.396088, 2.398882,
        2.266142, 1.888292, 1.902118, 1.959259, 1.937270, 2.010149, 2.313355, 2.269451, 2.033314, 2.060744, 2.100750, 2.119503,
        2.763421, 2.722165, 2.672967, 2.657082, 2.673849, 2.734887, 2.750037, 2.709443, 2.681277, 2.677600, 2.667745, 2.662083,
        3.219370, 3.188557, 3.220547, 3.377041, 3.391602, 3.234005, 3.215546, 3.213193, 3.213046, 3.151052, 3.371672, 3.356302
    ];

    const iveReturns = [
        0.000000, 0.036917, 0.034250, 0.059898, 0.040621, 0.017981, -0.018469, -0.079220, -0.147409, -0.051869, -0.055505, -0.037534,
        0.009732, 0.051506, 0.086282, 0.071894, 0.000959, 0.047551, 0.056297, 0.079677, 0.113140, 0.105188, 0.106711, 0.131468,
        0.204241, 0.218216, 0.264236, 0.286677, 0.318368, 0.305165, 0.373550, 0.324113, 0.356872, 0.416295, 0.456142, 0.489265,
        0.429667, 0.483689, 0.522648, 0.540696, 0.559444, 0.589898, 0.567005, 0.622831, 0.595009, 0.623520, 0.661947, 0.670493,
        0.595672, 0.683142, 0.658535, 0.682366, 0.694192, 0.660878, 0.668263, 0.567396, 0.523250, 0.635640, 0.644885, 0.615376,
        0.535455, 0.544579, 0.650874, 0.683734, 0.699154, 0.715269, 0.760874, 0.770844, 0.764165, 0.737599, 0.847024, 0.894860,
        0.905887, 0.978034, 0.955037, 0.953158, 0.946581, 0.983284, 1.010871, 0.985929, 1.051483, 1.075057, 1.144637, 1.183733,
        1.271663, 1.145502, 1.102094, 1.112668, 1.117859, 1.131001, 1.215947, 1.245553, 1.254620, 1.134143, 1.187862, 0.982389,
        1.151737, 1.199954, 1.222229, 1.313295, 1.138654, 1.310729, 1.351168, 1.288528, 1.375836, 1.438453, 1.532975, 1.609178,
        1.539381, 1.299101, 0.948054, 1.155306, 1.224931, 1.202788, 1.285028, 1.365640, 1.305486, 1.263252, 1.555409, 1.640927,
        1.598843, 1.752117, 1.928124, 2.034891, 2.106829, 2.071688, 2.096030, 2.146795, 2.042880, 2.181193, 2.077825, 2.293782,
        2.239106, 2.193052, 2.289730, 2.126215, 2.177763, 1.915395, 2.087612, 1.999595, 1.744618, 2.060894, 2.241562, 2.115614,
        2.332743, 2.231803, 2.274941, 2.331695, 2.269329, 2.490652, 2.611056, 2.510142, 2.349431, 2.288469, 2.603294, 2.803308,
        2.811400, 2.923822, 3.104636, 2.928418, 3.045530, 3.017726, 3.209550, 3.331842, 3.377639, 3.321467, 3.577461, 3.261012,
        3.379101, 3.402093, 3.270985, 3.075117
    ];

    // IWVL (iShares Edge MSCI World Value Factor UCITS ETF) - retornos acumulados a partir de 2014-10
    const iwvlRaw = [
        0.0, 0.014527354074354681, 0.004776152805309408, -0.022587031274292624, 0.04258705253031714, 0.03124377502137743, 0.06268659752992845, 0.07265673585199006, 0.04656716721567933, 0.052736348773709585, -0.017711430639769876, -0.0784079328698305, -0.002388038445467977, -0.018507468759717094, -0.032437832201298145, -0.12029847102378732, -0.12258706164004196, -0.06985071286633238, -0.05313429191930974, -0.044378100343011484, -0.08487560974424746, -0.03174131782493783, -0.011542324996113185, -0.004179086258162323, -0.0037810671981887145, 0.02049748814521135, 0.044378100343011484, 0.06308454067552871, 0.08895524817319655, 0.09253734379858525, 0.09930351598938891, 0.10766168850571356, 0.12238809006724183, 0.15900500852670252, 0.1530347985414724, 0.19004973606090636, 0.22507465419484607, 0.25253728610366144, 0.2803979370724503, 0.34487565832944655, 0.29850746268656714, 0.25810947702891784, 0.2955223576939521, 0.25850749608889156, 0.23422886483111793, 0.26885568799071047, 0.2517413238980877, 0.2732338217360464, 0.18308459229730256, 0.1852736591699704, 0.10069654474210976, 0.18726367855546489, 0.2059701188879819, 0.19363183168629505, 0.21432836731868, 0.11880599444185314, 0.19402985074626855, 0.19800996543163096, 0.14029849227981184, 0.1986069560644046, 0.23940296078202739, 0.2672636876651897, 0.30029843458488803, 0.2593034582944651, 0.12995022446361948, -0.028059698455962345, 0.025472612523320892, 0.05154229159378887, 0.06348255973550221, 0.03920400439210203, 0.09890549692941542, 0.06945276972073233, 0.028457717515935954, 0.19960196575715172, 0.25253728610366144, 0.27721393642140857, 0.3540298689657182, 0.4292537252701336, 0.4415920883861941, 0.49293525657843595, 0.45990050965873763, 0.456716357178949, 0.46945266344060954, 0.451542337142413, 0.45791049027324315, 0.40895528461209585, 0.504477581574549, 0.4985075234180658, 0.48935316095304726, 0.49452733281833017, 0.4137313615030318, 0.4503482040481188, 0.30626864457011815, 0.33771146707866917, 0.2943283764284048, 0.18109449699743463, 0.2640796110997745, 0.3643780608675373, 0.35721386961675994, 0.4487562796369713, 0.4296516684157339, 0.43263677340834894, 0.44756214654267734, 0.4057711321323072, 0.5052736196944962, 0.5665671884717041, 0.5251741172069342, 0.5032836003090018, 0.43164183962997504, 0.5379104234685945, 0.6222884904092818, 0.6254726428890702, 0.6425870828960665, 0.7333333029675839, 0.6660696760338931, 0.7122388241895989, 0.6881592404189987, 0.7556219148398631, 0.7607960867051462, 0.7850745661341729, 0.727761187956701, 0.7564179529598103, 0.7054725760844216, 0.7820896129703048, 0.8248755611590486, 0.8181094648826182, 0.8095522448791199
    ];
    
    const iwvlStartIndex = performanceLabels.findIndex(l => l === '10/2014');
    const harrisValueAtStart = harrisReturns[iwvlStartIndex];
    
    // Ajustar os retornos do IWVL para começar do mesmo ponto que o Harris
    const iwvlAdjusted = iwvlRaw.map(value => value + harrisValueAtStart);
    
    // Combinar os retornos do Harris até o início do IWVL com os retornos do IWVL
    const iwvlReturns = harrisReturns.slice(0, iwvlStartIndex).concat(iwvlAdjusted);

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
        const baseValueHarris = harrisReturns[startIndex];
        const baseValueSP500TR = originalSP500TR[startIndex];
        const baseValueIVE = iveReturns[startIndex];
        
        const normalizedHarris = harrisReturns.slice(startIndex).map(value => 
            value - baseValueHarris
        );
        
        const normalizedSP500TR = originalSP500TR.slice(startIndex).map(value => 
            value - baseValueSP500TR
        );

        const normalizedIVE = iveReturns.slice(startIndex).map(value => 
            value - baseValueIVE
        );
        
        const normalizedLabels = performanceLabels.slice(startIndex);

        chartInstance = new Chart(performanceCtx, {
            type: 'line',
            data: {
                labels: normalizedLabels,
                datasets: [
                    {
                        label: 'Harris Fund',
                        data: normalizedHarris,
                        backgroundColor: 'rgba(26, 54, 93, 0.5)',
                        borderColor: 'rgba(26, 54, 93, 1)',
                        borderWidth: 2,
                        pointRadius: 2,
                        tension: 0.1
                    },
                    {
                        label: 'S&P 500 TR',
                        data: normalizedSP500TR,
                        backgroundColor: 'rgba(153, 27, 27, 0.5)',
                        borderColor: 'rgba(153, 27, 27, 1)',
                        borderWidth: 2,
                        pointRadius: 0,
                        tension: 0.1
                    },
                    {
                        label: 'S&P 500 Value Index',
                        data: normalizedIVE,
                        backgroundColor: 'rgba(75, 192, 192, 0.5)',
                        borderColor: 'rgba(75, 192, 192, 1)',
                        borderWidth: 2,
                        pointRadius: 0,
                        tension: 0.1
                    },
                    {
                        label: 'IWVL (MSCI World Value ETF)',
                        data: iwvlReturns,
                        backgroundColor: 'rgba(180, 83, 9, 0.3)',
                        borderColor: '#b45309',
                        borderWidth: 2,
                        pointRadius: 0,
                        tension: 0.1,
                        spanGaps: true
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
                                return context.dataset.label + ': ' + (context.raw * 100).toFixed(2) + '%';
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
                                return (value * 100).toFixed(2) + '%';
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

// Função para download dos dados do Harris Fund
function downloadData() {
    let csvContent = "data:text/csv;charset=utf-8,";
    csvContent += "Fundo,Domicílio,Estilo,Política,Taxa (%),Gestora,Lançamento\n";
    
    // Dados do Harris Fund e concorrentes
    csvContent += "Harris US Value,Luxemburgo,Value,Acumulação,1.58,Harris Associates,2001\n";
    csvContent += "Dodge & Cox US Stock,EUA,Value,Distribuição,0.52,Dodge & Cox,1965\n";
    csvContent += "T. Rowe Price Value,EUA,Value,Distribuição,0.72,T. Rowe Price,1994\n";
    csvContent += "Fidelity US Value,EUA,Value,Distribuição,0.85,Fidelity,1978\n";
    csvContent += "JPMorgan US Value,EUA,Value,Distribuição,1.02,JPMorgan,1992\n";
    csvContent += "Wellington US Value,EUA,Value,Distribuição,1.15,Wellington,1928\n";
    csvContent += "American Funds Value,EUA,Value,Distribuição,1.25,Capital Group,1952\n";
    csvContent += "VUAA (ETF S&P 500),Irlanda,Passivo,Acumulação,0.07,Vanguard,2019\n";
    
    // Criação do elemento para download
    var encodedUri = encodeURI(csvContent);
    var link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "comparativo_fundos_value.csv");
    document.body.appendChild(link);
    
    // Download
    link.click();
    document.body.removeChild(link);
}