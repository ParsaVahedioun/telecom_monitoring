from pydantic import BaseModel
from datetime import datetime

class UserCreateSchema(BaseModel):
    name: str
    ip_address: str

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
