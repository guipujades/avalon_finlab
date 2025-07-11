from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, Boolean, JSON, ForeignKey, Index, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import uuid

Base = declarative_base()


class Fund(Base):
    __tablename__ = 'funds'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    fund_type = Column(String(50), nullable=False)  # FIA, MFO, etc
    cnpj = Column(String(20))
    administrator = Column(String(200))
    manager = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    positions = relationship("Position", back_populates="fund")
    transactions = relationship("Transaction", back_populates="fund")
    
    __table_args__ = (
        Index('idx_fund_code', 'code'),
        Index('idx_fund_type', 'fund_type'),
    )


class Asset(Base):
    __tablename__ = 'assets'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    symbol = Column(String(50), unique=True, nullable=False)
    name = Column(String(200))
    asset_type = Column(String(50), nullable=False)  # stock, bond, option, fund, etc
    exchange = Column(String(50))
    currency = Column(String(10), default='BRL')
    isin = Column(String(20))
    cusip = Column(String(20))
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    positions = relationship("Position", back_populates="asset")
    prices = relationship("Price", back_populates="asset")
    transactions = relationship("Transaction", back_populates="asset")
    
    __table_args__ = (
        Index('idx_asset_symbol', 'symbol'),
        Index('idx_asset_type', 'asset_type'),
    )


class Position(Base):
    __tablename__ = 'positions'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    fund_id = Column(String(36), ForeignKey('funds.id'), nullable=False)
    asset_id = Column(String(36), ForeignKey('assets.id'), nullable=False)
    quantity = Column(Float, nullable=False)
    average_price = Column(Float)
    current_price = Column(Float)
    market_value = Column(Float)
    cost_basis = Column(Float)
    unrealized_pnl = Column(Float)
    realized_pnl = Column(Float)
    position_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    fund = relationship("Fund", back_populates="positions")
    asset = relationship("Asset", back_populates="positions")
    
    __table_args__ = (
        Index('idx_position_fund_asset_date', 'fund_id', 'asset_id', 'position_date'),
        Index('idx_position_date', 'position_date'),
    )


class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    fund_id = Column(String(36), ForeignKey('funds.id'), nullable=False)
    asset_id = Column(String(36), ForeignKey('assets.id'), nullable=False)
    transaction_type = Column(String(20), nullable=False)  # buy, sell, dividend, etc
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    fees = Column(Float, default=0)
    transaction_date = Column(DateTime, nullable=False)
    settlement_date = Column(DateTime)
    broker = Column(String(100))
    order_id = Column(String(100))
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    fund = relationship("Fund", back_populates="transactions")
    asset = relationship("Asset", back_populates="transactions")
    
    __table_args__ = (
        Index('idx_transaction_fund_date', 'fund_id', 'transaction_date'),
        Index('idx_transaction_type', 'transaction_type'),
        Index('idx_transaction_date', 'transaction_date'),
    )


class Price(Base):
    __tablename__ = 'prices'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    asset_id = Column(String(36), ForeignKey('assets.id'), nullable=False)
    price_date = Column(DateTime, nullable=False)
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    adjusted_close = Column(Float)
    volume = Column(Float)
    bid = Column(Float)
    ask = Column(Float)
    last = Column(Float)
    source = Column(String(50))  # MT5, BTG, Yahoo, etc
    created_at = Column(DateTime, default=datetime.utcnow)
    
    asset = relationship("Asset", back_populates="prices")
    
    __table_args__ = (
        Index('idx_price_asset_date', 'asset_id', 'price_date'),
        Index('idx_price_date', 'price_date'),
        Index('idx_price_source', 'source'),
    )


class PortfolioSnapshot(Base):
    __tablename__ = 'portfolio_snapshots'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    fund_id = Column(String(36), ForeignKey('funds.id'), nullable=False)
    snapshot_date = Column(DateTime, nullable=False)
    total_value = Column(Float, nullable=False)
    cash_balance = Column(Float, default=0)
    total_cost = Column(Float)
    total_pnl = Column(Float)
    positions_count = Column(Integer)
    var_95 = Column(Float)
    var_99 = Column(Float)
    sharpe_ratio = Column(Float)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_snapshot_fund_date', 'fund_id', 'snapshot_date'),
        Index('idx_snapshot_date', 'snapshot_date'),
    )


class ApiLog(Base):
    __tablename__ = 'api_logs'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    endpoint = Column(String(200), nullable=False)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer)
    response_time_ms = Column(Float)
    error_message = Column(Text)
    request_data = Column(JSON)
    response_data = Column(JSON)
    source = Column(String(50))  # BTG, MT5, etc
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_api_log_created', 'created_at'),
        Index('idx_api_log_source', 'source'),
        Index('idx_api_log_status', 'status_code'),
    )


class OperationLog(Base):
    __tablename__ = 'operation_logs'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    operation_type = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False)  # success, error, warning
    duration_seconds = Column(Float)
    memory_usage_mb = Column(Float)
    cpu_usage_percent = Column(Float)
    input_data = Column(JSON)
    output_data = Column(JSON)
    error_details = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_operation_log_created', 'created_at'),
        Index('idx_operation_log_type', 'operation_type'),
        Index('idx_operation_log_status', 'status'),
    )


class User(Base):
    __tablename__ = 'users'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    last_login = Column(DateTime)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_user_username', 'username'),
        Index('idx_user_email', 'email'),
    )


class DatabaseManager:
    def __init__(self, connection_string: str):
        self.engine = create_engine(connection_string, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def create_tables(self):
        Base.metadata.create_all(bind=self.engine)
        
    def drop_tables(self):
        Base.metadata.drop_all(bind=self.engine)
        
    def get_session(self):
        return self.SessionLocal()
        
    def init_default_data(self):
        session = self.get_session()
        try:
            # Check if we already have data
            existing_funds = session.query(Fund).count()
            if existing_funds > 0:
                return
                
            # Create default funds
            fia_fund = Fund(
                code="AVALON_FIA",
                name="Avalon FIA Master",
                fund_type="FIA",
                cnpj="00.000.000/0001-00",
                administrator="Avalon Capital",
                manager="Avalon Asset Management"
            )
            
            mfo_fund = Fund(
                code="AVALON_MFO",
                name="Avalon MFO Master",
                fund_type="MFO",
                cnpj="00.000.000/0002-00",
                administrator="Avalon Capital",
                manager="Avalon Asset Management"
            )
            
            session.add(fia_fund)
            session.add(mfo_fund)
            session.commit()
            
        finally:
            session.close()


if __name__ == "__main__":
    # Example usage
    db = DatabaseManager("sqlite:///data/avalon_fund.db")
    db.create_tables()
    db.init_default_data()
    print("Database schema created successfully")