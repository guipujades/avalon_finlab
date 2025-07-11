import os
import asyncio
from dotenv import load_dotenv
from tavily import AsyncTavilyClient
from llama_index.llms.openai import OpenAI
from llama_index.core.agent.workflow import (
    FunctionAgent, 
    AgentWorkflow, 
    AgentInput,
    AgentOutput,
    ToolCall,
    ToolCallResult,
)

load_dotenv()
tavily_api_key = os.getenv('TAVILY_KEY')
api_key = os.getenv('OPENAI_API_KEY')
llm = OpenAI(model="gpt-4o-mini", api_key=api_key)

async def search_web(query: str) -> str:
    """Busca informações na web"""
    client = AsyncTavilyClient(api_key=tavily_api_key)
    return str(await client.search(query))

async def record_notes(notes: str, notes_title: str) -> str:
    """Grava notas sobre um tópico"""
    # Simplificado sem Context por enquanto
    return f"Notas '{notes_title}' gravadas: {notes[:100]}..."

async def write_report(report_content: str) -> str:
    """Escreve um relatório"""
    # Simplificado sem Context por enquanto  
    return f"Relatório escrito: {len(report_content)} caracteres"

async def review_report(review: str) -> str:
    """Revisa um relatório"""
    # Simplificado sem Context por enquanto
    return f"Revisão: {review}"

def create_agents():
    """Cria os agentes do workflow"""
    research_agent = FunctionAgent(
        name="ResearchAgent",
        description="Pesquisa informações na web e grava notas",
        system_prompt=(
            "Você é o AgentePesquisa que pode buscar informações na web e gravar notas. "
            "Use search_web para buscar informações e record_notes para gravar. "
            "Seja direto e objetivo."
        ),
        llm=llm,
        tools=[search_web, record_notes],
    )

    write_agent = FunctionAgent(
        name="WriteAgent", 
        description="Escreve relatórios baseados na pesquisa",
        system_prompt=(
            "Você é o AgenteEscrita que escreve relatórios em formato markdown. "
            "Use write_report para escrever o relatório final. "
            "Seja claro e organizado."
        ),
        llm=llm,
        tools=[write_report],
    )

    review_agent = FunctionAgent(
        name="ReviewAgent",
        description="Revisa relatórios e fornece feedback", 
        system_prompt=(
            "Você é o AgenteRevisao que revisa relatórios e fornece feedback. "
            "Use review_report para dar feedback. "
            "Seja construtivo."
        ),
        llm=llm,
        tools=[review_report],
    )
    
    return research_agent, write_agent, review_agent

def create_workflow(agents):
    """Cria o workflow com os agentes"""
    research_agent, write_agent, review_agent = agents
    
    workflow = AgentWorkflow.from_tools_or_functions(
        [search_web, record_notes, write_report, review_report],
        llm=llm,
        system_prompt="Sistema multi-agente para pesquisa, escrita e revisão de relatórios."
    )
    
    return workflow

async def run_workflow(workflow, user_message):
    """Executa o workflow com uma mensagem do usuário"""
    print("Processando solicitação...")
    response = await workflow.run(user_msg=user_message)
    return str(response)

async def main():
    """Função principal"""
    print("Sistema Multi-Agente de Pesquisa")
    print("Digite 'sair' para encerrar")
    
    # Cria agentes e workflow
    agents = create_agents()
    workflow = create_workflow(agents)
    
    while True:
        try:
            user_input = input("\nSua solicitação: ")
            
            if user_input.lower() in ['sair', 'exit', 'quit']:
                break
                
            if not user_input.strip():
                continue
            
            result = await run_workflow(workflow, user_input)
            
            print("\n" + "="*50)
            print("RESULTADO:")
            print("="*50)
            print(result)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Erro: {e}")

if __name__ == "__main__":
    asyncio.run(main())