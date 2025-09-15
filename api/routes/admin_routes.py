from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import asc
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
import io
import pandas as pd

from database import get_db
from models import User, TrafficLog


router = APIRouter(prefix="/admin/api", tags=["Admin API"])


# --- در ابتدای فایل:
from fastapi import Response
from fastapi.responses import StreamingResponse
import io
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
import pandas as pd


def to_aware_utc(dt):
    if dt is None:
        return None
    # اگر tzinfo نداره یا naive هست، فرض کن UTC بوده
    if getattr(dt, "tzinfo", None) is None or dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        return dt.replace(tzinfo=timezone.utc)
    # اگر tz داره، به UTC تبدیلش کن
    return dt.astimezone(timezone.utc)


# اگر pandas/openpyxl نداری، به requirements اضافه کن:
# pandas==2.2.2
# openpyxl==3.1.3

def _compute_deltas(rows: List[TrafficLog]):
    rows = sorted(rows, key=lambda r: r.timestamp)
    series = []
    for prev, cur in zip(rows, rows[1:]):
        dt = (cur.timestamp - prev.timestamp).total_seconds()
        if dt <= 0:
            continue
        drx = (cur.rx_bytes or 0) - (prev.rx_bytes or 0)
        dtx = (cur.tx_bytes or 0) - (prev.tx_bytes or 0)
        if drx < 0 or dtx < 0:  # wrap/reset
            continue
        rx_bps = (drx * 8.0) / dt
        tx_bps = (dtx * 8.0) / dt
        series.append({
            "t_start": prev.timestamp,
            "t_end": cur.timestamp,
            "rx_delta": drx,
            "tx_delta": dtx,
            "rx_bps": rx_bps,
            "tx_bps": tx_bps,
            "total_bps": rx_bps + tx_bps
        })
    return series

@router.get("/users/export")
def export_users(
    db: Session = Depends(get_db),
    hours: int = 24,
    window_seconds: int = 300,
    format: str = "xlsx",  # xlsx | csv
):
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=hours)

    users: List[User] = db.query(User).all()
    records: List[Dict[str, Any]] = []
    peaks: List[Dict[str, Any]] = []
    timeline_rows: List[Dict[str, Any]] = []

    for u in users:
        rows: List[TrafficLog] = (
            db.query(TrafficLog)
              .filter(TrafficLog.user_id == u.id,
                      TrafficLog.timestamp >= since,
                      TrafficLog.timestamp <= now)
              .order_by(TrafficLog.timestamp.asc())
              .all()
        )
        if len(rows) < 2:
            records.append({
                "user_id": u.id, "name": u.name, "ip": u.ip_address,
                "is_active": u.is_active,
                "rx_bytes": 0, "tx_bytes": 0,
                "avg_total_bps": 0.0,
                "peak_window_bps": 0.0
            })
            continue

        series = _compute_deltas(rows)
        total_rx = sum(p["rx_delta"] for p in series)
        total_tx = sum(p["tx_delta"] for p in series)
        avg_bps = sum(p["total_bps"] for p in series) / max(len(series), 1)

        # peak/min با پنجره‌های یکسان:
        t0 = series[0]["t_start"]
        buckets = {}
        def bidx(ts): return int((ts - t0).total_seconds() // window_seconds)
        for p in series:
            idx = bidx(p["t_start"])
            b = buckets.setdefault(idx, {"sum":0.0, "count":0})
            b["sum"] += p["total_bps"]
            b["count"] += 1
        peak_bps = 0.0
        if buckets:
            peak_bps = max((b["sum"]/b["count"]) for b in buckets.values() if b["count"]>0)

        records.append({
            "user_id": u.id,
            "name": u.name,
            "ip": u.ip_address,
            "is_active": u.is_active,
            "rx_bytes": total_rx,
            "tx_bytes": total_tx,
            "total_bytes": total_rx + total_tx,
            "avg_total_bps": avg_bps,
            "peak_window_bps": peak_bps,
        })

        # برای شیت timeline (12 اسلات مساوی)
        slots = 12
        slot_len = (now - since) / slots
        for i in range(slots):
            s = since + i*slot_len
            e = since + (i+1)*slot_len
            bytes_sum = sum(
                (p.get("rx_delta", 0) + p.get("tx_delta", 0))
                for p in series
                if p.get("t_end") and p["t_end"] > s and p["t_end"] <= e
                )

            timeline_rows.append({
                "user_id": u.id, "name": u.name, "ip": u.ip_address,
                "slot_end": e.isoformat(), "bytes": bytes_sum
            })

    # DataFrames
    df_summary = pd.DataFrame.from_records(records)
    df_timeline = pd.DataFrame.from_records(timeline_rows)

    if format.lower() == "csv":
        # یک CSV چند‌شیتی نداریم، دو فایل برگردوندن پیچیده می‌شه—پس summary را برمی‌گردونیم.
        csv_buf = io.StringIO()
        df_summary.to_csv(csv_buf, index=False)
        csv_buf.seek(0)
        filename = f"users_usage_{now.strftime('%Y%m%d_%H%M%S')}.csv"
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
        return Response(content=csv_buf.getvalue(), headers=headers, media_type="text/csv")

    # XLSX با چند شیت: Summary + Timeline (و قابل توسعه)
    xbuf = io.BytesIO()
    with pd.ExcelWriter(xbuf, engine="openpyxl") as writer:
        df_summary.to_excel(writer, index=False, sheet_name="Summary")
        if not df_timeline.empty:
            df_timeline.to_excel(writer, index=False, sheet_name="Timeline")
    xbuf.seek(0)
    filename = f"users_usage_{now.strftime('%Y%m%d_%H%M%S')}.xlsx"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(
        xbuf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers
    )


# Helper: محاسبه دلتای بایت و bps از لیست لاگ‌های مرتب‌شده

def compute_deltas(rows: List[TrafficLog]):
    series = []
    for prev, cur in zip(rows, rows[1:]):
        dt = (cur.timestamp - prev.timestamp).total_seconds()
        if dt <= 0:
            continue
        drx = (cur.rx_bytes or 0) - (prev.rx_bytes or 0)
        dtx = (cur.tx_bytes or 0) - (prev.tx_bytes or 0)
        if drx < 0 or dtx < 0:
            continue

        rx_bps = (drx * 8.0) / dt
        tx_bps = (dtx * 8.0) / dt

        t_start = to_aware_utc(prev.timestamp)
        t_end   = to_aware_utc(cur.timestamp)

        series.append({
            "dt": dt,
            "rx_delta": drx,
            "tx_delta": dtx,
            "rx_bps": rx_bps,
            "tx_bps": tx_bps,
            "total_bps": rx_bps + tx_bps,
            "t_start": t_start,
            "t_end": t_end,
        })
    return series


@router.get("/users/summary")
def get_user_summary(
    db: Session = Depends(get_db),
    hours: int = Query(24, ge=1, le=168, description="time window in hours"),
    window_seconds: int = Query(300, ge=60, le=3600, description="aggregation window for peak/min calc")
):
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=hours)

    users: List[User] = db.query(User).all()
    response: List[Dict[str, Any]] = []

    for user in users:
        # دریافت لاگ‌های این کاربر در بازه
        rows: List[TrafficLog] = (
            db.query(TrafficLog)
              .filter(TrafficLog.user_id == user.id, TrafficLog.timestamp >= since, TrafficLog.timestamp <= now)
              .order_by(asc(TrafficLog.timestamp))
              .all()
        )

        if len(rows) < 2:
            response.append({
                "id": user.id,
                "name": user.name,
                "ip": user.ip_address,
                "is_active": user.is_active,
                "latitude": getattr(user, "lat", None),
                "longitude": getattr(user, "long", None),
                "rx_bytes": 0,
                "tx_bytes": 0,
                "total_bps_avg": 0.0,
                "peak_window": None,
                "timeline": [],
            })
            continue

        series = compute_deltas(rows)
        for p in series:
            p["t_start"] = to_aware_utc(p["t_start"])
            p["t_end"]   = to_aware_utc(p["t_end"])

        # حجم مصرف در بازه (مبتنی بر delta)
        total_rx_bytes = sum(p["rx_delta"] for p in series)
        total_tx_bytes = sum(p["tx_delta"] for p in series)

        # میانگین bps در کل بازه
        avg_total_bps = sum(p["total_bps"] for p in series) / max(len(series), 1)

        # باکت‌بندی برای پیدا کردن peak/min پنجره‌ای
        t0 = series[0]["t_start"]
        buckets: Dict[int, Dict[str, Any]] = {}
        def bidx(ts: datetime):
            return int((ts - t0).total_seconds() // window_seconds)
        for p in series:
            idx = bidx(p["t_start"])
            b = buckets.setdefault(idx, {"sum":0.0, "count":0, "start":p["t_start"], "end":p["t_end"]})
            b["sum"] += p["total_bps"]
            b["count"] += 1
            if p["t_start"] < b["start"]: b["start"] = p["t_start"]
            if p["t_end"] > b["end"]: b["end"] = p["t_end"]
        def to_window_obj(b):
            if b["count"] == 0: return None
            return {"window_start": b["start"], "window_end": b["end"], "total_bps_avg": b["sum"] / b["count"]}
        windows = [to_window_obj(b) for b in buckets.values() if b["count"]>0]
        peak_w = max(windows, key=lambda w: w["total_bps_avg"]) if windows else None
        min_w = min(windows, key=lambda w: w["total_bps_avg"]) if windows else None

        # ساخت timeline (12 باکت مساوی روی بازه)
        slots = 12
        slot_len = (now - since) / slots
        timeline = []
        for i in range(slots):
            s = since + i*slot_len
            e = since + (i+1)*slot_len
            # جمع delta در بازهٔ این اسلات
            bytes_sum = sum(
                (p.get("rx_delta", 0) + p.get("tx_delta", 0))
                for p in series
                if p.get("t_end") and p["t_end"] > s and p["t_end"] <= e
                )

            timeline.append({"ts": e.isoformat(), "total_bytes": bytes_sum})

        response.append({
            "id": user.id,
            "name": user.name,
            "ip": user.ip_address,
            "is_active": user.is_active,
            "latitude": getattr(user, "lat", None),
            "longitude": getattr(user, "long", None),
            # حجم مصرف درست‌شده (delta-based)
            "rx_bytes": total_rx_bytes,
            "tx_bytes": total_tx_bytes,
            # bps
            "total_bps_avg": avg_total_bps,
            "peak_window": peak_w,
            "min_window": min_w,
            # سری زمانی
            "timeline": timeline,
        })

    return response

@router.get("/users/{user_id}/chart")
def user_chart(
    user_id: int,
    db: Session = Depends(get_db),
    hours: int = Query(24, ge=1, le=168),
    window_seconds: int = Query(300, ge=60, le=3600),
):
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=hours)

    user: User = db.query(User).filter(User.id == user_id).first()
    if not user:
        return JSONResponse({"error": "user not found"}, status_code=404)

    rows: List[TrafficLog] = (
        db.query(TrafficLog)
          .filter(TrafficLog.user_id == user_id,
                  TrafficLog.timestamp >= since,
                  TrafficLog.timestamp <= now)
          .order_by(asc(TrafficLog.timestamp))
          .all()
    )
    if len(rows) < 2:
        return {
            "user": {"id": user.id, "name": user.name, "ip": user.ip_address},
            "ts": [], "rx_bps": [], "tx_bps": [], "total_bps": [],
            "rx_bytes": [], "tx_bytes": [], "total_bytes": []
        }

    series = compute_deltas(rows)

    ts = [p["t_end"].isoformat() for p in series]
    rx_bps = [p["rx_bps"] for p in series]
    tx_bps = [p["tx_bps"] for p in series]
    total_bps = [p["total_bps"] for p in series]
    rx_bytes = [p["rx_delta"] for p in series]
    tx_bytes = [p["tx_delta"] for p in series]
    total_bytes = [p["rx_delta"] + p["tx_delta"] for p in series]

    return {
        "user": {"id": user.id, "name": user.name, "ip": user.ip_address},
        "ts": ts,
        "rx_bps": rx_bps,
        "tx_bps": tx_bps,
        "total_bps": total_bps,
        "rx_bytes": rx_bytes,
        "tx_bytes": tx_bytes,
        "total_bytes": total_bytes,
    }

@router.get("/users/{user_id}/export")
def export_single_user(
    user_id: int,
    db: Session = Depends(get_db),
    hours: int = Query(24, ge=1, le=168),
    window_seconds: int = Query(300, ge=60, le=3600),
    format: str = Query("xlsx", regex="^(xlsx|csv)$")
):
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=hours)

    u: User = db.query(User).filter(User.id == user_id).first()
    if not u:
        return JSONResponse({"error": "user not found"}, status_code=404)

    rows: List[TrafficLog] = (
        db.query(TrafficLog)
          .filter(TrafficLog.user_id == user_id,
                  TrafficLog.timestamp >= since,
                  TrafficLog.timestamp <= now)
          .order_by(asc(TrafficLog.timestamp)).all()
    )

    series = compute_deltas(rows) if len(rows) >= 2 else []
    summary = [{
        "user_id": u.id, "name": u.name, "ip": u.ip_address, "is_active": u.is_active,
        "rx_bytes": sum(p["rx_delta"] for p in series),
        "tx_bytes": sum(p["tx_delta"] for p in series),
        "total_bytes": sum(p["rx_delta"] + p["tx_delta"] for p in series),
        "avg_total_bps": (sum(p["total_bps"] for p in series) / max(len(series), 1)) if series else 0.0,
    }]

    df_summary = pd.DataFrame.from_records(summary)
    df_timeline = pd.DataFrame.from_records([{
        "t_start": p["t_start"], "t_end": p["t_end"],
        "rx_delta": p["rx_delta"], "tx_delta": p["tx_delta"],
        "rx_bps": p["rx_bps"], "tx_bps": p["tx_bps"], "total_bps": p["total_bps"]
    } for p in series])

    if format.lower() == "csv":
        buf = io.StringIO()
        df_timeline.to_csv(buf, index=False)
        buf.seek(0)
        headers = {"Content-Disposition": f'attachment; filename="user_{u.id}_timeline.csv"'}
        return Response(content=buf.getvalue(), headers=headers, media_type="text/csv")

    xbuf = io.BytesIO()
    with pd.ExcelWriter(xbuf, engine="openpyxl") as writer:
        df_summary.to_excel(writer, index=False, sheet_name="Summary")
        if not df_timeline.empty:
            df_timeline.to_excel(writer, index=False, sheet_name="Timeline")
    xbuf.seek(0)
    headers = {"Content-Disposition": f'attachment; filename="user_{u.id}_usage.xlsx"'}
    return StreamingResponse(
        xbuf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers
    )

