import base64
import binascii
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import os

# Function to decrypt the ENK (Encrypted NK)
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
