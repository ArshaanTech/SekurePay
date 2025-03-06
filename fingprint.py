from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Rectangle
from kivy.core.window import Window
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.screenmanager import Screen, ScreenManager

Window.size = (750, 1334)

class FingprintScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'fingprint'  # Name the screen as 'fingprint'

        # Set up the layout (using FloatLayout)
        layout = FloatLayout()

        # **Step 1**: Draw the blurred background image on the canvas.
        with self.canvas.before:
            self.rect = Rectangle(source='background.jpg', pos=self.pos, size=self.size)

        # **Step 2**: Update the background rectangle size and position when the window size changes.
        self.bind(size=self.update_rect, pos=self.update_rect)

        # **Step 3**: Add a Label
        label = Label(text="Press your registered finger against the sensor", size_hint=(None, None), size=(520,50),font_size=25,)
        label.pos = (self.width,300)
        layout.add_widget(label)

        # **Step 4**: Add an Image widget for the fingerprint symbol
        self.fingerprint_image = Image(source='fingsymb.png', size_hint=(None, None), size=(170, 250))
        self.fingerprint_image.pos = (self.width + 170, 400)
        layout.add_widget(self.fingerprint_image)


        # Add the layout to the screen
        self.add_widget(layout)

    def update_rect(self, instance, value):
        # Update the background rectangle size and position to match the layout's size
        self.rect.pos = self.pos
        self.rect.size = self.size

    # def check_fingerprint(self, instance):
        # This is where you would integrate actual fingerprint verification logic.
        # For now, we'll just simulate a success or failure with a random choice.

        # import random
        # result = random.choice(['success', 'failure'])  # Simulate a random result (success or failure)

        # if result == 'success':
        #     self.fingerprint_image.source = 'corfingsymb.png'  # Change to correct image
        # else:
        #     self.fingerprint_image.source = 'wrongfingsymb.png'  # Change to wrong image

        # # You can also add logic to reset the image after some time or based on user interaction

class FingprintApp(App):
    def build(self):
        # Create a ScreenManager and add the FingprintScreen
        sm = ScreenManager()
        sm.add_widget(FingprintScreen(name='fingprint'))  # Add FingprintScreen to the ScreenManager
        sm.current = 'fingprint'  # Set FingprintScreen as the starting screen
        return sm

# Run the app only if this file is executed directly
if __name__ == '__main__':
    FingprintApp().run()
