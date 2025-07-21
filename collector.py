import asyncio
from puresnmp import Client, V2C, PyWrapper
from config import TARGET_IP, COMMUNITY, INTERFACE_OID_BASE, INTERFACE_NAMES , INTERFACE_OID_TX_BASE
from database import SessionLocal
from models import TrafficLog, User


async def collect_and_store():
    session = SessionLocal()
    client = PyWrapper(Client(TARGET_IP, V2C(COMMUNITY)))

    user = session.query(User).filter_by(ip_address=TARGET_IP).first()
    if not user:
        user = User(ip_address=TARGET_IP, name="mikrotik")
        session.add(user)
        session.commit()

    for idx, name in INTERFACE_NAMES.items():
        rx_oid = f"{INTERFACE_OID_BASE}.{idx}"
        tx_oid = f"{INTERFACE_OID_TX_BASE}.{idx}"
        try:
            rx = await client.get(rx_oid)
            tx = await client.get(tx_oid)

            log = TrafficLog(
                user_id=user.id,
                interface_name=name,
                rx_bytes=int(rx),
                tx_bytes=int(tx)
            )
            session.add(log)
            print(f"[{name}] ⬇ rx: {rx} bytes | ⬆ tx: {tx} bytes")
        except Exception as e:
            print(f"⛔ خطا در دریافت {name}: {e}")

    session.commit()
    session.close()
