import cv2
from ultralytics import YOLO
import numpy as np



class CombinedDetector():
    def __init__(self, image_path):
        self.image_path = image_path
    
    def DetectComponents(self):
        img = cv2.imread(self.image_path)
        if img is None:
            print(f"Failed to load image from {self.image_path}. Please check the file path.")
            return "NONE", False

        octogon_model = YOLO('models/HC_TWO.pt')
        piston_model = YOLO('models/PISTON_UPDATED.pt')
        hc_one_model = YOLO('models/HC_ONE_old.pt')
    
        results = {
            'hc_two': octogon_model(img),
            'piston': piston_model(img),
            'hc_one': hc_one_model(img)
        }
        octogon_result = self.ProcessOctogon(results['hc_two'])
        piston_result = self.ProcessPiston(results['piston'])
        hc_one_result = self.ProcessHCOne(results['hc_one'])
    
        max_confidence = max(octogon_result[0], piston_result[0], hc_one_result[0]) 
        print("ocotogan confidence", octogon_result[0])
        print("piston confidence", piston_result[0])
        print("hc one confidence", hc_one_result[0])
    
        if max_confidence == 0:
            return "NONE", False
        components = [('HC_TWO', octogon_result), ('PISTON', piston_result), ('HC_ONE', hc_one_result)]
        best_component = max(components, key=lambda x: x[1][0])[0]
        if max_confidence > 0.1:
            return best_component, True
        else:
            return "NONE", False

    @staticmethod
    def ProcessOctogon(result):
        if not result or len(result) == 0:
            return [0, False]
        
        boxes = result[0].boxes
        if not boxes:
            return [0, False]
        
        box = boxes[0]
        class_id = int(box.cls[0])
        confidence = float(box.conf[0])
        
        return [confidence, True]

    @staticmethod
    def ProcessPiston(result):
        if not result or len(result) == 0:
            return [0, False]
        
        boxes = result[0].boxes
        if not boxes:
            return [0, False]
        
        box = boxes[0]
        class_id = int(box.cls[0])
        confidence = float(box.conf[0])
        
        return [confidence, True]

    @staticmethod
    def ProcessHCOne(result):
        if not result or len(result) == 0:
            return [0, False]
        
        boxes = result[0].boxes
        if not boxes:
            return [0, False]
        
        box = boxes[0]
        class_id = int(box.cls[0])
        confidence = float(box.conf[0])
        
        return [confidence, True]

# detector = CombinedDetector("images/current.jpg")
# result = detector.DetectComponents()
# print(result)
