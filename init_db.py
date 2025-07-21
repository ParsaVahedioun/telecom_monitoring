# init_db.py

from database import Base, engine
from models import User, TrafficLog  # اگر TrafficLog هم داری

print("⏳ ساخت جداول دیتابیس...")
Base.metadata.create_all(bind=engine)
print("✅ ساخت جداول انجام شد.")
