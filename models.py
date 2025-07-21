from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    ip_address = Column(String, unique=True)
    name = Column(String)

    logs = relationship("TrafficLog", back_populates="user")

class TrafficLog(Base):
    __tablename__ = 'traffic_logs'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    interface_name = Column(String)
    rx_bytes = Column(BigInteger)
    # اضافه به جدول TrafficLog
    tx_bytes = Column(BigInteger, default=0)

    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="logs")
