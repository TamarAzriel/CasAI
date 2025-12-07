from ultralytics import YOLO

# Load a model
model = YOLO("yolo11n.pt")  # load a pretrained model (recommended for training)

# Train the model
results = model.train(
    data="HomeObjects-3K.yaml",
    epochs=40, 
    imgsz=640
    )

#the model will be saved and we will move the best.onnx to the root of the folder