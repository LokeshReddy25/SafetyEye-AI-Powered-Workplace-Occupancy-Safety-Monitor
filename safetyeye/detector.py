import cv2
import sys
sys.path.insert(0, '..')

from ultralytics import YOLO
from config import CONFIDENCE_THRESHOLD, IOU_THRESHOLD, MODEL_PATH
from safetyeye.logger import get_logger

logger = get_logger()

class SafetyDetector:
    def __init__(self, model_path=MODEL_PATH):
        try:
            self.model = YOLO(model_path)
            logger.info(f"Model loaded: {model_path}")
        except Exception as e:
            logger.error(f"Model load failed: {e}")
            self.model = None

    def detect(self, frame):
        if self.model is None:
            return []
        try:
            results = self.model(frame, conf=CONFIDENCE_THRESHOLD, iou=IOU_THRESHOLD, verbose=False)
            return results[0]
        except Exception as e:
            logger.error(f"Detection error: {e}")
            return []

    def get_violations(self, detections):
        violations = []
        try:
            boxes = detections.boxes.xyxy.cpu().numpy()
            classes = detections.boxes.cls.cpu().numpy()
            names = self.model.names

            people = [boxes[i] for i, c in enumerate(classes) if names[int(c)] == "person"]
            helmets = [boxes[i] for i, c in enumerate(classes) if names[int(c)] == "helmet"]
            vests = [boxes[i] for i, c in enumerate(classes) if names[int(c)] == "vest"]

            for person_box in people:
                helmet_found = any(self._iou(person_box, h) > IOU_THRESHOLD for h in helmets)
                vest_found = any(self._iou(person_box, v) > IOU_THRESHOLD for v in vests)

                if not helmet_found:
                    violations.append({"type": "Helmet Missing", "box": person_box})
                if not vest_found:
                    violations.append({"type": "Vest Missing", "box": person_box})
        except Exception as e:
            logger.error(f"Violation detection error: {e}")

        return violations

    def _iou(self, box1, box2):
        x1_min, y1_min, x1_max, y1_max = map(int, box1)
        x2_min, y2_min, x2_max, y2_max = map(int, box2)

        inter_x_min = max(x1_min, x2_min)
        inter_y_min = max(y1_min, y2_min)
        inter_x_max = min(x1_max, x2_max)
        inter_y_max = min(y1_max, y2_max)

        inter_area = max(0, inter_x_max - inter_x_min) * max(0, inter_y_max - inter_y_min)
        box1_area = (x1_max - x1_min) * (y1_max - y1_min)
        box2_area = (x2_max - x2_min) * (y2_max - y2_min)
        union_area = box1_area + box2_area - inter_area

        return inter_area / union_area if union_area > 0 else 0

    def draw_boxes(self, frame, violations):
        for violation in violations:
            x1, y1, x2, y2 = map(int, violation["box"])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
            cv2.putText(frame, violation["type"], (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        return frame

detector = SafetyDetector()
