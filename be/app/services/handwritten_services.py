# handwritten_services.py

import os
import cv2
import numpy as np
from app.services.ocr.handwriting_model import VietnameseOCR
import re
def sanitize(obj):
    """Chuyển các kiểu không phải native Python sang kiểu JSON-friendly"""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.generic):
        return obj.item()
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize(v) for v in obj]
    return obj


def merge_nearby_boxes(boxes, horizontal_threshold=30, vertical_threshold=20):
    """
    Gộp các bounding box gần nhau thành 1 box lớn hơn
    
    Tham số:
    - boxes: danh sách các box [(x, y, w, h), ...]
    - horizontal_threshold: khoảng cách ngang tối đa để gộp (pixels)
    - vertical_threshold: khoảng cách dọc tối đa để coi là cùng hàng (pixels)
    
    Returns:
    - merged_boxes: danh sách các box đã gộp [(x, y, w, h), ...]
    """
    if len(boxes) == 0:
        return []
    
    # Chuyển sang định dạng [x1, y1, x2, y2] để dễ tính toán
    boxes_xyxy = []
    for (x, y, w, h) in boxes:
        boxes_xyxy.append([x, y, x + w, y + h])
    
    boxes_xyxy = np.array(boxes_xyxy)
    
    # Sắp xếp theo y (hàng ngang), sau đó theo x (trái -> phải)
    indices = np.lexsort((boxes_xyxy[:, 0], boxes_xyxy[:, 1]))
    boxes_sorted = boxes_xyxy[indices]
    
    merged = []
    visited = set()
    
    for i in range(len(boxes_sorted)):
        if i in visited:
            continue
        
        # Bắt đầu một nhóm mới
        group = [i]
        visited.add(i)
        
        current_box = boxes_sorted[i].copy()
        
        # Tìm các box khác cùng hàng và gần nhau
        for j in range(i + 1, len(boxes_sorted)):
            if j in visited:
                continue
            
            next_box = boxes_sorted[j]
            
            # Kiểm tra cùng hàng ngang (overlap về chiều dọc)
            y1_center = (current_box[1] + current_box[3]) / 2
            y2_top = next_box[1]
            y2_bottom = next_box[3]
            y2_center = (y2_top + y2_bottom) / 2
            
            # Cùng hàng nếu trung tâm của box này nằm trong vùng của box kia
            vertical_aligned = abs(y1_center - y2_center) <= vertical_threshold
            
            # Kiểm tra khoảng cách ngang
            horizontal_gap = next_box[0] - current_box[2]  # khoảng cách giữa 2 box
            
            if vertical_aligned and horizontal_gap <= horizontal_threshold:
                # Gộp vào nhóm
                group.append(j)
                visited.add(j)
                
                # Mở rộng current_box để bao gồm next_box
                current_box[0] = min(current_box[0], next_box[0])
                current_box[1] = min(current_box[1], next_box[1])
                current_box[2] = max(current_box[2], next_box[2])
                current_box[3] = max(current_box[3], next_box[3])
        
        # Lưu box đã merge
        x1, y1, x2, y2 = current_box
        merged.append((int(x1), int(y1), int(x2 - x1), int(y2 - y1)))
    
    return merged


def visualize_boxes(img, boxes, color=(0, 255, 0), label=""):
    """
    Vẽ bounding boxes lên ảnh để debug
    """
    img_vis = img.copy()
    for i, (x, y, w, h) in enumerate(boxes):
        cv2.rectangle(img_vis, (x, y), (x + w, y + h), color, 2)
        cv2.putText(img_vis, f"{label}{i}", (x, y - 5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    return img_vis


def extract_colored_regions(image_path, output_folder, prefix, 
                           merge_horizontal=True, 
                           horizontal_threshold=30,
                           vertical_threshold=20,
                           save_visualization=True):
    """
    Tách chữ xanh & đỏ, lấy bounding box và lưu các vùng crop ra folder.
    
    Tham số mới:
    - merge_horizontal: True để gộp các box gần nhau theo hàng ngang
    - horizontal_threshold: khoảng cách ngang tối đa để gộp (pixels)
    - vertical_threshold: khoảng cách dọc tối đa để coi là cùng hàng
    - save_visualization: True để lưu ảnh có vẽ bounding box
    
    Trả về:
        blue_boxes  = [(crop_path, x, y, w, h), ...]
        red_boxes   = [(crop_path, x, y, w, h), ...]
    """
    os.makedirs(output_folder, exist_ok=True)

    img = cv2.imread(image_path)
    if img is None:
        return [], []

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Mask chữ xanh
    lower_blue = np.array([90, 50, 50])
    upper_blue = np.array([135, 255, 255])
    mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)

    # Mask chữ đỏ (2 khoảng hue)
    lower_red1 = np.array([0, 70, 50])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 70, 50])
    upper_red2 = np.array([180, 255, 255])
    mask_red = cv2.inRange(hsv, lower_red1, upper_red1) | cv2.inRange(hsv, lower_red2, upper_red2)

    # Morphology làm mượt
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    mask_blue = cv2.morphologyEx(mask_blue, cv2.MORPH_CLOSE, kernel)
    mask_red = cv2.morphologyEx(mask_red, cv2.MORPH_CLOSE, kernel)

    # Tìm contours + lấy bounding box
    blue_boxes_raw, red_boxes_raw = [], []

    # Thu thập tất cả boxes trước khi merge
    for mask, box_list in [(mask_blue, blue_boxes_raw), (mask_red, red_boxes_raw)]:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w < 10 or h < 10:  # lọc noise nhỏ
                continue
            box_list.append((x, y, w, h))
    
    # Merge boxes nếu được yêu cầu
    if merge_horizontal:
        print(f"  📦 Trước merge: {len(blue_boxes_raw)} blue boxes, {len(red_boxes_raw)} red boxes")
        blue_boxes_merged = merge_nearby_boxes(blue_boxes_raw, horizontal_threshold, vertical_threshold)
        red_boxes_merged = merge_nearby_boxes(red_boxes_raw, horizontal_threshold, vertical_threshold)
        print(f"  ✅ Sau merge: {len(blue_boxes_merged)} blue boxes, {len(red_boxes_merged)} red boxes")
    else:
        blue_boxes_merged = blue_boxes_raw
        red_boxes_merged = red_boxes_raw
    
    # Lưu visualization nếu cần
    if save_visualization:
        vis_img = img.copy()
        
        # Vẽ boxes trước merge (màu nhạt)
        for (x, y, w, h) in blue_boxes_raw:
            cv2.rectangle(vis_img, (x, y), (x + w, y + h), (200, 200, 255), 1)
        for (x, y, w, h) in red_boxes_raw:
            cv2.rectangle(vis_img, (x, y), (x + w, y + h), (200, 200, 200), 1)
        
        # Vẽ boxes sau merge (màu đậm)
        for i, (x, y, w, h) in enumerate(blue_boxes_merged):
            cv2.rectangle(vis_img, (x, y), (x + w, y + h), (255, 0, 0), 2)
            cv2.putText(vis_img, f"B{i}", (x, y - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        
        for i, (x, y, w, h) in enumerate(red_boxes_merged):
            cv2.rectangle(vis_img, (x, y), (x + w, y + h), (0, 0, 255), 2)
            cv2.putText(vis_img, f"R{i}", (x, y - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        vis_path = os.path.join(output_folder, f"{prefix}_visualization.jpg")
        cv2.imwrite(vis_path, vis_img)
        print(f"  💾 Đã lưu visualization: {vis_path}")
    
    # Crop và lưu các vùng đã merge
    blue_boxes_final, red_boxes_final = [], []
    
    for i, (x, y, w, h) in enumerate(blue_boxes_merged):
        crop = img[y:y+h, x:x+w]
        crop_name = f"{prefix}_blue_{i}.png"
        crop_path = os.path.join(output_folder, crop_name)
        cv2.imwrite(crop_path, crop)
        blue_boxes_final.append((crop_path, int(x), int(y), int(w), int(h)))
    
    for i, (x, y, w, h) in enumerate(red_boxes_merged):
        crop = img[y:y+h, x:x+w]
        crop_name = f"{prefix}_red_{i}.png"
        crop_path = os.path.join(output_folder, crop_name)
        cv2.imwrite(crop_path, crop)
        red_boxes_final.append((crop_path, int(x), int(y), int(w), int(h)))

    return blue_boxes_final, red_boxes_final

def _clean_spacing(text: str) -> str:
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'\s+([,.;:!?])', r'\1', text)  # remove space before punctuation
    text = re.sub(r'([(\["])\s+', r'\1', text)
    return text

def combine_region_texts(regions, prefer='handwritten', join_with=' ' , line_threshold=None):
    """
    Gộp các đoạn text từ danh sách regions thành 1 đoạn văn.
    - regions: list of {'bbox':[x,y,w,h], 'handwritten':[...], 'printed':[...], ...}
    - prefer: 'handwritten' | 'printed' | 'mixed' (ưu tiên lấy text)
    - join_with: ký tự nối giữa các segment (mặc định ' ')
    - line_threshold: nếu truyền (pixels) -> nếu khoảng cách dọc giữa 2 region > threshold sẽ chèn newline
                       (mặc định None: không chèn newline, trả về 1 đoạn)
    Trả về: chuỗi văn bản đã gộp.
    """
    segs = []
    for r in regions:
        bbox = r.get('bbox') or [0,0,0,0]
        x, y, w, h = bbox if len(bbox) == 4 else (bbox[0], bbox[1], 0, 0)
        y_center = y + h / 2
        # Chọn text theo prefer
        if prefer == 'handwritten':
            texts = r.get('handwritten', []) or []
        elif prefer == 'printed':
            texts = r.get('printed', []) or []
        else:  # mixed
            texts = (r.get('handwritten') or []) + (r.get('printed') or [])
        # flatten và nối các phần trong region
        seg_text = ' '.join([t for t in texts if t])
        seg_text = _clean_spacing(seg_text)
        if seg_text:
            segs.append((y_center, x, seg_text))

    # Sắp xếp top->bottom, left->right
    segs.sort(key=lambda item: (item[0], item[1]))

    if not segs:
        return ""

    parts = []
    prev_y = None
    for y_center, x, text in segs:
        if line_threshold is not None and prev_y is not None:
            if abs(y_center - prev_y) > line_threshold:
                parts.append('\n')  # ngắt đoạn nếu khoảng cách lớn
        parts.append(text)
        prev_y = y_center

    paragraph = join_with.join([p for p in parts if p is not None])
    paragraph = _clean_spacing(paragraph)
    return paragraph

GLOBAL_OCR_ENGINE = None

def get_ocr_engine(use_ml=False):
    global GLOBAL_OCR_ENGINE
    if GLOBAL_OCR_ENGINE is None:
        print("⏳ Đang tải model OCR lần đầu tiên...")
        GLOBAL_OCR_ENGINE = VietnameseOCR(use_ml_classifier=use_ml)
        print("✅ Đã tải xong model OCR!")
    return GLOBAL_OCR_ENGINE

def process_handwritten_folder(folder_path: str, 
                               merge_horizontal=True,
                               horizontal_threshold=30,
                               vertical_threshold=20,
                               use_ml_classifier=False):
    """
    Xử lý toàn bộ ảnh trong 1 folder (qX hoặc aX)
    """
    results = []
    bbox_output = os.path.join(folder_path, "_bbox")
    os.makedirs(bbox_output, exist_ok=True)
    
    # 1. Lấy Engine (Singleton)
    ocr_engine = get_ocr_engine(use_ml=use_ml_classifier)

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if filename == "_bbox" or not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue

        print("\n" + "="*70)
        print(f"📄 Processing file: {filename}")

        # 2. Tách màu & Crop
        blue_boxes, red_boxes = extract_colored_regions(
            file_path, 
            bbox_output, 
            prefix=filename.split('.')[0],
            merge_horizontal=merge_horizontal,
            horizontal_threshold=horizontal_threshold,
            vertical_threshold=vertical_threshold,
            save_visualization=True
        )

        # 3. Chuẩn bị danh sách task (SỬA LẠI ĐOẠN NÀY ĐỂ TRÁNH LỖI TUPLE)
        all_tasks = []
        
        # blue_boxes là list các tuple: (crop_path, x, y, w, h)
        for item in blue_boxes:
            all_tasks.append({
                "crop_path": item[0],       # Lấy path từ tuple
                "bbox": item[1:],           # Lấy (x, y, w, h)
                "color": "blue"             # Gán màu thủ công
            })
            
        for item in red_boxes:
            all_tasks.append({
                "crop_path": item[0],
                "bbox": item[1:],
                "color": "red"
            })

        # Danh sách chứa kết quả sau khi AI đọc
        results_hw = []       # Chứa kết quả được model Handwritten đọc
        results_printed = []  # Chứa kết quả được model Printed đọc

        print(f"⚡ Bắt đầu xử lý thông minh {len(all_tasks)} vùng ảnh...")

        for task in all_tasks:
            # Truy cập bằng key dictionary thay vì index
            crop_path = task["crop_path"]
            
            # 4. Routing thông minh: Phân loại -> Chọn Model -> Đọc
            text_result, detected_type = ocr_engine.process_crop(crop_path)
            
            # Tạo object kết quả chuẩn
            result_item = {
                "text": text_result,
                "bbox": task["bbox"],         # [x, y, w, h]
                "source_color": task["color"],# blue/red
                "type": detected_type         # handwritten/printed
            }

            # Phân loại vào danh sách
            if detected_type == 'handwritten':
                results_hw.append(result_item)
            else:
                results_printed.append(result_item)

        # 5. Gộp text và lưu file
        base_name = os.path.splitext(filename)[0]
        
        # Gộp danh sách kết quả
        all_regions = results_hw + results_printed
        
        # Map lại dữ liệu để hàm combine_region_texts hiểu được
        mapped_regions = []
        for r in all_regions:
            item = {'bbox': r['bbox']}
            # combine_region_texts cần list text trong key 'handwritten' hoặc 'printed'
            if r['type'] == 'handwritten':
                item['handwritten'] = [r['text']]
            else:
                item['printed'] = [r['text']]
            mapped_regions.append(item)

        combined_handwritten = combine_region_texts(mapped_regions, prefer='handwritten', join_with=' ', line_threshold=vertical_threshold)
        combined_printed = combine_region_texts(mapped_regions, prefer='printed', join_with=' ', line_threshold=vertical_threshold)

        # Lưu file .txt
        hw_file_path = os.path.join(folder_path, f"{base_name}_chu_viet_tay.txt")
        printed_file_path = os.path.join(folder_path, f"{base_name}_chu_in.txt")
        try:
            with open(hw_file_path, "w", encoding="utf-8") as f:
                f.write(combined_handwritten or "")
            with open(printed_file_path, "w", encoding="utf-8") as f:
                f.write(combined_printed or "")
            print(f"  💾 Saved combined handwritten -> {hw_file_path}")
        except Exception as e:
            print(f"  ⚠️ Error saving combined text files: {e}")

        # 6. Trả về kết quả API
        results.append({
            "file": filename,
            "result": combined_handwritten + " " + combined_printed,
        })
        
        print(f"\n✅ Completed: {filename}")
        print(f"  - Handwritten regions detected: {len(results_hw)}")
        print(f"  - Printed regions detected: {len(results_printed)}")

    return sanitize(results)


def process_handwritten_batch(q_folder: str, a_folder: str,
                              merge_horizontal=True,
                              horizontal_threshold=30,
                              vertical_threshold=20,
                              use_ml_classifier=False):
    """
    Xử lý cả batch qX + aX
    
    Tham số:
    - q_folder: thư mục câu hỏi (qX)
    - a_folder: thư mục câu trả lời (aX)
    - merge_horizontal: True để gộp box theo hàng ngang
    - horizontal_threshold: khoảng cách ngang tối đa để gộp (pixels)
    - vertical_threshold: khoảng cách dọc tối đa để coi là cùng hàng (pixels)
    - use_ml_classifier: True để dùng ML classifier, False dùng rule-based
    """
    full_q_path = os.path.join("uploads/handwritten", q_folder)
    full_a_path = os.path.join("uploads/handwritten", a_folder)
    
    print("\n" + "="*70)
    print("🚀 BẮT ĐẦU XỬ LÝ BATCH")
    print("="*70)
    print(f"📁 Question folder: {q_folder}")
    print(f"📁 Answer folder: {a_folder}")
    print(f"⚙️  Merge horizontal: {merge_horizontal}")
    print(f"⚙️  Horizontal threshold: {horizontal_threshold}px")
    print(f"⚙️  Vertical threshold: {vertical_threshold}px")
    print(f"🤖 ML Classifier: {'Enabled' if use_ml_classifier else 'Rule-based'}")
    print("="*70)

    return {
        "question_results": process_handwritten_folder(
            full_q_path,
            merge_horizontal=merge_horizontal,
            horizontal_threshold=horizontal_threshold,
            vertical_threshold=vertical_threshold,
            use_ml_classifier=use_ml_classifier
        ),
        "answer_results": process_handwritten_folder(
            full_a_path,
            merge_horizontal=merge_horizontal,
            horizontal_threshold=horizontal_threshold,
            vertical_threshold=vertical_threshold,
            use_ml_classifier=use_ml_classifier
        )
    }