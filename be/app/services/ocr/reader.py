import easyocr
from vietocr.tool.predictor import Predictor
from vietocr.tool.config import Cfg
from PIL import Image
import numpy as np
import torch

class OCRReader:
    def __init__(self, langs=['vi'], gpu=False):
        self.reader = easyocr.Reader(langs, gpu=gpu)

    def read(self, img_path):
        # trả về danh sách tuples (bbox, text, confidence)
        return self.reader.readtext(img_path)
    
class OCRReader2:
    def __init__(self, gpu=False, model_type='handwritten'):
        self.device = 'cuda:0' if gpu and torch.cuda.is_available() else 'cpu'
        
        # --- CẤU HÌNH ĐỘNG DỰA TRÊN LOẠI CHỮ ---
        if model_type == 'printed':
            # CHIẾN LƯỢC CHO CHỮ IN: Dùng model vgg_seq2seq (nhẹ và nhanh)
            print(f"   [OCR] Loading 'vgg_seq2seq' for Printed text (GPU={gpu})...")
            try:
                self.config = Cfg.load_config_from_name('vgg_seq2seq')
            except:
                # Fallback nếu không tải được
                print("   [OCR] Fallback to 'vgg_transformer' for Printed text.")
                self.config = Cfg.load_config_from_name('vgg_transformer')
            
            # Tắt beamsearch để tăng tốc độ tối đa cho chữ in
            self.config['predictor']['beamsearch'] = False 
        else:
            # CHIẾN LƯỢC CHO CHỮ VIẾT TAY: Dùng model vgg_transformer (Chính xác cao)
            print(f"   [OCR] Loading 'vgg_transformer' for Handwritten text (GPU={gpu})...")
            self.config = Cfg.load_config_from_name('vgg_transformer')
            
            # Beamsearch giúp đọc chữ viết tay tốt hơn (nhưng chậm hơn chút)
            self.config['predictor']['beamsearch'] = True 

        # Cấu hình thiết bị chung
        self.config['device'] = self.device
        
        # Khởi tạo Predictor
        self.detector = Predictor(self.config)

    def predict(self, img_source):
        """
        Hàm mới: Chuyên dùng để dự đoán text từ 1 ảnh crop
        Input: đường dẫn ảnh (str) HOẶC ảnh numpy array HOẶC PIL Image
        Output: Chuỗi text (str)
        """
        try:
            # Xử lý input đa dạng
            if isinstance(img_source, str):
                img = Image.open(img_source).convert('RGB')
            elif isinstance(img_source, np.ndarray):
                img = Image.fromarray(img_source).convert('RGB')
            elif isinstance(img_source, Image.Image):
                img = img_source.convert('RGB')
            else:
                return "" # Input không hợp lệ

            # Dự đoán
            return self.detector.predict(img)
        except Exception as e:
            print(f"Error in OCR predict: {e}")
            return ""

    def read(self, img_path):
        """
        Hàm cũ: Giữ lại để tương thích với code cũ (trả về list tuple)
        """
        text = self.predict(img_path)
        # VietOCR không có bbox & confidence → trả theo format giả lập
        return [(None, text, 1.0)]