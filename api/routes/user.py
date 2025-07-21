from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import APIRouter, HTTPException, Depends , Form ,BackgroundTasks
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from api.schemas import UserSchema , TrafficLogSchema , UserCreateSchema
from typing import List
from models import User
from database import SessionLocal
from collector import collect_and_store
from datetime import datetime
import asyncio
from fastapi.responses import JSONResponse
import threading
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MAX_INSTANCES 
collect_status = {
    "last_success": None,   # زمان آخرین اجرای موفق
    "last_error": None      # پیام آخرین خطا (یا skip)
}


user_routes = APIRouter()
# --------------------
# connect to data base
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --------------------
#  (Scheduler) timeing

scheduler = BackgroundScheduler()

def collect_job():
    print("🕒 اجرای خودکار جمع‌آوری داده SNMP")
    asyncio.run(collect_and_store())

scheduler.add_job(collect_job, 'interval', seconds=30)
scheduler.start()
# --------------------
#  router User

@user_routes.post("/users", response_model=List[UserSchema])
def create_user(user: UserCreateSchema, db: Session = Depends(get_db)):
    if db.query(User).filter(User.ip_address == user.ip_address).first():
        raise HTTPException(status_code=400, detail="کاربری با این IP قبلاً ثبت شده")
    new_user = User(name=user.name, ip_address=user.ip_address)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@user_routes.post("/users")
def create_user(user: UserSchema, db: Session = Depends(get_db)):
    new_user = User(name=user.name, ip_address=user.ip_address)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"status": "User created"}

# -------------------------------
# collect-now
@user_routes.post("/collect-now")
async def collect_now(background_tasks: BackgroundTasks):
    background_tasks.add_task(collect_and_store)
    return {"status": "جمع‌آوری SNMP آغاز شد."}


@user_routes.get("/api/collect-status")
def get_collect_status():
    return JSONResponse(content=collect_status)

# تابع listener برای APScheduler
def job_listener(event):
    # اگر job با موفقیت اجرا شد
    if event.code == EVENT_JOB_EXECUTED:
        collect_status["last_success"] = datetime.utcnow().isoformat()
        collect_status["last_error"] = None
    # اگر خطای runtime داشت
    elif event.code == EVENT_JOB_ERROR:
        collect_status["last_error"] = f"خطا در اجرا: {event.exception}"
    # اگر skip به‌خاطر max instances رخ داد
    elif event.code == EVENT_JOB_MAX_INSTANCES:
        collect_status["last_error"] = "Skipped: maximum number of running instances reached"

# در جایی که Scheduler را راه‌اندازی می‌کنید:
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(collect_job, 'interval', seconds=30, id="collect_job")
# اضافه کردن listener
scheduler.add_listener(job_listener,
    EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_MAX_INSTANCES
)
scheduler.start()
