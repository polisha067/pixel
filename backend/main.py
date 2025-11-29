from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from routers import router
from database import init_db
import uvicorn
import os

app = FastAPI()

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    import traceback
    error_msg = str(exc)
    print(f"[ERROR] Unhandled exception: {error_msg}")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {error_msg}"}
    )

try:
    print("[INIT] Initializing database...")
    reset_db = os.getenv('RESET_DB', 'false').lower() == 'true'
    if reset_db:
        print("[INIT] Resetting database on startup (data will be cleared)")
    else:
        print("[INIT] Preserving existing database data")
    init_db(reset_db=reset_db)
    print("[INIT] Database initialized successfully")
except Exception as e:
    print(f"[INIT] Error initializing database: {str(e)}")
    import traceback
    traceback.print_exc()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')
print(f"[INIT] Frontend directory: {FRONTEND_DIR}")
print(f"[INIT] Frontend exists: {os.path.exists(FRONTEND_DIR)}")
if os.path.exists(FRONTEND_DIR):
    files = os.listdir(FRONTEND_DIR)
    print(f"[INIT] Frontend files: {files}")
    html_files = [f for f in files if f.endswith('.html')]
    print(f"[INIT] HTML files found: {html_files}")

if os.path.exists(FRONTEND_DIR):
    print(f"[INIT] Mounting static files from: {FRONTEND_DIR}")
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
    print(f"[INIT] Static files mounted successfully")
else:
    print(f"[INIT] WARNING: Frontend directory not found, static files not mounted")

app.include_router(router)

if __name__ == '__main__':
    print("=" * 50)
    print("Starting FastAPI server on http://127.0.0.1:8001")
    print(f"[INIT] Current working directory: {os.getcwd()}")
    print(f"[INIT] Script location: {__file__}")
    print(f"[INIT] BASE_DIR: {BASE_DIR}")
    print(f"[INIT] FRONTEND_DIR: {FRONTEND_DIR}")
    print("=" * 50)
    print("\n[INIT] Registered routes:")
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            print(f"  {list(route.methods)} {route.path}")
    print("=" * 50)
    host = os.getenv('HOST', '127.0.0.1')
    port = int(os.getenv('PORT', '8001'))
    print(f"[INIT] Starting server on {host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level='info')