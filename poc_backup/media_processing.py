import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List

DOCUMENTS_PATH = "knowledge_base"

class MediaProcessingProtocol:
    """Define o protocolo para processar diferentes tipos de mídia"""
    @staticmethod
    def get_media_type(file_path: Path) -> str:
        extension = file_path.suffix.lower()
        audio_extensions = ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.wma', '.aac']
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv']
        document_extensions = ['.pdf', '.txt', '.docx', '.doc', '.md', '.rtf']
        if extension in audio_extensions:
            return "audio"
        elif extension in video_extensions:
            return "video"
        elif extension in document_extensions:
            return "document"
        else:
            return "unknown"

    @staticmethod
    def create_processing_request(file_path: str, processing_type: str) -> Dict:
        return {
            "file_path": file_path,
            "processing_type": processing_type,
            "timestamp": datetime.now().isoformat(),
            "options": {
                "audio": {
                    "transcribe": True,
                    "language": "pt",
                    "extract_metadata": True
                },
                "video": {
                    "extract_audio": True,
                    "transcribe_audio": True,
                    "extract_keyframes": True,
                    "language": "pt"
                }
            }.get(processing_type, {})
        }

class ExternalToolsInterface:
    """Interface para ferramentas externas de processamento"""
    def __init__(self):
        self.available_tools = self.check_available_tools()
    def check_available_tools(self) -> Dict[str, bool]:
        return {
            "whisper_api": os.getenv("OPENAI_API_KEY") is not None,
            "assemblyai_api": os.getenv("ASSEMBLYAI_API_KEY") is not None,
            "google_speech_api": os.getenv("GOOGLE_CLOUD_CREDENTIALS") is not None,
            "local_whisper": False,
        }
    async def process_audio_with_openai(self, file_path: str) -> Dict:
        return {
            "status": "processed",
            "transcription": f"[Transcrição do áudio {file_path} seria gerada aqui]",
            "language": "pt",
            "duration": "00:00:00",
            "tool_used": "openai_whisper"
        }
    async def process_video(self, file_path: str) -> Dict:
        return {
            "status": "processed",
            "audio_extracted": True,
            "transcription": f"[Transcrição do vídeo {file_path} seria gerada aqui]",
            "keyframes": ["frame1.jpg", "frame2.jpg"],
            "duration": "00:00:00",
            "tool_used": "video_processor"
        }

def setup_knowledge_base_structure():
    base_path = Path(DOCUMENTS_PATH)
    folders = [
        "documentos/relatorios",
        "documentos/pesquisas",
        "documentos/notas",
        "audio/reunioes",
        "audio/podcasts",
        "audio/notas_voz",
        "video/apresentacoes",
        "video/tutoriais",
        "imagens/graficos",
        "imagens/diagramas"
    ]
    for folder in folders:
        (base_path / folder).mkdir(parents=True, exist_ok=True)
    readme_content = """# Base de Conhecimento Local

## Estrutura de Pastas

- **documentos/**: Arquivos de texto (PDF, DOCX, TXT, MD)
  - relatorios/: Relatórios formais
  - pesquisas/: Documentos de pesquisa
  - notas/: Notas e rascunhos

- **audio/**: Arquivos de áudio (MP3, WAV, M4A)
  - reunioes/: Gravações de reuniões
  - podcasts/: Podcasts relevantes
  - notas_voz/: Notas de voz pessoais

- **video/**: Arquivos de vídeo (MP4, AVI, MOV)
  - apresentacoes/: Vídeos de apresentações
  - tutoriais/: Vídeos educacionais

- **imagens/**: Imagens e gráficos
  - graficos/: Gráficos e visualizações
  - diagramas/: Diagramas e fluxogramas

## Formatos Suportados

### Documentos
- PDF, TXT, DOCX, DOC, MD, RTF

### Áudio
- MP3, WAV, M4A, FLAC, OGG, AAC
- Processamento automático de transcrição

### Vídeo
- MP4, AVI, MOV, MKV, WEBM
- Extração e transcrição de áudio

## Como Adicionar Conteúdo

1. Coloque os arquivos nas pastas apropriadas
2. Execute o comando 'scan' no sistema
3. Os arquivos serão indexados automaticamente

## Processamento de Mídia

- Áudio e vídeo são transcritos automaticamente
- As transcrições são armazenadas em cache
- O conteúdo transcrito fica pesquisável
"""
    with open(base_path / "README.md", 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print(f"Estrutura de pastas criada em: {base_path}")
    print("Consulte o arquivo README.md para mais informações") 