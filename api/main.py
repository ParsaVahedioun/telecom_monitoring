from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from api.routes.routes import router as monitor_router
from api.routes.user import user_routes as user_router  # <- اصلاح نام به router

app = FastAPI(title="Internet Usage Monitoring API")

# ثبت مسیرهای API بدون prefix (تغییر در اینجا مهمه)
app.include_router(monitor_router)
app.include_router(user_router) 

# routes frontend (static)
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "telecom_dashboard"))
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/", response_class=FileResponse)
def serve_index():
    return os.path.join(FRONTEND_DIR, "index.html")
