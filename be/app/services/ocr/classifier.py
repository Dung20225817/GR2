import os
import numpy as np

class Classifier:
    def __init__(self, use_ml=True, model_path="handwriting_classifier.pkl"):
        self.use_ml = use_ml
        self.model = None
        if use_ml and os.path.exists(model_path):
            import pickle
            with open(model_path, "rb") as f:
                self.model = pickle.load(f)

    def is_handwritten(self, features):
        if self.use_ml and self.model is not None:
            vec = np.array(list(features.values())).reshape(1, -1)
            pred = self.model.predict(vec)
            return bool(pred[0])
        return self._rule_based(features)

    def _rule_based(self, features):
        score = 0
        weights = {
            'confidence': -3.0,
            'edge_variance': 2.5,
            'gradient_variance': 2.0,
            'stroke_variance': 1.5,
            'angle_variance': 1.5,
            'texture_entropy': 1.0,
            'morphology_diff': 1.0,
            'contour_area_variance': 1.0
        }
        thresholds = {
            'confidence': 0.75,
            'edge_variance': 100,
            'gradient_variance': 1000,
            'stroke_variance': 55,
            'angle_variance': 8,
            'texture_entropy': 5.5,
            'morphology_diff': 15,
            'contour_area_variance': 500
        }
        if features['confidence'] < thresholds['confidence']:
            score += weights['confidence'] * (1 - features['confidence'])
        if features['edge_variance'] > thresholds['edge_variance']:
            score += weights['edge_variance']
        if features['gradient_variance'] > thresholds['gradient_variance']:
            score += weights['gradient_variance']
        if features['stroke_variance'] > thresholds['stroke_variance']:
            score += weights['stroke_variance']
        if features['angle_variance'] > thresholds['angle_variance']:
            score += weights['angle_variance']
        if features['texture_entropy'] > thresholds['texture_entropy']:
            score += weights['texture_entropy']
        if features['morphology_diff'] > thresholds['morphology_diff']:
            score += weights['morphology_diff']
        if features['contour_area_variance'] > thresholds['contour_area_variance']:
            score += weights['contour_area_variance']
        return score >= 8.0