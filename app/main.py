from fastapi import FastAPI
from app.api.v1.s3_routes import router

app = FastAPI(title="S3_service")

app.include_router(router)