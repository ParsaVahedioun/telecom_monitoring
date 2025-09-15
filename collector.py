import asyncio
from pysnmp.hlapi.asyncio import (
    getCmd,
    SnmpEngine,
    CommunityData,
    UdpTransportTarget,
    ContextData,
    ObjectType,
    ObjectIdentity,
)
from config import COMMUNITY, INTERFACE_OID_BASE, INTERFACE_NAMES, INTERFACE_OID_TX_BASE
from database import SessionLocal
from models import TrafficLog, User




# کلاس جایگزین PyWrapper روی TCP
class SNMPTCPWrapper:
    def __init__(self, ip, community, port=161, timeout=10, retries=3):
        self.ip = ip
        self.community = community
        self.port = port
        self.timeout = timeout
        self.retries = retries

    async def get(self, oid):
        iterator = getCmd(
            SnmpEngine(),
            CommunityData(self.community, mpModel=1),  # SNMPv2c
            UdpTransportTarget((self.ip, self.port), timeout=self.timeout, retries=self.retries),
            ContextData(),
            ObjectType(ObjectIdentity(oid))
        )
        errorIndication, errorStatus, errorIndex, varBinds = await iterator
        if errorIndication:
            raise Exception(errorIndication)
        elif errorStatus:
            raise Exception(f"{errorStatus.prettyPrint()} at {errorIndex}")
        else:
            for oid, val in varBinds:
                return int(val)


async def collect_and_store():
    session = SessionLocal()

    # 1. اگر هیچ کاربری وجود ندارد، یکی بساز برای تست
    users = session.query(User).all()
    if not users:
        default_user = User(
            name="default_test",
            ip_address="192.168.2.20",
            phone="unknown",
            region="test-region",
            latitude="0.0",
            longitude="0.0",
            plan="نامحدود",
            is_active=True
        )
        session.add(default_user)
        session.commit()
        users = [default_user]

    # 2. برای هر کاربر، SNMP بگیر (با TCP)
    for user in users:
        print(f"🕒 جمع‌آوری برای کاربر: {user.name} ({user.ip_address})")
        client = SNMPTCPWrapper(user.ip_address, COMMUNITY)

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
                print(f"[{user.name} - {name}] ⬇ {rx} bytes | ⬆ {tx} bytes")

            except Exception as e:
                print(f"⛔ خطا برای {user.name} - {name}: {e}")

        session.commit()

    session.close()
