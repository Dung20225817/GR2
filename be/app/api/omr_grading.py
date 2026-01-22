# app/api/omr_grading.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import os
import shutil
from typing import List
from starlette.concurrency import run_in_threadpool

# Import service vừa viết
from app.services.omr.omr_service import process_omr_exam

router = APIRouter()

BASE_OMR_DIR = "uploads/omr"
os.makedirs(BASE_OMR_DIR, exist_ok=True)

@router.post("/grade")
async def grade_exam(
    file: UploadFile = File(...),
    answers: str = Form(..., description="Chuỗi đáp án cách nhau bởi dấu phẩy, v.d: 1,2,0,1,4"),
    num_questions: int = Form(5),
    num_choices: int = Form(5)
):
    try:
        # 1. Parse đáp án từ string sang list int
        # Ví dụ input: "1,2,0,1,4" -> [1, 2, 0, 1, 4]
        try:
            answer_key = [int(x.strip()) for x in answers.split(',')]
        except ValueError:
            raise HTTPException(status_code=400, detail="Format đáp án không hợp lệ. Phải là số cách nhau bởi dấu phẩy.")

        if len(answer_key) != num_questions:
            raise HTTPException(status_code=400, detail=f"Số lượng đáp án ({len(answer_key)}) không khớp với số câu hỏi ({num_questions}).")

        # 2. Lưu file upload tạm thời
        file_location = os.path.join(BASE_OMR_DIR, file.filename)
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 3. Gọi Service xử lý
        result = await run_in_threadpool(
            process_omr_exam,       # Tên hàm
            image_path=file_location,
            output_folder=BASE_OMR_DIR,
            answer_key=answer_key,
            questions=num_questions,
            choices=num_choices
        )

        # 4. Kiểm tra lỗi từ service
        if "error" in result:
             return JSONResponse(status_code=400, content=result)

        # 5. Trả về kết quả JSON
        return JSONResponse(content={
            "message": "Chấm điểm thành công",
            "data": result,
            "image_url": f"/static/omr/{result['result_image']}" # Đường dẫn giả định nếu bạn config static files
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"message": "Lỗi server", "details": str(e)})