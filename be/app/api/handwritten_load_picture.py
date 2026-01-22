# api/handwritten_load_picture.py

from fastapi import APIRouter, UploadFile, File, Depends, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import os
from starlette.concurrency import run_in_threadpool
#import uuid dùng để tạo dãy ký tự ngẫu nhiên
import math
from datetime import datetime

from app.services.handwritten_services import process_handwritten_batch
from app.db_connect import get_db
from app.db.table import Picture

router = APIRouter()

BASE_DIR = "uploads/handwritten"
os.makedirs(BASE_DIR, exist_ok=True)


# ============================================================
#  Hàm lấy index folder kế tiếp (qX, aX)
# ============================================================
def get_next_index():
    existing = []
    for name in os.listdir(BASE_DIR):
        if name.startswith("q"):
            try:
                num = int(name[1:])
                existing.append(num)
            except:
                pass
    return 1 if not existing else max(existing) + 1


# ============================================================
#  Hàm xử lý giá trị float NaN/inf trả về JSON
# ============================================================
def sanitize(data):
    if isinstance(data, float) and (math.isnan(data) or math.isinf(data)):
        return None
    if isinstance(data, dict):
        return {k: sanitize(v) for k, v in data.items()}
    if isinstance(data, list):
        return [sanitize(i) for i in data]
    return data


# ============================================================
#  API UPLOAD ẢNH VÀ XỬ LÝ OCR CHO ẢNH VIẾT TAY
# ============================================================
@router.post("/upload")
async def upload_handwritten_images(
    uid: int = Form(...),                         # User ID
    question_images: list[UploadFile] = File(default=[]),
    result_images: list[UploadFile] = File(default=[]),
    db: Session = Depends(get_db)
):
    # ------------------------------------------------------------
    # 🔍 DEBUG: Kiểm tra số lượng ảnh nhận được
    # ------------------------------------------------------------
    print("=" * 60)
    print("📥 NHẬN ĐƯỢC TỪ FRONTEND:")
    print(f"   - Số ảnh câu hỏi (question_images): {len(question_images)}")
    print(f"   - Số ảnh kết quả (result_images): {len(result_images)}")
    # ------------------------------------------------------------
    # 1. Lấy index batch mới
    # ------------------------------------------------------------
    index = get_next_index()

    qi_folder = os.path.join(BASE_DIR, f"q{index}")
    ai_folder = os.path.join(BASE_DIR, f"a{index}")
    os.makedirs(qi_folder, exist_ok=True)
    os.makedirs(ai_folder, exist_ok=True)

    saved_files = {
        "q_folder": f"q{index}",
        "a_folder": f"a{index}",
        "question_images": [],
        "result_images": []
    }

    # ------------------------------------------------------------
    # 2. Lưu ảnh câu hỏi (qX)
    # ------------------------------------------------------------
    print(f"\n💾 LƯU ẢNH CÂU HỎI (vào folder {qi_folder}):")
    for idx, img in enumerate(question_images):
        ext = os.path.splitext(img.filename)[1]
        unique_name = f"q_{idx+1:03d}{ext}"  # ← q_001.png, q_002.png

        save_path = os.path.join(qi_folder, unique_name)
        with open(save_path, "wb") as buffer:
            buffer.write(await img.read())

        saved_files["question_images"].append(unique_name)
        print(f"   [{idx + 1}] {img.filename} → {unique_name}")

        # Lưu DB
        picture = Picture(
            p_name=unique_name,
            uuid=uid
        )
        db.add(picture)

    # ------------------------------------------------------------
    # 3. Lưu ảnh đáp án (aX)
    # ------------------------------------------------------------
    print(f"\n💾 LƯU ẢNH KẾT QUẢ (vào folder {ai_folder}):")
    for idx, img in enumerate(result_images):
        ext = os.path.splitext(img.filename)[1]
        unique_name = f"a_{idx+1:03d}{ext}"  # ← a_001.png, a_002.png

        save_path = os.path.join(ai_folder, unique_name)
        with open(save_path, "wb") as buffer:
            buffer.write(await img.read())

        saved_files["result_images"].append(unique_name)
        print(f"   [{idx + 1}] {img.filename} → {unique_name}")

        # Lưu DB
        picture = Picture(
            p_name=unique_name,
            uuid=uid
        )
        db.add(picture)

    print(f"\n📋 DANH SÁCH ANSWER IMAGES SAU KHI LƯU:")
    print(f"   {saved_files['result_images']}")

    # Commit vào DB
    db.commit()

    # Kiểm tra file thực tế trong folder
    print(f"\n🔍 KIỂM TRA FILE THỰC TẾ TRONG FOLDER:")
    print(f"   Question folder ({qi_folder}):")
    q_files = sorted(os.listdir(qi_folder))
    for f in q_files:
        print(f"      - {f}")

    print(f"   Answer folder ({ai_folder}):")
    a_files = sorted(os.listdir(ai_folder))
    for f in a_files:
        print(f"      - {f}")
    # ------------------------------------------------------------
    # 🔍 DEBUG: Kiểm tra file đã lưu
    # ------------------------------------------------------------
    print(f"\n📋 DANH SÁCH FILE ĐÃ LƯU:")
    print(f"   Question images: {saved_files['question_images']}")
    print(f"   Result images: {saved_files['result_images']}")

    # ------------------------------------------------------------
    # 4. Gọi xử lý OCR batch Q + A
    # ------------------------------------------------------------
    print("⏳ Bắt đầu xử lý OCR trong luồng riêng...")
    
    processing_result = await run_in_threadpool(
        process_handwritten_batch,  # Tên hàm
        saved_files["q_folder"],    # Tham số 1
        saved_files["a_folder"],    # Tham số 2
        merge_horizontal=True,      # Các tham số keyword...
        horizontal_threshold=50,
        vertical_threshold=30
    )

    sanitized_result = sanitize(processing_result)

    sanitized_result = sanitize(processing_result)

    print("Sanitized OCR answer Result:", sanitized_result["answer_results"])
    print("Sanitized OCR question Result:", sanitized_result["question_results"])

    return JSONResponse({
        "message": "Upload thành công!",
        "question_results": sanitized_result["question_results"],
        "answer_results":sanitized_result["answer_results"]
    })
