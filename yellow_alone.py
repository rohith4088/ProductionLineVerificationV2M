import cv2
import numpy as np

class YellowWasherDetect():
    def __init__(self , image_path):
        self.image_path = image_path
    def detect_washer(self, lower=np.array([18, 50, 80]), upper=np.array([30, 255, 255])):
        frame = cv2.imread(self.image_path)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, lower, upper)
        temp_mask = mask
        cv2.imwrite("yellow_mask.jpg" , temp_mask)
        circles = cv2.HoughCircles(mask, cv2.HOUGH_GRADIENT, dp=1, minDist=15, param1=50, param2=30, minRadius=30, maxRadius=250)
        if circles is not None:
        
            circles = np.uint16(np.around(circles))
            for i in circles[0, :]:
                cv2.circle(frame, (i[0], i[1]), i[2], (0, 255, 0), 2)
                cv2.circle(frame, (i[0], i[1]), 2, (0, 0, 255), 3)
            temp_frame = frame
            cv2.imwrite("yellow1.jpg",temp_frame)
            print("image_written")
            return True#, circles[0]
            #print('TRUE')
        else:
            return False#, None
            #print("FALSE")
yb = YellowWasherDetect("images/current.jpg")
print(yb.detect_washer())

