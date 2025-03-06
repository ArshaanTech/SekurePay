import os

# Define a global variable to store the logged-in user's information
current_user = None

# Define the file path to store the current user
CURRENT_USER_FILE = 'current_user.txt'

def save_current_user(username):
    """Save the current logged-in user to a file."""
    with open(CURRENT_USER_FILE, "w") as file:
        file.write(username)

def get_current_user():
    """Get the current logged-in user from the file."""
    if os.path.exists(CURRENT_USER_FILE):
        with open(CURRENT_USER_FILE, "r") as file:
            return file.read().strip()
    return None  # If the file doesn't exist, return None