import numpy as np
import cv2

def get_default_features():
    return {
        'confidence': 0.5,
        'confidence_squared': 0.25,
        'edge_density': 0,
        'edge_variance': 0,
        'edge_mean': 0,
        'gradient_variance': 0,
        'gradient_mean': 0,
        'gradient_std': 0,
        'stroke_variance': 0,
        'stroke_std': 0,
        'stroke_range': 0,
        'texture_entropy': 0,
        'angle_variance': 0,
        'bbox_aspect_ratio': 1,
        'hist_entropy': 0,
        'hist_variance': 0,
        'morphology_diff': 0,
        'contour_count': 0,
        'contour_area_variance': 0,
        'contour_area_mean': 0,
        'text_length': 0,
        'has_special_chars': 0,
        'fft_energy': 0,
        'fft_mean': 0
    }

def calculate_entropy(gray):
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
    total = hist.sum()
    if total == 0:
        return 0
    hist = hist / total
    return -np.sum(hist * np.log2(hist + 1e-10))

def calculate_angle_variance(bbox):
    pts = np.array(bbox, dtype=np.float32)
    v1 = pts[1] - pts[0]
    v2 = pts[2] - pts[1]
    a1 = np.arctan2(v1[1], v1[0]) * 180 / np.pi
    a2 = np.arctan2(v2[1], v2[0]) * 180 / np.pi
    return abs(a1 - a2)

def extract_features(img, bbox, text, confidence):
    try:
        pts = np.array(bbox, dtype=np.int32)
        x_min, y_min = int(min(pts[:,0])), int(min(pts[:,1]))
        x_max, y_max = int(max(pts[:,0])), int(max(pts[:,1]))
        h, w = img.shape[:2]
        x_min, y_min = max(0, x_min), max(0, y_min)
        x_max, y_max = min(w, x_max), min(h, y_max)
        if x_max <= x_min or y_max <= y_min:
            return get_default_features()
        region = img[y_min:y_max, x_min:x_max]
        if region.size == 0:
            return get_default_features()
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    except Exception:
        return get_default_features()

    features = {}
    features['confidence'] = confidence
    features['confidence_squared'] = confidence ** 2

    edges = cv2.Canny(gray, 50, 150)
    features['edge_density'] = np.sum(edges > 0) / edges.size
    features['edge_variance'] = np.var(edges)
    features['edge_mean'] = np.mean(edges)

    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    grad = np.sqrt(sobelx**2 + sobely**2)
    features['gradient_variance'] = np.var(grad)
    features['gradient_mean'] = np.mean(grad)
    features['gradient_std'] = np.std(grad)

    features['stroke_variance'] = np.var(gray)
    features['stroke_std'] = np.std(gray)
    features['stroke_range'] = np.ptp(gray)

    features['texture_entropy'] = calculate_entropy(gray)
    features['angle_variance'] = calculate_angle_variance(bbox)
    features['bbox_aspect_ratio'] = (x_max - x_min) / max(1, y_max - y_min)

    hist = cv2.calcHist([gray], [0], None, [256], [0,256]).flatten()
    s = hist.sum() if hist.sum() != 0 else 1
    hist = hist / s
    features['hist_entropy'] = -np.sum(hist * np.log2(hist + 1e-10))
    features['hist_variance'] = np.var(hist)

    kernel = np.ones((3,3), np.uint8)
    dil = cv2.dilate(gray, kernel, iterations=1)
    ero = cv2.erode(gray, kernel, iterations=1)
    features['morphology_diff'] = np.mean(np.abs(dil - ero))

    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        areas = [cv2.contourArea(c) for c in contours]
        features['contour_count'] = len(contours)
        features['contour_area_variance'] = np.var(areas) if len(areas) > 1 else 0
        features['contour_area_mean'] = np.mean(areas)
    else:
        features['contour_count'] = 0
        features['contour_area_variance'] = 0
        features['contour_area_mean'] = 0

    features['text_length'] = len(text)
    features['has_special_chars'] = int(any(not c.isalnum() and not c.isspace() for c in text))

    fft = np.fft.fft2(gray)
    fft_mag = np.abs(fft)
    features['fft_energy'] = np.sum(fft_mag ** 2)
    features['fft_mean'] = np.mean(fft_mag)

    return features