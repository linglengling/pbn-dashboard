import os
import threading
import time
import datetime
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .config import STATIC_DIR
from .database import init_db
from .routes import (
    auth_routes,
    stats_routes,
    sites_routes,
    servers_routes,
    backlinks_routes,
    posts_routes,
    settings_routes,
    users_routes,
    cloudflare_routes,
    vps_routes,
    audit_routes,
    clusters_routes,
    indexing_routes
)

app = FastAPI(title="PBN Management Dashboard V2", version="2.0.0")

# 1. Gzip Compression Middleware (Giảm 90% dung lượng truyền qua mạng)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 2. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Include API Routers
app.include_router(auth_routes.router)
app.include_router(stats_routes.router)
app.include_router(sites_routes.router)
app.include_router(servers_routes.router)
app.include_router(backlinks_routes.router)
app.include_router(posts_routes.router)
app.include_router(settings_routes.router)
app.include_router(users_routes.router)
app.include_router(cloudflare_routes.router)
app.include_router(vps_routes.router)
app.include_router(audit_routes.router)
app.include_router(clusters_routes.router)
app.include_router(indexing_routes.router)

# 4. WebSocket Realtime Hub
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo or process client message if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# 5. Startup Hook & Background Audit Cron Worker
def _audit_cron_daemon():
    time.sleep(30)
    while True:
        try:
            from .database import get_settings
            from .audit_runner import run_system_audit_job
            st = get_settings()
            enabled = st.get("AUTO_AUDIT_ENABLED", "1") == "1"
            if enabled:
                last_run_str = st.get("LAST_AUDIT_RUN")
                should_run = False
                if not last_run_str:
                    should_run = True
                else:
                    try:
                        last_run_dt = datetime.datetime.strptime(last_run_str, "%Y-%m-%d %H:%M:%S")
                        # Default interval: 3 days (259200 seconds)
                        if (datetime.datetime.now() - last_run_dt).total_seconds() >= 3 * 86400:
                            should_run = True
                    except Exception:
                        should_run = True
                
                if should_run:
                    run_system_audit_job()
        except Exception as e:
            print(f"[Audit Cron Daemon] Error: {e}")
        time.sleep(1800)

@app.on_event("startup")
def on_startup():
    init_db()
    threading.Thread(target=_audit_cron_daemon, daemon=True, name="AuditCronDaemon").start()

# 6. Static SPA Frontend Support (React 18 HTML5 History Routing)
static_path = Path(STATIC_DIR)
if static_path.exists() and (static_path / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(static_path / "assets")), name="assets")

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    # Don't intercept API routes or Swagger docs
    if full_path.startswith("api/") or full_path in ["docs", "redoc", "openapi.json", "ws"]:
        return None
    index_file = static_path / "index.html"
    if index_file.exists():
        return FileResponse(
            str(index_file),
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    return {"message": "PBN Dashboard V2 Python Backend Running! (SPA build not in static/)"}
