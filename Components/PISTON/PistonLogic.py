import cv2
from ultralytics import YOLO
import numpy as np
import requests
import logging
import time
logger = logging.getLogger(__name__)

class CheckPiston:
    def __init__(self, image_path):
        self.image_path = image_path
        self.model = YOLO("models/piston_final.pt")
        self.final_model = YOLO("models/seal_piston_one_26-09.pt")
        self.final_model2 = YOLO("models/Piston_Complete_Process.pt")
        self.final_model3 = YOLO("models/piston_final.pt")
        self.piston_seal_detected = False
        self.completed = False
        self.piston = False
    def upload_sequence_result(self, endpoint, result):
        url = f"http://localhost:3004/uploadSeq/{endpoint}"
        try:
            response = requests.post(url, files={'result': str(result)})
            response.raise_for_status()
            logger.info(f"Successfully uploaded {result} to {endpoint}.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to upload {result} to {endpoint}. Error: {e}")
    def is_process_complete(self,piston,piston_seal_detected1,completed1):
        print(piston_seal_detected1,completed1)
        self.piston_seal_detected = piston_seal_detected1
        self.completed = completed1
        self.piston = piston
        image = cv2.imread(self.image_path)
        if image is None:
            logger.error(f"Failed to load image from {self.image_path}")
            return False, self.piston_seal_detected, self.completed
        if not self.piston:
            final_results = self.final_model3.predict(source=image, conf=0.1, show=False)
            for final_result in final_results:
                for box, cls, conf in zip(final_result.boxes.xyxy, final_result.boxes.cls, final_result.boxes.conf):
                    class_name = self.final_model3.names[int(cls)]
                    confidence = float(conf)
                    print(confidence)
                    if class_name == "PISTON" and confidence >= 0.97:
                        self.piston = True
                        #self.upload_sequence_result("pistonb", True)
                        
                        break
                if self.piston:
                    break
        if not self.piston_seal_detected and self.piston:
            final_results = self.final_model.predict(source=image, conf=0.1, show=False)
            for final_result in final_results:
                for box, cls, conf in zip(final_result.boxes.xyxy, final_result.boxes.cls, final_result.boxes.conf):
                    class_name = self.final_model.names[int(cls)]
                    confidence = float(conf)
                    print(confidence)
                    if class_name == "seal-visible" and confidence >= 0.5:
                        self.piston_seal_detected = True
                        self.upload_sequence_result("pistonb", True)
                        
                        break
                if self.piston_seal_detected:
                    break
        if self.piston_seal_detected and self.piston and not self.completed:
            final_results = self.final_model2.predict(source=image, conf=0.1, show=False)
            for final_result in final_results:
                for box, cls, conf in zip(final_result.boxes.xyxy, final_result.boxes.cls, final_result.boxes.conf):
                    class_name = self.final_model2.names[int(cls)]
                    confidence = float(conf)
                    print(confidence)
                    if class_name == "COMPLETE" and confidence >= 0.7:
                        self.completed = True
                        self.upload_sequence_result("pistoncover", True)
                        logger.info("Process is COMPLETE!")
                        break
                if self.completed:
                    break
        return  self.piston,self.piston_seal_detected, self.completed
