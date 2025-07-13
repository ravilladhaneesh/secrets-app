from cryptography.fernet import Fernet

def encrypt_secret(data, key):
    key = key.encode() if isinstance(key, str) else key
    if data:
        fernet = Fernet(key)
        return fernet.encrypt(data.encode())
    return None
    

def decrypt_secret(encrypted_data, key):
    key = key.encode('utf-8') if isinstance(key, str) else key
    if encrypted_data:
        fernet = Fernet(key)
        return fernet.decrypt(encrypted_data).decode()
    return None