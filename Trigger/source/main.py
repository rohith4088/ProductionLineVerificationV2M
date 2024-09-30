import cv2
import os
import time
from threading import Thread
from pathlib import Path
from DetectComponent.detection import CombinedDetector
import numpy as np
class PeriodicImageCapture:
    def __init__(self, images_folder="images", interval=1.5):
        self.cap = cv2.VideoCapture(0)
        self.images_folder = images_folder
        self.interval = interval
        self.is_running = False
        self.latest_image_path = None
        
        if not os.path.exists(self.images_folder):
            os.makedirs(self.images_folder)
        
    def capture_and_save_frame(self):
        ret, frame = self.cap.read()
        if ret:
            roi_x, roi_y, roi_w, roi_h = 100, 100, 500, 500   
            roi_frame = frame[roi_y:roi_y + roi_h, roi_x:roi_x + roi_w].copy()
            process_frame = self.PreProcess(roi_frame)
            filename = f"{self.images_folder}/current.jpg"
            cv2.imwrite(filename, roi_frame)
            self.latest_image_path = filename
            return filename
        return None
    def PreProcess(self,image):
        image_float = image.astype(np.float32) / 255.0
        alpha = 0.1 #light intensity
        image_float = cv2.multiply(image_float , alpha)
        beta = 10 #contrast
        image_float = cv2.multiply(image_float , beta)
        gamma = 2 #exposure
        image_float = cv2.pow(image_float , gamma)
        
        image_processed = np.clip(image_float * 255 , 0 , 255).astype(np.uint8)
        
        return image_processed
        

    def run(self):
        self.is_running = True
        while self.is_running:
            start_time = time.time()
            self.capture_and_save_frame()
            elapsed_time = time.time() - start_time
            sleep_time = max(0, self.interval - elapsed_time)
            time.sleep(sleep_time)

    def start(self):
        self.thread = Thread(target=self.run)
        self.thread.start()

    def stop(self):
        self.is_running = False
        if hasattr(self, 'thread'):
            self.thread.join()
        self.cap.release()

    def get_latest_image_path(self):
        return self.latest_image_path

