import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from tavily import AsyncTavilyClient
from llama_index.llms.openai import OpenAI
from llama_index.core.agent.workflow import AgentWorkflow

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
    client = AsyncTavilyClient(api_key=tavily_api_key)
    return str(await client.search(query))

async def main():
    global tavily_api_key, api_key, workflow
    
    load_dotenv()
    tavily_api_key = os.getenv('TAVILY_KEY')
    api_key = os.getenv('OPENAI_API_KEY')
    
    llm = OpenAI(model="gpt-4.1-mini", api_key=api_key)
    get_date = get_current_date()

    workflow = AgentWorkflow.from_tools_or_functions(
        [search_web],
        llm=llm,
        system_prompt=f"""Você é um assistente de pesquisa inteligente com acesso à web.
        Você possui conhecimentos de economia e finanças e está sempre atualizado com as noticias do Brasil e do mundo.
        Sua pesquisa deve ser sempre feita tendo por base a data da pergunta: {get_date}.
        Dessa forma, caso a pergunta envolva algum dado, deve ser feita com a informação mais atualizada possível.
        
        OBJETIVO:
        Ajudar com pesquisas envolvendo economia e finanças na internet de forma eficiente e precisa.

        PROCESSO:
        1. Analise a pergunta do usuário
        2. Caso a pergunta não esteja clara o suficiente, tente entender melhor a pergunta do usuário, fazendo perguntas de esclarecimentos.
        3. Use search_web para buscar informações relevantes
        4. Forneça uma resposta clara baseada nos resultados

        REGRAS:
        - Seja específico e direto
        - Use fontes confiáveis
        - Inclua informações atualizadas

        Analise a pergunta e forneça a melhor resposta possível.""",
    )

    while True:
        try:
            user_prompt = input("\nSua pergunta ou 'sair' para encerrar o programa:")
            if user_prompt.lower() in ['sair', 'exit', 'quit']:
                break
            if not user_prompt.strip():
                continue
                
            response = await workflow.run(user_msg=user_prompt)
            print(f"\n{response}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Erro: {e}")

if __name__ == "__main__":
    asyncio.run(main())