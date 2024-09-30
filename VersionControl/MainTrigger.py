import requests
import schedule
import time
from Trigger.source import main as trigger_main
from DetectComponent.detection import CombinedDetector
from Components.HC_TWO import HcTwoLogic
from Components.HC_ONE import HcOneLogic
from Components.PISTON import PistonLogic

class ImageCaptureAndDetectWorkflow:
    def __init__(self, images_folder="images"):
        self.capture_object = trigger_main.PeriodicImageCapture(images_folder)
        self.detector = CombinedDetector(f"{images_folder}/current.jpg")
        self.hc_one_detected = False
        self.hc_two_detected = False
        self.piston_detected = False

    def run_workflow(self):
        print("Starting workflow")
        image_path = self.capture_object.capture_and_save_frame()
        print("Image captured at:", image_path)
        
        if not image_path:
            print("Failed to capture image")
            return False

        self.detector.image_path = image_path
        detection_result = self.detector.DetectComponents()
        print("Component detected:", detection_result[0])
        if detection_result[1] == True:
            url = "http://localhost:3004/uploadComp/"+detection_result[0]
            try:
                response = requests.post(url, files={'result':detection_result[0]})
                response.raise_for_status()
                print(f"Successfully uploaded {detection_result[0]} to the server.")
            except requests.exceptions.RequestException as e:
                print(f"Failed to upload {detection_result[0]}. Error: {e}")

        if detection_result[0] == 'HC_ONE' and not self.hc_one_detected:
            print("inside hc_one ")
            self.process_hc_one(image_path)
            self.hc_one_detected = True
        elif detection_result[0] == 'HC_TWO' and not self.hc_two_detected:
            self.process_hc_two(image_path)
            self.hc_two_detected = True
        elif detection_result[0] == 'PISTON' and not self.piston_detected:
            self.process_piston(image_path)
            self.piston_detected = True
        else:
            print(f"Component {detection_result[0]} already detected or unknown.")

        if self.hc_one_detected and self.hc_two_detected and self.piston_detected:
            print("All components have been detected. Workflow complete.")
            return True
        return False

    def process_hc_one(self, image_path):
        SEQ1 = False
        SEQ2 = False
        SEQ3 = False
        
        print("Processing HC_ONE")
        blue_obj = HcOneLogic.BlueWasherDetect(image_path)
        blue_result = blue_obj.combined_result()
        print("Blue washer detection result:", blue_result)
        if blue_result:
            SEQ1 = True
            url = "http://localhost:3004/uploadSeq/hce1blue"
            try:
                response = requests.post(url, files={'result':SEQ1})
                response.raise_for_status()
                print(f"Successfully uploaded {SEQ1} to the server.")
            except requests.exceptions.RequestException as e:
                print(f"Failed to upload {SEQ1}. Error: {e}")
        
        yellow_obj = HcOneLogic.YellowWasherDetect(image_path)
        yellow_result = yellow_obj.detect_washer()
        print("Yellow washer detection result:", yellow_result)
        if yellow_result:
            SEQ2 = True
            url = "http://localhost:3004/uploadSeq/hce1yellow"
            try:
                response = requests.post(url, files={'result':SEQ2})
                response.raise_for_status()
                print(f"Successfully uploaded {SEQ2} to the server.")
            except requests.exceptions.RequestException as e:
                print(f"Failed to upload {SEQ2}. Error: {e}")
        
        blackwhite_obj = HcOneLogic.blackWhiteDetect(image_path)
        blackwhite_result = blackwhite_obj.BlackWhiteCheck()
        print("Black and white detection result:", blackwhite_result)
        if blackwhite_result == 'correct':
            SEQ3 = True
            url = "http://localhost:3004/uploadSeq/hce1bandw"
            try:
                response = requests.post(url, files={'result':SEQ3})
                response.raise_for_status()
                print(f"Successfully uploaded {SEQ3} to the server.")
            except requests.exceptions.RequestException as e:
                print(f"Failed to upload {SEQ3}. Error: {e}")
        print("blue seal detection flags",SEQ1 ,SEQ2 , SEQ3)
        
        if SEQ1 and SEQ2 and SEQ3:
            print("uplaoding the hc_one final image")
            url = "http://localhost:3004/uploadFinalimg/hce1finalimg"
            f = open("images/current.jpg", 'rb')
            files = {"file": ("images/current.jpg", f)}
            resp = requests.post("http://localhost:3004/uploadFinalimg/hce1finalimg", files=files)
            print (resp.text)
        
            
            

    def process_hc_two(self, image_path):
        SEQ1 = False
        SEQ2 = False
        SEQ3 = False
        print("Processing HC_TWO")
        blue_obj = HcTwoLogic.BlueWasherDetect(image_path)
        blue_result = blue_obj.combined_result()
        print("Blue washer detection result:", blue_result)
        if blue_result:
            SEQ1 = True
            url = "http://localhost:3004/uploadSeq/hce2blue"
            try:
                response = requests.post(url, files={'result':SEQ1})
                response.raise_for_status()
                print(f"Successfully uploaded {SEQ1} to the server.")
            except requests.exceptions.RequestException as e:
                print(f"Failed to upload {SEQ1}. Error: {e}")
        
        yellow_obj = HcOneLogic.YellowWasherDetect(image_path)
        yellow_result = yellow_obj.detect_washer()
        print("Yellow washer detection result:", yellow_result)
        if yellow_result:
            SEQ2 = True
            url = "http://localhost:3004/uploadSeq/hce2yellow"
            try:
                response = requests.post(url, files={'result':SEQ2})
                response.raise_for_status()
                print(f"Successfully uploaded {SEQ2} to the server.")
            except requests.exceptions.RequestException as e:
                print(f"Failed to upload {SEQ2}. Error: {e}")
        
        blackwhite_obj = HcOneLogic.blackWhiteDetect(image_path)
        blackwhite_result = blackwhite_obj.BlackWhiteCheck()
        print("Black and white detection result:", blackwhite_result)
        if blackwhite_result == 'correct':
            SEQ3 = True
            url = "http://localhost:3004/uploadSeq/hce2bandw"
            try:
                response = requests.post(url, files={'result':SEQ3})
                response.raise_for_status()
                print(f"Successfully uploaded {SEQ3} to the server.")
            except requests.exceptions.RequestException as e:
                print(f"Failed to upload {SEQ3}. Error: {e}")
                
        print("yellow seal detection",SEQ1 ,SEQ2 , SEQ3)
        
        if SEQ1 and SEQ2 and SEQ3:
            print("uplaoding the hc_two final image")
            url = "http://localhost:3004/uploadFinalimg/hce2finalimg"
            f = open("images/current.jpg", 'rb')
            files = {"file": ("images/current.jpg", f)}
            resp = requests.post("http://localhost:3004/uploadFinalimg/hce2finalimg", files=files)
            print (resp.text)
    def process_piston(self , image_path):
        SEQ1 = False
        pistonobj = PistonLogic.CheckPiston(image_path)
        result = pistonobj.is_process_complete()
        if result:
            SEQ1 = True
            url = "http://localhost:3004/uploadSeq/pistonb"
            try:
                response = requests.post(url, files={'result':SEQ1})
                response.raise_for_status()
                print(f"Successfully uploaded {SEQ1} to the server.")
            except requests.exceptions.RequestException as e:
                    print(f"Failed to upload {SEQ1}. Error: {e}")
        if SEQ1:
            print("uplaoding the piston final image")
            url = "http://localhost:3004/uploadFinalimg/pistonfinalimg"
            f = open("images/current.jpg", 'rb')
            files = {"file": ("images/current.jpg", f)}
            resp = requests.post("http://localhost:3004/uploadFinalimg/pistonfinalimg", files=files)
            

def fetch_api_response(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def check_api():
    api_url = "http://localhost:3004/jobStartflag"
    data = fetch_api_response(api_url)
    
    if data and data.get('Status') == True:
        print("Received True response. Starting image capture and detection.")
        workflow = ImageCaptureAndDetectWorkflow()
        while not workflow.run_workflow():
            time.sleep(2)  
        print("Workflow completed successfully.")
        return schedule.CancelJob
    else:
        print("API response not True or failed to fetch data. Skipping workflow.")

def main():
    schedule.every(2).seconds.do(check_api)

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("Process interrupted by user. Shutting down.")

if __name__ == "__main__":
    main()