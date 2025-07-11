"""
ngrok http --domain=btgwh.ngrok.app 5001

"""

from flask import Flask, request, jsonify
import json
import zipfile
import os
import tempfile
import requests
import pandas as pd
import pickle
from pathlib import Path

app = Flask(__name__)

# Caminho para o arquivo pickle
database_path = Path(Path.home(), 'Documents', 'GitHub', 'database')
# pickle_file_path = Path(database_path, 'client_carteiras_historico_operacoes.pkl')
movimentacoes_pickle_file_path = Path(database_path, 'client_carteiras_historico_operacoes.pkl')
tir_mensal_pickle_file_path = Path(database_path, 'client_carteiras_tir_mensal.pkl')

# test1 = pickle.load(open(movimentacoes_pickle_file_path, 'rb'))
# test2 = pickle.load(open(tir_mensal_pickle_file_path, 'rb'))


def load_client_data(pickle_file_path):
    if os.path.exists(pickle_file_path):
        with open(pickle_file_path, 'rb') as f:
            return pickle.load(f)
    else:
        return {}

def save_client_data(client_data, pickle_file_path):
    with open(pickle_file_path, 'wb') as f:
        pickle.dump(client_data, f)

@app.route('/', methods=['GET'])
def home():
    return "Flask server is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        data = request.json
        print("Dados recebidos:", data)
        
        # Processar os dados recebidos
        process_received_data(data)
        
        return jsonify({"status": "success"}), 200

def download_and_extract_zip(url, extract_to):
    # Faz o download do arquivo zip
    response = requests.get(url)
    zip_path = os.path.join(extract_to, 'temp.zip')
    
    with open(zip_path, 'wb') as f:
        f.write(response.content)
    
    # Extrai o conteúdo do arquivo zip
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    
    os.remove(zip_path)

def process_received_data(data):
    
    tipo_dados = "movimentacao" if "startDate" in data["response"] else "tir_mensal"
    print(f"Tipo de dados: {tipo_dados}")
    
    # Carregar dados dos clientes do arquivo pickle
    pickle_file_path = movimentacoes_pickle_file_path if tipo_dados == "movimentacao" else tir_mensal_pickle_file_path
    client_data = load_client_data(pickle_file_path)   
    
    if tipo_dados == 'movimentacao':
        account_number = data['response']['accountNumber']
        if account_number:
            if account_number not in client_data:
                client_data[account_number] = []

    # Diretório temporário para salvar e extrair o arquivo zip
    with tempfile.TemporaryDirectory() as temp_dir:
        # URL do arquivo zip
        zip_url = data.get('response', {}).get('url')
        if not zip_url:
            print("URL do arquivo zip não encontrada nos dados recebidos.")
            return

        # Faz o download e extrai o conteúdo do arquivo zip
        download_and_extract_zip(zip_url, temp_dir)
        
        # Lista os arquivos extraídos
        extracted_files = os.listdir(temp_dir)
        print("Arquivos extraídos:", extracted_files)

        for file_name in extracted_files:
            file_path = os.path.join(temp_dir, file_name)
        
            if file_name.endswith('.csv'):
                
                # Carrega o arquivo CSV em um DataFrame
                df = pd.read_csv(file_path)
                
                if tipo_dados == "movimentacao":
                    
                    if account_number not in client_data:
                        client_data[account_number] = []
                            
                    client_data[account_number] = df
                    print("Dados do arquivo CSV:", df)
                    
                elif tipo_dados == 'tir_mensal':
                    print('De a referencia de mes e ano para o dicionario. Formato: mmyyyy')
                    ref = input()
                    client_data[ref] = df
                    
                else:
                    print('Erro na leitura do arquivo extraido...')

    # Salvar os dados atualizados no arquivo pickle
    save_client_data(client_data, pickle_file_path)
    print("Dados processados e salvos com sucesso.")

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001, debug=True)









































# from flask import Flask, request, jsonify
# import json

# app = Flask(__name__)

# @app.route('/', methods=['GET'])
# def home():
#     return "Flask server is running!"

# @app.route('/webhook', methods=['POST'])
# def webhook():
#     if request.method == 'POST':
#         data = request.json
#         print("Dados recebidos:", data)
        
#         # Processar os dados recebidos
#         process_received_data(data)
        
#         return jsonify({"status": "success"}), 200

# def process_received_data(data):
#     """
#     Função para processar os dados recebidos via webhook.
#     Aqui você pode adicionar lógica para salvar os dados em um banco de dados,
#     enviar notificações, etc.
#     """
#     # Exemplo: Salvar dados em um arquivo JSON
#     with open('received_data.json', 'a') as f:
#         json.dump(data, f)
#         f.write('\n')
#     print("Dados processados e salvos com sucesso.")

# if __name__ == '__main__':
#     app.run(host="0.0.0.0", port=5001, debug=True)
    

