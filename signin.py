import cv2
import numpy as np
import os
import random
import string
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.graphics import Rectangle
from kivy.uix.screenmanager import ScreenManager
from home_screen import HomePage
from Send_Money import SendMoneyScreen
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import base64
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding


# Encryption class
class Encryption:
    def __init__(self):
        # Generate a random 256-bit key for AES encryption
        self.key = os.urandom(32)  # AES-256 requires 32 bytes for the key
        self.backend = default_backend()

    def encrypt_nk(self, nk):
        """Encrypt the NK using AES encryption."""
        nk_bytes = nk.encode('utf-8')
        padder = padding.PKCS7(128).padder()
        padded_nk = padder.update(nk_bytes) + padder.finalize()
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=self.backend)
        encryptor = cipher.encryptor()
        encrypted_nk = encryptor.update(padded_nk) + encryptor.finalize()
        return base64.b64encode(iv + encrypted_nk).decode('utf-8')

    def decrypt_enk(self, enk):
        """Decrypt the ENK back to NK."""
        enk_bytes = base64.b64decode(enk)
        iv = enk_bytes[:16]
        encrypted_nk = enk_bytes[16:]
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=self.backend)
        decryptor = cipher.decryptor()
        decrypted_nk_padded = decryptor.update(encrypted_nk) + decryptor.finalize()
        unpadder = padding.PKCS7(128).unpadder()
        decrypted_nk = unpadder.update(decrypted_nk_padded) + unpadder.finalize()
        return decrypted_nk.decode('utf-8')


class SigninPage(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'signin_screen'

        # Layout setup
        layout = BoxLayout(orientation='vertical', padding=290, spacing=50, size_hint=(None, None), size=(750, 1334))
        blayout = BoxLayout(orientation='vertical', padding=75, spacing=50, size_hint=(None, None), size=(750, 1334))

        # Draw background image on canvas
        with self.canvas.before:
            self.rect = Rectangle(source='background.jpg', pos=self.pos, size=self.size)

        # Bind size and position to update background image when the window size changes
        self.bind(size=self.update_rect, pos=self.update_rect)

        # Create a BoxLayout to center the content vertically and horizontally
        content_layout = BoxLayout(orientation='vertical', spacing=20, size_hint=(None, None), size=(250, 110))
        content_layout.pos_hint = {'center_x': 0.5, 'center_y': 0.5}  # Center the content in the parent layout

        bottom_layout = BoxLayout(orientation='vertical', spacing=0, size_hint=(None, None), size=(100, 50))
        bottom_layout.pos_hint = {'center_x': 0, 'center_y': 0.0}

        # Username Label and Input
        self.username_label = Label(text='Enter Preferred Username', size_hint=(None, None), size=(200, 10), font_size=25, color=(0, 0, 0, 1))
        self.username_input = TextInput(multiline=False, size_hint=(None, None), size=(200, 30))

        # Add the label and input to the content layout
        content_layout.add_widget(self.username_label)
        content_layout.add_widget(self.username_input)

        # Sign In button (add it under the input fields)
        self.sign_in_button = Button(
            text='Sign In', 
            size_hint=(None, None), 
            size=(200, 50), 
            on_press=self.on_sign_in_button_press,
            background_normal='',  # Remove default background image
            background_color=(1, 1, 1, 0.6),  # Set background color (RGBA: White)
            color=(0, 0, 0, 1)  # Set text color (RGBA: Black)
        )
        # Add button to the content layout
        content_layout.add_widget(self.sign_in_button)

        # Add the content layout to the main layout
        layout.add_widget(content_layout)
        blayout.add_widget(bottom_layout)

        # Add the layout to the screen
        self.add_widget(layout)
        self.add_widget(blayout)

        # Bind the input text to the on_text_input function
        self.username_input.bind(on_text=self.on_text_input)

        # PIN input setup
        self.pin_label = Label(text='Create a 4-Digit PIN', size_hint=(None, None), size=(200, 10), font_size=25, color=(0, 0, 0, 1))
        self.pin_input = TextInput(multiline=False, size_hint=(None, None), size=(200, 30), input_filter='int')
        self.pin_input.max_length = 4  # Set max_length separately after initialization
        self.pin_input.disabled = True  # Disable PIN input until username is entered

        # Initialize encryption class
        self.encryption = Encryption()

    def update_rect(self, instance, value):
        # Update the background rectangle size and position to match the layout's size
        self.rect.pos = self.pos
        self.rect.size = self.size

    def on_sign_in_button_press(self, instance):
        username = self.username_input.text.strip()

        if username == '':
            self.show_popup("Error", "Please enter a username.")
            return

        # Enable the PIN input once the username is entered
        self.pin_input.disabled = False
        self.pin_input.pos = (250, 250)
        self.pin_input.hint_text = 'Create a 4 Digit PIN'
        self.add_widget(self.pin_input)

        # Capture and save face data for training
        self.capture_and_train_face(username)

    def show_popup(self, title, message):
        popup = Popup(title=title, content=Label(text=message), size_hint=(None, None), size=(200, 100))
        popup.open()

    def capture_and_train_face(self, username):
        """Face capture and training process for sign-in."""
        cap = cv2.VideoCapture(0)  # Open the webcam

        if not cap.isOpened():
            self.show_popup("Error", "Could not open webcam.")
            return

        # Initialize face cascade for detecting faces
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

        # Directory for storing face images
        face_data_dir = 'face_data'
        if not os.path.exists(face_data_dir):
            os.makedirs(face_data_dir)

        count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                self.show_popup("Error", "Failed to capture image.")
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

            for (x, y, w, h) in faces:
                face_roi = gray[y:y + h, x:x + w]
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                # Save captured face image with username
                face_filename = f'{face_data_dir}/{username}_{count}.png'
                cv2.imwrite(face_filename, face_roi)
                count += 1

            # Display the frame
            cv2.imshow("Capture Face", frame)

            if count >= 10:  # Capture at least 10 images
                break

            # Exit the loop if the user presses 'q' (key press)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

        # After capturing faces, train the recognizer
        self.train_model(username)
        self.show_popup("Success", "Face data captured successfully. Training the model now.")

    def train_model(self, username):
        """Train the face recognizer with captured data."""
        face_data_dir = 'face_data'
        images = []
        labels = []

        for filename in os.listdir(face_data_dir):
            if filename.endswith(".png"):
                img = cv2.imread(f'{face_data_dir}/{filename}', cv2.IMREAD_GRAYSCALE)
                images.append(img)
                label = self.create_label(username)  # Create a label based on the username
                labels.append(label)

        # Train the model
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.train(images, np.array(labels))

        # Save the trained model
        recognizer.save('face_model.yml')

        # Save labels to a separate file
        np.save("labels.npy", {label: username for label, username in zip(labels, [username] * len(labels))})

        # Ask user to create PIN (SK)
        self.pin_input.bind(on_text_validate=self.on_pin_created)

    def create_label(self, username):
        """Create a unique label for each user based on their username."""
        return hash(username)  # Create a label based on the username hash

    def on_pin_created(self, instance):
        """Handle the PIN input and combine it with the private key (pk)."""
        sk = self.pin_input.text.strip()
        if len(sk) != 4:
            self.show_popup("Error", "PIN must be 4 digits.")
            return

        # Generate the private key (pk)
        pk = self.generate_private_key()

        # Create NK by combining SK and PK
        nk = self.create_nk(sk, pk)

        # Encrypt NK into ENK
        enk = self.encryption.encrypt_nk(nk)

        # Store the ENK instead of the NK
        self.store_user_data(self.username_input.text, enk)

    def generate_private_key(self):
        """Generate a random private key (pk)."""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=16))

    def create_nk(self, sk, pk):
        """Combine sk (PIN) and pk (private key) to create NK.""" 
        return sk + pk

    def store_user_data(self, username, enk):
        """Store necessary data for user."""
        # Create a read-only TextInput for ENK
        enk_input = TextInput(text=('Please save your ENK: ' + enk), readonly=True, size_hint=(None, None), size=(350, 50))
        enk_input.pos_hint = {'center_x': 0.45, 'center_y': 0.3}  # Center the ENK input

        # Add the ENK input to the screen
        self.add_widget(enk_input)

        # Create the Next button to navigate to the login screen
        next_button = Button(
            text='Next',
            size_hint=(None, None),
            size=(100, 50),
            background_normal='',
            background_color=(1, 1, 1, 0.6),
            color=(0, 0, 0, 1)
        )
        next_button.pos = (250,150)

        # Bind the button's on_press event to the on_next_press method
        next_button.bind(on_press=self.on_next_press)

        # Add the Next button to the screen
        self.add_widget(next_button)

    def on_next_press(self, instance):
        """Handle the 'Next' button press and switch to the login screen.""" 
        self.manager.current = 'home_screen'

    def on_text_input(self, instance, value):
        # Limit the input to 4 characters
        if len(value) > 4:
            instance.text = value[:4]



class MyApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(HomePage(name='home_screen'))
        sm.add_widget(SigninPage(name='signin_screen'))
        sm.add_widget(SendMoneyScreen(name='send_money_screen'))
        sm.current = 'signin_screen'  # Start with the SigninScreen
        return sm


if __name__ == "__main__":
    MyApp().run()