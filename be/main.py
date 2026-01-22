# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles # Import để serve ảnh kết quả
import os

from app.api import auth
from app.api.handwritten_load_picture import router as handwritten_router
from app.api.omr_grading import router as omr_router # <--- IMPORT MỚI

app = FastAPI(title="OCR Grading API")

# Tạo thư mục uploads nếu chưa có
os.makedirs("uploads/omr", exist_ok=True)

# Mount thư mục uploads để xem được ảnh kết quả qua URL
# Ví dụ: http://localhost:8000/static/omr/graded_1.jpg
app.mount("/static", StaticFiles(directory="uploads"), name="static")

origins = [
    "http://localhost:5173",
    "http://192.168.1.10:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(handwritten_router, prefix="/api/handwritten")
app.include_router(omr_router, prefix="/api/omr") # <--- ĐĂNG KÝ ROUTER MỚI

@app.get("/")
def root():
    return {"message": "OCR backend is running"}