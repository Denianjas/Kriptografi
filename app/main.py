from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routes import aes_image_routes
from app.routes.aeslsb import router as gabungan

app = FastAPI(title="AES + LSB Image API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(gabungan, prefix="/aeslsb", tags=["AES + LSB"])
app.include_router(aes_image_routes.router, prefix="/aes-image", tags=["AES Image"])

# Root endpoint
@app.get("/")
def root():
    return {"message": "Selamat datang! /docs untuk dokumentasi API"}
