
from ultralytics import YOLO
model = YOLO("yolo11n.pt")

model.train(
    data="/content/merged_canteen_dataset/data.yaml",
    epochs=200,
    imgsz=640,
    batch=16,
    device=0,
    patience=50,
    project="/content/drive/MyDrive/YOLO_Training",
    name="canteen_merged_80_20",
    save_period=10
)