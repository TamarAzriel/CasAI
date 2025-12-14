from ultralytics import YOLO

# Load a model
model = YOLO("YOLO11s-seg.pt")  # load a pretrained model (recommended for training)

# Train the model
results = model.train(
    data="HomeObjects-3K.yaml",
    epochs=100, 
    imgsz=640
    )