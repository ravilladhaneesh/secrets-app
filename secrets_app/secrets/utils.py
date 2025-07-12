from cryptography.fernet import Fernet

def encrypt_secret(data, key):

    if data:
        fernet = Fernet(key)
        return fernet.encrypt(data.encode())
    return None
    

def decrypt_secret(encrypted_data, key):
    if encrypted_data:
        fernet = Fernet(key)
        return fernet.decrypt(encrypted_data).decode()
    return None