from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from app.utils.aesutil import enkripsi, dekripsi
from app.utils.lsbutil import encode_lsb
import base64
from PIL import Image
import io

router = APIRouter()

@router.post("/enkripsi")
async def aeslsbekrip(
    file: UploadFile = File(...),
    key: str = Form(...),
    text: str = Form(...)
):
    try:
        key_bit = key.encode('utf-8')
        image_bit = await file.read()

        # Validasi input
        if not text:
            return JSONResponse(status_code=400, content={"error": "message tidak boleh kosong."})

        if len(key_bit) not in {16, 24, 32}:
            return JSONResponse(status_code=400, content={"error": "Key harus 16, 24, atau 32 bytes."})
        
        if file.content_type not in ["image/png", "image/jpeg"]:
            return JSONResponse(status_code=400, content={"error": "Hanya file PNG dan JPEG yang diizinkan."})

        # --- Enkripsi teks ---
        text_enkrip = enkripsi(text, key_bit)

        # --- Buka gambar dari bytes ---
        image_stream = io.BytesIO(image_bit)
        image = Image.open(image_stream)

        # --- LSB: sisipkan teks terenkripsi ke dalam gambar ---
        encoded_image = encode_lsb(image, text_enkrip)

        # --- Simpan hasil ke memory ---
        output_buffer = io.BytesIO()
        encoded_image.save(output_buffer, format="PNG")
        output_buffer.seek(0)

        # --- Konversi ke base64 untuk dikirim ke frontend ---
        encoded_b64 = base64.b64encode(output_buffer.read()).decode('utf-8')
        link = f"data:image/png;base64,{encoded_b64}"

        return {
            "preview": link,
            "filename": "test.png",
            "message_pre_encrypt": text_enkrip,
        }

    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})
