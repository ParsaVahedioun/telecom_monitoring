# SNMP Internet Usage Monitoring
سامانهٔ مانیتورینگ و تحلیل مصرف اینترنت کاربران بر پایهٔ **SNMP** با Backend **FastAPI** و داشبورد وب **Bootstrap + Chart.js**.
---
## ✨ هایلایت‌ها (آخرین آپدیت‌ها)

- بازطراحی کامل **داشبورد ادمین** با KPIها، رنکینگ، Scatter RX/TX، Heatmap مکانی و سری‌زمانی مصرف کل.
- صفحهٔ مجزای **جزئیات پهنای‌باند هر کاربر** با:
  - فیلتر بازهٔ زمانی (۱/۶/۱۲/۲۴ ساعت و سفارشی) و **پنجرهٔ تجمیع** (۱/۵/۱۰/۳۰ دقیقه)
  - **سرعت لحظه‌ای** RX/TX (bps) + نسبت RX/TX (Donut)
  - آمار **Max/Min/Average** برای RX/TX و **پیک پنجره‌ای** (بازهٔ زمانی با بیشترین میانگین پهنای‌باند)
  - خروجی‌گیری **CSV/XLSX** (داشبورد و صفحهٔ کاربر)
- ارتقای اندپوینت‌ها و دیتابیس:
  - `GET /admin/api/users/summary?hours&window_seconds` → دادهٔ رنکینگ و سری‌زمانی
  - `GET /api/users/{user_id}/bandwidth?since&until&window_seconds` → سری bps + max/min window + پیک‌ها
  - ایندکس ترکیبی روی `(user_id, timestamp)` برای سرعت گزارش‌گیری
- **سازگاری Python 3.13** (جایگزینی کتابخانهٔ SNMP قدیمی وابسته به `imp` → استفاده از کلاینت‌های سازگار مثل `puresnmp`).
- رفع روتینگ فرانت‌اند: اضافه شدن مسیرهای استاتیک `"/admin"`, `"/admin/user-bandwidth"` و لینک جزئیات هر کاربر.

---
## 🧮 فرمول‌های محاسبه

برای دو نمونهٔ متوالی از شمارنده‌های ترافیک:
```
Δt   = t[i] - t[i-1]                (sec)
Δrx  = rx_bytes[i] - rx_bytes[i-1]
Δtx  = tx_bytes[i] - tx_bytes[i-1]
if Δrx < 0 or Δtx < 0:  # overflow/reset
    skip

rx_bps    = (Δrx * 8) / Δt
tx_bps    = (Δtx * 8) / Δt
total_bps = rx_bps + tx_bps
```

- **Max/Min point**: بیشترین/کمترین مقدار `total_bps` در نقاط سری.
- **پنجرهٔ تجمیع**: تقسیم سری به باکت‌هایی با طول `window_seconds` و محاسبهٔ **میانگین** در هر باکت.
- **پیک پنجره‌ای**: باکتی که بیشترین `total_bps_avg` را دارد (با `window_start/end`).

---
## 🧩 Tech Stack

- **Backend**: FastAPI (Python 3.13), SQLAlchemy
- **Frontend**: Bootstrap 5, Chart.js, DataTables, Leaflet (+ Heatmap)
- **DB**: SQLite (قابل مهاجرت به PostgreSQL)
- **SNMP**: پیشنهاد `puresnmp` (یا معادل سازگار با 3.13)
- **Export**: CSV / XLSX (SheetJS یا openpyxl/pandas)

---
## 🛣️ ساختار پروژه (نمونه)

```
telecom_monitoring/
├─ api/
│  ├─ main.py
│  ├─ routes/
│  │  ├─ admin_routes.py
│  │  ├─ bandwidth.py
│  │  ├─ routes.py
│  │  └─ user.py
├─ models.py
├─ database.py
├─ telecom_dashboard/
│  ├─ admin/index.html
│  ├─ admin/user_bandwidth.html
│  └─ assets/...
└─ docs/
   └─ images/
      ├─ dashboard_ranking.png
      ├─ user_ratio_kpis.png
      └─ user_timeseries.png
```

---
## 🖼️ اسکرین‌شات‌ها

![dashboard_ranking.png](docs/images/dashboard_ranking.png)

![user_ratio_kpis.png](docs/images/user_ratio_kpis.png)

![user_timeseries.png](docs/images/user_timeseries.png)


---
## 🔌 اندپوینت‌های کلیدی

- `GET /api/collect-status` → آخرین وضعیت جمع‌آوری (موفق/خطا)
- `GET /admin/api/users/summary?hours=24&window_seconds=300`
- `GET /api/users/{user_id}/bandwidth?since&until&window_seconds=300`
- `GET /admin/api/users/export?hours=24&window_seconds=300&format=xlsx|csv`
- `GET /api/users` ، `POST /api/users` ، `DELETE /api/users/{id}`

---
## ⚙️ راه‌اندازی سریع

```bash
python -m venv venv
source venv/bin/activate   # یا venv\Scripts\activate در ویندوز
pip install -r requirements.txt
uvicorn api.main:app --reload
# داشبورد: http://127.0.0.1:8000/admin
```

> توجه: مقادیر حساس مثل SNMP community/IP را در `.env` یا `config.py` نگه دارید و در `.gitignore` قرار دهید.

---
## 🚀 نقشهٔ راه

- SNMP v3 (Auth/Priv)، هشدارهای آستانه‌ای (Alerting)، گزارش‌های زمان‌بندی‌شده PDF
- پیش‌تجمیع (۱m/۵m/۱۰m) و پارتیشن‌بندی زمانی در پایگاه داده
- RBAC، Audit Log، Token-based API
