import os
from pathlib import Path
from typing import Dict, Any, Optional
import json
from dataclasses import dataclass, asdict
from datetime import timedelta


@dataclass
class BTGConfig:
    api_key: str = ""
    api_secret: str = ""
    base_url: str = "https://api.btgpactual.com"
    timeout: int = 30
    max_retries: int = 3
    
    
@dataclass
class MT5Config:
    login: str = ""
    password: str = ""
    server: str = ""
    timeout: int = 60000
    
    
@dataclass
class DatabaseConfig:
    type: str = "sqlite"
    host: str = "localhost"
    port: int = 5432
    database: str = "avalon_fund"
    username: str = ""
    password: str = ""
    pool_size: int = 5
    
    @property
    def connection_string(self) -> str:
        if self.type == "sqlite":
            return f"sqlite:///data/avalon_fund.db"
        elif self.type == "postgresql":
            return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        else:
            raise ValueError(f"Unsupported database type: {self.type}")
            
            
@dataclass
class SecurityConfig:
    secret_key: str = ""
    jwt_secret: str = ""
    password_salt: str = ""
    session_lifetime: timedelta = timedelta(hours=24)
    max_login_attempts: int = 5
    lockout_duration: timedelta = timedelta(minutes=30)
    
    
@dataclass
class LoggingConfig:
    level: str = "INFO"
    log_dir: str = "logs"
    max_file_size_mb: int = 100
    backup_count: int = 10
    memory_tracking_enabled: bool = True
    
    
@dataclass
class ScheduleConfig:
    daily_update_time: str = "09:00"
    price_update_interval_minutes: int = 30
    market_open_time: str = "09:00"
    market_close_time: str = "18:00"
    enable_weekend_updates: bool = False
    
    
@dataclass
class AppConfig:
    app_name: str = "Avalon Fund Tracker"
    environment: str = "development"
    debug: bool = False
    data_dir: str = "internal_data"
    temp_dir: str = "temp"
    
    btg: BTGConfig = None
    mt5: MT5Config = None
    database: DatabaseConfig = None
    security: SecurityConfig = None
    logging: LoggingConfig = None
    schedule: ScheduleConfig = None
    
    def __post_init__(self):
        if self.btg is None:
            self.btg = BTGConfig()
        if self.mt5 is None:
            self.mt5 = MT5Config()
        if self.database is None:
            self.database = DatabaseConfig()
        if self.security is None:
            self.security = SecurityConfig()
        if self.logging is None:
            self.logging = LoggingConfig()
        if self.schedule is None:
            self.schedule = ScheduleConfig()
            
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppConfig':
        btg_data = data.pop('btg', {})
        mt5_data = data.pop('mt5', {})
        db_data = data.pop('database', {})
        security_data = data.pop('security', {})
        logging_data = data.pop('logging', {})
        schedule_data = data.pop('schedule', {})
        
        return cls(
            **data,
            btg=BTGConfig(**btg_data) if btg_data else BTGConfig(),
            mt5=MT5Config(**mt5_data) if mt5_data else MT5Config(),
            database=DatabaseConfig(**db_data) if db_data else DatabaseConfig(),
            security=SecurityConfig(**security_data) if security_data else SecurityConfig(),
            logging=LoggingConfig(**logging_data) if logging_data else LoggingConfig(),
            schedule=ScheduleConfig(**schedule_data) if schedule_data else ScheduleConfig()
        )


class ConfigManager:
    def __init__(self, config_file: str = "config.json", env_prefix: str = "AVALON_"):
        self.config_file = Path(config_file)
        self.env_prefix = env_prefix
        self.config: AppConfig = AppConfig()
        
        # Load configuration
        self.load_config()
        
    def load_config(self):
        # First, load from file if exists
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                data = json.load(f)
                self.config = AppConfig.from_dict(data)
                
        # Then, override with environment variables
        self._load_from_env()
        
        # Validate configuration
        self._validate_config()
        
    def _load_from_env(self):
        # Load environment-specific settings
        env = os.getenv(f"{self.env_prefix}ENVIRONMENT", self.config.environment)
        self.config.environment = env
        self.config.debug = env == "development"
        
        # BTG Configuration
        if api_key := os.getenv(f"{self.env_prefix}BTG_API_KEY"):
            self.config.btg.api_key = api_key
        if api_secret := os.getenv(f"{self.env_prefix}BTG_API_SECRET"):
            self.config.btg.api_secret = api_secret
            
        # MT5 Configuration
        if mt5_login := os.getenv(f"{self.env_prefix}MT5_LOGIN"):
            self.config.mt5.login = mt5_login
        if mt5_password := os.getenv(f"{self.env_prefix}MT5_PASSWORD"):
            self.config.mt5.password = mt5_password
        if mt5_server := os.getenv(f"{self.env_prefix}MT5_SERVER"):
            self.config.mt5.server = mt5_server
            
        # Database Configuration
        if db_type := os.getenv(f"{self.env_prefix}DB_TYPE"):
            self.config.database.type = db_type
        if db_host := os.getenv(f"{self.env_prefix}DB_HOST"):
            self.config.database.host = db_host
        if db_port := os.getenv(f"{self.env_prefix}DB_PORT"):
            self.config.database.port = int(db_port)
        if db_name := os.getenv(f"{self.env_prefix}DB_NAME"):
            self.config.database.database = db_name
        if db_user := os.getenv(f"{self.env_prefix}DB_USER"):
            self.config.database.username = db_user
        if db_password := os.getenv(f"{self.env_prefix}DB_PASSWORD"):
            self.config.database.password = db_password
            
        # Security Configuration
        if secret_key := os.getenv(f"{self.env_prefix}SECRET_KEY"):
            self.config.security.secret_key = secret_key
        else:
            # Generate a random secret key if not provided
            import secrets
            self.config.security.secret_key = secrets.token_hex(32)
            
        if jwt_secret := os.getenv(f"{self.env_prefix}JWT_SECRET"):
            self.config.security.jwt_secret = jwt_secret
        else:
            self.config.security.jwt_secret = self.config.security.secret_key
            
    def _validate_config(self):
        # Create necessary directories
        Path(self.config.data_dir).mkdir(exist_ok=True)
        Path(self.config.temp_dir).mkdir(exist_ok=True)
        Path(self.config.logging.log_dir).mkdir(exist_ok=True)
        
        # Validate required fields for production
        if self.config.environment == "production":
            if not self.config.btg.api_key or not self.config.btg.api_secret:
                raise ValueError("BTG API credentials are required in production")
            if self.config.debug:
                raise ValueError("Debug mode cannot be enabled in production")
                
    def save_config(self, exclude_secrets: bool = True):
        data = self.config.to_dict()
        
        if exclude_secrets:
            # Remove sensitive information
            data['btg']['api_key'] = ""
            data['btg']['api_secret'] = ""
            data['mt5']['password'] = ""
            data['database']['password'] = ""
            data['security']['secret_key'] = ""
            data['security']['jwt_secret'] = ""
            
        with open(self.config_file, 'w') as f:
            json.dump(data, f, indent=2)
            
    def get_config(self) -> AppConfig:
        return self.config
        
        
# Singleton instance
_config_manager: Optional[ConfigManager] = None


def get_config() -> AppConfig:
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager.get_config()


def initialize_config(config_file: str = "config.json", env_prefix: str = "AVALON_"):
    global _config_manager
    _config_manager = ConfigManager(config_file, env_prefix)
    return _config_manager.get_config()