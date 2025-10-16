from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.aeslsb import router as gabungan

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router
app.include_router(gabungan, prefix="/aeslsb", tags=["aeslsb"])

@app.get("/")
def root():
    return {"message": "/docs untuk dokumentasi API"}