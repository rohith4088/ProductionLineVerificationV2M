from ultralytics import YOLO

def check_final_step(image_path):
        final_model = YOLO("models/Piston_Complete_Process.pt")
        # Check if the process is "COMPLETE" or "INCOMPLETE" using live feed
        final_results = final_model.predict(source=image_path, conf=0.1, show=False)
        for final_result in final_results:
            for box, cls, conf in zip(final_result.boxes.xyxy, final_result.boxes.cls, final_result.boxes.conf):
                class_name = final_model.names[int(cls)]
                confidence = float(conf)
                print(confidence)
                if class_name == "COMPLETE" and confidence >= 0.8:
                    print("Process is COMPLETE!")
                    return True
                elif class_name == "INCOMPLETE":
                    print("Process is INCOMPLETE!")
                    return False
        return False
path = 'images/current.jpg'
res = check_final_step(path)
print(res)
