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
        try:
            user_prompt = input("\n💬 Sua pergunta: ")
            
            # Comandos especiais
            if user_prompt.lower() in ['sair', 'exit', 'quit']:
                print("👋 Encerrando o agente. Até logo!")
                break
            
            if user_prompt.lower() == 'limpar':
                # Reinicia a memória
                memory.reset()
                print("🗑️  Histórico de conversas limpo!")
                continue
            
            if user_prompt.lower() == 'resumo':
                # Obtém o resumo da conversa
                chat_history = memory.get()
                if chat_history:
                    print("\n📋 === RESUMO DA CONVERSA ===")
                    for i, msg in enumerate(chat_history):
                        role = "Você" if msg.role == "user" else "Assistente"
                        content_preview = msg.content[:150] + "..." if len(msg.content) > 150 else msg.content
                        print(f"\n[{i+1}] {role}: {content_preview}")
                else:
                    print("📭 Histórico vazio.")
                continue
            
            if not user_prompt.strip():
                continue
            
            # Executa a query com streaming
            print("\n🔍 Processando...")
            response = await agent.achat(user_prompt)
            
            # Exibe a resposta
            print(f"\n🤖 {response}")
           
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrompido pelo usuário.")
            break
        except Exception as e:
            print(f"❌ Erro: {e}")
            print("Tente novamente ou digite 'sair' para encerrar.")

if __name__ == "__main__":
    asyncio.run(main())