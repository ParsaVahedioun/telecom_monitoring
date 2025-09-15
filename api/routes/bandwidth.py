# telecom_monitoring/api/routes/bandwidth.py
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import SessionLocal
from models import TrafficLog, User

router = APIRouter(prefix="/api/users", tags=["bandwidth"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- helpers ---
def as_naive_utc(dt: datetime) -> datetime:
    """هر datetime ورودی را به UTC بدون tzinfo تبدیل می‌کند تا مقایسه‌ها امن باشد."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt  # فرض: همین الآن UTC-naive ذخیره شده
    return dt.astimezone(timezone.utc).replace(tzinfo=None)

def decimate(points: List["BandwidthPoint"], max_points: int) -> List["BandwidthPoint"]:
    """اگر سری خیلی بزرگ بود، با نمونه‌برداری یکنواخت سبک کن."""
    n = len(points)
    if n <= max_points:
        return points
    step = n / max_points
    out = []
    i = 0.0
    while int(i) < n:
        out.append(points[int(i)])
        i += step
    if out[-1] is not points[-1]:
        out.append(points[-1])
    return out

# --- models ---
class BandwidthPoint(BaseModel):
    t_start: datetime
    t_end: datetime
    rx_bps: float
    tx_bps: float
    total_bps: float
    # اختیاری: دلتاهای بایت برای نمایش حجم مصرف در همان بازه
    rx_bytes_delta: Optional[int] = None
    tx_bytes_delta: Optional[int] = None

class WindowStat(BaseModel):
    window_start: datetime
    window_end: datetime
    rx_bps_avg: float
    tx_bps_avg: float
    total_bps_avg: float

class BandwidthResponse(BaseModel):
    user_id: int
    window_seconds: int
    series: List[BandwidthPoint]
    max_window: Optional[WindowStat] = None
    min_window: Optional[WindowStat] = None
    stats: Dict[str, float]

@router.get("/{user_id}/bandwidth", response_model=BandwidthResponse)
def get_user_bandwidth(
    user_id: int,
    db: Session = Depends(get_db),
    since: Optional[datetime] = Query(None, description="ISO datetime"),
    until: Optional[datetime] = Query(None, description="ISO datetime"),
    hours: Optional[int] = Query(24, ge=1, le=168, description="میان‌بُر: اگر since/until ندهی، از اکنون-ساعت استفاده می‌شود"),
    window_seconds: int = Query(300, ge=60, le=3600, description="aggregation window (e.g., 300s = 5 min)"),
    include_bytes: bool = Query(True, description="دلتا بایت هر بازه هم برگردانده شود؟"),
    max_points: int = Query(1500, ge=100, le=10000, description="سقف تعداد نقاط سری برای سبک شدن پاسخ"),
):
    # همه‌چیز را UTC naive نگه داریم تا با timestamp های دیتابیس (معمولاً naive) سازگار باشد
    now = datetime.utcnow()
    if until is None:
        until = now
    else:
        until = as_naive_utc(until)
    if since is None:
        since = until - timedelta(hours=hours or 24)
    else:
        since = as_naive_utc(since)

    # وجود کاربر
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # دریافت لاگ‌ها
    rows: List[TrafficLog] = (
        db.query(TrafficLog)
        .filter(
            TrafficLog.user_id == user_id,
            TrafficLog.timestamp >= since,
            TrafficLog.timestamp <= until,
        )
        .order_by(TrafficLog.timestamp.asc())
        .all()
    )

    if len(rows) < 2:
        return BandwidthResponse(
            user_id=user_id,
            window_seconds=window_seconds,
            series=[],
            max_window=None,
            min_window=None,
            stats={
                "avg_bps": 0.0,
                "p95_bps": 0.0,
                "max_bps": 0.0,
                "rx_bytes_total": 0.0,
                "tx_bytes_total": 0.0,
                "total_bytes": 0.0,
                "live_rx_bps": 0.0,
                "live_tx_bps": 0.0,
                "live_total_bps": 0.0,
            },
        )

    # محاسبه نرخ bps و دلتا بایت بین نمونه‌ها (هندل reset/wrap + زمان)
    series: List[BandwidthPoint] = []
    for prev, cur in zip(rows, rows[1:]):
        prev_ts = as_naive_utc(prev.timestamp)
        cur_ts = as_naive_utc(cur.timestamp)
        dt = (cur_ts - prev_ts).total_seconds()
        if dt <= 0:
            continue
        drx = (cur.rx_bytes or 0) - (prev.rx_bytes or 0)
        dtx = (cur.tx_bytes or 0) - (prev.tx_bytes or 0)
        if drx < 0 or dtx < 0:
            # counter wrap/reset → رد کن
            continue
        rx_bps = (drx * 8) / dt
        tx_bps = (dtx * 8) / dt
        series.append(
            BandwidthPoint(
                t_start=prev_ts,
                t_end=cur_ts,
                rx_bps=rx_bps,
                tx_bps=tx_bps,
                total_bps=rx_bps + tx_bps,
                rx_bytes_delta=drx if include_bytes else None,
                tx_bytes_delta=dtx if include_bytes else None,
            )
        )

    if not series:
        return BandwidthResponse(
            user_id=user_id,
            window_seconds=window_seconds,
            series=[],
            max_window=None,
            min_window=None,
            stats={
                "avg_bps": 0.0,
                "p95_bps": 0.0,
                "max_bps": 0.0,
                "rx_bytes_total": 0.0,
                "tx_bytes_total": 0.0,
                "total_bytes": 0.0,
                "live_rx_bps": 0.0,
                "live_tx_bps": 0.0,
                "live_total_bps": 0.0,
            },
        )

    # اگر خیلی زیاد است، سبک کن تا فرانت کند نشود
    series = decimate(series, max_points)

    # باکت‌بندی برای پیدا کردن پرمصرف‌ترین/کم‌مصرف‌ترین پنجره‌ها
    t0 = series[0].t_start
    buckets: Dict[int, Dict[str, Any]] = {}

    def bucket_idx(ts: datetime) -> int:
        return int((ts - t0).total_seconds() // window_seconds)

    for p in series:
        idx = bucket_idx(p.t_start)
        b = buckets.setdefault(
            idx,
            {
                "rx_sum": 0.0,
                "tx_sum": 0.0,
                "total_sum": 0.0,
                "count": 0,
                "start": p.t_start,
                "end": p.t_end,
            },
        )
        b["rx_sum"] += p.rx_bps
        b["tx_sum"] += p.tx_bps
        b["total_sum"] += p.total_bps
        b["count"] += 1
        if p.t_start < b["start"]:
            b["start"] = p.t_start
        if p.t_end > b["end"]:
            b["end"] = p.t_end

    windows: List[WindowStat] = []
    for b in buckets.values():
        if b["count"] == 0:
            continue
        windows.append(
            WindowStat(
                window_start=b["start"],
                window_end=b["end"],
                rx_bps_avg=b["rx_sum"] / b["count"],
                tx_bps_avg=b["tx_sum"] / b["count"],
                total_bps_avg=b["total_sum"] / b["count"],
            )
        )

    max_window = max(windows, key=lambda w: w.total_bps_avg) if windows else None
    min_window = min(windows, key=lambda w: w.total_bps_avg) if windows else None

    # آمار کلی
    totals = [p.total_bps for p in series]
    avg_bps = sum(totals) / len(totals)
    max_bps = max(totals)
    p95_bps = sorted(totals)[int(0.95 * (len(totals) - 1))]
    # حجم مصرف کل بازه از روی دلتاها
    rx_bytes_total = float(sum((p.rx_bytes_delta or 0) for p in series))
    tx_bytes_total = float(sum((p.tx_bytes_delta or 0) for p in series))
    live_rx_bps = series[-1].rx_bps
    live_tx_bps = series[-1].tx_bps
    live_total_bps = series[-1].total_bps

    return BandwidthResponse(
        user_id=user_id,
        window_seconds=window_seconds,
        series=series,
        max_window=max_window,
        min_window=min_window,
        stats={
            "avg_bps": avg_bps,
            "p95_bps": p95_bps,
            "max_bps": max_bps,
            "rx_bytes_total": rx_bytes_total,
            "tx_bytes_total": tx_bytes_total,
            "total_bytes": rx_bytes_total + tx_bytes_total,
            "live_rx_bps": live_rx_bps,
            "live_tx_bps": live_tx_bps,
            "live_total_bps": live_total_bps,
        },
    )
