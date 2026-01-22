from app.services.ocr.reader import OCRReader2
from app.services.ocr.classifier import Classifier
import cv2
import os

# [LƯU Ý]: Các import cũ (preprocessing, features, io_utils, visualize) 
# có thể bỏ nếu không dùng hàm legacy bên dưới nữa.

class VietnameseOCR:
    def __init__(self, use_ml_classifier=True, gpu=False):
        # [FIX 1]: Lưu biến cấu hình vào self để dùng ở hàm khác
        self.use_ml = use_ml_classifier
        
        # Classifier (nếu có dùng sau này)
        self.classifier = Classifier(use_ml=use_ml_classifier)

        # 2. Load 2 Model OCR chuyên biệt
        print("Load Printed OCR Engine...")
        self.print_engine = OCRReader2(gpu=gpu, model_type='printed') 
        
        print("Load Handwritten OCR Engine...")
        self.hw_engine = OCRReader2(gpu=gpu, model_type='handwritten') 

    def predict_type(self, img_crop):
        """
        Dùng model CNN để đoán xem ảnh crop là chữ in hay viết tay.
        Trả về: 'handwritten' hoặc 'printed'
        """
        # [FIX 1]: Bây giờ self.use_ml đã tồn tại, không bị lỗi nữa
        if not self.use_ml:
            return 'handwritten' # Mặc định
        
        # --- LOGIC GIẢ LẬP (Thay bằng model thật của bạn) ---
        # label = self.classifier.predict(img_crop)
        # return 'handwritten' if label == 1 else 'printed'
        
        return 'handwritten' 

    def process_crop(self, crop_path):
        """
        Hàm xử lý thông minh cho 1 ảnh crop (Đây là hàm chính dùng cho luồng mới)
        """
        # 1. Đọc ảnh
        img = cv2.imread(crop_path)
        if img is None:
            return "", "handwritten" # Xử lý trường hợp ảnh lỗi

        # 2. Phân loại (Classification)
        text_type = self.predict_type(img)
        
        # 3. Định tuyến (Routing) sang đúng model
        if text_type == 'printed':
            # Dùng model chữ in (nhanh, chuẩn font)
            # Hàm predict của OCRReader2 đã được update để nhận path hoặc numpy array
            results = self.print_engine.predict(crop_path)
            return results, 'printed'
        else:
            # Dùng model viết tay
            results = self.hw_engine.predict(crop_path)
            return results, 'handwritten'

    # =========================================================================
    # [CẢNH BÁO]: CÁC HÀM DƯỚI ĐÂY LÀ CODE CŨ (LEGACY)
    # Không tương thích với luồng "Tách màu -> Crop" mới.
    # Nên xóa hoặc giữ để tham khảo, nhưng ĐỪNG GỌI CHÚNG trong luồng mới.
    # =========================================================================
    
    # def detect_handwriting_vs_print(self, img_path):
    #     ... (Code cũ này sẽ lỗi vì OCRReader2 mới không trả về bbox chuẩn) ...

    # def process_image(self, img_path, ...):
    #     ...