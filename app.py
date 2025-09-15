from database import init_db
from collector import collect_and_store
from apscheduler.schedulers.blocking import BlockingScheduler
import asyncio

def job():
    print("🕒 اجرای خودکار جمع‌آوری داده SNMP")
    asyncio.run(collect_and_store())

if __name__ == "__main__":
    init_db()
    scheduler = BlockingScheduler()
    # scheduler.add_job(job, 'interval', minutes=0.1)
    scheduler.add_job(job, 'interval', seconds=120, max_instances=10, coalesce=False)

    print("🚀 مانیتورینگ SNMP هر ۵ دقیقه شروع شد...")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("⛔ متوقف شد.")
