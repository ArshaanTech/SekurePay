import cv2
import numpy as np

# Load the trained model
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read("face_model.yml")  # Load trained model
label_dict = np.load("labels.npy", allow_pickle=True).item()  # Load label mapping

# Start webcam
cap = cv2.VideoCapture(0)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

print("🎥 Face Recognition Started. Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(50, 50))

    for (x, y, w, h) in faces:
        face_roi = gray[y:y + h, x:x + w]  # Extract face region
        label, confidence = recognizer.predict(face_roi)  # Recognize face

        if confidence < 60:  # Confidence threshold (lower = better match)
            name = label_dict[label]
            text = f"{name} ({round(confidence, 2)})"
            color = (0, 255, 0)  # Green for recognized face
        else:
            text = "Unknown"
            color = (0, 0, 255)  # Red for unknown face

        cv2.putText(frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

    cv2.imshow("Face Recognition", frame)

    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()