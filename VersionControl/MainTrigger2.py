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
        print("Processing HC_ONE")
        while True:
            blue_obj = HcOneLogic.BlueWasherDetect(image_path)
            blue_result = blue_obj.combined_result()
            print("Blue washer detection result:", blue_result)
            if blue_result:
                self.upload_sequence_result("hce1blue", True)
                break
            else:
                print("Blue washer not detected. Retrying...")
                time.sleep(1)  # Wait for 2 seconds before retrying
                image_path = self.capture_object.capture_and_save_frame()
        

        while True:
            yellow_obj = HcOneLogic.YellowWasherDetect(image_path)
            yellow_result = yellow_obj.detect_washer()
            print("Yellow washer detection result:", yellow_result)
            if yellow_result:
                self.upload_sequence_result("hce1yellow", True)
                break
            else:
                print("Yellow washer not detected. Retrying...")
                time.sleep(1)
                image_path = self.capture_object.capture_and_save_frame()
        

        while True:
            blackwhite_obj = HcOneLogic.blackWhiteDetect(image_path)
            blackwhite_result = blackwhite_obj.BlackWhiteCheck()
            print("Black and white detection result:", blackwhite_result)
            if blackwhite_result == 'correct':
                self.upload_sequence_result("hce1bandw", True)
                break
            else:
                print("Black and white not correct. Retrying...")
                time.sleep(1)
                image_path = self.capture_object.capture_and_save_frame()
        
        print("All HC_ONE checks completed successfully")
        self.upload_final_image("hce1finalimg", image_path)

    def process_hc_two(self, image_path):
        print("Processing HC_TWO")
        
        while True:
            blue_obj = HcTwoLogic.BlueWasherDetect(image_path)
            blue_result = blue_obj.combined_result()
            print("Blue washer detection result:", blue_result)
            if blue_result:
                self.upload_sequence_result("hce2blue", True)
                break
            else:
                print("Blue washer not detected. Retrying...")
                time.sleep(1)
                image_path = self.capture_object.capture_and_save_frame()

        while True:
            yellow_obj = HcOneLogic.YellowWasherDetect(image_path)
            yellow_result = yellow_obj.detect_washer()
            print("Yellow washer detection result:", yellow_result)
            if yellow_result:
                self.upload_sequence_result("hce2yellow", True)
                break
            else:
                print("Yellow washer not detected. Retrying...")
                time.sleep(1)
                image_path = self.capture_object.capture_and_save_frame()
                
        while True:
            blackwhite_obj = HcOneLogic.blackWhiteDetect(image_path)
            blackwhite_result = blackwhite_obj.BlackWhiteCheck()
            print("Black and white detection result:", blackwhite_result)
            if blackwhite_result == 'correct':
                self.upload_sequence_result("hce2bandw", True)
                break
            else:
                print("Black and white not correct. Retrying...")
                time.sleep(1)
                image_path = self.capture_object.capture_and_save_frame()
        
        print("All HC_TWO checks completed successfully")
        self.upload_final_image("hce2finalimg", image_path)

    def process_piston(self, image_path):
        print("Processing PISTON")
        
        while True:
            pistonobj = PistonLogic.CheckPiston(image_path)
            result = pistonobj.is_process_complete()
            if result:
                self.upload_sequence_result("pistonb", True)
                break
            else:
                print("Piston process not complete. Retrying...")
                time.sleep(1)
                image_path = self.capture_object.capture_and_save_frame()
        
        print("PISTON check completed successfully")
        self.upload_final_image("pistonfinalimg", image_path)

    def upload_sequence_result(self, endpoint, result):
        url = f"http://localhost:3004/uploadSeq/{endpoint}"
        try:
            response = requests.post(url, files={'result': str(result)})
            response.raise_for_status()
            print(f"Successfully uploaded {result} to {endpoint}.")
        except requests.exceptions.RequestException as e:
            print(f"Failed to upload {result} to {endpoint}. Error: {e}")

    def upload_final_image(self, endpoint, image_path):
        url = f"http://localhost:3004/uploadFinalimg/{endpoint}"
        try:
            with open(image_path, 'rb') as f:
                files = {"file": (image_path, f)}
                response = requests.post(url, files=files)
                response.raise_for_status()
            print(f"Successfully uploaded final image to {endpoint}.")
        except requests.exceptions.RequestException as e:
            print(f"Failed to upload final image to {endpoint}. Error: {e}")

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
    
    if data and data.get('flag') == True:
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
    