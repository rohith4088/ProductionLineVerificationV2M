import cv2
import numpy as np

class BlueWasherDetect:
    def __init__(self, image_path):
        self.image_path = image_path

    def detect_washer(self, lower=np.array([94, 80, 2]), upper=np.array([130, 255, 255])):
        frame = cv2.imread(self.image_path)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, lower, upper)
        circles = cv2.HoughCircles(mask, cv2.HOUGH_GRADIENT, dp=1, minDist=15, param1=50, param2=30, minRadius=15, maxRadius=900)
    
        if circles is not None:
            circles = np.uint16(np.around(circles))
            for i in circles[0, :]:
                cv2.circle(frame, (i[0], i[1]), i[2], (0, 255, 0), 2)
                cv2.circle(frame, (i[0], i[1]), 2, (0, 0, 255), 3)
            return True
        else:
            return False

    def check_orientation(self):
        frame = cv2.imread(self.image_path)
        
        color_ranges = {
            'blue': (np.array([100, 150, 50]), np.array([140, 255, 255])),
        }
        
        #roi_x, roi_y, roi_w, roi_h = 100, 100, 260, 240
        #roi_frame = frame[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w].copy()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        lower_silver = 160
        upper_silver = 255
        silver_mask = cv2.inRange(gray, lower_silver, upper_silver)
        
        blue_mask = None
        for color_name, (lower, upper) in color_ranges.items():
            mask = cv2.inRange(hsv, lower, upper)
            if color_name == 'blue':
                blue_mask = mask

        def analyze_frame():
            if blue_mask is not None:
                contours, _ = cv2.findContours(blue_mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if len(contours) > 0:
                    largest_contour = max(contours, key=cv2.contourArea)
                    contour_mask = np.zeros_like(blue_mask)
                    cv2.drawContours(contour_mask, [largest_contour], -1, 255, thickness=cv2.FILLED)
                    inverted_contour_mask = cv2.bitwise_not(contour_mask)
                    gap_in_contour = cv2.bitwise_and(blue_mask, blue_mask, mask=inverted_contour_mask)
                    gap_count = cv2.countNonZero(gap_in_contour)
                    return gap_count <= 250
            return False
        
        def check_hidden_cover_two():
            blue_present = cv2.countNonZero(blue_mask) > 250 if blue_mask is not None else False
            silver_present = cv2.countNonZero(silver_mask) > 250
            return blue_present and silver_present
        
        frame_analysis_passed = analyze_frame()
        hidden_cover_passed = check_hidden_cover_two()
        
        return hidden_cover_passed and frame_analysis_passed

    def combined_result(self):
        washer_result = self.detect_washer()
        orientation_result = self.check_orientation()
        return washer_result , orientation_result



class YellowWasherDetect():
    def __init__(self , image_path):
        self.image_path = image_path
    def detect_washer(self, lower=np.array([10, 70, 60]), upper=np.array([30, 255, 255])):
        frame = cv2.imread(self.image_path)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, lower, upper)
        circles = cv2.HoughCircles(mask, cv2.HOUGH_GRADIENT, dp=1, minDist=15, param1=50, param2=30, minRadius=30, maxRadius=300)
        if circles is not None:
            circles = np.uint16(np.around(circles))
            for i in circles[0, :]:
                cv2.circle(frame, (i[0], i[1]), i[2], (0, 255, 0), 2)
                cv2.circle(frame, (i[0], i[1]), 2, (0, 0, 255), 3)
            return True#, circles[0]
            #print('TRUE')
        else:
            return False#, None
            #print("FALSE")
        

from ultralytics import YOLO

class blackWhiteDetect:
    def __init__(self, image_path):
        self.image_path = image_path
    
    def BlackWhiteCheck(self):
        """Checks black and white using a pre-trained YOLO model."""
        model = YOLO('models2/black_and_white.pt')
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
                return orientation_label == 'correct'
            else:
                return False
        else:
            return False
