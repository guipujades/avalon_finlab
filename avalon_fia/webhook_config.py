"""
Configuracao de webhook para receber notificacoes da API BTG
sobre atualizacoes de posicoes do parceiro
"""

import json
from flask import Flask, request, jsonify
import logging
from datetime import datetime

app = Flask(__name__)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('webhook_btg.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@app.route('/webhook/positions-by-partner', methods=['POST'])
def positions_webhook():
    """
    Endpoint para receber notificacoes do BTG sobre posicoes atualizadas
    """
    try:
        # Registrar a requisicao
        logger.info(f"Webhook recebido as {datetime.now()}")
        
        # Obter dados do webhook
        data = request.get_json()
        logger.info(f"Dados recebidos: {json.dumps(data, indent=2)}")
        
        # Processar notificacao
        if data:
            # Aqui voce pode adicionar logica para processar a notificacao
            # Por exemplo, disparar um processo de atualizacao de dados
            
            # Salvar notificacao em arquivo para analise
            with open(f'webhook_notification_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'w') as f:
                json.dump(data, f, indent=2)
            
            return jsonify({"status": "success", "message": "Webhook processado"}), 200
        else:
            logger.warning("Webhook recebido sem dados")
            return jsonify({"status": "error", "message": "Sem dados"}), 400
            
    except Exception as e:
        logger.error(f"Erro ao processar webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/webhook/status', methods=['GET'])
def webhook_status():
    """
    Endpoint para verificar se o webhook esta funcionando
    """
    return jsonify({
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "endpoint": "/webhook/positions-by-partner"
    }), 200


if __name__ == '__main__':
    # Rodar servidor webhook
    # Em producao, use um servidor WSGI como gunicorn
    print("Iniciando servidor webhook na porta 5000...")
    print("Endpoint do webhook: http://localhost:5000/webhook/positions-by-partner")
    print("Status: http://localhost:5000/webhook/status")
    app.run(host='0.0.0.0', port=5000, debug=True)