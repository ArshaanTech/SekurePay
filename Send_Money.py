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
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import base64
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from decrypt import decrypt_enk, extract_pk_from_nk
from currentuser import get_current_user  # Assuming you have this function to get logged-in user
import base64
import binascii
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import os

class SendMoneyScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'send_money_screen'
        username = get_current_user()  # Get the logged-in username

        # Layout setup
        tlayout = BoxLayout(orientation='horizontal', padding=600, spacing=20, size_hint=(None, None), size=(0, 1300))
        layout = BoxLayout(orientation='vertical', padding=225, spacing=20, size_hint=(None, None), size=(750, 1334))

        if username:
            greeting_label = Label(
                text=f"Welcome, {username}",
                font_size=25,
                size_hint=(None, None),
                size=(self.width-300, 320),  # Label size
                pos=(50, self.height +600),  # Position at the top
                color=(0, 0, 0, 1)  # Text color (black)
            )
        layout.add_widget(greeting_label)

        # Draw background image
        with self.canvas.before:
            self.rect = Rectangle(source='background.jpg', pos=self.pos, size=self.size)

        self.bind(size=self.update_rect, pos=self.update_rect)

        # Add an image to the screen
        self.user_image = Image(source='smsm.png', size_hint=(None, None), size=(110, 105))
        tlayout.add_widget(self.user_image)

        # Input fields for recipient details
        self.recipient_name_label = Label(text="Recipient Name", size_hint=(None, None), size=(200, 10), font_size=25)
        self.recipient_name_input = TextInput(multiline=False, size_hint=(None, None), size=(250, 30))

        self.amount_label = Label(text="Amount", size_hint=(None, None), size=(200, 10), font_size=25)
        self.amount_input = TextInput(multiline=False, size_hint=(None, None), size=(250, 30))

        self.account_label = Label(text="Account Number", size_hint=(None, None), size=(200, 10), font_size=25)
        self.account_input = TextInput(multiline=False, size_hint=(None, None), size=(250, 30))

        layout.add_widget(self.recipient_name_label)
        layout.add_widget(self.recipient_name_input)
        layout.add_widget(self.amount_label)
        layout.add_widget(self.amount_input)
        layout.add_widget(self.account_label)
        layout.add_widget(self.account_input)

        # Send Button
        self.send_button = Button(
            text="Send", 
            size_hint=(None, None), 
            size=(200, 50), 
            on_press=self.on_send_button_press,
            background_normal='',
            background_color=(1, 1, 1, 0.6),
            color=(0, 0, 0, 1)
        )
        layout.add_widget(self.send_button)

        self.add_widget(layout)
        self.add_widget(tlayout)

    def update_rect(self, instance, value):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def on_send_button_press(self, instance):
        recipient_name = self.recipient_name_input.text.strip()
        amount = self.amount_input.text.strip()
        account_number = self.account_input.text.strip()

        if recipient_name == '' or amount == '' or account_number == '':
            self.show_popup("Error", "Please fill in all fields.")
            return
        else:
            self.show_pin_popup()

    def show_pin_popup(self):
        """Popup to input ENK and PIN for transaction."""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # ENK Input Field
        self.enk_input = TextInput(hint_text="Enter Encrypted Key (ENK)", size_hint=(None, None), size=(200, 40))
        
        # PIN Input Field
        self.pin_input = TextInput(password=True, hint_text="Enter PIN", size_hint=(None, None), size=(200, 40))
        
        # Submit Button
        pin_button = Button(text="Submit", size_hint=(None, None), size=(200, 50), on_press=self.on_pin_submit)

        content.add_widget(self.enk_input)
        content.add_widget(self.pin_input)
        content.add_widget(pin_button)

        self.pin_popup = Popup(title="Enter ENK and PIN", content=content, size_hint=(None, None), size=(300, 250))
        self.pin_popup.open()

    def on_pin_submit(self, instance):
        entered_encrypted_key = self.enk_input.text.strip()
        entered_pin = self.pin_input.text.strip()

        # Validate that both fields are filled
        if not entered_encrypted_key or not entered_pin:
            self.show_popup("Error", "Both fields are required.")
            return

        # Get the logged-in user's ENK and PK (assuming get_current_user provides this information)
        username = get_current_user()  # Assuming this function gives the current logged-in user

        # Retrieve the user's key (here using the PIN as the key for simplicity)
        key = entered_pin.encode('utf-8')  # You might need to adjust how you store or generate the key
        iv = os.urandom(16)  # In actual practice, IV should be saved or securely shared

        # Decrypt the ENK to get the NK
        nk = decrypt_enk(entered_encrypted_key, key, iv)
        if nk is None:
            self.show_popup("Error", "Failed to decrypt ENK.")
            return
        
        # Extract PK from the NK
        pk = extract_pk_from_nk(nk)

        # Check if extracted pk matches stored pk
        if pk == self.get_user_pk(username):  # Assuming you have a function to get the stored pk from the user data
            self.show_popup("Success", "Transaction Successful!")
            self.pin_popup.dismiss()
        else:
            self.show_popup("Error", "Incorrect PIN or Public Key. Please try again.")

    def get_user_pk(self, username):
        """Retrieve the stored public key (pk) for the user."""
        # This should retrieve the stored pk from a database or file
        pk_file = f'{username}_pk.dat'
        if os.path.exists(pk_file):
            with open(pk_file, 'r') as file:
                return file.read().strip()
        return None

    def show_popup(self, title, message):
        popup = Popup(title=title, content=Label(text=message), size_hint=(None, None), size=(200, 100))
        popup.open()


# Decrypt ENK function (already provided in your code):
def decrypt_enk(enk, key, iv):
    try:
        # Decode the encrypted NK from base64
        encrypted_nk = base64.b64decode(enk)
        
        # Create AES cipher object
        cipher = AES.new(key, AES.MODE_CBC, iv)
        
        # Decrypt the encrypted NK and unpad it
        nk = unpad(cipher.decrypt(encrypted_nk), AES.block_size)
        return nk.decode('utf-8')  # Convert from bytes to string
    except (binascii.Error, ValueError) as e:
        print(f"Error decrypting ENK: {e}")
        return None

# Function to extract the public key (PK) from the NK (user private key and salt)
def extract_pk_from_nk(nk):
    try:
        # In this example, assume the PK is stored as part of the NK (modify as per your data structure)
        # Here we just return the first 16 characters of NK as a simulated public key.
        # You may need to adjust this based on how the public key is stored in NK.
        return nk[:16]  # Extract first 16 characters (example, adjust as needed)
    except Exception as e:
        print(f"Error extracting PK: {e}")
        return None


class MyApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(SendMoneyScreen(name='send_money_screen'))  # Add the SendMoneyScreen
        sm.current = 'send_money_screen'  # Start with the SendMoneyScreen
        return sm


if __name__ == "__main__":
    MyApp().run()