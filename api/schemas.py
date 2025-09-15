from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserCreateSchema(BaseModel):
    name: str
    phone: str
    ip_address: str
    region: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    plan: Optional[str] = "نامحدود"
    is_active: Optional[bool] = True

class UserSchema(BaseModel):
    id: int
    ip_address: str
    name: str
    class Config:
        orm_mode = True

class TrafficLogSchema(BaseModel):
    id: int
    interface_name: str
    rx_bytes: int
    tx_bytes: int
    timestamp: datetime

    class Config:
        orm_mode = True
