from fastapi import FastAPI
from .routes import router as callout_router
from .admin import router as admin_router

app = FastAPI(title="Lootmore API", version="0.1")

app.include_router(callout_router)
app.include_router(admin_router)

@app.get("/health")
def health():
    return {"ok": True}
