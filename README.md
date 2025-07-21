# README

## معرفی پروژه

این پروژه یک داشبورد **مانیتورینگ مصرف اینترنت** مبتنی بر FastAPI و Chart.js است که به صورت لحظه‌ای میزان **دریافت (RX)** و **ارسال (TX)** ترافیک را نمایش می‌دهد.

---

## تاریخچه نسخه‌ها

### نسخه ۱.۰: نمایش پایه‌ای RX و TX

* راه‌اندازی ساده FastAPI برای جمع‌آوری داده‌های SNMP توسط تابع `collect_and_store`.
* ذخیره ترافیک ورودی و خروجی (rx\_bytes, tx\_bytes) در جدول `TrafficLog`.
* API `/admin/traffic?range=now` برای بازگرداندن مقادیر RX و TX.
* فرانت‌اند ساده با Chart.js برای رسم دو خط RX و TX.

### نسخه ۲.۰: آمار تفکیکی (Min / Max / Avg)

* افزودن API جدید `/admin/api/traffic-stats` با پارامترهای `start` و `end` برای محاسبه‌ی:

  * حداقل (min)
  * حداکثر (max)
  * میانگین (avg)
* تفکیک جداگانه‌ی RX و TX در خروجی JSON.
* نمایش مقادیر Min/Max/Avg در کارت‌های مجزا در فرانت‌اند.

### نسخه ۳.۰: بهبود لاگ‌ها و قابلیت اتصال

* پیاده‌سازی badge وضعیت اتصال `/admin/ping` برای نمایش آنلاین/آفلاین بودن SNMP.
* endpoint `/admin/api/collect-status` برای گزارش آخرین موفقیت یا خطا (شامل skip به‌خاطر max instances).
* نمایش پیام خطا در UI هنگام مشکلات SNMP یا زمان‌بندی.

### نسخه ۴.۰: ارتقای UI/UX و گراف‌های پیشرفته

* حالت **دارک مود** با فونت فارسی (`Vazirmatn`).
* استایل مینیمال و کارت‌های نئومورفیک برای آمار.
* افزودن نمودار دایره‌ای نسبت RX به TX (`rxTxRatio`).
* نمایش **سرعت لحظه‌ای** (Kb/s) برای RX و TX در کارت‌های اختصاصی.
* بهبود محور زمان با:

  * تبدیل به فرمت **تاریخ و زمان فارسی**
  * نمایش **ثانیه**
  * استفاده از TimeZone `Asia/Tehran`
* افزودن Dataset سوم برای نمایش **میانگین (AVG)** روی چارت با رنگ بنفش.
* امکان **تغییر تم** بین تاریک/روشن.

---

## نصب و راه‌اندازی

1. کلون کردن مخزن:

   ```bash
   git clone <repository-url>
   cd project-directory
   ```

2. ایجاد و فعال‌سازی محیط مجازی:

   ```bash
   python -m venv venv
   source venv/bin/activate  # لینوکس/مک
   venv\Scripts\activate     # ویندوز
   ```

3. نصب پیش‌نیازها:

   ```bash
   pip install -r requirements.txt
   ```

4. تنظیمات متغیرهای محیطی:

   * `DB_URL` در فایل `config.py`
   * `TARGET_IP`, `COMMUNITY`, `INTERFACE_OID_BASE`, ...

5. اجرای Migrations (در صورت نیاز):

   ```bash
   alembic upgrade head
   ```

6. اجرای سرور:

   ```bash
   uvicorn api.main:app --reload
   ```

---

## استفاده

* **جمع‌آوری خودکار**: Scheduler هر ۳۰ ثانیه داده SNMP را می‌گیرد.
* **Endpoint‌ها**:

  * `GET /admin/traffic?range=<now|1h|1d|1w|1m>`
  * `GET /admin/api/traffic-stats?start=YYYY-MM-DD HH:MM&end=YYYY-MM-DD HH:MM`
  * `GET /admin/ping`
  * `GET /admin/api/collect-status`
  * `GET /admin/api/live-speed`
* **فرانت‌اند**: در `index.html` با Chart.js و کارت‌های Bootstrap.

---

## توسعه و آینده

* افزودن **فیلتر کاربران** و چندین دستگاه.
* نمودارهای پیشرفته‌تر با **ApexCharts** یا **Recharts**.
* ارسال **هشدار (Alert)** در صورت عبور از سقف مصرف.
* **ذخیره‌سازی** و **بازیابی** داده‌ها در بازه‌های طولانی‌تر.
* اضافه کردن** تحلیل ماشین** از مصرف کاربران
*ایجاد پنل ادمین برای مانیتورینگ همه کاربران و تست ایپی های مختلف

---

## مشارکت

خوشحال می‌شویم Pull Request بفرستید و باگ‌ها را گزارش کنید!
