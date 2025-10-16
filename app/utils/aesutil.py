from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64

def enkripsi(pesan: str, key: bytes) -> str:
    cipher = AES.new(key, AES.MODE_EAX)
    nonce = cipher.nonce
    ciphertext, tag = cipher.encrypt_and_digest(pesan.encode('utf-8'))
    return base64.b64encode(nonce + ciphertext).decode('utf-8')

def dekripsi(encrypted_text: str, key: bytes) -> str:
    data = base64.b64decode(encrypted_text)
    nonce = data[:16]
    ciphertext = data[16:]
    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
    decrypted = cipher.decrypt(ciphertext)
    return decrypted.decode('utf-8')