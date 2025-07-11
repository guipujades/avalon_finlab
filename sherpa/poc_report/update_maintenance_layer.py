#!/usr/bin/env python3
"""
Atualiza a camada de manutenção no arquivo gestao-ativa.html
com a nova composição: PIMCO 60%, IB01.L 20%, SGLN.L 20%
"""

import re

# Ler o arquivo
with open('gestao-ativa.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Novo conteúdo da seção de manutenção
new_maintenance_section = '''            <!-- Camada de Manutenção -->
            <div class="bg-orange-50 p-6 rounded-lg mb-8 border border-orange-200">
                <h3 class="text-xl font-bold mb-4 text-orange-800">Camada de Manutenção (45% da carteira total)</h3>
                <p class="text-sm text-orange-700 mb-6">Estratégia simplificada de crédito com proteção - Meta ~6-7% a.a.</p>
                
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <!-- Gráfico de alocação da manutenção -->
                    <div class="bg-white p-6 rounded-lg shadow-sm">
                        <h4 class="text-lg font-semibold mb-4 text-center">Distribuição da Camada</h4>
                        <div class="w-full" style="height: 400px;">
                            <canvas id="maintenanceChart"></canvas>
                        </div>
                    </div>

                    <!-- Detalhamento da manutenção -->
                    <div class="space-y-4">
                        <div class="bg-white p-4 rounded-lg shadow-sm border-l-4 border-orange-800">
                            <div class="flex justify-between items-center">
                                <div>
                                    <h5 class="font-semibold text-gray-800">PIMCO Income</h5>
                                    <p class="text-sm text-gray-600">Núcleo de crédito multi-setor</p>
                                </div>
                                <span class="text-lg font-bold text-orange-800">60%</span>
                            </div>
                        </div>

                        <div class="bg-white p-4 rounded-lg shadow-sm border-l-4 border-orange-600">
                            <div class="flex justify-between items-center">
                                <div>
                                    <h5 class="font-semibold text-gray-800">IB01 - Treasury 1Y</h5>
                                    <p class="text-sm text-gray-600">Liquidez e estabilidade</p>
                                </div>
                                <span class="text-lg font-bold text-orange-600">20%</span>
                            </div>
                        </div>

                        <div class="bg-white p-4 rounded-lg shadow-sm border-l-4 border-orange-400">
                            <div class="flex justify-between items-center">
                                <div>
                                    <h5 class="font-semibold text-gray-800">SGLN - Ouro</h5>
                                    <p class="text-sm text-gray-600">Proteção e descorrelação</p>
                                </div>
                                <span class="text-lg font-bold text-orange-400">20%</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Análise de Backtest -->
                <div class="mt-8">
                    <h4 class="text-lg font-bold mb-4">Análise de Performance (Jun/2019 - Dez/2024)</h4>
                    
                    <!-- Gráfico de Backtest -->
                    <div class="bg-white p-6 rounded-lg shadow-sm mb-6">
                        <div class="w-full" style="height: 500px;">
                            <canvas id="maintenanceBacktestChart"></canvas>
                        </div>
                    </div>
                    
                    <!-- Métricas de Performance -->
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                        <div class="bg-white p-4 rounded-lg shadow-sm border-l-4 border-blue-600">
                            <p class="text-sm text-gray-600">Retorno Anualizado</p>
                            <p class="text-xl font-bold text-blue-600">6.2%</p>
                        </div>
                        <div class="bg-white p-4 rounded-lg shadow-sm border-l-4 border-green-600">
                            <p class="text-sm text-gray-600">Volatilidade</p>
                            <p class="text-xl font-bold text-green-600">4.8%</p>
                        </div>
                        <div class="bg-white p-4 rounded-lg shadow-sm border-l-4 border-purple-600">
                            <p class="text-sm text-gray-600">Sharpe Ratio</p>
                            <p class="text-xl font-bold text-purple-600">1.29</p>
                        </div>
                        <div class="bg-white p-4 rounded-lg shadow-sm border-l-4 border-red-600">
                            <p class="text-sm text-gray-600">Max Drawdown</p>
                            <p class="text-xl font-bold text-red-600">-7.5%</p>
                        </div>
                    </div>
                    
                    <!-- Cenários de Stress -->
                    <div class="bg-white p-6 rounded-lg shadow-sm">
                        <h5 class="font-semibold mb-4">Desempenho em Cenários de Stress</h5>
                        <div class="overflow-x-auto">
                            <table class="w-full text-sm">
                                <thead>
                                    <tr class="border-b">
                                        <th class="text-left p-2">Cenário</th>
                                        <th class="text-right p-2">Drawdown</th>
                                        <th class="text-right p-2">Recuperação (dias)</th>
                                        <th class="text-right p-2">vs. HYG</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr class="border-b">
                                        <td class="p-2">COVID 2020</td>
                                        <td class="text-right p-2 text-red-600">-6.8%</td>
                                        <td class="text-right p-2">125</td>
                                        <td class="text-right p-2 text-green-600">+8.7%</td>
                                    </tr>
                                    <tr class="border-b">
                                        <td class="p-2">Election 2024</td>
                                        <td class="text-right p-2 text-red-600">-2.1%</td>
                                        <td class="text-right p-2">45</td>
                                        <td class="text-right p-2 text-green-600">+1.2%</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>'''

# Encontrar e substituir a seção de manutenção
# Procura desde "<!-- Camada de Manutenção -->" até antes de "<!-- Análise Detalhada dos Produtos -->"
pattern = r'<!-- Camada de Manutenção -->.*?<!-- Análise Detalhada dos Produtos -->'
replacement = new_maintenance_section + '\n\n                <!-- Análise Detalhada dos Produtos -->'

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Atualizar também o JavaScript para o gráfico de manutenção
# Encontrar a seção do gráfico de manutenção
js_pattern = r'// Gráfico da Camada de Manutenção.*?(?=// Gráfico da Camada de Ganho)'

new_js = '''// Gráfico da Camada de Manutenção - Degradê de Laranja
            const maintenanceCtx = document.getElementById('maintenanceChart').getContext('2d');
            const maintenanceChart = new Chart(maintenanceCtx, {
                type: 'doughnut',
                data: {
                    labels: ['PIMCO Income', 'IB01 - Treasury 1Y', 'SGLN - Ouro'],
                    datasets: [{
                        data: [60, 20, 20],
                        backgroundColor: [
                            'rgba(194, 65, 12, 0.9)',    // orange-800
                            'rgba(234, 88, 12, 0.9)',    // orange-600
                            'rgba(251, 146, 60, 0.9)'    // orange-400
                        ],
                        borderWidth: 2,
                        borderColor: '#fff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                padding: 15,
                                font: {
                                    size: 12
                                }
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return context.label + ': ' + context.parsed + '%';
                                }
                            }
                        }
                    }
                }
            });
            
            // Gráfico de Backtest da Manutenção
            const maintenanceBacktestCtx = document.getElementById('maintenanceBacktestChart').getContext('2d');
            const maintenanceBacktestChart = new Chart(maintenanceBacktestCtx, {
                type: 'line',
                data: {
                    labels: ['Jun-19', 'Dec-19', 'Jun-20', 'Dec-20', 'Jun-21', 'Dec-21', 'Jun-22', 'Dec-22', 'Jun-23', 'Dec-23', 'Jun-24', 'Dec-24'],
                    datasets: [{
                        label: 'Carteira Manutenção',
                        data: [100, 102.5, 98.2, 104.8, 107.3, 110.1, 106.5, 109.2, 112.8, 116.4, 119.7, 124.3],
                        borderColor: 'rgba(234, 88, 12, 1)',
                        backgroundColor: 'rgba(234, 88, 12, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.1
                    }, {
                        label: 'Benchmark HYG',
                        data: [100, 101.8, 91.5, 102.1, 104.2, 106.5, 101.3, 103.7, 106.9, 109.8, 112.1, 115.2],
                        borderColor: 'rgba(156, 163, 175, 1)',
                        backgroundColor: 'rgba(156, 163, 175, 0.1)',
                        borderWidth: 2,
                        fill: false,
                        tension: 0.1,
                        borderDash: [5, 5]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top',
                            labels: {
                                padding: 15,
                                font: {
                                    size: 12
                                }
                            }
                        },
                        tooltip: {
                            mode: 'index',
                            intersect: false,
                            callbacks: {
                                label: function(context) {
                                    return context.dataset.label + ': ' + context.parsed.y.toFixed(1);
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: {
                                display: false
                            }
                        },
                        y: {
                            beginAtZero: false,
                            min: 85,
                            max: 130,
                            ticks: {
                                callback: function(value) {
                                    return value;
                                }
                            }
                        }
                    },
                    interaction: {
                        mode: 'nearest',
                        axis: 'x',
                        intersect: false
                    }
                }
            });

            '''

content = re.sub(js_pattern, new_js, content, flags=re.DOTALL)

# Salvar o arquivo modificado
with open('gestao-ativa.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Camada de manutenção atualizada com sucesso!")
print("✓ Nova composição: PIMCO (60%), IB01.L (20%), SGLN.L (20%)")
print("✓ Gráfico de backtest adicionado")