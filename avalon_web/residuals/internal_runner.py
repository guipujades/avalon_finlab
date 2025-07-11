import os
import sys
from datetime import datetime, timedelta
import time
import schedule
from pathlib import Path
from typing import Dict, Any, List
import json
import pickle

from logging_infrastructure import FundLogger, track_operation

# Import existing modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trackfia.api_btg_utils import main as fetch_btg_data_fia
from trackfia.mt5_connect import MT5DataFetcher
from trackfia.manager import PortfolioManager
from trackfia.VaR import calculate_var_portfolio
from trackmfo.api_btg_mfo_utils import update_accounts_data as fetch_btg_data_mfo


class InternalFundRunner:
    def __init__(self, data_dir: str = "internal_data", log_dir: str = "logs"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.logger = FundLogger("fund_runner", log_dir)
        
        # Initialize components
        self.mt5_fetcher = None
        self.portfolio_manager = PortfolioManager()
        
        # Data storage
        self.current_data = {
            "fia": {},
            "mfo": {},
            "prices": {},
            "portfolios": {},
            "calculations": {}
        }
        
        self.load_existing_data()
        
    def load_existing_data(self):
        data_file = self.data_dir / "current_data.json"
        if data_file.exists():
            with open(data_file, 'r') as f:
                self.current_data = json.load(f)
            self.logger.logger.info("Loaded existing data from disk")
            
    def save_data(self):
        data_file = self.data_dir / "current_data.json"
        with open(data_file, 'w') as f:
            json.dump(self.current_data, f, indent=2, default=str)
        self.logger.logger.info("Saved current data to disk")
        
    @track_operation(logger=None, operation_type="btg_data_fetch")
    def fetch_btg_data(self):
        try:
            # Fetch FIA data
            self.logger.memory_tracker.take_snapshot("Before BTG FIA fetch")
            fia_data = self._fetch_fia_data()
            self.logger.memory_tracker.take_snapshot("After BTG FIA fetch")
            
            if fia_data:
                self.current_data["fia"]["btg_data"] = fia_data
                self.current_data["fia"]["last_update"] = datetime.now().isoformat()
                self.logger.log_data_update("fia_btg", len(fia_data.get("positions", [])), "BTG API")
            
            # Fetch MFO data
            self.logger.memory_tracker.take_snapshot("Before BTG MFO fetch")
            mfo_data = self._fetch_mfo_data()
            self.logger.memory_tracker.take_snapshot("After BTG MFO fetch")
            
            if mfo_data:
                self.current_data["mfo"]["btg_data"] = mfo_data
                self.current_data["mfo"]["last_update"] = datetime.now().isoformat()
                self.logger.log_data_update("mfo_btg", len(mfo_data.get("accounts", [])), "BTG API")
                
            self.save_data()
            
        except Exception as e:
            self.logger.logger.error(f"Error fetching BTG data: {e}")
            
    def _fetch_fia_data(self) -> Dict[str, Any]:
        # Simulate API call without actual credentials
        self.logger.logger.info("Fetching FIA data from BTG API")
        # In production, this would call the actual API
        return {
            "positions": [],
            "timestamp": datetime.now().isoformat()
        }
        
    def _fetch_mfo_data(self) -> Dict[str, Any]:
        # Simulate API call without actual credentials
        self.logger.logger.info("Fetching MFO data from BTG API")
        # In production, this would call the actual API
        return {
            "accounts": [],
            "timestamp": datetime.now().isoformat()
        }
        
    @track_operation(logger=None, operation_type="price_update")
    def update_prices(self):
        if not self.mt5_fetcher:
            self.logger.logger.warning("MT5 fetcher not initialized")
            return
            
        try:
            # Get unique symbols from portfolios
            symbols = set()
            if "fia" in self.current_data and "positions" in self.current_data["fia"]:
                symbols.update([pos.get("symbol") for pos in self.current_data["fia"].get("positions", [])])
                
            for symbol in symbols:
                if symbol:
                    price_data = self.mt5_fetcher.get_current_price(symbol)
                    if price_data:
                        self.current_data["prices"][symbol] = {
                            "bid": price_data.get("bid"),
                            "ask": price_data.get("ask"),
                            "last": price_data.get("last"),
                            "timestamp": datetime.now().isoformat()
                        }
                        
            self.logger.log_data_update("prices", len(self.current_data["prices"]), "MT5")
            self.save_data()
            
        except Exception as e:
            self.logger.logger.error(f"Error updating prices: {e}")
            
    @track_operation(logger=None, operation_type="portfolio_calculation")
    def calculate_portfolios(self):
        try:
            # Calculate FIA portfolio
            if "fia" in self.current_data and "btg_data" in self.current_data["fia"]:
                fia_positions = self.current_data["fia"]["btg_data"].get("positions", [])
                fia_portfolio = self.portfolio_manager.calculate_portfolio_value(
                    fia_positions, 
                    self.current_data.get("prices", {})
                )
                self.current_data["portfolios"]["fia"] = {
                    "total_value": fia_portfolio.get("total_value"),
                    "positions_count": len(fia_positions),
                    "timestamp": datetime.now().isoformat()
                }
                self.logger.log_calculation(
                    "portfolio_value", 
                    {"type": "fia", "positions": len(fia_positions)},
                    fia_portfolio.get("total_value")
                )
                
            # Calculate VaR if we have price history
            if self.current_data.get("prices"):
                var_result = self._calculate_var()
                if var_result:
                    self.current_data["calculations"]["var"] = var_result
                    self.logger.log_calculation(
                        "value_at_risk",
                        {"confidence": 0.95, "period": "1day"},
                        var_result
                    )
                    
            self.save_data()
            
        except Exception as e:
            self.logger.logger.error(f"Error calculating portfolios: {e}")
            
    def _calculate_var(self) -> Dict[str, Any]:
        # Placeholder for VaR calculation
        return {
            "var_95": 0.0,
            "var_99": 0.0,
            "timestamp": datetime.now().isoformat()
        }
        
    @track_operation(logger=None, operation_type="daily_routine")
    def run_daily_routine(self):
        self.logger.logger.info("Starting daily routine")
        
        # Morning data fetch
        self.fetch_btg_data()
        time.sleep(5)  # Small delay between operations
        
        # Update prices
        self.update_prices()
        time.sleep(5)
        
        # Calculate portfolios and risk
        self.calculate_portfolios()
        
        # Generate daily report
        report = self.logger.generate_daily_report()
        
        self.logger.logger.info("Daily routine completed")
        
    def run_continuous(self):
        # Schedule daily routines
        schedule.every().day.at("09:00").do(self.run_daily_routine)
        schedule.every().day.at("15:30").do(self.update_prices)
        schedule.every().day.at("16:00").do(self.calculate_portfolios)
        
        # Price updates every 30 minutes during market hours
        for hour in range(9, 18):
            for minute in ["00", "30"]:
                schedule.every().day.at(f"{hour:02d}:{minute}").do(self.update_prices)
                
        self.logger.logger.info("Internal runner started with scheduled tasks")
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                self.logger.logger.info("Internal runner stopped by user")
                break
            except Exception as e:
                self.logger.logger.error(f"Error in continuous run: {e}")
                time.sleep(300)  # Wait 5 minutes on error
                
                
def main():
    runner = InternalFundRunner()
    
    # For testing, just run once
    runner.run_daily_routine()
    
    # For production, uncomment the line below
    # runner.run_continuous()
    

if __name__ == "__main__":
    main()