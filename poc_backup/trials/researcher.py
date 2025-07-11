import os
import json
import subprocess
import urllib.request
import time
import sys
import threading
import queue
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
CLAUDE_API_KEY = os.getenv('ANTHROPIC_API_KEY')
CLAUDE_MODEL = "claude-opus-4-20250514"

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

def check_uvx_available():
    """Verifica se uvx está disponível no sistema"""
    try:
        result = subprocess.run(['uvx', '--version'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        return result.returncode == 0
    except:
        return False

def Environment():
    """Estado do ambiente de pesquisa"""
    return {
        "user_question": None,
        "web_content": [],
        "current_step": "initial",
        "cycle_count": 0,
        "max_cycles": 3
    }

class MCPFetchClient:
    """Cliente para servidor MCP fetch"""
    
    def __init__(self):
        """Inicializa servidor MCP fetch"""
        self.process = None
        self.mcp_available = False
        
        if not check_uvx_available():
            print("uvx não encontrado. Instale com: pip install uv")
            sys.exit(1)
        
        try:
            self.process = subprocess.Popen(
                ["uvx", "mcp-server-fetch"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0,
                universal_newlines=True,
                env=os.environ.copy()
            )
            
            time.sleep(2)
            if self.process.poll() is None:
                self._initialize_mcp()
            else:
                stderr = self.process.stderr.read()
                print(f"Erro ao iniciar MCP: {stderr}")
                sys.exit(1)
                
        except Exception as e:
            print(f"Erro: {e}")
            sys.exit(1)
    
    def _initialize_mcp(self):
        """Inicializa protocolo MCP"""
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "web-research-agent",
                    "version": "1.0.0"
                }
            }
        }
        
        self._send_mcp_message(init_request)
        response = self._read_mcp_response(timeout=10)
        
        if response and "result" in response:
            self.mcp_available = True
        else:
            print("Falha na inicialização MCP")
            sys.exit(1)
    
    def _is_process_alive(self):
        """Verifica se o processo MCP ainda está rodando"""
        if not self.process:
            return False
        return self.process.poll() is None
    
    def _send_mcp_message(self, message):
        """Envia mensagem via protocolo MCP"""
        if not self._is_process_alive():
            raise Exception("Processo MCP não está rodando")
            
        message_json = json.dumps(message) + "\n"
        self.process.stdin.write(message_json)
        self.process.stdin.flush()
        time.sleep(0.1)
    
    def _read_mcp_response(self, timeout=5):
        """Lê resposta do servidor MCP com timeout"""
        if not self._is_process_alive():
            return None
            
        response_queue = queue.Queue()
        
        def read_line():
            try:
                line = self.process.stdout.readline()
                if line and line.strip():
                    response_queue.put(line.strip())
            except:
                pass
        
        read_thread = threading.Thread(target=read_line)
        read_thread.daemon = True
        read_thread.start()
        
        try:
            line = response_queue.get(timeout=timeout)
            return json.loads(line)
        except:
            return None
    
    def fetch_web_content(self, url):
        """Busca conteúdo web via MCP"""
        if not self.mcp_available:
            return "Erro: MCP não disponível"
        
        fetch_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "fetch",
                "arguments": {"url": url}
            }
        }
        
        self._send_mcp_message(fetch_request)
        response = self._read_mcp_response(timeout=20)
        
        if response and "result" in response:
            content = response["result"].get("content", [])
            if content and len(content) > 0:
                text_content = content[0].get("text", "")
                if text_content:
                    if len(text_content) > 2500:
                        text_content = text_content[:2500] + "\n... [conteúdo truncado]"
                    return text_content
        
        return "Erro: Não foi possível obter conteúdo"
    
    def __del__(self):
        """Termina o processo MCP"""
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
            except:
                try:
                    self.process.kill()
                except:
                    pass

def Tools(env):
    """Ferramentas de pesquisa usando MCP"""
    
    mcp_client = MCPFetchClient()
    
    def run(action):
        """Executa ação e atualiza estado do ambiente"""
        action = action.strip()
        
        if action.startswith("fetch:"):
            url = action.replace("fetch:", "").strip()
            content = mcp_client.fetch_web_content(url)
            
            env["web_content"].append({
                "url": url,
                "content": content
            })
            
            env["current_step"] = "content_fetched"
            return f"Conteúdo obtido: {url[:60]}..."
        
        elif action == "responder":
            env["current_step"] = "ready_to_respond"
            return "Preparando resposta"
        
        else:
            return f"Ação não reconhecida: {action}"
    
    return {"run": run}

system_prompt = """
Você é um assistente de pesquisa web. Data atual: {current_date}

INSTRUÇÕES:
- Responda APENAS com "fetch:URL" ou "responder"
- Use Google Search primeiro: fetch:https://www.google.com/search?q=TERMO&hl=pt-BR
- Sem explicações ou texto extra

Qual ação executar?
"""

def call_claude_api(prompt):
    """Chama Claude API para decisões do agente"""
    
    current_date = get_current_date()
    
    if not CLAUDE_API_KEY:
        print("Configure CLAUDE_API_KEY")
        sys.exit(1)
    
    prompt_with_date = prompt.format(current_date=current_date)
    
    data = {
        "model": CLAUDE_MODEL,
        "max_tokens": 50,
        "messages": [{"role": "user", "content": prompt_with_date}],
        "temperature": 0.1
    }
    
    json_data = json.dumps(data).encode('utf-8')
    
    request = urllib.request.Request(
        'https://api.anthropic.com/v1/messages',
        data=json_data,
        headers={
            'x-api-key': CLAUDE_API_KEY,
            'content-type': 'application/json',
            'anthropic-version': '2023-06-01'
        }
    )
    
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            result = json.loads(response.read().decode('utf-8'))
            response_text = result["content"][0]["text"].strip()
            
            if not (response_text.startswith("fetch:") or response_text == "responder"):
                return "fetch:https://www.google.com/search?q=informacao&hl=pt-BR"
            
            return response_text
    
    except Exception as e:
        print(f"Erro Claude API: {e}")
        sys.exit(1)

def generate_claude_response(question, web_data):
    """Gera resposta final usando Claude com dados obtidos"""
    
    current_date = get_current_date()
    all_content = ""
    sources = []
    
    for item in web_data:
        all_content += f"\n--- {item['url']} ---\n{item['content']}\n"
        sources.append(item['url'])
    
    final_prompt = f"""
    Data atual: {current_date}
    Pergunta: {question}
    
    Dados obtidos:
    {all_content[:3000]}
    
    Responda de forma clara e precisa, mencionando a data da consulta.
    """
    
    data = {
        "model": CLAUDE_MODEL,
        "max_tokens": 400,
        "messages": [{"role": "user", "content": final_prompt}]
    }
    
    json_data = json.dumps(data).encode('utf-8')
    
    request = urllib.request.Request(
        'https://api.anthropic.com/v1/messages',
        data=json_data,
        headers={
            'x-api-key': CLAUDE_API_KEY,
            'content-type': 'application/json',
            'anthropic-version': '2023-06-01'
        }
    )
    
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result["content"][0]["text"].strip(), sources
    
    except Exception as e:
        return f"Erro ao gerar resposta: {e}", sources

def run_research_agent(user_question):
    """Executa agente de pesquisa web"""
    
    current_date = get_current_date()
    
    print(f"\nPergunta: {user_question}")
    print("-" * 40)
    
    env = Environment()
    tools = Tools(env)
    env["user_question"] = user_question
    
    max_attempts = 5
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        
        current_context = f"""
        {system_prompt}
        
        Pergunta: {env['user_question']}
        Sites já consultados: {len(env['web_content'])}
        
        Responda com "fetch:URL" ou "responder":
        """
        
        action = call_claude_api(current_context)
        print(f"Ação: {action}")
        
        result = tools["run"](action)
        print(result)
        
        if (action == "responder" or 
            env["current_step"] == "ready_to_respond" or
            len(env["web_content"]) >= 2):
            break
    
    final_answer, sources = generate_claude_response(
        user_question, 
        env["web_content"]
    )
    
    print(f"\nResposta:")
    print("-" * 40)
    print(final_answer)
    
    print(f"\nFontes:")
    for source in sources:
        print(f"- {source}")
    
    return final_answer

def main():
    """Função principal do agente"""
    
    print("Agente de Pesquisa Web MCP")
    print("-" * 40)
    
    if not CLAUDE_API_KEY:
        print("Configure CLAUDE_API_KEY")
        return
    
    while True:
        try:
            question = input("\nPergunta (ou 'sair'): ").strip()
            
            if question.lower() in ['sair', 'exit', 'quit', '']:
                break
            
            run_research_agent(question)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Erro: {e}")

if __name__ == "__main__":
    main()