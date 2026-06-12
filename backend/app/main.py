from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, meal, recommend, report, user
from app.services.security import allowed_origins
from app.services.store import ensure_store, supabase_enabled

app = FastAPI(title="Healthy Food MVP API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ensure_store()
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(meal.router)
app.include_router(recommend.router)
app.include_router(report.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "data_source": "supabase" if supabase_enabled() else "local"}
