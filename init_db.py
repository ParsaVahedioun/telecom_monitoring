# sync_db.py
from database import engine, Base
import models

print("⏳ پاک‌سازی جداول قبلی …")
Base.metadata.drop_all(bind=engine)

print("⏳ ایجاد جداول جدید …")
Base.metadata.create_all(bind=engine)

print("✅ عملیات همگام‌سازی پایان یافت.")
