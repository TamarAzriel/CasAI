**Overview**
- **Purpose**: Sequence of steps to prepare data, train the similarity model and yolo model, then run the app for testing.

**Steps**
- **1. Run Scrape Script**: Download the CSV metadata and image directories.
  - Script: `data/ikea-scrape.py`
  - Expected outputs: an images directory under `data/ikea-data/` (subfolders like `beds/`, `chairs/`, etc.) and a CSV metadata file (check the script for exact filenames).
  - Example (Windows `cmd.exe`):

```
python data\ikea-scrape.py
```

- **2. Train Similarity Detector**: Use the similarity scripts / notebook to build a similarity model. The project contains `model/similarity-detector-train.ipynb` and `model/embed-ds.py` (if present) — use whichever workflow you prefer.
  - The user-provided dataset to combine/use: https://cvml.comp.nus.edu.sg/furniture/index.html (download and place dataset where the notebook expects it or update the notebook paths).
  - Typical steps:

```
# Open the notebook:
jupyter notebook model\similarity-detector-train.ipynb
```

- **3. Run YOLO model**: load the data and train with API
  - Script: `yolo-train\YOLO_train_v2.py`
  - Open and run the code. you can add epochs if you like


- **5. Run the App**: After training completes and model artifacts are saved into the expected locations, start the app for testing.
  - App entrypoint: `app\app.py`
  - Example:

```
python app\app.py
```

**Quick Checklist**
- **install requirements** `pip install -r requirements.txt`
- **Scraper:** `python data\ikea-scrape.py` -> confirm CSV + images in `data\ikea-data\`
- **Similarity:** run `model\similarity-detector-train.ipynb` (or `python model\embed-ds.py`)
- **Train YOLO:** `python yolo-train\YOLO_train_v2.py` (confirm args/paths)
- **Run app:** `python app\app.py`
- **added minor update
