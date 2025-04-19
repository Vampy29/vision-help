import cv2
import numpy as np
import os

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

recognizer = cv2.face.LBPHFaceRecognizer_create()

images = []
ids = []
id_counter = 0

for root, dirs, files in os.walk("Dataset"):
    for dir in dirs:
        id_counter += 1
        for file in os.listdir(os.path.join(root, dir)):
            if file.endswith("jpg") or file.endswith("png"):
                img_path = os.path.join(root, dir, file)
                img = cv2.imread(img_path)
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
                
                for (x, y, w, h) in faces:
                    roi_gray = gray[y:y+h, x:x+w]
                    images.append(roi_gray)
                    ids.append(id_counter)

# Convert ids to numpy array
ids = np.array(ids)

# Train the model
recognizer.train(images, ids)
recognizer.save("trained_model.yml")
