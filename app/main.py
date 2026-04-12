from fastapi import FastAPI
from app.controllers.distributor_controller import router as distributor_router

app = FastAPI(title="Demand Planning Agent")

app.include_router(distributor_router)


@app.get("/")
def health_check():
    return {"message": "Demand Planning Agent is running"}

@app.get("/health")
def health():
    return {"status": "ok"}