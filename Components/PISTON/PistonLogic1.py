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
        self.final_model = YOLO("models/Piston_Complete_Process.pt")
        self.bearing_detected = False
        self.piston_seal_detected = False
        self.completed = False

    def upload_sequence_result(self, endpoint, result):
        url = f"http://localhost:3004/uploadSeq/{endpoint}"
        try:
            response = requests.post(url, files={'result': str(result)})
            response.raise_for_status()
            logger.info(f"Successfully uploaded {result} to {endpoint}.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to upload {result} to {endpoint}. Error: {e}")

    def is_process_complete(self,bearing_detected1,piston_seal_detected1,completed1):
        print(bearing_detected1,piston_seal_detected1,completed1)
        self.bearing_detected = bearing_detected1
        self.piston_seal_detected = piston_seal_detected1
        self.completed = completed1
        image = cv2.imread(self.image_path)
        if image is None:
            logger.error(f"Failed to load image from {self.image_path}")
            return False, self.bearing_detected, self.piston_seal_detected, self.completed

        hsv_frame = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        lower_black = np.array([0, 0, 0])
        upper_black = np.array([180, 255, 50])
        black_mask = cv2.inRange(hsv_frame, lower_black, upper_black)
        kernel = np.ones((5, 5), np.uint8)
        black_mask = cv2.morphologyEx(black_mask, cv2.MORPH_CLOSE, kernel)
        black_mask = cv2.morphologyEx(black_mask, cv2.MORPH_OPEN, kernel)

        height, width = black_mask.shape
        black_mask[0:int(height * 0.1), :] = 0
        black_mask[int(height * 0.9):, :] = 0

        gray_frame = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, silver_mask = cv2.threshold(gray_frame, 200, 255, cv2.THRESH_BINARY)
        black_mask = cv2.bitwise_and(black_mask, cv2.bitwise_not(silver_mask))

        # Step 1: Detect bearing
        if not self.bearing_detected:
            circles = cv2.HoughCircles(black_mask, cv2.HOUGH_GRADIENT, dp=1.2, minDist=50,
                                       param1=50, param2=30, minRadius=10, maxRadius=100)
            if circles is not None:
                circles = np.round(circles[0, :]).astype("int")
                for (x, y, r) in circles:
                    if r >= 60:
                        logger.info(f"Bearing detected - Center: ({x}, {y}), Radius: {r}")
                        self.bearing_detected = True
                        self.upload_sequence_result("pistonb", True)
                        break

        # Step 2: Detect piston seal
        if self.bearing_detected and not self.piston_seal_detected:
            #time.sleep(2.2)
            circles = cv2.HoughCircles(black_mask, cv2.HOUGH_GRADIENT, dp=1.2, minDist=50,
                                       param1=50, param2=30, minRadius=12, maxRadius=200)
            if circles is not None:
                circles = np.round(circles[0, :]).astype("int")
                for (x, y, r) in circles:
                    if 40 <= r < 60:
                        logger.info(f"Piston seal detected - Center: ({x}, {y}), Radius: {r}")
                        self.piston_seal_detected = True
                        self.upload_sequence_result("pistonbrng", True)
                        break

        # Step 3: Check if process is complete
        if self.bearing_detected and self.piston_seal_detected and not self.completed:
            final_results = self.final_model.predict(source=image, conf=0.1, show=False)
            for final_result in final_results:
                for box, cls, conf in zip(final_result.boxes.xyxy, final_result.boxes.cls, final_result.boxes.conf):
                    class_name = self.final_model.names[int(cls)]
                    confidence = float(conf)
                    if class_name == "COMPLETE" and confidence >= 0.8:
                        self.completed = True
                        self.upload_sequence_result("pistoncover", True)
                        logger.info("Process is COMPLETE!")
                        break
                if self.completed:
                    break

        # Return True if all steps are completed, along with individual step results
        #all_completed = self.bearing_detected and self.piston_seal_detected and self.completed
        return  self.bearing_detected, self.piston_seal_detected, self.completed
