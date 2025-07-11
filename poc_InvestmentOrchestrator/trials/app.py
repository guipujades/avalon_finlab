from flask import Flask, render_template, request, jsonify
import asyncio
import os
from dotenv import load_dotenv
from tavily import AsyncTavilyClient
from llama_index.llms.openai import OpenAI
from llama_index.core.agent.workflow import AgentWorkflow

load_dotenv()

app = Flask(__name__)

# Configuração dos agentes
tavily_api_key = os.getenv('TAVILY_KEY')
api_key = os.getenv('OPENAI_API_KEY')
llm = OpenAI(model="gpt-4o-mini", api_key=api_key)

async def search_web(query: str) -> str:
    """Busca informações na web"""
    client = AsyncTavilyClient(api_key=tavily_api_key)
    result = await client.search(query)
    return str(result)

# Criar workflow simples
workflow = AgentWorkflow.from_tools_or_functions(
    [search_web],
    llm=llm,
    system_prompt="""Você é um assistente de pesquisa inteligente com acesso à web.
    Você possui conhecimentos de economia e finanças.
    
    Você pode:
    1. Responder perguntas diretamente se souber
    2. Fazer perguntas de esclarecimento se necessário  
    3. Buscar informações na web quando precisar de dados atuais
    
    Seja direto e objetivo nas suas respostas.""",
)

async def run_workflow_async(user_message):
    """Executa o workflow de forma assíncrona"""
    try:
        response = await workflow.run(user_msg=user_message)
        return str(response)
    except Exception as e:
        return f"Erro no workflow: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message.strip():
            return jsonify({'error': 'Mensagem vazia'}), 400
        
        # Executar workflow usando asyncio.run
        try:
            response = asyncio.run(run_workflow_async(user_message))
        except Exception as e:
            response = f"Erro na execução: {str(e)}"
        
        return jsonify({
            'response': response,
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Erro interno: {str(e)}',
            'status': 'error'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 