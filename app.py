import cv2
import torch
from PIL import Image
import numpy as np
from near import depth_estimator, model as near_model, normalize_depth, smooth_depth, check_proximity, object_thresholds
from vision import model as vision_model, get_compact_directions
import math
import warnings
import pyttsx3
import queue
import speech_recognition as sr
from recognition import recognize_faces
import threading

warnings.filterwarnings("ignore")

# Initialize text-to-speech engine and queues
engine = pyttsx3.init()
speech_queue = queue.Queue()
voice_command_queue = queue.Queue()

# Initialize voice recognition components
recognizer = sr.Recognizer()
mic = sr.Microphone()

# Initialize face recognition components
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
recognizer_face = cv2.face.LBPHFaceRecognizer_create()
recognizer_face.read("trained_model.yml")

relationships = {
    1: {"name": "Akshay Kumar", "relationships": "Friend"}
}

# Function to speak text using the speech queue
def speak(text):
    """Queue speech requests instead of calling runAndWait() in multiple threads."""
    speech_queue.put(text)

# Function to listen for voice commands continuously in a separate thread
def voice_listener():
    """Thread for continuous voice recognition."""
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        speak("Voice assistant activated. Say 'hi [object]' or 'who'.")

    while True:
        try:
            with mic as source:
                audio = recognizer.listen(source, phrase_time_limit=3)
            text = recognizer.recognize_google(audio).lower()
            if text.startswith(('hi', 'who')):
                voice_command_queue.put(text)
                print(f"Voice command detected: {text}")
        except sr.UnknownValueError:
            pass  # Ignore unrecognized audio
        except Exception as e:
            print(f"Voice error: {e}")

# Start the voice listener in a separate thread
voice_thread = threading.Thread(target=voice_listener, daemon=True)
voice_thread.start()

# Main video processing loop variables
video_path = '/Users/reetvikchatterjee/Desktop/VisionHelp/test.mp4'  # Replace with your video path
cap = cv2.VideoCapture(video_path)

FRAME_SKIP = 3  # Process every 3rd frame for efficiency
frame_count = 0
DETECTION_THRESHOLD = 0.7  # Confidence threshold for object detection

# Main video processing loop
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1
    if frame_count % FRAME_SKIP != 0:
        continue  # Skip this frame

    # Process frame for nearby object detection using depth estimation
    image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    depth_map = depth_estimator(image)["depth"]
    depth_array = np.array(depth_map)
    depth_array = normalize_depth(depth_array)
    depth_array = smooth_depth(depth_array)

    results = near_model(frame)
    close_objects, all_objects = check_proximity(depth_array, results, lambda obj: object_thresholds.get(obj, 20))

    for obj in results.xyxy[0]:
        x1, y1, x2, y2, conf, cls = obj.tolist()
        if conf < DETECTION_THRESHOLD:
            continue  # Skip objects below the confidence threshold

        x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
        cls = int(cls)
        object_name = results.names[cls]
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, f"{object_name}: {conf:.2f}", (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

    if close_objects:
        warning_message = f"Warning: {', '.join(set(close_objects))} nearby!"
        cv2.putText(frame, warning_message, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
        print(warning_message)
        speak(warning_message)

    # Process voice commands from the queue
    if not voice_command_queue.empty():
        command = voice_command_queue.get().lower()

        # Handle object directions (e.g., "hi chair")
        if command.startswith('hi '):
            obj_name = command.split('hi ', 1)[-1]
            image_width, image_height = image.size[0], image.size[1]
            results_vision = vision_model(image)
            detections = results_vision.pandas().xyxy[0]
            object_positions = {}

            for _, obj in detections.iterrows():
                if obj['confidence'] < DETECTION_THRESHOLD:
                    continue

                name = obj['name']
                xmin, ymin, xmax, ymax = obj[['xmin', 'ymin', 'xmax', 'ymax']]
                center_x = (xmin + xmax) / 2
                center_y = (ymin + ymax) / 2

                if name == obj_name:
                    if name in object_positions:
                        object_positions[name].append((center_x, center_y))
                    else:
                        object_positions[name] = [(center_x, center_y)]

            if obj_name in object_positions:
                start_x, start_y = image_width / 2, image_height / 2
                nearest_obj = min(object_positions[obj_name], 
                                  key=lambda pos: math.sqrt((pos[0] - start_x)**2 + (pos[1] - start_y)**2))
                directions = get_compact_directions(start_x, start_y,
                                                    nearest_obj[0], nearest_obj[1])
                speak(f"Directions to {obj_name}: {directions}")
            else:
                speak(f"{obj_name} not found in current view.")

        # Handle face recognition (e.g., "who")
        elif command == 'who':
            gray_frame = cv2.cvtColor(frame.copy(), cv2.COLOR_BGR2GRAY)
            faces_detected = face_cascade.detectMultiScale(gray_frame,
                                                           scaleFactor=1.1,
                                                           minNeighbors=5,
                                                           minSize=(30, 30))

            if len(faces_detected) > 0:
                for (x, y, w, h) in faces_detected[:1]:  # Process only the first detected face
                    roi_gray = gray_frame[y:y+h, x:x+w]
                    label_face_recog, confidence_face_recog = recognizer_face.predict(roi_gray)

                    if confidence_face_recog < 70:  # Lower confidence is better in LBPHFaceRecognizer
                        person_info = relationships.get(label_face_recog)
                        if person_info:
                            speak(f"{person_info['name']}, your {person_info['relationships']}")
                        else:
                            speak("Unknown person detected.")
                    else:
                        speak("Person not recognized.")
            else:
                speak("No faces detected.")

    # Display the processed video frame with bounding boxes and warnings
    cv2.imshow('Video', frame)

    # Process speech queue in the main loop to handle TTS requests sequentially
    while not speech_queue.empty():
        try:
            text_to_speak = speech_queue.get_nowait()
            engine.say(text_to_speak)
            engine.runAndWait()
        except Exception as e:
            print(f"Speech Error: {e}")

    # Press 'q' to quit the program manually
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Clean up
cap.release()
cv2.destroyAllWindows()
voice_thread.join(timeout=1)
