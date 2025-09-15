from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey, DateTime , Boolean
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    phone = Column(String, unique=True, nullable=False)
    ip_address = Column(String, unique=True, nullable=False)
    region = Column(String)
    latitude = Column(String)
    longitude = Column(String)
    plan = Column(String, default="نامشخص")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    email = Column(String, nullable=True)
    usage_limit = Column(Float, nullable=True)
    last_seen = Column(DateTime, nullable=True)
    device_type = Column(String, default="router")
    logs = relationship("TrafficLog", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(name={self.name}, ip={self.ip_address})>"

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
