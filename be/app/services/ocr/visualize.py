import cv2
import numpy as np

def visualize_results(img_path, handwritten, printed, output_path):
    img = cv2.imread(img_path)
    if img is None:
        return None
    for d in handwritten:
        bbox = np.array(d['bbox'], dtype=np.int32)
        cv2.polylines(img, [bbox], True, (0,0,255), 2)
        cv2.putText(img, "Viết tay", tuple(bbox[0]), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)
    for d in printed:
        bbox = np.array(d['bbox'], dtype=np.int32)
        cv2.polylines(img, [bbox], True, (0,255,0), 2)
        cv2.putText(img, "Chữ in", tuple(bbox[0]), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)
    cv2.imwrite(output_path, img)
    return output_path