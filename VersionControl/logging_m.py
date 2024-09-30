import requests
import schedule
import time
import logging
from datetime import datetime
import shutil
from Trigger.source import main as trigger_main
from DetectComponent.detection import CombinedDetector
from Components.HC_TWO import HcTwoLogic
from Components.HC_ONE import HcOneLogic
from Components.PISTON import PistonLogic
import Jetson.GPIO as GPIO

buzzer=15


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ImageCaptureAndDetectWorkflow:
    def __init__(self, images_folder="images", max_retries=10):
        self.capture_object = trigger_main.PeriodicImageCapture(images_folder)
        self.detector = CombinedDetector(f"{images_folder}/current.jpg")
        self.hc_one_detected = False
        self.hc_two_detected = False
        self.piston_detected = False
        self.max_retries = max_retries
        self.buzzer_pin = 15
        self.setup_gpio()
    
    def setup_gpio(self):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.buzzer_pin, GPIO.OUT, initial=GPIO.LOW)

    def teardown_gpio(self):
        GPIO.cleanup(self.buzzer_pin)

    def buzz(self, duration_ms=100):
        GPIO.output(self.buzzer_pin, GPIO.HIGH)
        time.sleep(duration_ms / 1000)
        GPIO.output(self.buzzer_pin, GPIO.LOW)

    def run_workflow(self):
        logger.info("Starting workflow")
        image_path = self.capture_object.capture_and_save_frame()
        logger.info(f"Image captured at: {image_path}")
        
        if not image_path:
            logger.error("Failed to capture image")
            return False

        self.detector.image_path = image_path
        detection_result = self.detector.DetectComponents()
        logger.info(f"Component detected: {detection_result[0]}")
#        if detection_result[1]:
#            url = f"http://localhost:3004/uploadComp/{detection_result[0]}"
#            try:
#                response = requests.post(url, files={'result': detection_result[0]})
#                response.raise_for_status()
#                logger.info(f"Successfully uploaded {detection_result[0]} to the server.")
#            except requests.exceptions.RequestException as e:
#                logger.error(f"Failed to upload {detection_result[0]}. Error: {e}")
                
        if detection_result[1]:
            if self.hc_one_detected == False:
                logger.info("Processing HC_ONE")
                url = f"http://localhost:3004/uploadComp/HC_ONE"
                try:
                    response = requests.post(url, files={'result': 'HC_ONE'})
                    response.raise_for_status()
                    logger.info(f"Successfully uploaded HC_ONE to the server.")
                except requests.exceptions.RequestException as e:
                    logger.error(f"Failed to upload HC_ONE. Error: {e}")
                self.process_hc_one(image_path)
                self.hc_one_detected = True
            elif self.piston_detected == False:
                logger.info("Processing Piston")
                url = f"http://localhost:3004/uploadComp/PISTON"
                try:
                    response = requests.post(url, files={'result': 'PISTON'})
                    response.raise_for_status()
                    logger.info(f"Successfully uploaded PISTON to the server.")
                except requests.exceptions.RequestException as e:
                    logger.error(f"Failed to upload PISTON. Error: {e}")
                self.process_hc_one(image_path)
                self.piston_detected = True
                
            elif self.hc_two_detected == False:
                logger.info("Processing HC_TWO")
                url = f"http://localhost:3004/uploadComp/HC_TWO"
                try:
                    response = requests.post(url, files={'result': 'HC_TWO'})
                    response.raise_for_status()
                    logger.info(f"Successfully uploaded 'HC_TWO to the server.")
                except requests.exceptions.RequestException as e:
                    logger.error(f"Failed to upload HC_TWO. Error: {e}")
                self.process_hc_two(image_path)
                self.hc_two_detected = True
                    
        # if detection_result[0] == 'HC_ONE' and not self.hc_one_detected:
        #     logger.info("Processing HC_ONE")
        #     self.process_hc_one(image_path)
        #     self.hc_one_detected = True
        # elif detection_result[0] == 'HC_TWO' and not self.hc_two_detected:
        #     self.process_hc_two(image_path)
        #     self.hc_two_detected = True
        # elif detection_result[0] == 'PISTON' and not self.piston_detected:
        #     self.process_piston(image_path)
        #     self.piston_detected = True
        else:
            logger.info(f"Component {detection_result[0]} already detected or unknown.")

        if self.hc_one_detected and self.hc_two_detected and self.piston_detected:
            logger.info("All components have been detected. Workflow complete.")
            self.hc_one_detected = False
            self.piston_detected = False
            self.hc_two_detected = False
            time.sleep(10)
            return True
        return False

    def process_hc_one(self, image_path):
        logger.info("Processing HC_ONE")
        
        for _ in range(self.max_retries):
            blue_obj = HcOneLogic.BlueWasherDetect(image_path)
            blue_result = blue_obj.combined_result()
            logger.info(f"Blue washer detection result: {blue_result}")
            if not blue_result: #code for buzz
                self.buzz()
            if blue_result:
                #folder = "research"
                #timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                self.upload_sequence_result("hce1blue", True)
                #new_path = f"{folder}/hcone_{timestamp}_blueseal.jpg"
                #shutil.copy2(image_path, new_path)
                break
            else:
                logger.warning("Blue washer not detected. Retrying...")
                time.sleep(1)
                image_path = self.capture_object.capture_and_save_frame()
        else:
            logger.error("Max retries reached for blue washer detection in HC_ONE")
            self.upload_sequence_result("hce1blue", True)
            return
            

        for _ in range(self.max_retries):
            yellow_obj = HcOneLogic.YellowWasherDetect(image_path)
            yellow_result = yellow_obj.detect_washer()
            logger.info(f"Yellow washer detection result: {yellow_result}")
            if not yellow_result:
                self.buzz()
            if yellow_result:
                #folder = "research"
                #timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") 
                self.upload_sequence_result("hce1yellow", True)
                #new_path = f"{folder}/hcone_{timestamp}_yellowseal.jpg"
                #shutil.copy2(image_path, new_path)
                break
            else:
                logger.warning("Yellow washer not detected. Retrying...")
                time.sleep(1)
                image_path = self.capture_object.capture_and_save_frame()
        else:
            logger.error("Max retries reached for yellow washer detection in HC_ONE")
            self.upload_sequence_result("hce1yellow", True)
            return

        for _ in range(self.max_retries):
            blackwhite_obj = HcOneLogic.blackWhiteDetect(image_path)
            blackwhite_result = blackwhite_obj.BlackWhiteCheck()
            logger.info(f"Black and white detection result: {blackwhite_result}")
            if blackwhite_result == 'correct':
                self.buzz()
                #folder = "research"
                #timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                self.upload_sequence_result("hce1bandw", True)
                #new_path = f"{folder}/hcone_{timestamp}_blackwhiteseal.jpg"
                #shutil.copy2(image_path, new_path)
                break
            else:
                logger.warning("Black and white not correct. Retrying...")
                time.sleep(1)
                image_path = self.capture_object.capture_and_save_frame()
        else:
            logger.error("Max retries reached for black and white detection in HC_ONE")
            self.upload_sequence_result("hce1bandw", True)
#            time.sleep(7)
#            self.upload_final_image("hce1finalimage",image_path)
            #return
            
        
        logger.info("All HC_ONE checks completed successfully")
        time.sleep(7)
        self.upload_final_image("hce1finalimg", image_path)

    def process_hc_two(self, image_path):
        logger.info("Processing HC_TWO")
        
        for _ in range(self.max_retries):
            blue_obj = HcTwoLogic.BlueWasherDetect(image_path)
            blue_result = blue_obj.combined_result()
            logger.info(f"Blue washer detection result: {blue_result}")
            if blue_result:
                #folder = "research"
                #timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                self.upload_sequence_result("hce2blue", True)
                #new_path = f"{folder}/hctwo_{timestamp}_blueseal.jpg"
                #shutil.copy2(image_path, new_path) 
                break
            else:
                logger.warning("Blue washer not detected. Retrying...")
                time.sleep(1)
                image_path = self.capture_object.capture_and_save_frame()
        else:
            logger.error("Max retries reached for blue washer detection in HC_TWO")
            self.upload_sequence_result("hce2blue", True)
            return

        for _ in range(self.max_retries):
            yellow_obj = HcTwoLogic.YellowWasherDetect(image_path)
            yellow_result = yellow_obj.detect_washer()
            logger.info(f"Yellow washer detection result: {yellow_result}")
            if yellow_result:
                #folder = "research"
                #timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                self.upload_sequence_result("hce2yellow", True)
                #new_path = f"{folder}/hctwo_{timestamp}_yellowseal.jpg"
                #shutil.copy2(image_path, new_path)
                break
            else:
                logger.warning("Yellow washer not detected. Retrying...")
                time.sleep(1)
                image_path = self.capture_object.capture_and_save_frame()
        else:
            logger.error("Max retries reached for yellow washer detection in HC_TWO")
            self.upload_sequence_result("hce2yellow", True)
            return
                
        for _ in range(self.max_retries):
            blackwhite_obj = HcTwoLogic.blackWhiteDetect(image_path)
            blackwhite_result = blackwhite_obj.BlackWhiteCheck()
            logger.info(f"Black and white detection result: {blackwhite_result}")
            if blackwhite_result == 'correct':
                # folder = "research"
                # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                self.upload_sequence_result("hce2bandw", True)
                # new_path = f"{folder}/hctwo_{timestamp}_blackwhiteseal.jpg"
                # shutil.copy2(image_path, new_path) 
                break
            else:
                logger.warning("Black and white not correct. Retrying...")
                time.sleep(1)
                image_path = self.capture_object.capture_and_save_frame()
        else:
            logger.error("Max retries reached for black and white detection in HC_TWO")
            self.upload_sequence_result("hce2bandw", True)
            return
        
        logger.info("All HC_TWO checks completed successfully")
        time.sleep(7)
        self.upload_final_image("hce2finalimg", image_path)

    def process_piston(self, image_path):
        logger.info("Processing PISTON")
        
        for _ in range(self.max_retries):
            pistonobj = PistonLogic.CheckPiston(image_path)
            result = pistonobj.is_process_complete()
            if result:
                #folder = "research" commeneted for sotring images locally
                #timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") 
                self.upload_sequence_result("pistonb", True)
                #new_path = f"{folder}/piston_{timestamp}_cover.jpg"
                #shutil.copy2(image_path, new_path)   
                break
            else:
                logger.warning("Piston process not complete. Retrying...")
                time.sleep(1)
                image_path = self.capture_object.capture_and_save_frame()
        else:
            logger.error("Max retries reached for piston process")
            self.upload_sequence_result("pistonb", True)
            return
        
        logger.info("PISTON check completed successfully")
        time.sleep(7)
        self.upload_final_image("pistonfinalimg", image_path)

    def upload_sequence_result(self, endpoint, result):
        url = f"http://localhost:3004/uploadSeq/{endpoint}"
        try:
            response = requests.post(url, files={'result': str(result)})
            response.raise_for_status()
            logger.info(f"Successfully uploaded {result} to {endpoint}.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to upload {result} to {endpoint}. Error: {e}")

    def upload_final_image(self, endpoint, image_path):
        url = f"http://localhost:3004/uploadFinalimg/{endpoint}"
        f = open("/home/wipro/wipro/ProductionLineVerification-main/images/current.jpg", 'rb')
        files = {"file": ("/home/wipro/wipro/ProductionLineVerification-main/images/current.jpg", f)}
        resp = requests.post(url , files = files)
        print (resp.text)

def fetch_api_response(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"An error occurred: {e}")
        return None

def check_api():
    api_url = "http://localhost:3004/jobStartflag"
    data = fetch_api_response(api_url)
    if data and data.get('flag') == True:
        logger.info("Received True response. Starting image capture and detection.")
        workflow = ImageCaptureAndDetectWorkflow()
        while not workflow.run_workflow():
            time.sleep(2)
        logger.info("Workflow completed successfully.")
    else:
        logger.info("API response not True or failed to fetch data. Skipping workflow.")

def main():
    try:
        while True:
            check_api()
            time.sleep(2)  # Wait for 2 seconds before checking the API again
    except KeyboardInterrupt:
        logger.info("Process interrupted by user. Shutting down.")

if __name__ == "__main__":
    main()