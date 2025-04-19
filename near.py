import torch
from transformers import pipeline
from PIL import Image
import numpy as np
import cv2

# Load models
depth_estimator = pipeline("depth-estimation", model="depth-anything/Depth-Anything-V2-Small-hf")
model = torch.hub.load('ultralytics/yolov5', 'yolov5s')

def normalize_depth(depth_array):
    return cv2.normalize(depth_array, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

def smooth_depth(depth_array):
    return cv2.GaussianBlur(depth_array, (5, 5), 0)

def adaptive_threshold(depth_array):
    mean_depth = np.mean(depth_array)
    std_depth = np.std(depth_array)
    return mean_depth - std_depth

# Define object-specific thresholds (in normalized depth units)
object_thresholds = {
    'person': 30, 'chair': 15, 'table': 25, 'car': 40, 'bicycle': 20,
    'motorcycle': 35, 'bus': 50, 'truck': 45, 'dog': 10, 'cat': 10,
    'bottle': 5, 'laptop': 10, 'tv': 20, 'couch': 30, 'bed': 35,
    'refrigerator': 25, 'book': 5, 'clock': 10, 'vase': 8, 'potted plant': 12
}

def check_proximity(depth_array, results, get_threshold_func):
    close_objects = []
    all_objects = []
    adaptive_thresh = adaptive_threshold(depth_array)
    
    for det in results.xyxy[0]:
        x1, y1, x2, y2, conf, cls = det.tolist()
        if conf < 0.5:  # Confidence filtering
            continue
        x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
        object_name = results.names[int(cls)]
        object_depth = np.mean(depth_array[y1:y2, x1:x2])
        
        all_objects.append(f"{object_name} (depth: {object_depth:.2f})")
        
        threshold = get_threshold_func(object_name)  # Call the function with object_name
        if object_depth < min(threshold, adaptive_thresh):
            close_objects.append(object_name)
    
    return close_objects, all_objects


def process_image(image_path):
    image = Image.open(image_path)
    image_np = np.array(image)

    depth_map = depth_estimator(image)["depth"]
    depth_array = np.array(depth_map)
    depth_array = normalize_depth(depth_array)
    depth_array = smooth_depth(depth_array)

    results = model(image_np)
    close_objects, all_objects = check_proximity(depth_array, results, 20)

    return close_objects, all_objects, results

def main():
    image_path = '/Users/reetvikchatterjee/Desktop/living-room-article-chair-22.jpg'
    close_objects, all_objects, results = process_image(image_path)

    print("All detected objects:")
    for obj in all_objects:
        print(f"- {obj}")

    if close_objects:
        print(f"\nWarning: {', '.join(set(close_objects))} {'is' if len(set(close_objects)) == 1 else 'are'} very close!")
    else:
        print("\nAll objects are at a safe distance.")

    img = results.render()[0]
    cv2.imshow('Object Detection', img[:, :, ::-1])
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
