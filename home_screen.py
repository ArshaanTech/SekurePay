from kivy.uix.screenmanager import Screen
from kivy.uix.button import Button
from kivy.graphics import Rectangle, RoundedRectangle
from kivy.core.window import Window
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from Send_Money import SendMoneyScreen

# Set window size
Window.size = (750, 1334)

# Function to get the logged-in user from the file
def get_current_user():
    """Get the current logged-in user from the file."""
    try:
        with open("current_user.txt", "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        return None

class HomePage(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'home_screen'  # Give the screen a name

        # Layout setup
        layout = FloatLayout()
        layout2 = FloatLayout()

        # **Step 1**: Draw the blurred background image on the canvas.
        with self.canvas.before:
            self.rect = Rectangle(source='background.jpg', pos=self.pos, size=self.size)

        # **Step 2**: Update the background rectangle size and position when the window size changes.
        self.bind(size=self.update_rect, pos=self.update_rect)

        # **Step 3**: Create the white box layout with rounded corners that sits at the bottom of the screen.
        with self.canvas.before:
            self.background_box = RoundedRectangle(
                size=(self.width, 400),  # Set the size of the rounded box
                pos=(0, 0),  # Position the box at the bottom of the screen
                radius=[(25, 25), (25, 25), (0, 0), (0, 0)]  # Curved corners at top-left and top-right
            )

        # **Step 4**: Bind the rounded box layout to update dynamically with the screen size
        self.bind(size=self.update_box, pos=self.update_box)

        # **Step 5**: Add a button with an image (smsm.png) positioned in the second quarter from the left and above the white box
        button_width = 200  # Button width
        button_height = 100  # Button height

        # Add "Hello, User" label at the top of the screen
        username = get_current_user()  # Get the logged-in username
        if username:
            greeting_label = Label(
                text=f"Welcome, {username}",
                font_size=25,
                size_hint=(None, None),
                size=(self.width, 40),  # Label size
                pos=(50, self.height +600),  # Position at the top
                color=(1, 1, 1, 1)  # Text color (black)
            )
        layout.add_widget(greeting_label)

        box_layout = BoxLayout(orientation='vertical', spacing=30, size_hint=(None, None), size=(self.width*4, 300))
        box_layout.pos = (self.width/2.4, 100)

        # The first button is placed in the second quarter from the left and above the white box.
        self.senm = Button(
            background_normal='smsm.png', text='\n\n\n\n\n\nSend Money',font_size=(20),  # Use the image as the button's background
            size_hint=(None, None),  # Set specific size (fixed)
            on_press=self.on_senm_button_press,
            size=(button_width/1.8, button_height/1),  # Set the size of the button (normal size)
            pos=(self.width / 3, self.height / 2 + 400)  # Position the button in the second quarter from the left and above the white box
        )
        layout.add_widget(self.senm)  # Add the button to the layout
        
        self.reqm = Button(
            background_normal='rmrm.png', text='\n\n\n\n\n\nRequest Money',font_size=(20),  # Use the image as the button's background
            size_hint=(None, None),  # Set specific size (fixed)
            size=(button_width/1.4, button_height/0.8),  # Set the size of the button (normal size)
            pos=(self.width / 0.29 , self.height / 2 + 400)  # Position the button in the second quarter from the left and above the white box
        )
        layout2.add_widget(self.reqm)  # Add the button to the layout

        # **Step 6**: Create a BoxLayout for the three buttons inside the white rounded box
        box_layout = BoxLayout(orientation='vertical', spacing=30, size_hint=(None, None), size=(self.width*4, 300))
        box_layout.pos = (self.width/2.4, 100)  # Position the BoxLayout inside the white rounded box with some padding

        # Add buttons to the BoxLayout
        button1 = Button(text="Transfer History", size_hint_y=None, height=50)
        button2 = Button(text="Bank Balance", size_hint_y=None, height=50)
        button3 = Button(text="Security", size_hint_y=None, height=50)

        box_layout.add_widget(button1)
        box_layout.add_widget(button2)
        box_layout.add_widget(button3)

        layout.add_widget(box_layout)  # Add the box layout with buttons to the main layout
        
        profile_button_size = 80  # Define the size of the profile button (adjust as needed)
        
        self.profile_button = Button(
            background_normal='userprofile.png', # Set the profile image as the button's background
            size_hint=(None, None),
            size=(profile_button_size, profile_button_size),  # Set size of the button (icon size)
            pos=(self.width*6.5, self.height*(6.5))  # Position it at the top-right corner
        )
        
        layout.add_widget(self.profile_button)

        # Add the layout to the screen
        self.add_widget(layout)
        self.add_widget(layout2)

    def update_rect(self, instance, value):
        # Update the background rectangle size and position to match the layout's size
        self.rect.pos = self.pos
        self.rect.size = self.size

    def update_box(self, instance, value):
        # Update the position and size of the rounded box to stay at the bottom
        self.background_box.pos = (0, 0)  # Position at the bottom
        self.background_box.size = (self.width, 400)  # Set the size of the box
    
    def on_senm_button_press(self, instance):
        self.manager.current = 'send_money_screen'


class HomePageApp(App):
    def build(self):
        # Since we are testing HomePage independently, create a ScreenManager
        sm = ScreenManager()
        sm.add_widget(HomePage(name='home_screen'))  # Add HomePage to the ScreenManager
        sm.add_widget(SendMoneyScreen(name='send_money_screen'))
        sm.current = 'home_screen'  # Set HomePage as the starting screen
        return sm

# Run the app only if this file is executed directly
if __name__ == '__main__':
    HomePageApp().run()
