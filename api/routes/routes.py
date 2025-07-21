from fastapi import APIRouter, Depends, HTTPException,BackgroundTasks
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User, TrafficLog
from api.schemas import UserSchema, TrafficLogSchema
from typing import List
from datetime import datetime
from fastapi import Query
from sqlalchemy import func
from typing import Optional
from collector import collect_and_store
import asyncio

router = APIRouter(prefix="/admin")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from database import SessionLocal
from models import TrafficLog
from fastapi.responses import JSONResponse

@router.get("/traffic")
def get_traffic(
    range: str = Query("1h", regex="^(now|1h|1d|1w|1m)$"),
    db: Session = Depends(get_db)
):
    now = datetime.utcnow()
    delta = {
        "now": timedelta(minutes=5),
        "1h": timedelta(hours=1),
        "1d": timedelta(days=1),
        "1w": timedelta(weeks=1),
        "1m": timedelta(days=30),
    }.get(range, timedelta(hours=1))

    from_time = now - delta

    logs = db.query(TrafficLog).filter(TrafficLog.timestamp >= from_time).order_by(TrafficLog.timestamp).all()

    grouped_data = {}
    for log in logs:
        key = f"{log.user_id}-{log.interface_name}"
        if key not in grouped_data:
            grouped_data[key] = {
                "user_id": log.user_id,
                "interface": log.interface_name,
                "timestamps": [],
                "rx": [],
                "tx": [],
            }
        grouped_data[key]["timestamps"].append(log.timestamp.isoformat())
        grouped_data[key]["rx"].append(log.rx_bytes)
        grouped_data[key]["tx"].append(log.tx_bytes)

    return JSONResponse(content=list(grouped_data.values()))


@router.get("/api/traffic-stats")
def get_traffic_stats(
    start: Optional[str] = Query(None, description="Start time in YYYY-MM-DD HH:MM"),
    end: Optional[str] = Query(None, description="End time in YYYY-MM-DD HH:MM")
):
    session = SessionLocal()
    try:
        user_id = 1  # تست: فقط یک یوزر پیش‌فرض

        # پارس کردن تاریخ‌ها
        start_time = datetime.strptime(start, "%Y-%m-%d %H:%M") if start else None
        end_time = datetime.strptime(end, "%Y-%m-%d %H:%M") if end else None

        query = session.query(
            func.min(TrafficLog.rx_bytes).label("min_rx"),
            func.max(TrafficLog.rx_bytes).label("max_rx"),
            func.avg(TrafficLog.rx_bytes).label("avg_rx"),
            func.min(TrafficLog.tx_bytes).label("min_tx"),
            func.max(TrafficLog.tx_bytes).label("max_tx"),
            func.avg(TrafficLog.tx_bytes).label("avg_tx"),
        ).filter(TrafficLog.user_id == user_id)

        # فیلتر بازه زمانی در صورت نیاز
        if start_time:
            query = query.filter(TrafficLog.timestamp >= start_time)
        if end_time:
            query = query.filter(TrafficLog.timestamp <= end_time)

        stats = query.first()

        return {
            "rx": {
                "min": stats.min_rx or 0,
                "max": stats.max_rx or 0,
                "avg": round(stats.avg_rx or 0, 2)
            },
            "tx": {
                "min": stats.min_tx or 0,
                "max": stats.max_tx or 0,
                "avg": round(stats.avg_tx or 0, 2)
            }
        }

    except Exception as e:
        return {"error": str(e)}
    finally:
        session.close()

@router.get("/users/{user_id}/traffic", response_model=List[TrafficLogSchema])
def get_traffic(
    user_id: int,
    db: Session = Depends(get_db),
    from_time: datetime = Query(None, alias="from"),
    to_time: datetime = Query(None, alias="to")
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    query = db.query(TrafficLog).filter(TrafficLog.user_id == user_id)

    if from_time:
        query = query.filter(TrafficLog.timestamp >= from_time)
    if to_time:
        query = query.filter(TrafficLog.timestamp <= to_time)

    return query.order_by(TrafficLog.timestamp.desc()).all()


@router.get("/api/live-speed")
def get_live_speed(db: Session = Depends(get_db)):
    user_id = 1  # در آینده میشه داینامیک کرد

    # جدیدترین رکورد کاربر از جدول ترافیک
    latest = db.query(TrafficLog) \
        .filter(TrafficLog.user_id == user_id) \
        .order_by(TrafficLog.timestamp.desc()) \
        .first()

    if not latest:
        return {"rx": 0, "tx": 0}

    return {
        "rx": latest.rx_bytes,
        "tx": latest.tx_bytes
    }
