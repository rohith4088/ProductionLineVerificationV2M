import requests
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
import time


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ImageCaptureAndDetectWorkflow:
    def __init__(self, images_folder="images", max_retries=1000):
        self.capture_object = trigger_main.PeriodicImageCapture(images_folder)
        self.detector = CombinedDetector(f"{images_folder}/current.jpg")
        self.max_retries = max_retries
        self.components = ['HC_ONE', 'PISTON', 'HC_TWO']
        self.current_component_index = 0
        self.detected_components = set()

    def run_workflow(self):
        logger.info("Starting workflow")
        #time.sleep(2)
        self.capture_object.start()
        time.sleep(1)
        component_detected, result = self.detector.DetectComponents()
        print(result)
        if result:
            logger.info(f"Component detected: {component_detected}. Proceeding with the fixed workflow.")
        else:
            logger.warning("No component detected. Skipping workflow.")
            self.capture_object.stop()
            return False
        
        for component in self.components:
            logger.info(f"Processing {component}")
            self.upload_component_name(component)
            
            image_path = self.capture_object.capture_and_save_frame()
            logger.info(f"Image captured at: {image_path}")
            
            if not image_path:
                logger.error("Failed to capture image")
                return False

            self.detector.image_path = image_path
            hcone_url = "http://localhost:3004/modelflag/hce1mname"
            hctwo_url = "http://localhost:3004/modelflag/hce2mname"
            piston_url = "http://localhost:3004/modelflag/pistonmname"
            def fetch_api_response_hcone(hcone_url):
                try:
                    response = requests.get(hcone_url)
                    response.raise_for_status()
                    return response.json()
                except requests.RequestException as e:
                    logger.error(f"An error occurred: {e}")
                    return None
            def fetch_api_response_hctwo(hctwo_url):
                try:
                    response = requests.get(hctwo_url)
                    response.raise_for_status()
                    return response.json()
                except requests.RequestException as e:
                    logger.error(f"An error occurred: {e}")
                    return None
            def fetch_api_response_piston(piston_url):
                try:
                    response = requests.get(piston_url)
                    response.raise_for_status()
                    return response.json()
                except requests.RequestException as e:
                    logger.error(f"An error occurred: {e}")
                    return None
            if component == 'HC_ONE':
                data = fetch_api_response_hcone(hcone_url)
                if data and data.get('flag') == True:
                    self.process_hc_one(image_path)
                else:
                    logger.info("the hc one name and make is not enetred")
                
            elif component == 'PISTON':
                #time.sleep(5)
                data = fetch_api_response_piston(piston_url)
                if data and data.get("flag") == True:
                    self.process_piston(image_path)
                else:
                    logger.info("piston make not entered ")
            elif component == 'HC_TWO':
                #time.sleep(5)
                data  = fetch_api_response_hctwo(hctwo_url)
                if data and data.get("flag") == True:
                    self.process_hc_two(image_path)
                else:
                    logger.info("hc two make not entered")
            
            self.detected_components.add(component)

        logger.info("All components have been processed. Workflow complete.")
        self.current_component_index = 0
        self.detected_components.clear()
        self.capture_object.stop()
        return True

    def upload_component_name(self, component):
        endpoint = ''
        if component == 'HC_ONE':
            endpoint = 'HC_ONE'
        elif component == 'PISTON':
            endpoint = 'PISTON'
        elif component == 'HC_TWO':
            endpoint = 'HC_TWO'
        
        url = f"http://localhost:3004/UploadComp/{endpoint}"
        try:
            response = requests.post(url, files={'result': 'true'})
            response.raise_for_status()
            logger.info(f"Successfully uploaded component name: {component} to {endpoint}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to upload component name: {component} to {endpoint}. Error: {e}")

    def process_hc_one(self, image_path):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(15, GPIO.OUT, initial=GPIO.LOW)
        #trig_pin = 15
        logger.info("Processing HC_ONE")

        # Blue washer detection
        for _ in range(self.max_retries):
            blue_obj = HcOneLogic.BlueWasherDetect(image_path)
            washer_result , orientation_result = blue_obj.combined_result()
            logger.info(f"Blue washer detection result: {washer_result , orientation_result}")
            # if orientation_result is False:
            #     GPIO.output(15, GPIO.HIGH)
            #     time.sleep(0.2)
            #     print("pulling low")
            #     GPIO.output(15, GPIO.LOW)
                
            if washer_result and orientation_result:
                GPIO.output(15, GPIO.HIGH)
                time.sleep(0.2)
                print("pulling low")
                GPIO.output(15, GPIO.LOW)
                time.sleep(0.2)
                GPIO.output(15, GPIO.HIGH)
                time.sleep(0.2)
                print("pulling low")
                GPIO.output(15, GPIO.LOW)
                self.upload_sequence_result("hce1blue", True)
                #time.sleep(1)
                
                break  # Exit the loop if blue washer is detected
            else:
                GPIO.output(15, GPIO.LOW)
                logger.warning("Blue washer not detected. Retrying...")
                time.sleep(1)
                image_path = self.capture_object.capture_and_save_frame()
        else:
            logger.error("Max retries reached for blue washer detection in HC_ONE")
            self.upload_sequence_result("hce1blue", True)  # Upload True and move on

        # Yellow washer detection
        for _ in range(self.max_retries):
            yellow_obj = HcOneLogic.YellowWasherDetect(image_path)
            yellow_result = yellow_obj.detect_washer()
            logger.info(f"Yellow washer detection result: {yellow_result}")
            if yellow_result:
                GPIO.output(15, GPIO.HIGH)
                time.sleep(0.2)
                print("pulling low")
                GPIO.output(15, GPIO.LOW)
                time.sleep(0.2)
                GPIO.output(15, GPIO.HIGH)
                time.sleep(0.2)
                print("pulling low")
                GPIO.output(15, GPIO.LOW)
                self.upload_sequence_result("hce1yellow", True)
                break  # Exit the loop if yellow washer is detected
            else:
                GPIO.output(15, GPIO.LOW)
                logger.warning("Yellow washer not detected. Retrying...")
                time.sleep(1)
                image_path = self.capture_object.capture_and_save_frame()
        else:
            logger.error("Max retries reached for yellow washer detection in HC_ONE")
            self.upload_sequence_result("hce1yellow", True)  # Upload True and move on

        # Black and white detection
        for _ in range(self.max_retries):
            blackwhite_obj = HcOneLogic.blackWhiteDetect(image_path)
            blackwhite_result = blackwhite_obj.BlackWhiteCheck()
            #logger.info("this is the result from black and white for hc_one",blackwhite_result)
            logger.info(f"Black and white detection result: {blackwhite_result}")
            
            # if blackwhite_result == "wrong":
            #     GPIO.output(15, GPIO.HIGH)
            #     time.sleep(2)
            #     print("pulling low wrong")
            #     GPIO.output(15, GPIO.LOW)
                
            if blackwhite_result  == 'correct':
                GPIO.output(15, GPIO.HIGH)
                time.sleep(0.2)
                print("pulling low")
                GPIO.output(15, GPIO.LOW)
                time.sleep(0.2)
                GPIO.output(15, GPIO.HIGH)
                time.sleep(0.2)
                print("pulling low")
                GPIO.output(15, GPIO.LOW)
                self.upload_sequence_result("hce1bandw", True)
                time.sleep(3)
                print("pausing for a second")
                break  # Exit the loop if black and white is correct
            else:
                logger.warning("Black and white not correct. Retrying...")
                #time.sleep(1)
                image_path = self.capture_object.capture_and_save_frame()
		    
        else:
            logger.error("Max retries reached for black and white detection in HC_ONE")
         
            self.upload_sequence_result("hce1bandw", True)  # Upload True and move on
        for _ in range(self.max_retries):
            print("inside inne rlogic")
            innerobj = HcOneLogic.HcOneInner(image_path)
            innerres = innerobj.DetectInner()
            print(innerres)
            if innerres:
                GPIO.output(15, GPIO.HIGH)
                time.sleep(0.2)
                print("pulling low")
                GPIO.output(15, GPIO.LOW)
                time.sleep(0.2)
                GPIO.output(15, GPIO.HIGH)
                time.sleep(0.2)
                print("pulling low")
                GPIO.output(15, GPIO.LOW)
                self.upload_sequence_result("hce1inner", True)
                break
            else:
                logger.warning("inner bearing not correct. Retrying...")
                time.sleep(1)
                image_path = self.capture_object.capture_and_save_frame()
        else:
            logger.error("Max retries reached for black and white detection in HC_ONE")
            self.upload_sequence_result("hce1inner", True)

        # All checks completed, upload the final image
        logger.info("All HC_ONE checks completed successfully")
        time.sleep(6)  # Final image delay
        image_path = self.capture_object.capture_and_save_frame()
        self.upload_final_image("hce1finalimg", image_path)
        time.sleep(6)

    def process_hc_two(self, image_path):
        logger.info("Processing HC_TWO")
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(15, GPIO.OUT, initial=GPIO.LOW)

        # Blue washer detection
        for _ in range(self.max_retries):
            blue_obj = HcTwoLogic.BlueWasherDetect(image_path)
            washer_result , orientation_result = blue_obj.combined_result()
            logger.info(f"Blue washer detection result: {washer_result , orientation_result}")
            # if orientation_result is False:
            #     GPIO.output(15, GPIO.HIGH)
            #     time.sleep(0.2)
            #     print("pulling low")
            #     GPIO.output(15, GPIO.LOW)
                
 
            if washer_result and orientation_result:
                GPIO.output(15, GPIO.HIGH)
                time.sleep(0.2)
                print("pulling low")
                GPIO.output(15, GPIO.LOW)
                time.sleep(0.2)
                GPIO.output(15, GPIO.HIGH)
                time.sleep(0.2)
                print("pulling low")
                GPIO.output(15, GPIO.LOW)
                self.upload_sequence_result("hce2blue", True)
                break  # Exit the loop if blue washer is detected
            else:
                logger.warning("Blue washer not detected. Retrying...")
                time.sleep(1)
                image_path = self.capture_object.capture_and_save_frame()
        else:
            logger.error("Max retries reached for blue washer detection in HC_TWO")
            self.upload_sequence_result("hce2blue", True)  # Upload True and move on

        # Yellow washer detection
        for _ in range(self.max_retries):
            yellow_obj = HcTwoLogic.YellowWasherDetect(image_path)
            yellow_result = yellow_obj.detect_washer()
            logger.info(f"Yellow washer detection result: {yellow_result}")
            if yellow_result:
                GPIO.output(15, GPIO.HIGH)
                time.sleep(0.2)
                print("pulling low")
                GPIO.output(15, GPIO.LOW)
                time.sleep(0.2)
                GPIO.output(15, GPIO.HIGH)
                time.sleep(0.2)
                print("pulling low")
                GPIO.output(15, GPIO.LOW)
                self.upload_sequence_result("hce2yellow", True)
                break  # Exit the loop if yellow washer is detected
            else:
                logger.warning("Yellow washer not detected. Retrying...")
                time.sleep(1)
                image_path = self.capture_object.capture_and_save_frame()
        else:
            logger.error("Max retries reached for yellow washer detection in HC_TWO")
            self.upload_sequence_result("hce2yellow", True)  # Upload True and move on

        # Black and white detection
        for _ in range(self.max_retries):
            blackwhite_obj = HcTwoLogic.blackWhiteDetect(image_path)
            blackwhite_result = blackwhite_obj.BlackWhiteCheck()
            #logger.info("this is the result from black and white for hc_two",blackwhite_result)
            logger.info(f"Black and white detection result: {blackwhite_result}")
            if blackwhite_result:
                GPIO.output(15, GPIO.HIGH)
                time.sleep(0.2)
                print("pulling low")
                GPIO.output(15, GPIO.LOW)
                time.sleep(0.2)
                GPIO.output(15, GPIO.HIGH)
                time.sleep(0.2)
                print("pulling low")
                GPIO.output(15, GPIO.LOW)
                self.upload_sequence_result("hce2bandw", True)
                break  # Exit the loop if black and white is correct
            else:
                logger.warning("Black and white not correct. Retrying...")
                #time.sleep(1)
                image_path = self.capture_object.capture_and_save_frame()
        else:
            logger.error("Max retries reached for black and white detection in HC_TWO")
            self.upload_sequence_result("hce2bandw", True)  # Upload True and move on

        # All checks completed, upload the final image
        logger.info("All HC_TWO checks completed successfully")
        time.sleep(6)  # Final image delay
        image_path = self.capture_object.capture_and_save_frame()
        self.upload_final_image("hce2finalimg", image_path)
        time.sleep(6)
        
    def process_piston(self, image_path):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(15, GPIO.OUT, initial=GPIO.LOW)
        logger.info("Processing PISTON")
        piston = False 
        pistonseal_result = False 
        completed = False

        for _ in range(self.max_retries):
            #bearing_result = False 
            #pistonseal_result = False 
            #completed = False
            piston_obj = PistonLogic.CheckPiston(image_path)
            piston,pistonseal_result , completed = piston_obj.is_process_complete(piston,pistonseal_result,completed)
            #complete_res = piston_obj.check_final_step()
            logger.info(f"Piston detection result: {pistonseal_result , completed,piston}")
            #print("this is the compplete result",complete_res)
            if pistonseal_result and completed and piston:
                #self.upload_sequence_result("pistonb", True)
                #self.upload_sequence_result("pistoncover" , True)
                break
            #complete_res = piston_obj.check_final_step()
            #print("this is the compplete result",complete_res)

            else:
                logger.warning("Piston process not complete. Retrying...")
                time.sleep(1)
                image_path = self.capture_object.capture_and_save_frame()
                
        else:
            logger.error("Max retries reached for piston detection")
            self.upload_sequence_result("pistonb", True)
            self.upload_sequence_result("pistoncover" , True)

        logger.info("PISTON check completed successfully")
        time.sleep(6)
        image_path = self.capture_object.capture_and_save_frame()
        self.upload_final_image("pistonfinalimg", image_path)
        time.sleep(6)


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
        try:
            with open(image_path, 'rb') as f:
                files = {"file": (image_path, f)}
                print(files)
                response = requests.post(url, files=files)
                response.raise_for_status()
            logger.info(f"Successfully uploaded final image to {endpoint}.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to upload final image to {endpoint}. Error: {e}")

def fetch_api_response(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"An error occurred: {e}")
        return None

def check_reset():
    reset_url = "http://localhost:3004/resetflag"
    data = fetch_api_response(reset_url)
    return data and data.get('reset') == True

def check_api():
    api_url = "http://localhost:3004/jobStartflag"
    data = fetch_api_response(api_url)
    
    if data and data.get('flag') == True:
        logger.info("Received True response. Starting image capture and detection.")
        workflow = ImageCaptureAndDetectWorkflow()
        workflow.run_workflow()
        logger.info("Workflow completed successfully.")
    else:
        logger.info("API response not True or failed to fetch data. Skipping workflow.")

def main():
    while True:
        if check_reset():
            logger.info("Reset signal received. Restarting from the beginning.")
            continue  

        check_api()
        logger.info("Completed one full cycle. Checking API again in 2 seconds.")
        time.sleep(2)

if __name__ == "__main__":
    main()