import cv2
import numpy as np
import os

# Load the Local Binary Patterns Histogram recognizer
recognizer = cv2.face.LBPHFaceRecognizer_create()

dataset_path = "dataset"  # Folder where face images are stored
images, labels, label_dict = [], [], {}

# Collect images and labels
def collect_images():
    person_id = 0
    for person_name in os.listdir(dataset_path):
        person_folder = os.path.join(dataset_path, person_name)
        if not os.path.isdir(person_folder):
            continue

        label_dict[person_id] = person_name  # Map ID to name

        for image_name in os.listdir(person_folder):
            image_path = os.path.join(person_folder, image_name)
            img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)  # Convert to grayscale
            if img is None:
                continue

            images.append(img)
            labels.append(person_id)

        person_id += 1

collect_images()

# Convert lists to NumPy arrays
images = np.array(images, dtype='uint8')
labels = np.array(labels, dtype='int32')

# Train the recognizer
recognizer.train(images, labels)
recognizer.save("face_model.yml")  # Save trained model
np.save("labels.npy", label_dict)  # Save label mapping

print(f"✅ Model trained with {len(labels)} images and saved as face_model.yml!")