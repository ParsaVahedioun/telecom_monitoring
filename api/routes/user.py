from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import APIRouter, HTTPException, Depends , Form ,BackgroundTasks , UploadFile, File ,status
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from api.schemas import UserSchema , TrafficLogSchema , UserCreateSchema
from typing import List
from models import User
from database import SessionLocal
from collector import collect_and_store
from datetime import datetime
import asyncio
from sqlalchemy import func  # ← این خط ضروریه
from models import TrafficLog
from fastapi.responses import JSONResponse
import threading
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MAX_INSTANCES 
collect_status = {
    "last_success": None,
    "last_error": None
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
@user_routes.post("/api/users/add")
def add_user(user_data: UserCreateSchema, db: Session = Depends(get_db)):
    existing_ip = db.query(User).filter(User.ip_address == user_data.ip_address).first()
    if existing_ip:
        raise HTTPException(status_code=400, detail="این IP قبلاً ثبت شده است.")

    existing_phone = db.query(User).filter(User.phone == user_data.phone).first()
    if existing_phone:
        raise HTTPException(status_code=400, detail="این شماره تلفن قبلاً ثبت شده است.")

    new_user = User(
        name=user_data.name,
        phone=user_data.phone,
        ip_address=user_data.ip_address,
        region=user_data.region,
        latitude=user_data.latitude,
        longitude=user_data.longitude,
        plan=user_data.plan,
        is_active=user_data.is_active,
        created_at=datetime.utcnow()
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "کاربر با موفقیت اضافه شد.", "user_id": new_user.id}

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

    if event.code == EVENT_JOB_EXECUTED:
        collect_status["last_success"] = datetime.utcnow().isoformat()
        collect_status["last_error"] = None

    elif event.code == EVENT_JOB_ERROR:
        collect_status["last_error"] = f"خطا در اجرا: {event.exception}"

    elif event.code == EVENT_JOB_MAX_INSTANCES:
        collect_status["last_error"] = "Skipped: maximum number of running instances reached"

@user_routes.get("/api/users/list", response_model=List[dict])
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    usage_data = {
        user_id: {"rx_sum": rx_sum, "tx_sum": tx_sum}
        for user_id, rx_sum, tx_sum in db.query(
            TrafficLog.user_id,
            func.sum(TrafficLog.rx_bytes).label("rx_sum"),
            func.sum(TrafficLog.tx_bytes).label("tx_sum")
        ).group_by(TrafficLog.user_id).all()
    }

    # برگرداندن لیست دیکشنری
    return [
        {
            "id": u.id,
            "name": u.name,
            "phone": u.phone,
            "ip_address": u.ip_address,
            "region": u.region,
            "plan": u.plan,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat(),
            "latitude": u.latitude,
            "longitude": u.longitude,
            "rx_sum": usage_data.get(u.id, {}).get("rx_sum", 0),
            "tx_sum": usage_data.get(u.id, {}).get("tx_sum", 0)
        }
        for u in users
    ]

# 2) حذف کاربر
@user_routes.delete("/api/users/delete/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="کاربر یافت نشد")
    db.delete(user)
    db.commit()
    return JSONResponse(status_code=status.HTTP_200_OK,
                        content={"message": "کاربر با موفقیت حذف شد."})


# در جایی که Scheduler را راه‌اندازی می‌کنید:
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(collect_job, 'interval', seconds=30, id="collect_job")
# اضافه کردن listener
scheduler.add_listener(job_listener,
    EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_MAX_INSTANCES
)
scheduler.start()
