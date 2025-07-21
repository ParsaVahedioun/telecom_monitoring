from sqlalchemy import create_engine , func
from sqlalchemy.orm import sessionmaker
from models import Base, User, TrafficLog
from config import DB_URL
from datetime import datetime

engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)

def create_user(name, ip_address):
    session = SessionLocal()
    user = User(name=name, ip_address=ip_address)
    session.add(user)
    session.commit()
    session.close()

def get_users():
    session = SessionLocal()
    users = session.query(User).all()
    session.close()
    return users

def get_user_traffic_stats(user_id, from_time: datetime = None, to_time: datetime = None):
    session = SessionLocal()
    query = session.query(
        func.max(TrafficLog.rx_bytes + TrafficLog.tx_bytes).label("max_usage"),
        func.min(TrafficLog.rx_bytes + TrafficLog.tx_bytes).label("min_usage"),
        func.avg(TrafficLog.rx_bytes + TrafficLog.tx_bytes).label("avg_usage")
    ).filter(TrafficLog.user_id == user_id)

    if from_time:
        query = query.filter(TrafficLog.timestamp >= from_time)
    if to_time:
        query = query.filter(TrafficLog.timestamp <= to_time)

    result = query.one()
    session.close()

    return {
        "max_usage": int(result.max_usage) if result.max_usage is not None else 0,
        "min_usage": int(result.min_usage) if result.min_usage is not None else 0,
        "avg_usage": round(result.avg_usage, 2) if result.avg_usage is not None else 0
    }

def get_user_traffic(user_id, from_time: datetime = None, to_time: datetime = None):
    session = SessionLocal()
    query = session.query(TrafficLog).filter(TrafficLog.user_id == user_id)
    if from_time:
        query = query.filter(TrafficLog.timestamp >= from_time)
    if to_time:
        query = query.filter(TrafficLog.timestamp <= to_time)
    traffic = query.order_by(TrafficLog.timestamp.desc()).all()
    session.close()
    return traffic
