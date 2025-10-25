from PIL import Image
import io

def encode_lsb(image_bytes: bytes, message: str) -> bytes:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    binary_message = ''.join(format(ord(c), '08b') for c in message)
    binary_message += '11111110'

    pixels = list(img.getdata())
    new_pixels = []
    data_index = 0

    for pixel in pixels:
        r, g, b = pixel
        if data_index < len(binary_message):
            r = (r & ~1) | int(binary_message[data_index])
            data_index += 1
        if data_index < len(binary_message):
            g = (g & ~1) | int(binary_message[data_index])
            data_index += 1
        if data_index < len(binary_message):
            b = (b & ~1) | int(binary_message[data_index])
            data_index += 1
        new_pixels.append((r, g, b))

    img.putdata(new_pixels)

    output = io.BytesIO()
    img.save(output, format='PNG', optimize=True)
    output.seek(0)
    return output.getvalue()

def decode_lsb(image_bytes: bytes) -> str:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    pixels = list(img.getdata())

    binary_message = ""
    for pixel in pixels:
        for color in pixel:
            binary_message += str(color & 1)

    message = ""
    for i in range(0, len(binary_message), 8):
        byte = binary_message[i:i+8]
        if byte == '11111110':
            break
        message += chr(int(byte, 2))
    return message