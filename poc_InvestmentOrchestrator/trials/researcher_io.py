import os
import requests
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Verificações de Chave (importante ter)
if not GEMINI_API_KEY or "YOUR_API_KEY" in GEMINI_API_KEY or "SUA_CHAVE_AQUI" in GEMINI_API_KEY :
    print("ERRO: GEMINI_API_KEY não configurada ou é um placeholder. Verifique seu .env ou o código.")
    exit()

GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
if not GOOGLE_SEARCH_API_KEY or "YOUR_API_KEY" in GOOGLE_SEARCH_API_KEY or "SUA_CHAVE_AQUI" in GOOGLE_SEARCH_API_KEY:
    print("ERRO: GOOGLE_SEARCH_API_KEY não configurada ou é um placeholder.")
    exit()

GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID", "27f848d8f57a848d1") # Seu CX ID
if not GOOGLE_CSE_ID or "SEU_GOOGLE_CSE_ID" in GOOGLE_CSE_ID:
    print("ERRO: GOOGLE_CSE_ID não configurado ou é um placeholder.")
    exit()


# --- Função da Ferramenta: Busca no Google ---
def perform_google_search(query: str, num_results: int = 3):
    print(f"Buscando no Google: '{query}' ({num_results} resultados)")
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': GOOGLE_SEARCH_API_KEY,
        'cx': GOOGLE_CSE_ID,
        'q': query,
        'num': num_results,
        'hl': 'pt-BR' # Resultados em português
    }
    try:
        response_req = requests.get(url, params=params, timeout=10)
        response_req.raise_for_status()
        search_results = response_req.json()
        if 'items' in search_results and len(search_results['items']) > 0:
            results_text = f"Resultados da pesquisa para '{query}':\n"
            for i, item in enumerate(search_results['items']):
                title = item.get('title', 'N/A')
                link = item.get('link', 'N/A')
                snippet = item.get('snippet', 'N/A')
                # Tentar ser mais informativo no snippet para o LLM
                results_text += f"{i+1}. Título: {title}\n   Snippet: {snippet}\n   Fonte: {link}\n\n"
            return results_text.strip()
        else:
            return f"Nenhum resultado encontrado na web para '{query}'."
    except requests.exceptions.HTTPError as http_err:
        error_details = f" Detalhes: {http_err.response.text if http_err.response else 'Sem detalhes na resposta'}"
        return f"Erro HTTP ao buscar na web: {http_err}.{error_details}"
    except requests.exceptions.RequestException as e:
        return f"Erro de conexão ao buscar na web: {e}"
    except Exception as e:
        return f"Erro inesperado na busca web: {e}"

# --- Configuração do Cliente Gemini ---
try:
    genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"Erro ao configurar o cliente Gemini: {e}")
    exit()

model_name = "gemini-1.5-flash-latest" # Ou gemini-1.5-pro-latest para melhor raciocínio

# SUGESTÃO B: Refinar a Descrição da Ferramenta
google_search_tool = genai.types.FunctionDeclaration(
    name="perform_google_search",
    description=(
        "Realiza uma pesquisa na internet usando o Google para encontrar informações atuais e específicas. "
        "Após a busca, analise os snippets de texto retornados para extrair diretamente a resposta à pergunta do usuário, "
        "como o valor da taxa Selic do Brasil, cotações de moedas, etc. "
        "Use quando a informação solicitada provavelmente não está no conhecimento base do modelo ou requer dados em tempo real."
    ),
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "A consulta de pesquisa precisa e concisa a ser usada no Google (ex: 'taxa selic brasil hoje', 'cotação dólar hoje')."
            },
            "num_results": {
                "type": "integer",
                "description": "Número de resultados a serem retornados (opcional, padrão 3)."
            }
        },
        "required": ["query"]
    }
)

# SUGESTÃO A: Adicionar Prompt de Sistema
system_instruction_text = """
Você é um assistente de pesquisa eficiente e direto. Seu objetivo é responder às perguntas dos usuários com informações precisas.
Ao usar a ferramenta de busca no Google ('perform_google_search'):
1. A ferramenta fornecerá trechos de texto (snippets) de páginas da web.
2. Examine cuidadosamente esses snippets para encontrar a informação específica solicitada.
3. Se um valor numérico ou fato específico (como a taxa Selic) estiver visível nos snippets, extraia-o e forneça-o diretamente como resposta.
4. Se os snippets apenas indicarem um link ou uma forma de obter a informação, mas não a informação em si, você pode mencionar isso, mas deixe claro que o valor exato não foi encontrado nos trechos fornecidos.
5. Priorize fornecer o dado concreto se ele estiver nos resultados da busca. Não diga apenas para o usuário consultar um link se o snippet já contém a resposta.
"""

try:
    model = genai.GenerativeModel(
        model_name=model_name,
        tools=[google_search_tool],
        system_instruction=system_instruction_text # <<<<<<< ADICIONADO SYSTEM INSTRUCTION
    )
    chat = model.start_chat(enable_automatic_function_calling=False) # Controle manual é mais robusto aqui
except Exception as e:
    print(f"Erro ao inicializar o modelo Gemini ({model_name}): {e}")
    exit()

# --- Loop Principal do Agente ---
print(f"Agente de Pesquisa com Gemini ({model_name}) e Google Search")
print("Digite 'sair' para terminar.")

while True:
    user_prompt = input("\nSua pergunta: ")
    if user_prompt.lower() == 'sair':
        print("Até logo!")
        break
    if not user_prompt.strip():
        continue

    print(f"\nGemini processando '{user_prompt}'...")
    
    try:
        current_response = chat.send_message(user_prompt)

        while True: # Loop para lidar com chamadas de função
            function_call_to_check = None
            # Verifica se há candidatos e partes na resposta
            if current_response.candidates and current_response.candidates[0].content and current_response.candidates[0].content.parts:
                for part in current_response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call and part.function_call.name:
                        function_call_to_check = part.function_call
                        break # Encontrou uma function_call, sai do loop de partes
            
            if function_call_to_check:
                function_call = function_call_to_check
                function_name = function_call.name
                print(f"Gemini solicitou a ferramenta: {function_name}")

                if function_name == "perform_google_search":
                    query_args = function_call.args
                    search_query = query_args.get("query")
                    num_results_req = query_args.get("num_results", 3)

                    if not search_query:
                        print("Erro: consulta de busca vazia fornecida pelo Gemini.")
                        tool_response_content = {
                            "error": "A consulta de pesquisa (query) estava vazia. Por favor, forneça uma consulta válida."
                        }
                    else:
                        search_results_text = perform_google_search(search_query, num_results_req)
                        print(f"Resultados obtidos (para Gemini): {len(search_results_text)} caracteres")
                        tool_response_content = {"content": search_results_text}
                    
                    print(f"Enviando resultado da ferramenta '{function_name}' de volta ao Gemini...")
                    current_response = chat.send_message(
                        [
                            {
                                "function_response": {
                                    "name": function_name,
                                    "response": tool_response_content,
                                }
                            }
                        ]
                    )
                    # current_response é atualizado, o loop continua para verificar a nova resposta do Gemini
                
                else:
                    print(f"Função desconhecida solicitada pelo Gemini: {function_name}. Ignorando.")
                    # Para evitar loop infinito se o Gemini insistir em função desconhecida
                    current_response = None 
                    break # Sai do loop de ferramentas
            
            else:
                # Se não há function_call, o Gemini deve ter respondido com texto ou a resposta é inválida.
                break # Sai do loop de ferramentas, current_response deve ter a resposta final ou ser None

        # Após o loop, current_response deve conter a resposta final do Gemini (ou ser None)
        if current_response:
            try:
                # Tenta obter o texto da resposta.
                # O Gemini 1.5 Pro/Flash às vezes retorna uma resposta com múltiplas partes,
                # mesmo que a resposta seja puramente textual. Precisamos concatenar.
                final_text_parts = []
                if current_response.candidates and current_response.candidates[0].content and current_response.candidates[0].content.parts:
                    for part in current_response.candidates[0].content.parts:
                        if hasattr(part, 'text'):
                            final_text_parts.append(part.text)
                        # Ignora function_call aqui, pois já deveriam ter sido tratadas
                
                if final_text_parts:
                    final_answer = "".join(final_text_parts)
                    print("\nResposta Final:")
                    print(final_answer)
                elif hasattr(current_response, 'text'): # Fallback para modelos mais antigos ou respostas simples
                     final_answer = current_response.text
                     print("\nResposta Final (via .text):")
                     print(final_answer)
                else:
                    # Se chegou aqui, não conseguiu extrair texto.
                    print("\nErro: Não foi possível extrair texto da resposta final do Gemini.")
                    # A depuração abaixo pode ajudar
                    if current_response.candidates:
                        for i, candidate in enumerate(current_response.candidates):
                            print(f"  Candidato {i}: {len(candidate.content.parts)} partes")
                            for j, part_debug in enumerate(candidate.content.parts):
                                print(f"    Parte {j} (debug): {part_debug}")
                    else:
                        print(f"  Resposta completa (debug): {current_response}")

            except ValueError as ve: # Erro específico se tentar .text em function_call
                print(f"\nErro ao extrair texto da resposta final: {ve}")
                # Sua depuração original era boa aqui:
                if current_response.candidates:
                    for i, candidate in enumerate(current_response.candidates):
                        print(f"Candidato {i}: {len(candidate.content.parts)} partes")
                        for j, part_debug in enumerate(candidate.content.parts):
                            if hasattr(part_debug, 'function_call') and part_debug.function_call:
                                print(f"  Parte {j} (debug): function_call ({part_debug.function_call.name})")
                            else:
                                print(f"  Parte {j} (debug): {part_debug}")
        else:
            print("\nNenhuma resposta final do Gemini foi obtida após o processamento das ferramentas.")

    except Exception as e:
        print(f"Erro geral durante a interação com o Gemini: {e}")
        import traceback
        traceback.print_exc()