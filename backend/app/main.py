from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import meal, recommend, report, user
from app.services.store import ensure_store

app = FastAPI(title="Healthy Food MVP API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ensure_store()
app.include_router(user.router)
app.include_router(meal.router)
app.include_router(recommend.router)
app.include_router(report.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
