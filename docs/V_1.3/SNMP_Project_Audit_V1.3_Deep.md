# Deep Scan Addendum
## Models Found
### telecom_monitoring/models.py:User
- `id`: Column(Integer, primary_key=True)
- `name`: Column(String, nullable=False)
- `phone`: Column(String, unique=True, nullable=False)
- `ip_address`: Column(String, unique=True, nullable=False)
- `region`: Column(String)
- `latitude`: Column(String)
- `longitude`: Column(String)
- `plan`: Column(String, default="نامشخص")
- `is_active`: Column(Boolean, default=True)
- `created_at`: Column(DateTime, default=datetime.utcnow)
- `email`: Column(String, nullable=True)
- `usage_limit`: Column(Float, nullable=True)
- `last_seen`: Column(DateTime, nullable=True)
- `device_type`: Column(String, default="router")

### telecom_monitoring/models.py:TrafficLog
- `id`: Column(Integer, primary_key=True)
- `user_id`: Column(Integer, ForeignKey('users.id'))
- `interface_name`: Column(String)
- `rx_bytes`: Column(BigInteger)
- `tx_bytes`: Column(BigInteger, default=0)
- `timestamp`: Column(DateTime, default=datetime.utcnow)


## OIDs Found
- 1.3.6.1.2.1.2.2.1.10
- 1.3.6.1.2.1.2.2.1.16

## Issues Detected
- [ ] Duplicate SQLAlchemy Base definitions detected in: telecom_monitoring/base.py, telecom_monitoring/models.py
- [ ] APSheduler usage found in: telecom_monitoring/app.py, telecom_monitoring/api/routes/user.py. Ensure it's initialized on startup, not per-request.
- [ ] Hard-coded SNMP COMMUNITY in: telecom_monitoring/config.py. Move to environment variables.
- [ ] CORS middleware not configured in: telecom_monitoring/api/main.py
- [ ] Static file mounting missing in: telecom_monitoring/app.py
