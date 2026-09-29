from ultralytics import YOLO
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import numpy as np
import cv2
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "atirah.pt")

CONFIDENCE = 0.50

model = YOLO(MODEL_PATH)

app = Flask(__name__)
CORS(app)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "running",
        "model": os.path.basename(MODEL_PATH)
    })


@app.route("/detect", methods=["POST"])
def detect():
    try:
        if "image" not in request.files:
            return jsonify({
                "error": "No image received"
            }), 400

        image_bytes = request.files["image"].read()

        image_array = np.frombuffer(
            image_bytes,
            dtype=np.uint8
        )

        frame = cv2.imdecode(
            image_array,
            cv2.IMREAD_COLOR
        )

        if frame is None:
            return jsonify({
                "error": "Unable to decode image"
            }), 400

        results = model.predict(
            source=frame,
            conf=CONFIDENCE,
            verbose=False
        )

        detected_items = []
        detections = []

        boxes = results[0].boxes

        if boxes is not None:
            class_ids = boxes.cls.tolist()
            confidence_scores = boxes.conf.tolist()
            coordinates = boxes.xyxy.tolist()

            for class_id, confidence, box in zip(
                class_ids,
                confidence_scores,
                coordinates
            ):
                class_name = results[0].names[int(class_id)]

                detected_items.append(class_name)

                detections.append({
                    "name": class_name,
                    "confidence": round(
                        float(confidence),
                        3
                    ),
                    "box": {
                        "x1": round(float(box[0]), 2),
                        "y1": round(float(box[1]), 2),
                        "x2": round(float(box[2]), 2),
                        "y2": round(float(box[3]), 2)
                    }
                })

        return jsonify({
            "detected": detected_items,
            "detections": detections,
            "count": len(detected_items)
        })

    except Exception as error:
        print("Detection error:", error)

        return jsonify({
            "error": str(error)
        }), 500


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5001,
        debug=False,
        threaded=True,
        use_reloader=False
    )