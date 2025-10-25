from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from pathlib import Path

NONCE_SIZE = 16  # EAX nonce length (we'll read cipher.nonce len)
TAG_SIZE = 16    # tag size

def encrypt_bytes_to_file(image_bytes: bytes, key: bytes, out_path: str) -> None:
    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(image_bytes)
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(cipher.nonce)
        f.write(tag)
        f.write(ciphertext)


def decrypt_file_to_bytes(encrypted_path: str, key: bytes) -> bytes:
    with open(encrypted_path, "rb") as f:
        nonce = f.read(NONCE_SIZE)
        tag = f.read(TAG_SIZE)
        ciphertext = f.read()

    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
    plain = cipher.decrypt_and_verify(ciphertext, tag)
    return plain
