"""
Módulo Track MFO - Sistema de captura e análise de múltiplas carteiras
"""

from .portfolio_capture import PortfolioCapture, PortfolioCaptureConfig
from .data_storage import PortfolioDataStorage
from .website_integration import WebsiteDataProcessor
from .api_btg_mfo_utils import process_account_data, get_total_amount

__all__ = [
    'PortfolioCapture',
    'PortfolioCaptureConfig',
    'PortfolioDataStorage',
    'WebsiteDataProcessor',
    'process_account_data',
    'get_total_amount'
]

__version__ = '1.0.0'