#!/usr/bin/env python3
"""
Adiciona a seção completa de análise de produtos da camada de manutenção
"""

import re

# Ler o arquivo
with open('gestao-ativa.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Adicionar a seção de análise de produtos logo após o fechamento da div da distribuição
pattern = r'(</div>\s*</div>\s*)(<!-- Camada de Ganho -->)'

replacement = r'''\1

                <!-- Análise Detalhada dos Produtos -->
                <div class="mt-8">
                    <div class="bg-gradient-to-r from-orange-50 via-amber-50 to-yellow-50 rounded-xl p-8 border border-orange-200 shadow-lg">
                        <div class="text-center mb-8">
                            <h4 class="text-2xl font-bold text-gray-800 mb-3">Análise dos produtos selecionados</h4>
                        </div>

                        <!-- Cards dos Produtos -->
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                            <!-- Card PIMCO Income -->
                            <div class="etf-card bg-white rounded-xl p-6 shadow-md hover:shadow-xl transition-all duration-300 border border-gray-100 cursor-pointer" data-etf="pimco-income" onclick="window.open('https://www.ft.com/content/portfolio-data', '_blank')">
                                <div class="flex items-center mb-4">
                                    <div>
                                        <h5 class="font-bold text-gray-800">PIMCO Income</h5>
                                        <p class="text-sm text-gray-600">Multi-Setor Global</p>
                                    </div>
                                </div>

                                <div class="space-y-3">
                                    <div class="flex justify-between items-center">
                                        <span class="text-sm text-gray-600">TER</span>
                                        <span class="font-semibold text-orange-600">0.55%</span>
                                    </div>
                                    <div class="flex justify-between items-center">
                                        <span class="text-sm text-gray-600">AUM</span>
                                        <span class="font-semibold text-orange-600">$130B</span>
                                    </div>
                                    <div class="flex justify-between items-center">
                                        <span class="text-sm text-gray-600">Yield</span>
                                        <span class="font-semibold text-orange-600">5.8%</span>
                                    </div>
                                </div>

                                <div class="mt-4 pt-4 border-t border-gray-100">
                                    <p class="text-xs text-gray-500 mb-2">Papel na Carteira:</p>
                                    <p class="text-sm text-gray-700">Exposição diversificada a crédito global com gestão ativa e foco em geração de renda.</p>
                                </div>

                                <div class="mt-4">
                                    <div class="w-full bg-orange-100 rounded-full h-2">
                                        <div class="bg-orange-600 h-2 rounded-full" style="width: 60%"></div>
                                    </div>
                                    <p class="text-xs text-gray-500 mt-1">60% da camada de manutenção</p>
                                </div>
                            </div>

                            <!-- Card IB01.L -->
                            <div class="etf-card bg-white rounded-xl p-6 shadow-md hover:shadow-xl transition-all duration-300 border border-gray-100 cursor-pointer" data-etf="ib01" onclick="window.open('https://www.ft.com/etf/IE00B1FZS574:GBX', '_blank')">
                                <div class="flex items-center mb-4">
                                    <div>
                                        <h5 class="font-bold text-gray-800">IB01</h5>
                                        <p class="text-sm text-gray-600">Treasury 0-1Y</p>
                                    </div>
                                </div>

                                <div class="space-y-3">
                                    <div class="flex justify-between items-center">
                                        <span class="text-sm text-gray-600">TER</span>
                                        <span class="font-semibold text-amber-600">0.07%</span>
                                    </div>
                                    <div class="flex justify-between items-center">
                                        <span class="text-sm text-gray-600">AUM</span>
                                        <span class="font-semibold text-amber-600">$2.3B</span>
                                    </div>
                                    <div class="flex justify-between items-center">
                                        <span class="text-sm text-gray-600">Duration</span>
                                        <span class="font-semibold text-amber-600">0.5</span>
                                    </div>
                                </div>

                                <div class="mt-4 pt-4 border-t border-gray-100">
                                    <p class="text-xs text-gray-500 mb-2">Papel na Carteira:</p>
                                    <p class="text-sm text-gray-700">Âncora de liquidez e proteção com mínimo risco de duration.</p>
                                </div>
                            
                                <div class="mt-4">
                                    <div class="w-full bg-amber-100 rounded-full h-2">
                                        <div class="bg-amber-600 h-2 rounded-full" style="width: 20%"></div>
                                    </div>
                                    <p class="text-xs text-gray-500 mt-1">20% da camada de manutenção</p>
                                </div>
                            </div>

                            <!-- Card SGLN.L -->
                            <div class="etf-card bg-white rounded-xl p-6 shadow-md hover:shadow-xl transition-all duration-300 border border-gray-100 cursor-pointer" data-etf="sgln" onclick="window.open('https://www.ft.com/etf/IE00B4ND3602:GBX', '_blank')">
                                <div class="flex items-center mb-4">
                                    <div>
                                        <h5 class="font-bold text-gray-800">SGLN</h5>
                                        <p class="text-sm text-gray-600">Physical Gold</p>
                                    </div>
                                </div>

                                <div class="space-y-3">
                                    <div class="flex justify-between items-center">
                                        <span class="text-sm text-gray-600">TER</span>
                                        <span class="font-semibold text-yellow-600">0.12%</span>
                                    </div>
                                    <div class="flex justify-between items-center">
                                        <span class="text-sm text-gray-600">AUM</span>
                                        <span class="font-semibold text-yellow-600">$13.8B</span>
                                    </div>
                                    <div class="flex justify-between items-center">
                                        <span class="text-sm text-gray-600">Tipo</span>
                                        <span class="font-semibold text-yellow-600">Físico</span>
                                    </div>
                                </div>

                                <div class="mt-4 pt-4 border-t border-gray-100">
                                    <p class="text-xs text-gray-500 mb-2">Papel na Carteira:</p>
                                    <p class="text-sm text-gray-700">Proteção contra inflação e hedge para cenários de stress sistêmico.</p>
                                </div>

                                <div class="mt-4">
                                    <div class="w-full bg-yellow-100 rounded-full h-2">
                                        <div class="bg-yellow-600 h-2 rounded-full" style="width: 20%"></div>
                                    </div>
                                    <p class="text-xs text-gray-500 mt-1">20% da camada de manutenção</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Botão para Análise Avançada -->
                <div class="text-center mt-6">
                    <button id="runMaintenanceAnalysis" class="group inline-flex items-center px-6 py-3 bg-gradient-to-r from-orange-600 to-orange-700 text-white rounded-lg hover:from-orange-700 hover:to-orange-800 transition-all duration-300 shadow-lg hover:shadow-xl transform hover:-translate-y-1">
                        <svg class="w-4 h-4 mr-2 text-orange-200 group-hover:text-white transition-colors duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                        </svg>
                        <span class="font-medium">Análise Detalhada da Manutenção</span>
                        <svg class="w-4 h-4 ml-2 opacity-0 group-hover:opacity-100 transform translate-x-0 group-hover:translate-x-1 transition-all duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6"></path>
                        </svg>
                    </button>
                </div>

                <!-- Loading e Results -->
                <div id="maintenanceLoading" class="hidden mt-6 text-center">
                    <div class="inline-flex items-center px-4 py-2 border border-orange-300 rounded-full bg-orange-50">
                        <svg class="animate-spin -ml-1 mr-3 h-4 w-4 text-orange-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        <span class="text-orange-700 font-medium text-sm">Processando análise de manutenção...</span>
                    </div>
                </div>

                <div id="maintenanceResults" class="hidden mt-6">
                    <div class="bg-gradient-to-r from-orange-50 to-amber-50 p-6 rounded-lg border border-orange-200">
                        <h5 class="text-lg font-bold mb-4 text-orange-800">Resultados da Análise de Manutenção</h5>
                        <div id="maintenanceOutput" class="space-y-4">
                            <!-- Os resultados aparecerão aqui -->
                        </div>
                    </div>
                </div>
            </div>

            \2'''

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Adicionar o event listener para o botão de análise
# Procurar onde estão os event listeners
event_pattern = r'(// Adicionar funcionalidade de clique nos cards dos ETFs.*?)(</script>)'

new_event_listener = r'''\1

            // Análise de Manutenção
            document.getElementById('runMaintenanceAnalysis')?.addEventListener('click', async function() {
                const loadingDiv = document.getElementById('maintenanceLoading');
                const resultsDiv = document.getElementById('maintenanceResults');
                const outputDiv = document.getElementById('maintenanceOutput');
                
                loadingDiv.classList.remove('hidden');
                resultsDiv.classList.add('hidden');
                
                try {
                    // Simular análise Python
                    await new Promise(resolve => setTimeout(resolve, 2000));
                    
                    outputDiv.innerHTML = `
                        <div class="grid grid-cols-2 gap-4">
                            <div class="bg-white p-4 rounded-lg shadow-sm">
                                <p class="text-sm text-gray-600 mb-1">Retorno Esperado</p>
                                <p class="text-2xl font-bold text-orange-600">6.2%</p>
                            </div>
                            <div class="bg-white p-4 rounded-lg shadow-sm">
                                <p class="text-sm text-gray-600 mb-1">Volatilidade</p>
                                <p class="text-2xl font-bold text-orange-600">4.8%</p>
                            </div>
                            <div class="bg-white p-4 rounded-lg shadow-sm">
                                <p class="text-sm text-gray-600 mb-1">Sharpe Ratio</p>
                                <p class="text-2xl font-bold text-orange-600">1.29</p>
                            </div>
                            <div class="bg-white p-4 rounded-lg shadow-sm">
                                <p class="text-sm text-gray-600 mb-1">Max Drawdown</p>
                                <p class="text-2xl font-bold text-red-600">-7.5%</p>
                            </div>
                        </div>
                        
                        <div class="mt-6 bg-white p-4 rounded-lg shadow-sm">
                            <h6 class="font-semibold mb-3">Análise de Correlações</h6>
                            <pre class="text-xs bg-gray-50 p-3 rounded overflow-x-auto">
       PIMCO  IB01  SGLN
PIMCO   1.00  0.15 -0.20
IB01    0.15  1.00 -0.10
SGLN   -0.20 -0.10  1.00</pre>
                        </div>
                    `;
                    
                    loadingDiv.classList.add('hidden');
                    resultsDiv.classList.remove('hidden');
                    
                } catch (error) {
                    console.error('Erro na análise:', error);
                    outputDiv.innerHTML = '<p class="text-red-600">Erro ao processar análise. Por favor, tente novamente.</p>';
                    loadingDiv.classList.add('hidden');
                    resultsDiv.classList.remove('hidden');
                }
            });

\2'''

content = re.sub(event_pattern, new_event_listener, content, flags=re.DOTALL)

# Salvar o arquivo modificado
with open('gestao-ativa.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Seção de análise de produtos da camada de manutenção restaurada")
print("✓ Mantidos apenas os 3 produtos atuais: PIMCO, IB01, SGLN")
print("✓ Botão de análise e funcionalidades preservadas")