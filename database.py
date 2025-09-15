# database.py
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from config import DB_URL
from datetime import datetime
from base import Base           # ← Base اینجا
# در این فایل نباید به models import کنیم

from sqlalchemy.orm import Session
from typing import Generator

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    # اگر بخواهید دیتابیس را از اول بسازید:
    Base.metadata.create_all(bind=engine)

# متدهای CRUD را اینجا تعریف کنید، اما import مدل‌ها را داخل توابع انجام دهید:

def create_user(name, ip_address):
    from models import User
    session = SessionLocal()
    user = User(name=name, ip_address=ip_address)
    session.add(user)
    session.commit()
    session.close()

def get_users():
    from models import User
    session = SessionLocal()
    users = session.query(User).all()
    session.close()
    return users

def get_user_traffic_stats(user_id, from_time: datetime = None, to_time: datetime = None):
    from models import TrafficLog
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
        "max_usage": int(result.max_usage or 0),
        "min_usage": int(result.min_usage or 0),
        "avg_usage": round(result.avg_usage or 0, 2)
    }

def get_user_traffic(user_id, from_time: datetime = None, to_time: datetime = None):
    from models import TrafficLog
    session = SessionLocal()
    query = session.query(TrafficLog).filter(TrafficLog.user_id == user_id)
    if from_time:
        query = query.filter(TrafficLog.timestamp >= from_time)
    if to_time:
        query = query.filter(TrafficLog.timestamp <= to_time)
    traffic = query.order_by(TrafficLog.timestamp.desc()).all()
    session.close()
    return traffic
