# face_verification.py
import cv2
import numpy as np
import os

# Load the trained model
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read("face_model.yml")  # Load trained model
label_dict = np.load("labels.npy", allow_pickle=True).item()  # Load label mapping

def verify_face(username):
    # Set up webcam capture
    cap = cv2.VideoCapture(0)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    print("Starting face recognition...")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Error: Failed to capture image.")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(50, 50))

        for (x, y, w, h) in faces:
            face_roi = gray[y:y + h, x:x + w]  # Extract face region
            label, confidence = recognizer.predict(face_roi)

            if confidence < 60:  # Confidence threshold (lower = better match)
                name = label_dict[label]
                if name == username:
                    print(f"✔️ Face verified: {username}")
                    cap.release()
                    cv2.destroyAllWindows()
                    return True  # Verified the user
            else:
                print("❌ Face not recognized.")
                cap.release()
                cv2.destroyAllWindows()
                return False  # Failed verification

        cv2.imshow("Face Recognition", frame)

        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return False
