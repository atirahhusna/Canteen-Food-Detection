import torch
from torchvision import models, transforms
from PIL import Image
import cv2
import numpy as np

def detect_circle(image_path):
  
    # Load model architecture (must match how it was trained)
    model = models.efficientnet_b0(pretrained=False) # Changed from resnet18 to efficientnet_b0
    model.classifier[1] = torch.nn.Linear(model.classifier[1].in_features, 4)  # 2 classes: 'circle', 'other'


    # Load trained weights
    model.load_state_dict(torch.load('shape_model.pth', map_location=torch.device('cpu'), weights_only=True))
    model.eval()

    # Image preprocessing
    transform = transforms.Compose([
        transforms.Resize((224, 224)),  # Resize to match input size
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],  # ImageNet stats
                            std=[0.229, 0.224, 0.225])
    ])

    # Load and prepare image
    img = Image.open(image_path).convert('RGB')
    input_tensor = transform(img).unsqueeze(0)  # Add batch dimension

    # Inference
    with torch.no_grad():
        output = model(input_tensor)
        predicted_class = torch.argmax(output, 1).item()

    # Map to labels
    class_names = ['alacarte', 'circle', 'cup','other']
    shape = class_names[predicted_class]
    print(f"Shape: {shape}")
    print(f'Predicted Class: {predicted_class} -> {class_names[predicted_class]}')

    return shape