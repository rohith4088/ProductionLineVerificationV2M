import requests
import time
import logging
from datetime import datetime
import Jetson.GPIO as GPIO
from Trigger.source import main as trigger_main
from DetectComponent.detection import CombinedDetector
from Components.HC_TWO import HcTwoLogic
from Components.HC_ONE import HcOneLogic
from Components.PISTON import PistonLogic

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ImageCaptureAndDetectWorkflow:
    def __init__(self, images_folder="images", max_retries=1000):
        self.capture_object = trigger_main.PeriodicImageCapture(images_folder)
        self.detector = CombinedDetector(f"{images_folder}/current.jpg")
        self.max_retries = max_retries
        self.components = ['HC_ONE', 'PISTON', 'HC_TWO']
        self.detected_components = set()
        self.api_base_url = "http://localhost:3004"
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(15, GPIO.OUT, initial=GPIO.LOW)

    def run_workflow(self):
        logger.info("Starting workflow")
        self.capture_object.start()
        time.sleep(1)
        component_detected, result = self.detector.DetectComponents()
        
        if not result:
            logger.warning("No component detected. Skipping workflow.")
            self.capture_object.stop()
            return False
        
        logger.info(f"Component detected: {component_detected}. Proceeding with the fixed workflow.")
        
        for component in self.components:
            logger.info(f"Processing {component}")
            self.upload_component_name(component)
            
            image_path = self.capture_object.capture_and_save_frame()
            if not image_path:
                logger.error("Failed to capture image")
                return False

            self.detector.image_path = image_path
            
            if self.fetch_api_response(f"/modelflag/{component.lower()}mname").get('flag'):
                getattr(self, f"process_{component.lower()}")(image_path)
            else:
                logger.info(f"{component} make not entered")
            
            self.detected_components.add(component)

        logger.info("All components have been processed. Workflow complete.")
        self.detected_components.clear()
        self.capture_object.stop()
        return True

    def upload_component_name(self, component):
        self.make_api_request('post', f"/UploadComp/{component}", files={'result': 'true'})

    def process_hc_one(self, image_path):
        self.process_component(image_path, HcOneLogic, 'hce1')

    def process_hc_two(self, image_path):
        self.process_component(image_path, HcTwoLogic, 'hce2')

    def process_piston(self, image_path):
        piston_obj = PistonLogic.CheckPiston(image_path)
        piston, pistonseal_result, completed = False, False, False
        
        for _ in range(self.max_retries):
            piston, pistonseal_result, completed = piston_obj.is_process_complete(piston, pistonseal_result, completed)
            if pistonseal_result and completed and piston:
                break
            image_path = self.capture_object.capture_and_save_frame()
        
        self.upload_sequence_result("pistonb", True)
        self.upload_sequence_result("pistoncover", True)
        self.upload_final_image("pistonfinalimg", image_path)

    def process_component(self, image_path, ComponentLogic, prefix):
        for check in ['blue', 'yellow', 'bandw']:
            for _ in range(self.max_retries):
                result = getattr(ComponentLogic, f"{check.capitalize()}WasherDetect")(image_path).detect_washer()
                if result:
                    self.pulse_gpio()
                    self.upload_sequence_result(f"{prefix}{check}", True)
                    break
                image_path = self.capture_object.capture_and_save_frame()
        
        self.upload_final_image(f"{prefix}finalimg", image_path)

    def pulse_gpio(self):
        GPIO.output(15, GPIO.HIGH)
        time.sleep(0.2)
        GPIO.output(15, GPIO.LOW)
        time.sleep(0.2)
        GPIO.output(15, GPIO.HIGH)
        time.sleep(0.2)
        GPIO.output(15, GPIO.LOW)

    def upload_sequence_result(self, endpoint, result):
        self.make_api_request('post', f"/uploadSeq/{endpoint}", files={'result': str(result)})

    def upload_final_image(self, endpoint, image_path):
        with open(image_path, 'rb') as f:
            self.make_api_request('post', f"/uploadFinalimg/{endpoint}", files={"file": (image_path, f)})
            
            
    def fetch_api_response(self, endpoint):
        return self.make_api_request('get', endpoint)

    def make_api_request(self, method, endpoint, **kwargs):
        url = f"{self.api_base_url}{endpoint}"
        try:
            response = getattr(requests, method)(url, **kwargs)
            response.raise_for_status()
            return response.json() if method == 'get' else None
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None

def check_reset():
    workflow = ImageCaptureAndDetectWorkflow()
    return workflow.fetch_api_response("/resetflag").get('reset') == True

def check_api():
    workflow = ImageCaptureAndDetectWorkflow()
    if workflow.fetch_api_response("/jobStartflag").get('flag') == True:
        logger.info("Received True response. Starting image capture and detection.")
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