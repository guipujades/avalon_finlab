#!/usr/bin/env python3
"""
Agente de Análise Financeira para Chimpa Invest
===============================================
Baseado no IntelligentResearchAgent do poc_InvestmentOrchestrator.
Adaptado para analisar relatórios de valuation e releases financeiros.

Funcionalidades:
1. Análise detalhada dos dados de valuation (arquivo TXT)
2. Análise do release parsed da empresa
3. Geração de insights combinados
4. Análise rápida para áudio (2 minutos)
5. Análise detalhada para relatório completo
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from dotenv import load_dotenv

# OpenAI/ChatGPT integration
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Fallback para requests se OpenAI não estiver disponível
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class ChimpaAnalysisAgent:
    """Agente de análise financeira para Chimpa Invest"""
    
    def __init__(self, openai_api_key: str = None):
        """
        Inicializa o agente de análise
        
        Args:
            openai_api_key: Chave da API do OpenAI (se None, tentará obter do .env)
        """
        load_dotenv()
        
        # Configuração da API
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY não encontrada. Configure no .env ou passe como parâmetro.")
        
        # Configurar cliente OpenAI
        if OPENAI_AVAILABLE:
            self.client = AsyncOpenAI(api_key=self.api_key)
            self.use_openai_lib = True
            print("ANALYSIS AGENT: Cliente OpenAI configurado")
        else:
            self.client = None
            self.use_openai_lib = False
            print("[AVISO] ANALYSIS AGENT: Usando requests para API OpenAI")
        
        # Configurações do modelo
        self.model_config = {
            "detailed_analysis": {
                "model": "gpt-4-turbo-preview",
                "max_tokens": 3000,
                "temperature": 0.1
            },
            "quick_analysis": {
                "model": "gpt-3.5-turbo",
                "max_tokens": 800,
                "temperature": 0.2
            }
        }
        
        # Prompts do sistema
        self.system_prompts = {
            "detailed_analyst": """Você é um analista financeiro sênior especializado em análise fundamentalista brasileira.
            
ESPECIALIDADES:
- Análise de demonstrações financeiras (DRE, Balanço, DFC)
- Múltiplos de valuation (P/L, EV/EBITDA, P/VPA, etc.)
- Análise setorial e comparativa
- Identificação de tendências e riscos
- Comunicação clara para investidores

METODOLOGIA:
1. Analise os dados quantitativos primeiro
2. Contextualize com informações qualitativas
3. Compare com setor e histórico
4. Identifique pontos de atenção
5. Forneça conclusão clara e objetiva

FORMATO DE RESPOSTA:
- Use linguagem técnica mas acessível
- Destaque insights principais
- Indique riscos e oportunidades
- Sugira pontos para monitoramento""",

            "quick_analyst": """Você é um analista financeiro especializado em comunicação concisa para investidores.

OBJETIVO: Análise rápida e objetiva para áudio de 2 minutos (aproximadamente 300 palavras).

FOCO:
- Top 3 insights mais relevantes
- Principal risco identificado
- Principal oportunidade
- Conclusão resumida sobre a empresa

FORMATO:
- Linguagem direta e clara
- Sem jargões excessivos
- Destaque números principais
- Conclusão prática para investimento""",

            "integration_analyst": """Você é especialista em combinar dados quantitativos (valuation) com informações qualitativas (releases).

PROCESSO:
1. Analise os dados de valuation (métricas, tendências, múltiplos)
2. Combine com informações do release (contexto, estratégia, outlook)
3. Identifique convergências e divergências
4. Gere insights únicos da combinação dos dados

PONTOS DE ATENÇÃO:
- Consistência entre números e narrativa
- Qualidade dos resultados vs. perspectivas
- Fatores que podem impactar métricas futuras
- Sustentabilidade das tendências observadas"""
        }
        
        # Configurações de análise
        self.analysis_config = {
            "detailed_max_words": 2000,
            "quick_max_words": 300,
            "key_metrics_focus": [
                "receita_liquida", "lucro_liquido", "ebit", "ebitda",
                "margem_liquida", "margem_ebitda", "roe", "roa", "roic",
                "divida_liquida", "liquidez_corrente", "p_l", "ev_ebitda"
            ]
        }
        
        # Cache de análises
        self.analysis_cache = {}
        
        print(f"CHIMPA ANALYSIS AGENT: Inicializado com modelo {self.model_config['detailed_analysis']['model']}")
    
    async def analyze_complete_valuation(self, valuation_txt_path: str, 
                                       parsed_release_path: str = None,
                                       analysis_type: str = "detailed") -> Dict:
        """
        Análise completa combinando valuation e release
        
        Args:
            valuation_txt_path: Caminho para o arquivo TXT de valuation
            parsed_release_path: Caminho para o release parsed (opcional)
            analysis_type: 'detailed' ou 'quick'
        
        Returns:
            Dict com análise completa
        """
        start_time = datetime.now()
        
        try:
            # Carregar dados de valuation
            valuation_data = self._load_valuation_txt(valuation_txt_path)
            if not valuation_data:
                return {"error": "Erro ao carregar dados de valuation", "status": "failed"}
            
            # Carregar release se fornecido
            release_data = None
            if parsed_release_path and Path(parsed_release_path).exists():
                release_data = self._load_parsed_release(parsed_release_path)
            
            # Análise dos dados de valuation
            valuation_analysis = await self._analyze_valuation_data(valuation_data, analysis_type)
            
            # Análise do release (se disponível)
            release_analysis = None
            if release_data:
                release_analysis = await self._analyze_release_data(release_data, analysis_type)
            
            # Análise integrada
            integrated_analysis = await self._integrate_analyses(
                valuation_analysis, release_analysis, analysis_type
            )
            
            # Montar resultado final
            result = {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "analysis_type": analysis_type,
                "empresa": valuation_data.get("empresa", "N/A"),
                "periodo": valuation_data.get("periodo", "N/A"),
                "valuation_analysis": valuation_analysis,
                "release_analysis": release_analysis,
                "integrated_analysis": integrated_analysis,
                "metadata": {
                    "valuation_file": valuation_txt_path,
                    "release_file": parsed_release_path,
                    "processing_time": (datetime.now() - start_time).total_seconds(),
                    "model_used": self.model_config[f"{analysis_type}_analysis"]["model"]
                }
            }
            
            # Cache da análise
            cache_key = f"{Path(valuation_txt_path).stem}_{analysis_type}"
            self.analysis_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            return {
                "error": f"Erro na análise: {str(e)}",
                "status": "failed",
                "timestamp": datetime.now().isoformat()
            }
    
    def _load_valuation_txt(self, file_path: str) -> Dict:
        """Carrega e processa arquivo TXT de valuation"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extrair informações básicas do header
            lines = content.split('\n')
            empresa = "N/A"
            periodo = "N/A"
            
            for line in lines[:10]:  # Primeiras 10 linhas
                if "RELATÓRIO COMPLETO DE VALUATION TEMPORAL" in line:
                    parts = line.split(' - ')
                    if len(parts) > 1:
                        empresa = parts[1].strip()
                elif "Período:" in line:
                    periodo = line.replace("Período:", "").strip()
                    break
            
            return {
                "empresa": empresa,
                "periodo": periodo,
                "content": content,
                "file_size": len(content),
                "sections": self._identify_valuation_sections(content)
            }
            
        except Exception as e:
            print(f"[ERRO] Erro ao carregar valuation TXT: {e}")
            return None
    
    def _load_parsed_release(self, file_path: str) -> Dict:
        """Carrega release parsed (TXT ou JSON)"""
        try:
            file_path = Path(file_path)
            
            if file_path.suffix.lower() == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {
                        "type": "json",
                        "content": data,
                        "summary": data.get("summary", ""),
                        "key_points": data.get("key_points", [])
                    }
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    return {
                        "type": "txt",
                        "content": content,
                        "word_count": len(content.split())
                    }
                    
        except Exception as e:
            print(f"[ERRO] Erro ao carregar release: {e}")
            return None
    
    def _identify_valuation_sections(self, content: str) -> Dict:
        """Identifica seções principais no arquivo de valuation"""
        sections = {}
        
        section_markers = {
            "dados_mercado": "DADOS DE MERCADO",
            "estatisticas_5anos": "ESTATÍSTICAS DOS ÚLTIMOS 5 ANOS",
            "serie_temporal": "SÉRIE TEMPORAL COMPLETA",
            "indicadores_prazos": "INDICADORES DE PRAZOS"
        }
        
        lines = content.split('\n')
        for i, line in enumerate(lines):
            for section_key, marker in section_markers.items():
                if marker in line:
                    sections[section_key] = {
                        "start_line": i,
                        "title": line.strip(),
                        "found": True
                    }
        
        return sections
    
    async def _analyze_valuation_data(self, valuation_data: Dict, analysis_type: str) -> Dict:
        """Analisa dados de valuation usando ChatGPT"""
        
        content = valuation_data["content"]
        empresa = valuation_data["empresa"]
        
        # Preparar prompt baseado no tipo de análise
        if analysis_type == "detailed":
            prompt = f"""Analise detalhadamente os dados de valuation da empresa {empresa}:

DADOS DE VALUATION:
{content[:3000]}  # Limitar para evitar excesso de tokens

ANÁLISE SOLICITADA:
1. SITUAÇÃO FINANCEIRA ATUAL
   - Principais métricas de rentabilidade
   - Situação de endividamento e liquidez
   - Comparação com histórico de 5 anos

2. TENDÊNCIAS IDENTIFICADAS
   - Evolução das margens
   - Crescimento de receita e lucro
   - Padrões de endividamento

3. PONTOS DE ATENÇÃO
   - Métricas que se deterioraram
   - Sinais de alerta
   - Inconsistências nos dados

4. OPORTUNIDADES
   - Pontos fortes identificados
   - Melhoria nas métricas
   - Potencial de crescimento

Seja específico com números e percentuais. Foque em insights acionáveis."""

        else:  # quick
            prompt = f"""Análise RÁPIDA (máximo 300 palavras) dos dados de valuation da {empresa}:

DADOS PRINCIPAIS:
{content[:1500]}

FORNEÇA:
1. TOP 3 INSIGHTS mais importantes
2. PRINCIPAL RISCO identificado
3. PRINCIPAL OPORTUNIDADE 
4. CONCLUSÃO RESUMIDA para investimento

Use números específicos. Seja direto e objetivo."""
        
        # Fazer chamada para ChatGPT
        response = await self._call_chatgpt(
            prompt, 
            self.system_prompts["detailed_analyst" if analysis_type == "detailed" else "quick_analyst"],
            analysis_type
        )
        
        return {
            "analysis": response,
            "metrics_analyzed": list(valuation_data.get("sections", {}).keys()),
            "empresa": empresa,
            "analysis_type": analysis_type
        }
    
    async def _analyze_release_data(self, release_data: Dict, analysis_type: str) -> Dict:
        """Analisa dados do release usando ChatGPT"""
        
        if release_data["type"] == "json":
            content = f"Resumo: {release_data.get('summary', '')}\nPontos principais: {release_data.get('key_points', [])}"
        else:
            content = release_data["content"][:2000]  # Limitar tamanho
        
        prompt = f"""Analise o release financeiro da empresa:

RELEASE CONTENT:
{content}

{"ANÁLISE DETALHADA:" if analysis_type == "detailed" else "ANÁLISE RÁPIDA (200 palavras):"}
1. PRINCIPAIS RESULTADOS do período
2. OUTLOOK E PERSPECTIVAS da gestão
3. FATORES QUALITATIVOS relevantes
4. RISCOS E OPORTUNIDADES mencionados

{"Seja detalhado e técnico." if analysis_type == "detailed" else "Seja conciso e objetivo."}"""
        
        response = await self._call_chatgpt(
            prompt,
            self.system_prompts["detailed_analyst" if analysis_type == "detailed" else "quick_analyst"],
            analysis_type
        )
        
        return {
            "analysis": response,
            "content_type": release_data["type"],
            "word_count": release_data.get("word_count", 0)
        }
    
    async def _integrate_analyses(self, valuation_analysis: Dict, 
                                release_analysis: Dict, analysis_type: str) -> Dict:
        """Integra análises de valuation e release"""
        
        valuation_text = valuation_analysis["analysis"]
        release_text = release_analysis["analysis"] if release_analysis else "Não disponível"
        
        prompt = f"""Combine e integre as análises quantitativas (valuation) e qualitativas (release):

ANÁLISE QUANTITATIVA (VALUATION):
{valuation_text}

ANÁLISE QUALITATIVA (RELEASE):
{release_text}

{"INTEGRAÇÃO DETALHADA:" if analysis_type == "detailed" else "INTEGRAÇÃO RÁPIDA (250 palavras):"}
1. CONVERGÊNCIAS entre dados quantitativos e narrativa
2. DIVERGÊNCIAS ou inconsistências identificadas
3. INSIGHTS ÚNICOS da combinação dos dados
4. RECOMENDAÇÃO FINAL baseada na análise integrada

{"Forneça análise aprofundada e estruturada." if analysis_type == "detailed" else "Seja direto e prático para decisão de investimento."}"""
        
        response = await self._call_chatgpt(
            prompt,
            self.system_prompts["integration_analyst"],
            analysis_type
        )
        
        return {
            "integrated_analysis": response,
            "has_release_data": release_analysis is not None,
            "analysis_type": analysis_type
        }
    
    async def _call_chatgpt(self, prompt: str, system_prompt: str, analysis_type: str) -> str:
        """Faz chamada para ChatGPT API"""
        
        config = self.model_config[f"{analysis_type}_analysis"]
        
        try:
            if self.use_openai_lib and OPENAI_AVAILABLE:
                # Usar biblioteca oficial OpenAI
                response = await self.client.chat.completions.create(
                    model=config["model"],
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=config["max_tokens"],
                    temperature=config["temperature"]
                )
                return response.choices[0].message.content
                
            else:
                # Usar requests como fallback
                return await self._call_chatgpt_requests(prompt, system_prompt, config)
                
        except Exception as e:
            return f"Erro na análise via ChatGPT: {str(e)}"
    
    async def _call_chatgpt_requests(self, prompt: str, system_prompt: str, config: Dict) -> str:
        """Fallback usando requests"""
        
        if not REQUESTS_AVAILABLE:
            return "Erro: Nem OpenAI nem requests disponíveis"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": config["model"],
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": config["max_tokens"],
            "temperature": config["temperature"]
        }
        
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                return f"Erro HTTP {response.status_code}: {response.text}"
                
        except Exception as e:
            return f"Erro na requisição: {str(e)}"
    
    def generate_audio_summary(self, analysis_result: Dict) -> str:
        """Gera resumo otimizado para áudio de 2 minutos"""
        
        if analysis_result.get("status") != "success":
            return "Erro: Análise não foi bem-sucedida"
        
        integrated = analysis_result.get("integrated_analysis", {})
        analysis_text = integrated.get("integrated_analysis", "")
        
        # Se a análise integrada estiver vazia, usar análise de valuation
        if not analysis_text:
            valuation = analysis_result.get("valuation_analysis", {})
            analysis_text = valuation.get("analysis", "Análise não disponível")
        
        # Adicionar metadados do áudio
        empresa = analysis_result.get("empresa", "Empresa")
        
        audio_summary = f"""ANÁLISE FINANCEIRA - {empresa}

{analysis_text}

---
Esta análise foi gerada automaticamente pelo Chimpa Invest Analysis Agent.
Duração estimada: ~2 minutos de áudio.
Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}"""
        
        return audio_summary
    
    def save_analysis_report(self, analysis_result: Dict, output_path: str = None) -> str:
        """Salva relatório completo da análise"""
        
        if not output_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            empresa = analysis_result.get("empresa", "empresa").replace(" ", "_")
            output_path = f"analysis_report_{empresa}_{timestamp}.json"
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(analysis_result, f, indent=2, ensure_ascii=False)
            
            print(f"[RELATORIO] Relatório salvo em: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"[ERRO] Erro ao salvar relatório: {e}")
            return None


# Função de conveniência para uso direto
async def analyze_company_valuation(valuation_txt_path: str, 
                                  parsed_release_path: str = None,
                                  analysis_type: str = "detailed",
                                  openai_api_key: str = None) -> Dict:
    """
    Função de conveniência para análise direta
    
    Args:
        valuation_txt_path: Caminho para arquivo TXT de valuation
        parsed_release_path: Caminho para release parsed (opcional)
        analysis_type: 'detailed' ou 'quick'
        openai_api_key: Chave OpenAI (opcional)
    
    Returns:
        Dict com resultado da análise
    """
    agent = ChimpaAnalysisAgent(openai_api_key)
    return await agent.analyze_complete_valuation(
        valuation_txt_path, parsed_release_path, analysis_type
    )


# Exemplo de uso
if __name__ == "__main__":
    async def exemplo_uso():
        """Exemplo de como usar o agente"""
        
        # Caminhos de exemplo
        valuation_path = "data/valuation_temporal_BBAS3_20250627_134021_COMPLETO.txt"
        release_path = "documents/parsed/BANCO_DO_BRASIL_SA_20250603_Apresentação_Institucional_1T25_parsed.txt"
        
        # Verificar se arquivos existem
        if not Path(valuation_path).exists():
            print(f"[ERRO] Arquivo de valuation não encontrado: {valuation_path}")
            return
        
        print("[INICIANDO] Iniciando análise...")
        
        # Análise detalhada
        result = await analyze_company_valuation(
            valuation_path, 
            release_path if Path(release_path).exists() else None,
            "detailed"
        )
        
        if result.get("status") == "success":
            print("[CONCLUIDO] Análise detalhada concluída!")
            
            # Salvar relatório
            agent = ChimpaAnalysisAgent()
            report_path = agent.save_analysis_report(result)
            
            # Gerar resumo para áudio
            audio_summary = agent.generate_audio_summary(result)
            print(f"\n[AUDIO] RESUMO PARA ÁUDIO:")
            print("=" * 50)
            print(audio_summary[:500] + "..." if len(audio_summary) > 500 else audio_summary)
            
        else:
            print(f"[ERRO] Erro na análise: {result.get('error')}")
    
    # Executar exemplo se chamado diretamente
    asyncio.run(exemplo_uso())