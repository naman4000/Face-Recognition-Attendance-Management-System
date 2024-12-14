import cv2
import os
import numpy as np
from datetime import datetime, timedelta
import mysql.connector
from init_db import get_connection
import pygetwindow as gw

# Paths
HAARCASCADE_PATH = "utils/haarcascade/haarcascade_frontalface_alt2.xml"
TRAINER_PATH = "trainer/trainer.yml"
TEMP_DIR = "trainer/temp_images"

import os
import cv2
import numpy as np

def train_model(enrollment, name):
    """Train the face recognition model with images captured from the webcam."""
    # Create the temp directory if it doesn't exist
    os.makedirs(TEMP_DIR, exist_ok=True)
    face_cascade = cv2.CascadeClassifier(HAARCASCADE_PATH)
    recognizer = cv2.face.LBPHFaceRecognizer_create()

    cap = cv2.VideoCapture(0)
    count = 0

    # Configure the camera window
    window_name = "Capturing Faces"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 640, 480)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)

    try:
        while count < 100:  # Capture up to 100 images for a single person
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame.")
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)

            for (x, y, w, h) in faces:
                count += 1
                face_img = gray[y:y + h, x:x + w]
                
                # Save the image with unique filenames
                image_filename = f"{TEMP_DIR}/{name}_{enrollment}_{count}.jpg"
                cv2.imwrite(image_filename, face_img)

                # Draw a rectangle around the detected face
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

            # Display the camera feed in the configured window
            cv2.imshow(window_name, frame)

            # Break if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    except Exception as e:
        cap.release()
        cv2.destroyAllWindows()
        raise Exception(f"Error during face capture: {str(e)}")

    cap.release()
    cv2.destroyAllWindows()

    # Train the model with the captured images
    image_paths = [os.path.join(TEMP_DIR, f) for f in os.listdir(TEMP_DIR) if f.endswith('.jpg')]
    faces = []
    ids = []

    try:
        is_model_empty = False
        # Check if the trainer file exists and has valid data
        if os.path.exists(TRAINER_PATH):
            try:
                recognizer.read(TRAINER_PATH)
                print("Existing model loaded successfully!")
            except cv2.error:
                print("Trainer file is empty or corrupted. Training a new model.")
                is_model_empty = True
        else:
            is_model_empty = True

        # Load face data for training
        for img_path in image_paths:
            face = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
            faces.append(face)
            ids.append(int(enrollment))  # Ensure the enrollment ID is passed properly

        # Decide whether to train or update the model
        if is_model_empty:
            recognizer.train(faces, np.array(ids))  # Train a new model
            print(f"New model trained for {name} ({enrollment}).")
        else:
            recognizer.update(faces, np.array(ids))  # Update the existing model
            print(f"Model updated with new data for {name} ({enrollment}).")

        # Save the updated model
        recognizer.save(TRAINER_PATH)
        print(f"Model saved to {TRAINER_PATH}.")

        # Delete temporary images after training
        for img_path in image_paths:
            os.remove(img_path)  # Delete the face images after training

    except Exception as e:
        raise Exception(f"Error during model training: {str(e)}")

    print(f"Face data added successfully for {name} ({enrollment}).")



def recognize_faces(subject):
    """Recognize a single face and return the most reliable enrollment ID."""
    if not subject:
        print("Error: Subject is required!")
        return {"error": "Subject is required!"}

    # Load recognizer and Haarcascade
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    try:
        recognizer.read(TRAINER_PATH)
    except Exception as e:
        print(f"Error: Model not found. Please train the model. {e}")
        return {"error": "Model not found. Please train the model."}

    face_cascade = cv2.CascadeClassifier(HAARCASCADE_PATH)
    if face_cascade.empty():
        print("Error: Haarcascade file not found or incorrect path.")
        return {"error": "Haarcascade file not found."}

    # Initialize database connection
    connection = get_connection()
    if not connection:
        print("Error: Unable to connect to the database.")
        return {"error": "Database connection failed."}
    cursor = connection.cursor(dictionary=True)

    # Webcam initialization
    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        print("Error: Unable to access the webcam.")
        return {"error": "Unable to access the webcam."}

    # Create the OpenCV window
    cv2.namedWindow("Filling Attendance...", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Filling Attendance...", 640, 480)
    cv2.setWindowProperty("Filling Attendance...", cv2.WND_PROP_TOPMOST, 1)

    font = cv2.FONT_HERSHEY_SIMPLEX
    print("Camera is on. Recognizing faces...")

    # Recognition timing and result tracking
    start_time = datetime.now()
    timeout = timedelta(seconds=5)  # Recognition timeout set to 5 seconds
    id_counts = {}  # Dictionary to count occurrences of each ID
    best_face_id = None
    best_confidence = 100  # Initialize with a high confidence score
    face_detected = False  # Track if any face is detected

    while (datetime.now() - start_time) < timeout:
        ret, frame = cam.read()
        if not ret:
            print("Failed to capture frame.")
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)

        if len(faces) > 0:
            face_detected = True  # At least one face is detected

        for (x, y, w, h) in faces:
            # Recognize the face
            Id, conf = recognizer.predict(gray[y:y + h, x:x + w])

            if conf < 50:  # Confidence threshold for recognition
                id_counts[Id] = id_counts.get(Id, 0) + 1  # Increment ID count

                # Update the best confidence ID if necessary
                if conf < best_confidence:
                    best_confidence = conf
                    best_face_id = Id

                # Display the recognized ID
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, f"ID: {Id} ", (x, y - 10), font, 1, (0, 255, 0), 2)
            else:  # Handle unrecognized faces
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                cv2.putText(frame, "Unknown", (x, y - 10), font, 1, (0, 0, 255), 2)

        # Show the webcam feed
        cv2.imshow("Filling Attendance...", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):  # Exit on 'q'
            break

    # Cleanup resources
    cam.release()
    cv2.destroyAllWindows()
    cursor.close()
    connection.close()

    # Determine the final result
    if not face_detected:  # No face was detected at all
        print("No face detected.")
        return {"error": "No face detected during the session."}
    
    if best_face_id and id_counts.get(best_face_id, 0) > 8:  # Reliable face ID
        print(f"Reliable ID: {best_face_id}, Confidence: {best_confidence}, Frequency: {id_counts[best_face_id]}")
        return {"enrollment": best_face_id}
    elif face_detected:  # Face detected but confidence is too low
        print("Unknown face detected.")
        return {"error": "Unknown face detected or Unable to identify"}
