
import cv2
import os

# Define dataset path
DATASET_PATH = "dataset"

# Create folder for new person
def create_person_folder(person_name):
    person_folder = os.path.join(DATASET_PATH, person_name)
    if not os.path.exists(person_folder):
        os.makedirs(person_folder)
        print(f"📁 Created folder: {person_folder}")
    else:
        print(f"⚠️ Folder already exists: {person_folder}")
    return person_folder

# Capture images from webcam
def capture_images(person_name, num_images=50):
    person_folder = create_person_folder(person_name)
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("❌ Error: Could not open webcam.")
        return

    count = 0
    while count < num_images:
        ret, frame = cap.read()
        if not ret:
            print("❌ Error: Failed to capture image.")
            break

        img_path = os.path.join(person_folder, f"{person_name}_{count}.jpg")
        cv2.imwrite(img_path, frame)
        print(f"✅ Saved: {img_path}")
        
        cv2.imshow("Capturing Images", frame)
        count += 1

        # Wait 500ms (0.5s) before capturing next image
        if cv2.waitKey(500) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("🎉 Image capture complete!")

# Get person name and start capturing
if __name__ == "__main__":  # Corrected line here
    person_name = input("Enter person's name: ").strip()
    capture_images(person_name, num_images=50)
