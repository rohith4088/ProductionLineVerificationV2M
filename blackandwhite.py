import cv2
from ultralytics import YOLO

class blackWhiteDetect:
    def __init__(self, image_path):
        self.image_path = image_path
    
    def BlackWhiteCheck(self):
        """Checks black and white using a pre-trained YOLO model."""
        model = YOLO("models/black_and_white_FOR_HC_TWO.pt")
        img = cv2.imread(self.image_path)
        if img is None:
            print(f"Failed to load image from {self.image_path}. Please check the file path.")
            return False
        
        results = model(img)
        if results and len(results) > 0:
            result = results[0]
            if len(result.boxes) > 0:
                box = result.boxes[0]
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                print(confidence)
                orientation_labels = {0: 'correct', 1: 'wrong'}
                orientation_label = orientation_labels.get(class_id, 'Unknown')
                
                print(f"Washer orientation: {orientation_label} (Confidence: {confidence:.2f})")
                if confidence > 0.05:
                    return True
            else:
                return False
        else:
            return False

# Usage
bwo = blackWhiteDetect("images/current.jpg")
result = bwo.BlackWhiteCheck()
print(result)
