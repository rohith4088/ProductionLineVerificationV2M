import cv2
import numpy as np

class HcOneInner():
    def __init__(self, image_path):
        self.image_path = image_path
        self.img = cv2.imread(self.image_path)
    def DetectInner(self):
        lower_black = np.array([0, 0, 0])
        upper_black = np.array([180, 255, 50])
        #frame = self.image_path
        #hsv_frame = cv2.cvtColor(self.img, cv2.COLOR_BGR2HSV)
        black_mask = cv2.inRange(self.img, lower_black, upper_black)

        kernel = np.ones((3, 3), np.uint8)
        black_mask = cv2.morphologyEx(black_mask, cv2.MORPH_CLOSE, kernel)
        black_mask = cv2.morphologyEx(black_mask, cv2.MORPH_OPEN, kernel)

        height, width = black_mask.shape
        black_mask[0:int(height * 0.1), :] = 0
        black_mask[int(height * 0.9):, :] = 0
        gray_frame = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)
        _, silver_mask = cv2.threshold(gray_frame, 200, 255, cv2.THRESH_BINARY)
        black_mask = cv2.bitwise_and(black_mask, cv2.bitwise_not(silver_mask))
        cv2.imwrite("mainblackmask.jpg",black_mask)
        circles = cv2.HoughCircles(black_mask, cv2.HOUGH_GRADIENT, dp=1, minDist=2, param1=50, param2=30, minRadius=5, maxRadius=350)
    
        if circles is not None:
            circles = np.uint16(np.around(circles))
            for i in circles[0, :]:
                cv2.circle(self.img, (i[0], i[1]), i[2], (0, 255, 0), 2)
                cv2.circle(self.img, (i[0], i[1]), 2, (0, 0, 255), 3)
            cv2.imwrite("circle_hconeinner.jpg" , self.img)
            return True
        else:
            return False
            
            
inner_obj = HcOneInner("images/current.jpg")
res = inner_obj.DetectInner()
print(res)
