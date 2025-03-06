import os
import cv2
import numpy as np
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
from kivy.uix.image import Image
from home_screen import HomePage  # Assuming HomePage is in 'home_screen.py'
from signin import SigninPage  # Assuming SigninPage is in 'signin.py'
from Send_Money import SendMoneyScreen  # Assuming SendMoneyScreen is in 'Send_Money.py'
from currentuser import save_current_user, get_current_user  # Assuming currentuser.py contains these functions
from kivy.graphics import Rectangle

# File path for storing the logged-in user's info
CURRENT_USER_FILE = 'current_user.txt'

# Function to save the logged-in user to a file
def save_current_user(username):
    """Save the current logged-in user to a file."""
    with open(CURRENT_USER_FILE, "w") as file:
        file.write(username)

# Function to get the logged-in user from the file
def get_current_user():
    """Get the current logged-in user from the file."""
    if os.path.exists(CURRENT_USER_FILE):
        with open(CURRENT_USER_FILE, "r") as file:
            return file.read().strip()
    return None

# Initialize face recognizer
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read("face_model.yml")  # Load the pre-trained model
label_dict = np.load("labels.npy", allow_pickle=True).item()  # Load label mapping

# Setup window size
Window.size = (750, 1334)

class LoginPage(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'login_screen'

        # Layout setup
        layout = BoxLayout(orientation='vertical', padding=290, spacing=50, size_hint=(None, None), size=(750, 1334))
        blayout = BoxLayout(orientation='vertical', padding=75, spacing=50, size_hint=(None, None), size=(750, 1334))

        # Draw background image on canvas
        with self.canvas.before:
            self.rect = Rectangle(source='background.jpg', pos=self.pos, size=self.size)

        # Bind size and position to update background image when the window size changes
        self.bind(size=self.update_rect, pos=self.update_rect)

        # User image
        self.user_image = Image(source='user.png', size_hint=(None, None), size=(110, 105))
        layout.add_widget(self.user_image)

        # Create layout for username and login button
        content_layout = BoxLayout(orientation='vertical', spacing=20, size_hint=(None, None), size=(250, 110))
        content_layout.pos_hint = {'center_x': 0.5, 'center_y': 0.5}

        bottom_layout = BoxLayout(orientation='vertical', spacing=0, size_hint=(None, None), size=(100, 50))
        bottom_layout.pos_hint = {'center_x': 0, 'center_y': 0.0}

        # Username Label and Input
        self.username_label = Label(text='Enter Username', size_hint=(None, None), size=(200, 10), font_size=25, color=(0, 0, 0, 1))
        self.username_input = TextInput(multiline=False, size_hint=(None, None), size=(200, 30))

        # Add the label and input to the content layout
        content_layout.add_widget(self.username_label)
        content_layout.add_widget(self.username_input)

        # Login button
        self.login_button = Button(
            text='Next', 
            size_hint=(None, None), 
            size=(200, 50), 
            on_press=self.on_login_button_press,
            background_normal='',
            background_color=(1, 1, 1, 0.6),
            color=(0, 0, 0, 1)
        )
        content_layout.add_widget(self.login_button)

        # Sign In button
        self.signin_button = Button(
            text='Sign In', 
            size_hint=(None, None), 
            size=(60, 50), 
            on_press=self.on_signin_button_press,
            background_normal='',
            background_color=(1, 1, 1, 0.6),
            color=(0, 0, 0, 1)
        )
        bottom_layout.add_widget(self.signin_button)

        layout.add_widget(content_layout)
        blayout.add_widget(bottom_layout)
        self.add_widget(layout)
        self.add_widget(blayout)

    def update_rect(self, instance, value):
        """Update the background rectangle size and position."""
        self.rect.pos = self.pos
        self.rect.size = self.size

    def on_signin_button_press(self, instance):
        """Switch to the SignIn screen."""
        self.manager.current = 'signin_screen'

    def on_login_button_press(self, instance):
        """Handle login button press."""
        username = self.username_input.text.strip()

        if username == '':
            self.show_popup("Error", "Please enter a username.")
            return

        # Verify face before proceeding to sign in screen
        detected_name = self.verify_face(username)

        if detected_name is None:
            self.show_popup("Error", "Face recognition failed. Please try again.")
        elif detected_name == username:
            # Store the logged-in user and proceed
            save_current_user(username)
            self.manager.current = 'home_screen'
        else:
            self.show_popup("Error", "Username and face do not match.")

    def show_popup(self, title, message):
        """Show a popup message."""
        popup = Popup(title=title, content=Label(text=message), size_hint=(None, None), size=(200, 100))
        popup.open()

    def verify_face(self, username):
        """Face verification process using OpenCV and the pre-trained model."""
        cap = cv2.VideoCapture(0)  # Open the webcam

        if not cap.isOpened():
            print("❌ Error: Could not open webcam.")
            return None

        # Initialize face cascade for detecting faces
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Error: Failed to capture image.")
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

            for (x, y, w, h) in faces:
                face_roi = gray[y:y + h, x:x + w]  # Extract face region
                label, confidence = recognizer.predict(face_roi)
                
                # Handle case where label is not found in label_dict
                try:
                    if confidence < 60:  # If confidence is below threshold, consider it a match
                        name = label_dict[label]
                        cap.release()
                        cv2.destroyAllWindows()
                        return name
                except KeyError:
                    print(f"❌ Error: Unrecognized label {label}. This may be caused by a failed recognition.")
                    cap.release()
                    cv2.destroyAllWindows()
                    return None

        cap.release()
        cv2.destroyAllWindows()
        return None  # If no face was verified, return None

class MyApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(LoginPage(name='login_screen'))  # LoginPage
        sm.add_widget(HomePage(name='home_screen'))  # Assuming you have a HomePage
        sm.add_widget(SigninPage(name='signin_screen'))  # Assuming you have a SigninPage
        sm.add_widget(SendMoneyScreen(name='send_money_screen'))
        sm.current = 'login_screen'  # Start with the login screen
        return sm

if __name__ == "__main__":
    MyApp().run()
