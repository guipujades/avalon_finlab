import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from tavily import AsyncTavilyClient
from llama_index.llms.openai import OpenAI
from llama_index.core.agent import FunctionCallingAgentWorker
from llama_index.core.agent import AgentRunner
from llama_index.core.tools import FunctionTool
from llama_index.core.memory import ChatMemoryBuffer

def get_current_date():
    """Retorna a data atual formatada em português"""
    now = datetime.now()
    months = [
        "janeiro", "fevereiro", "março", "abril", "maio", "junho",
        "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
    ]
    day = now.day
    month = months[now.month - 1]
    year = now.year
    weekdays = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]
    weekday = weekdays[now.weekday()]
   
    return f"{weekday}-feira, {day} de {month} de {year}"

async def search_web(query: str) -> str:
    """
    Pesquisa informações na web usando Tavily.
    
    Args:
        query: A consulta de pesquisa
        
    Returns:
        Resultados da pesquisa formatados como string
    """
    client = AsyncTavilyClient(api_key=tavily_api_key)
    results = await client.search(query)
    return str(results)

async def main():
    global tavily_api_key, api_key
   
    load_dotenv()
    tavily_api_key = os.getenv('TAVILY_KEY')
    api_key = os.getenv('OPENAI_API_KEY')
   
    # Inicializa o LLM
    llm = OpenAI(model="gpt-4o-mini", api_key=api_key)
    
    # Cria a ferramenta de pesquisa
    search_tool = FunctionTool.from_defaults(
        fn=search_web,
        name="search_web",
        description="Pesquisa informações na web sobre economia, finanças e notícias atuais"
    )
    
    # Obtém a data atual
    get_date = get_current_date()
    
    # Prompt do sistema
    system_prompt = f"""Você é um assistente de pesquisa inteligente com acesso à web.
Você possui conhecimentos de economia e finanças e está sempre atualizado com as noticias do Brasil e do mundo.
Sua pesquisa deve ser sempre feita tendo por base a data da pergunta: {get_date}.
Dessa forma, caso a pergunta envolva algum dado, deve ser feita com a informação mais atualizada possível.

OBJETIVO:
Ajudar com pesquisas envolvendo economia e finanças na internet de forma eficiente e precisa.

PROCESSO:
1. Analise a pergunta do usuário considerando o contexto de conversas anteriores
2. Caso a pergunta não esteja clara, faça perguntas de esclarecimento
3. Use search_web para buscar informações relevantes quando necessário
4. Forneça respostas claras baseadas nos resultados e no contexto da conversa

REGRAS:
- Seja específico e direto
- Use fontes confiáveis
- Inclua informações atualizadas
- Mantenha continuidade com as conversas anteriores
- Referencie informações discutidas anteriormente quando relevante
- Lembre-se do contexto e das preferências do usuário ao longo da conversa"""
    
    # Cria a memória de chat
    memory = ChatMemoryBuffer.from_defaults(
        llm=llm,
        token_limit=3000,  # Limite de tokens para o contexto
    )
    
    # Cria o agente worker
    agent_worker = FunctionCallingAgentWorker.from_tools(
        tools=[search_tool],
        llm=llm,
        system_prompt=system_prompt,
        verbose=True
    )
    
    # Cria o AgentRunner com memória
    agent = AgentRunner(
        agent_worker,
        memory=memory,
    )
    
    print("🤖 Agente de pesquisa iniciado com memória de contexto!")
    print("📝 Comandos disponíveis:")
    print("   - 'sair' para encerrar")
    print("   - 'limpar' para limpar o histórico")
    print("   - 'resumo' para ver um resumo da conversa")
    print("-" * 50)
    
    while True:
        print("=" * 60)
        print("SISTEMA DE PESQUISA INTELIGENTE")
        print("=" * 60)
        print("Comandos disponíveis:")
        print("• Digite uma pergunta diretamente")
        print("• 'exit' ou 'quit' para sair")
        print("• 'clear' para limpar a tela")
        print("• 'memory' para ver a memória")
        print("• 'reset_memory' para resetar memória")
        print("=" * 60)
        
        user_input = input("\nDigite sua pergunta: ").strip()
        
        if user_input.lower() in ['exit', 'quit', 'sair']:
            print("Até logo!")
            break
        elif user_input.lower() == 'clear':
            clear_screen()
            continue
        elif user_input.lower() == 'memory':
            print(f"\nMemória atual: {len(memory.memories)} entradas")
            for i, mem in enumerate(memory.memories[-5:], 1):
                print(f"{i}. {mem['question'][:50]}...")
            continue
        elif user_input.lower() == 'reset_memory':
            memory = ChatMemoryBuffer.from_defaults(
                llm=llm,
                token_limit=3000,  # Limite de tokens para o contexto
            )
            print("Memória resetada!")
            continue
        elif not user_input:
            continue
        
        try:
            print("\nProcessando...")
            
            # Verifica memória primeiro
            memory_response = await memory.search_similar(user_input)
            if memory_response:
                print(f"\nResposta da memória: {memory_response}")
                continue
            
            # Faz pesquisa
            result = await agent.achat(user_input)
            memory.add_memory(user_input, result)
            print(f"\nResposta: {result}")
            
        except KeyboardInterrupt:
            print("\n\nInterrompido pelo usuário.")
            break
        except Exception as e:
            print(f"ERRO: {e}")

if __name__ == "__main__":
    asyncio.run(main())