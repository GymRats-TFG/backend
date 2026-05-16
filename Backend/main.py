from fastapi import FastAPI
from routers.auth import router as auth_router
from routers.users import router as users_router
from routers.gyms import router as gyms_router

app = FastAPI(title="GymRats API")

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(gyms_router)

@app.get("/")
def read_root():
    return {"message": "GymRats API is running 🚀"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "0.0.3"}