import logging
import psutil
import os
import json
from datetime import datetime
from pathlib import Path
import tracemalloc
from functools import wraps
import time
from typing import Dict, Any, Optional


class MemoryTracker:
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.process = psutil.Process(os.getpid())
        self.snapshots = []
        tracemalloc.start()
        
    def get_memory_info(self) -> Dict[str, Any]:
        memory_info = self.process.memory_info()
        cpu_percent = self.process.cpu_percent(interval=0.1)
        
        current, peak = tracemalloc.get_traced_memory()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "rss_mb": memory_info.rss / 1024 / 1024,
            "vms_mb": memory_info.vms / 1024 / 1024,
            "cpu_percent": cpu_percent,
            "tracemalloc_current_mb": current / 1024 / 1024,
            "tracemalloc_peak_mb": peak / 1024 / 1024
        }
    
    def take_snapshot(self, label: str = ""):
        snapshot = tracemalloc.take_snapshot()
        self.snapshots.append({
            "timestamp": datetime.now().isoformat(),
            "label": label,
            "snapshot": snapshot
        })
        
    def compare_snapshots(self, idx1: int = -2, idx2: int = -1) -> Optional[str]:
        if len(self.snapshots) < 2:
            return None
            
        snapshot1 = self.snapshots[idx1]["snapshot"]
        snapshot2 = self.snapshots[idx2]["snapshot"]
        
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        
        result = []
        result.append(f"\nMemory comparison: {self.snapshots[idx1]['label']} -> {self.snapshots[idx2]['label']}")
        result.append("="*50)
        
        for stat in top_stats[:10]:
            result.append(str(stat))
            
        return "\n".join(result)


class FundLogger:
    def __init__(self, name: str, log_dir: str = "logs"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # File handler for general logs
        log_file = self.log_dir / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Memory tracker
        self.memory_tracker = MemoryTracker(log_dir)
        
        # Operations log file
        self.operations_log = self.log_dir / f"operations_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
    def log_operation(self, operation_type: str, data: Dict[str, Any], status: str = "success"):
        operation = {
            "timestamp": datetime.now().isoformat(),
            "operation_type": operation_type,
            "status": status,
            "data": data,
            "memory": self.memory_tracker.get_memory_info()
        }
        
        with open(self.operations_log, 'a') as f:
            f.write(json.dumps(operation) + '\n')
            
        self.logger.info(f"Operation logged: {operation_type} - {status}")
        
    def track_memory(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_memory = self.memory_tracker.get_memory_info()
            self.memory_tracker.take_snapshot(f"Before {func.__name__}")
            
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                status = "success"
                error = None
            except Exception as e:
                result = None
                status = "error"
                error = str(e)
                self.logger.error(f"Error in {func.__name__}: {error}")
                raise
            finally:
                end_time = time.time()
                self.memory_tracker.take_snapshot(f"After {func.__name__}")
                end_memory = self.memory_tracker.get_memory_info()
                
                memory_diff = {
                    "function": func.__name__,
                    "duration_seconds": end_time - start_time,
                    "memory_delta_mb": end_memory["rss_mb"] - start_memory["rss_mb"],
                    "start_memory": start_memory,
                    "end_memory": end_memory,
                    "status": status,
                    "error": error
                }
                
                self.log_operation(f"function_call_{func.__name__}", memory_diff, status)
                
                # Log memory comparison
                comparison = self.memory_tracker.compare_snapshots()
                if comparison:
                    self.logger.debug(comparison)
                    
            return result
        return wrapper
        
    def log_data_update(self, data_type: str, records_count: int, source: str, metadata: Dict[str, Any] = None):
        data = {
            "data_type": data_type,
            "records_count": records_count,
            "source": source,
            "metadata": metadata or {}
        }
        self.log_operation("data_update", data)
        
    def log_api_call(self, endpoint: str, method: str, status_code: int, response_time: float, metadata: Dict[str, Any] = None):
        data = {
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "response_time_seconds": response_time,
            "metadata": metadata or {}
        }
        status = "success" if 200 <= status_code < 300 else "error"
        self.log_operation("api_call", data, status)
        
    def log_calculation(self, calculation_type: str, input_data: Dict[str, Any], result: Any, metadata: Dict[str, Any] = None):
        data = {
            "calculation_type": calculation_type,
            "input_summary": {k: str(v)[:100] for k, v in input_data.items()},
            "result_summary": str(result)[:200],
            "metadata": metadata or {}
        }
        self.log_operation("calculation", data)
        
    def generate_daily_report(self) -> Dict[str, Any]:
        report = {
            "date": datetime.now().strftime('%Y-%m-%d'),
            "operations": [],
            "memory_summary": {
                "current": self.memory_tracker.get_memory_info(),
                "snapshots_count": len(self.memory_tracker.snapshots)
            }
        }
        
        if self.operations_log.exists():
            with open(self.operations_log, 'r') as f:
                for line in f:
                    report["operations"].append(json.loads(line))
                    
        report_file = self.log_dir / f"daily_report_{datetime.now().strftime('%Y%m%d')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        self.logger.info(f"Daily report generated: {report_file}")
        return report


# Example usage decorator for tracking specific operations
def track_operation(logger: FundLogger, operation_type: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                logger.log_operation(
                    operation_type, 
                    {"function": func.__name__, "args_count": len(args), "kwargs_count": len(kwargs)},
                    "success"
                )
                return result
            except Exception as e:
                logger.log_operation(
                    operation_type,
                    {"function": func.__name__, "error": str(e)},
                    "error"
                )
                raise
        return wrapper
    return decorator