# app/services/omr_service.py
import cv2
import numpy as np
import os
from app.services.omr import until # Import file until.py cùng thư mục

def process_omr_exam(image_path: str, output_folder: str, answer_key: list, questions=5, choices=5):
    """
    Xử lý ảnh trắc nghiệm OMR.
    
    Args:
        image_path: Đường dẫn ảnh đầu vào.
        output_folder: Thư mục để lưu ảnh kết quả.
        answer_key: List đáp án đúng (ví dụ: [1, 0, 2, 1, 4]).
        questions: Số câu hỏi.
        choices: Số lựa chọn.
        
    Returns:
        dict: Kết quả chấm (score, grading array, output_image_path)
    """
    
    # Cấu hình kích thước ảnh chuẩn hóa
    heightImg = 700
    widthImg = 700
    
    img = cv2.imread(image_path)
    if img is None:
        return {"error": "Không thể đọc file ảnh"}

    # --- 1. Tiền xử lý (Preprocessing) ---
    img = cv2.resize(img, (widthImg, heightImg))
    imgContours = img.copy()
    imgFinal = img.copy()
    imgBiggestContours = img.copy()

    imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    imgBlur = cv2.GaussianBlur(imgGray, (5, 5), 1)
    
    # Canny Edge Detection
    v = np.median(imgBlur)
    imgCanny = cv2.Canny(imgBlur, 10, 50)

    # --- 2. Tìm Contours ---
    contours, hierarchy = cv2.findContours(imgCanny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    cv2.drawContours(imgContours, contours, -1, (0, 255, 0), 10)

    # Tìm hình chữ nhật (khung bài thi & khung điểm)
    rectCon = until.rectContours(contours)
    
    # Nếu không tìm thấy đủ khung hình chữ nhật
    if len(rectCon) < 2:
        return {"error": "Không tìm thấy khung bài thi. Vui lòng chụp ảnh rõ nét hơn."}

    biggestContour = until.getCornerPoints(rectCon[0]) # Khung trả lời
    gradePoints = until.getCornerPoints(rectCon[1])    # Khung điểm số

    if biggestContour.size != 0 and gradePoints.size != 0:
        # Reorder points
        biggestContour = until.reorder(biggestContour)
        gradePoints = until.reorder(gradePoints)

        # --- 3. Warp Perspective (Biến đổi góc nhìn) ---
        pt1 = np.float32(biggestContour)
        pt2 = np.float32([[0, 0], [widthImg, 0], [0, heightImg], [widthImg, heightImg]])
        matrix = cv2.getPerspectiveTransform(pt1, pt2)
        imgWarpColored = cv2.warpPerspective(img, matrix, (widthImg, heightImg))

        ptG1 = np.float32(gradePoints)
        ptG2 = np.float32([[0, 0], [325, 0], [0, 150], [325, 150]])
        matrixG = cv2.getPerspectiveTransform(ptG1, ptG2)
        imgGradeDisplay = cv2.warpPerspective(img, matrixG, (325, 150))

        # --- 4. Apply Threshold & Split Boxes ---
        imgWarpGray = cv2.cvtColor(imgWarpColored, cv2.COLOR_BGR2GRAY)
        imgThresh = cv2.threshold(imgWarpGray, 170, 255, cv2.THRESH_BINARY_INV)[1]

        boxes = until.slpitBoxes(imgThresh)
        
        # Đếm pixel để xác định tô cái nào
        myPixelVal = np.zeros((questions, choices))
        countC = 0
        countR = 0

        for image in boxes:
            totalPixels = cv2.countNonZero(image)
            myPixelVal[countR][countC] = totalPixels
            countC += 1
            if countC == choices:
                countR += 1
                countC = 0

        # --- 5. Chọn đáp án người dùng (User Answers) ---
        myIndex = []
        for x in range(0, questions):
            arr = myPixelVal[x]
            myIndexVal = np.where(arr == np.amax(arr))
            myIndex.append(int(myIndexVal[0][0]))

        # --- 6. Chấm điểm (Grading) ---
        grading = []
        for x in range(0, questions):
            if answer_key[x] == myIndex[x]:
                grading.append(1)
            else:
                grading.append(0)
        
        score = (sum(grading) / questions) * 100

        # --- 7. Vẽ kết quả lên ảnh ---
        imgResult = imgWarpColored.copy()
        imgResult = until.showAnswers(imgResult, myIndex, grading, answer_key, questions, choices)
        
        imRawDrawing = np.zeros_like(imgWarpColored)
        imRawDrawing = until.showAnswers(imRawDrawing, myIndex, grading, answer_key, questions, choices)
        
        invMatrix = cv2.getPerspectiveTransform(pt2, pt1)
        imgInvWarp = cv2.warpPerspective(imRawDrawing, invMatrix, (widthImg, heightImg))

        # Vẽ điểm số
        imRawGrade = np.zeros_like(imgGradeDisplay)
        cv2.putText(imRawGrade, f"{int(score)}%", (60, 100), cv2.FONT_HERSHEY_COMPLEX, 3, (0, 255, 0), 3)

        invMatrixG = cv2.getPerspectiveTransform(ptG2, ptG1)
        imgGradeDisplay = cv2.warpPerspective(imRawGrade, invMatrixG, (widthImg, heightImg))

        # Tổng hợp ảnh cuối cùng
        imgFinal = cv2.addWeighted(imgFinal, 1, imgInvWarp, 0.5, 0)
        imgFinal = cv2.addWeighted(imgFinal, 1, imgGradeDisplay, 0.5, 0)

        # --- 8. Lưu ảnh kết quả ---
        base_name = os.path.basename(image_path)
        result_name = f"graded_{base_name}"
        result_path = os.path.join(output_folder, result_name)
        cv2.imwrite(result_path, imgFinal)

        return {
            "success": True,
            "score": score,
            "user_answers": myIndex,
            "correct_answers": answer_key,
            "result_image": result_name  # Trả về tên file để frontend load
        }
    
    return {"error": "Không thể xử lý bài thi (Lỗi contour)"}