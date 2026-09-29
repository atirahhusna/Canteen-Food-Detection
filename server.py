from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import cv2
import numpy as np
import os
from datetime import datetime
from ultralytics import YOLO
import math
import base64
from collections import Counter
import api
import log
import shapedetect
import shapeclassify
import json




app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

@app.route("/processTabletGET", methods=["GET"])
def testTablet():             
        result = api.getRequest("isTablet")
        return result


@app.route("/checkMMEStar", methods=["GET"])
def check():   
        txid = request.args.get("transactionid")     
        result = api.getCheckMMEStar(txid)
        return result

@app.route('/test-crash', methods=["GET"])
def test_crash():
        try:
                print("test crash")
                raise Exception("Intentional crash for BAT file test")

        except Exception as e:
                os._exit(1)


@app.route("/processGET", methods=["GET"])
def test():        
        result = api.getRequest("")
        return result


@app.route("/processCategoryGET", methods=["GET"])
def testCategory():
        result = api.getRequestCategory()
        return result

@app.route("/processPOST", methods=["POST"])
def test2():  
            

        data = request.json       
        
        response = api.postRequestSave(data)
                
        return jsonify(response)

# Load model ONCE only
model = YOLO("latest.pt")

@app.route("/process", methods=["POST"])
def process_image():
        try: 
                print("start img process")
                
               
                # global detected_objects
                detected_objects = []  # Reset detected objects for each frame

                # Get request info from client
                terminal_id = request.headers.get("X-Terminal-ID", "UNKNOWN")
                transaction_id = request.headers.get("X-Transaction-ID", "1234") 
                

                date = datetime.now().strftime("%Y%m%d")
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

                # Unique base name for this request
                base_name = f"{terminal_id}_{transaction_id}_{timestamp}"

                # Prepare save directory               
                SAVE_DIR = "shot" + date
                os.makedirs(SAVE_DIR, exist_ok=True)
                save_path = os.path.join(SAVE_DIR, f"shot_{base_name}.jpg")

                # Stream image data to disk in chunks
                with open(save_path, 'wb') as f:
                        chunk_size = 8192
                        while True:
                                chunk = request.stream.read(chunk_size)
                                if not chunk:
                                        break
                                f.write(chunk)

                # Convert saved image to OpenCV format
                image = cv2.imread(save_path)
                if image is None:
                        return "Invalid image data", 400

                # Perform YOLO detection
                results = model(image, conf=0.5)

                # Extract detection details
                boxes = results[0].boxes.xyxy.tolist()
                confidences = results[0].boxes.conf.tolist()
                classes = results[0].boxes.cls.tolist()
                names = results[0].names

                ori_image = image.copy()
                
                #get class index
                if 1 in classes:
                        index = classes.index(1)
                        x1, y1, x2, y2 = boxes[index]

                        # Assume you've detected an A4 paper and found its height in pixels
                        a4_height_in_pixels = y2 - y1
                        a4_width_in_pixels = x2 - x1

                        # Known height of an A4 paper in millimeters
                        a4_height_in_mm = 32
                        a4_width_in_mm = 44

                        # Calculate the pixels-per-millimeter ratio
                        h_pixels_per_mm = a4_height_in_pixels / a4_height_in_mm #11
                        w_pixels_per_mm = a4_width_in_pixels / a4_width_in_mm #13
                else:
                        h_pixels_per_mm = 11
                        w_pixels_per_mm = 13

                # Crop directory
                crop_dir = "cropped_objects"
                os.makedirs(crop_dir, exist_ok=True)

                # Counter for saved crops
                count = 1
                

                # Draw bounding boxes on the frame
                for i, (box, cls, conf) in enumerate(zip(boxes, classes, confidences)): 
                        
                        cup_found = any(names[int(cls)] == "cup" for cls in classes)
   
                        name = names[int(cls)] 
                        
                        
                        x1, y1, x2, y2 = int(box[0]), int(box[1]), int(box[2]), int(box[3])

                        h = y2 - y1
                        w = x2 - x1
                        
                        # Now you can estimate the size of any object in millimeters
                        estimated_object_height = h / h_pixels_per_mm
                        estimated_object_weight = w / w_pixels_per_mm
                        perimeter =  math.floor((estimated_object_height + estimated_object_weight) * 2)
                        aspect_ratio = round(estimated_object_weight / estimated_object_height,2)

                        result = ""
                        if cup_found:
                                if name == "cup" : 
                                        # result = name   

                                        # Crop and save image with unique id + counter                            
                                        cropped_object = ori_image[y1:y2, x1:x2]
                                        crop_filename = os.path.join(crop_dir, f"{base_name}_{count}.jpg")
                                        cv2.imwrite(crop_filename, cropped_object)
                                        count += 1  

                                        isCircle = shapeclassify.detect_circle(crop_filename)
                                        if isCircle == "cup":
                                                result = "SmallCup"
                                                #remove cup until finalize price
                                                # detected_objects.append(result)
                                                ##test start - capture all object and its perimeter##
                                                # detected_objects.append(result) 
                                                cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                                                cv2.putText(image, str(result) + " p: " +str(perimeter) + " r: " + str(aspect_ratio), (x1 + 5, y1 + 50),
                                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2) 
                                                ##test start## 

            
                                if name == "canteen" :    
                                        # Check if the detected object's bounding box is within the ROI
                                        # result = name   

                                        # Crop and save image with unique id + counter
                                        cropped_object = ori_image[y1:y2, x1:x2]
                                        crop_filename = os.path.join(crop_dir, f"{base_name}_{count}.jpg")
                                        cv2.imwrite(crop_filename, cropped_object)
                                        count += 1 

                                        isCircle = shapeclassify.detect_circle(crop_filename)  

                                        if isCircle == "circle":                         

                                                if perimeter >= 230 and perimeter < 300 : 
                                                        isoval = shapedetect.detect_shape(crop_filename)
                                                        if isoval == "oval":
                                                                result = "OvalPlate"                                                              
                                                        else:
                                                                result = "SmallPlate" 

                                                        detected_objects.append(result)
                                                                
                                                                                                                                        
                                                if perimeter > 100 and perimeter < 230 :
                                                        
                                                        result = "SmallBowl" 
                                                        detected_objects.append(result)
                                                                                                        
                                                if perimeter >= 300 and perimeter < 350 :
                                        
                                                        result = "MediumPlate" 
                                                        detected_objects.append(result)

                                                if perimeter >= 350 and perimeter <= 500 :
                                                        result = "BigPlate"
                                                        detected_objects.append(result)


                                                
                                                        
                                                

                                                if result != "" :
                                                        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                                                        cv2.putText(image, str(result) + " p: " +str(perimeter) + " r: " + str(aspect_ratio), (x1 + 5, y1 + 50),
                                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2) 
                                                        ##test start## 
                                        elif isCircle == "cup":
                                                result = "SmallCup"
                                                #remove cup until finalize price
                                                # detected_objects.append(result)
                                                ##test start - capture all object and its perimeter##
                                                # detected_objects.append(result) 
                                                cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                                                cv2.putText(image, str(result) + " p: " +str(perimeter) + " r: " + str(aspect_ratio), (x1 + 5, y1 + 50),
                                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2) 
                                                ##test start## 
                                        else:
                                
                                                if perimeter >= 300 and perimeter <= 500 :
                                                        result = "alacarte" 
                                                        detected_objects.append(result) 
                                                
                                                else:
                                                        if perimeter >= 185 and perimeter < 300 :
                                                                result = "SquarePlate" 
                                                                detected_objects.append(result) 
                                                        

                                                if result != "" :
                                                        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                                                        cv2.putText(image, str(result) + " p: " +str(perimeter) + " r: " + str(aspect_ratio), (x1 + 5, y1 + 50),
                                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2) 
                                                        ##test start## 
                        
                        else:
                                if name == "canteen" :    
                                        # Check if the detected object's bounding box is within the ROI
                
                                        # result = name   

                                        # Crop and save image with unique id + counter
                                        cropped_object = ori_image[y1:y2, x1:x2]
                                        crop_filename = os.path.join(crop_dir, f"{base_name}_{count}.jpg")
                                        cv2.imwrite(crop_filename, cropped_object)
                                        count += 1  

                                        isCircle = shapeclassify.detect_circle(crop_filename)  

                                        if isCircle == "circle":                           

                                                if perimeter >= 65 and perimeter < 85 : 
                                                        isoval = shapedetect.detect_shape(crop_filename)
                                                        if isoval == "oval":
                                                                result = "OvalPlate"                                                              
                                                        else:
                                                                result = "SmallPlate" 
                                                        
                                                        detected_objects.append(result)
                                                                                                                                
                                                if perimeter >= 50 and perimeter < 65 :
                                                        result = "SmallBowl"  
                                                        detected_objects.append(result) 

                                                if perimeter >= 85 and perimeter < 110 :
                                                        result = "MediumPlate"   
                                                        detected_objects.append(result)                                    
                                                                                                        
                                                if perimeter >= 110 and perimeter <= 130 :
                                                        result = "BigPlate"
                                                        detected_objects.append(result)
                                                        

                                                #remove cup until finalize price
                                                # if perimeter >= 40 and perimeter < 50 :
                                                #         result = "SmallCup" 


                                                # detected_objects.append(result)
                                                        

                                                ##test start - capture all object and its perimeter##
                                                if result != "" :
                                                        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                                                        cv2.putText(image, str(result) + " p: " +str(perimeter) + " r: " + str(aspect_ratio), (x1 + 5, y1 + 50),
                                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2) 
                                                        ##test start## 

                                        elif isCircle == "cup":
                                                result = "SmallCup"
                                                #remove cup until finalize price
                                                # detected_objects.append(result)
                                                ##test start - capture all object and its perimeter##
                                                # detected_objects.append(result) 
                                                cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                                                cv2.putText(image, str(result) + " p: " +str(perimeter) + " r: " + str(aspect_ratio), (x1 + 5, y1 + 50),
                                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2) 
                                                ##test start## 
                                        else:
                                                if perimeter >= 90 and perimeter <= 140 :
                                                        result = "alacarte" 
                                                        detected_objects.append(result)
                                                
                                                else:
                                                        if perimeter >= 55 and perimeter < 90 :
                                                                result = "SquarePlate" 
                                                                detected_objects.append(result)
                                                        else:
                                                                result = "others"

                                                ##test start - capture all object and its perimeter##
                                                if result != "" :
                                                        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                                                        cv2.putText(image, str(result) + " p: " +str(perimeter) + " r: " + str(aspect_ratio), (x1 + 5, y1 + 50),
                                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2) 
                                                        ##test start## 


                # Save the processed image with a timestamp   
                ## Ensure the save directory exists
                result_dir = "result" + date
                os.makedirs(result_dir, exist_ok=True)  

                result_filename = os.path.join(result_dir, f"{base_name}_result.jpg")
                cv2.imwrite(result_filename, image)

                
                log.infolog(f"Original image saved at: {save_path}")
                log.infolog(f"Result image saved at: {result_filename}")

                # Send the processed image back to the client
                _, buffer = cv2.imencode(".jpg", image)
                # return send_file(io.BytesIO(buffer), mimetype="image/jpeg")
                image_base64 = base64.b64encode(buffer).decode('utf-8')
                # Return both the image and the description
                # Example image description (replace with actual detection output)

                # print("test")
                description = [] 
                counter = Counter(detected_objects)
                temp = set()
                for sub in detected_objects:
                    if sub not in temp:
                        result = api.getRequest(sub)
                        print(result)
                        data = json.loads(result)
                        price = data[0]['price']
                        itemid = data[0]['id']
                        url = data[0]['url']
                        details = data[0]['details']
                        data = {
                            "id": itemid,
                            "item": sub,
                            "count": counter[sub],
                            "price": price,
                            "url" : url  ,
                            "details": details                          
                        }
                        description.append(data)
                        temp.add(sub)  

                # description = [
                #         {"item": "Plate", "price": "2.00"},
                #         {"item": "Bowl", "price": "3.00"}
                # ]
                print("end")
                return jsonify({
                        "status": "success",
                        "terminal_id": terminal_id,
                        "transaction_id": transaction_id,
                        "imgid": result_filename,
                        "description": description,
                        "image": image_base64
                })
        
        except Exception as e:
                log.infolog( str(e))
                print( str(e))

                return jsonify({
                "status": "error",
                "message": str(e)
                }), 500


#--------START ATIRAH TEST---------
# Load model ONCE only
model2 = YOLO("atirah.pt")

@app.route("/testprocessGET", methods=["GET"])
def testprocessGET():        
        result = api.testgetRequest("")
        return result

@app.route("/process_live_preview", methods=["POST"])
def process_live_preview():
    try:
        terminal_id = request.headers.get(
            "X-Terminal-ID",
            "UNKNOWN"
        )

        transaction_id = request.headers.get(
            "X-Transaction-ID",
            "1234"
        )

        # Read raw image bytes sent by JavaScript
        image_bytes = request.get_data()

        if not image_bytes:
            return jsonify({
                "status": "error",
                "message": "No image data received"
            }), 400

        # Convert bytes into OpenCV image
        image_array = np.frombuffer(
            image_bytes,
            dtype=np.uint8
        )

        image = cv2.imdecode(
            image_array,
            cv2.IMREAD_COLOR
        )

        if image is None:
            return jsonify({
                "status": "error",
                "message": "Invalid image data"
            }), 400

        # Run YOLO
        results = model2.predict(
            source=image,
            conf=0.5,
            verbose=False
        )

        # Draw YOLO boxes
        processed_image = results[0].plot()

        # Convert result to Base64
        success, buffer = cv2.imencode(
            ".jpg",
            processed_image
        )

        if not success:
            return jsonify({
                "status": "error",
                "message": "Unable to encode image"
            }), 500

        image_base64 = base64.b64encode(
            buffer
        ).decode("utf-8")

        return jsonify({
            "status": "success",
            "terminal_id": terminal_id,
            "transaction_id": transaction_id,
            "image": image_base64
        })

    except Exception as error:
        print("Preview error:", error)

        return jsonify({
            "status": "error",
            "message": str(error)
        }), 500

@app.route("/process_live", methods=["POST"])
def process_live():
        try: 
                print("start img process")
                
               
                # global detected_objects
                detected_objects = []  # Reset detected objects for each frame

                # Get request info from client
                terminal_id = request.headers.get("X-Terminal-ID", "UNKNOWN")
                transaction_id = request.headers.get("X-Transaction-ID", "1234") 
                

                date = datetime.now().strftime("%Y%m%d")
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

                # Unique base name for this request
                base_name = f"{terminal_id}_{transaction_id}_{timestamp}"

                # Prepare save directory               
                SAVE_DIR = "shot" + date
                os.makedirs(SAVE_DIR, exist_ok=True)
                save_path = os.path.join(SAVE_DIR, f"shot_{base_name}.jpg")

                # Stream image data to disk in chunks
                with open(save_path, 'wb') as f:
                        chunk_size = 8192
                        while True:
                                chunk = request.stream.read(chunk_size)
                                if not chunk:
                                        break
                                f.write(chunk)

                # Convert saved image to OpenCV format
                image = cv2.imread(save_path)
                if image is None:
                        return "Invalid image data", 400

                # Perform YOLO detection
                results = model2(image, conf=0.5)

                # Extract detection details
                boxes = results[0].boxes.xyxy.tolist()
                confidences = results[0].boxes.conf.tolist()
                classes = results[0].boxes.cls.tolist()
                names = results[0].names

                ori_image = image.copy()
                
                #get class index
                if 1 in classes:
                        index = classes.index(1)
                        x1, y1, x2, y2 = boxes[index]

                        # Assume you've detected an A4 paper and found its height in pixels
                        a4_height_in_pixels = y2 - y1
                        a4_width_in_pixels = x2 - x1

                        # Known height of an A4 paper in millimeters
                        a4_height_in_mm = 32
                        a4_width_in_mm = 44

                        # Calculate the pixels-per-millimeter ratio
                        h_pixels_per_mm = a4_height_in_pixels / a4_height_in_mm #11
                        w_pixels_per_mm = a4_width_in_pixels / a4_width_in_mm #13
                else:
                        h_pixels_per_mm = 11
                        w_pixels_per_mm = 13

                # Crop directory
                crop_dir = "cropped_objects"
                os.makedirs(crop_dir, exist_ok=True)

                # Counter for saved crops
                count = 1
                

                # Draw bounding boxes on the frame
                for i, (box, cls, conf) in enumerate(zip(boxes, classes, confidences)): 
                        
                        cup_found = any(names[int(cls)] == "cup" for cls in classes)
   
                        name = names[int(cls)] 
                        
                        
                        x1, y1, x2, y2 = int(box[0]), int(box[1]), int(box[2]), int(box[3])

                        h = y2 - y1
                        w = x2 - x1
                        
                        # Now you can estimate the size of any object in millimeters
                        estimated_object_height = h / h_pixels_per_mm
                        estimated_object_weight = w / w_pixels_per_mm
                        perimeter =  math.floor((estimated_object_height + estimated_object_weight) * 2)
                        aspect_ratio = round(estimated_object_weight / estimated_object_height,2)

                        result = ""
                         

                        # Crop and save image with unique id + counter                            
                        cropped_object = ori_image[y1:y2, x1:x2]
                        crop_filename = os.path.join(crop_dir, f"{base_name}_{count}.jpg")
                        cv2.imwrite(crop_filename, cropped_object)
                        count += 1  

                        result = name
                        #remove cup until finalize price
                        detected_objects.append(result)
                        ##test start - capture all object and its perimeter##
                        # detected_objects.append(result) 
                        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(image, str(result) + " p: " +str(perimeter) + " r: " + str(aspect_ratio), (x1 + 5, y1 + 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2) 
                        ##test start## 

            

                # Save the processed image with a timestamp   
                ## Ensure the save directory exists
                result_dir = "result" + date
                os.makedirs(result_dir, exist_ok=True)  

                result_filename = os.path.join(result_dir, f"{base_name}_result.jpg")
                cv2.imwrite(result_filename, image)

                
                log.infolog(f"Original image saved at: {save_path}")
                log.infolog(f"Result image saved at: {result_filename}")

                # Send the processed image back to the client
                _, buffer = cv2.imencode(".jpg", image)
                # return send_file(io.BytesIO(buffer), mimetype="image/jpeg")
                image_base64 = base64.b64encode(buffer).decode('utf-8')
                # Return both the image and the description
                # Example image description (replace with actual detection output)

                # print("test")
                description = [] 
                counter = Counter(detected_objects)
                temp = set()
                for sub in detected_objects:
                    if sub not in temp:
                        result = api.testgetRequest(sub)
                        print(result)
                        data = json.loads(result)
                        price = data[0]['price']
                        itemid = data[0]['id']
                        url = data[0]['url']
                        details = data[0]['details']
                        data = {
                            "id": itemid,
                            "item": sub,
                            "count": counter[sub],
                            "price": price,
                            "url" : url  ,
                            "details": details                          
                        }
                        description.append(data)
                        temp.add(sub)  

                # description = [
                #         {"item": "Plate", "price": "2.00"},
                #         {"item": "Bowl", "price": "3.00"}
                # ]
                print("end")
                return jsonify({
                        "status": "success",
                        "terminal_id": terminal_id,
                        "transaction_id": transaction_id,
                        "imgid": result_filename,
                        "description": description,
                        "image": image_base64
                })
        
        except Exception as e:
                log.infolog( str(e))
                print( str(e))

                return jsonify({
                "status": "error",
                "message": str(e)
                }), 500

@app.route("/health", methods=["GET"])
def health():
    return {
        "status": "success",
        "message": "YOLO server is running"
    }, 200


if __name__ == "__main__":
      app.run(host='0.0.0.0', port=5000)
