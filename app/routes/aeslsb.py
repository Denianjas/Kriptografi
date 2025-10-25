from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from app.utils.aesutil import enkripsi, dekripsi
from app.utils.lsbutil import encode_lsb,decode_lsb
import base64

router = APIRouter()

@router.post("/enkripsi")
async def aeslsbekrip(
    file: UploadFile = File(...),
    text: str = Form(...),
    key: str = Form(...)
):
    try:
        key_bit = key.encode('utf-8')
        image_bit = await file.read()

        if not text:
            return JSONResponse(status_code=400, content={"error": "message tidak boleh kosong."})

        if len(key_bit) not in {16, 24, 32}:
            return JSONResponse(status_code=400, content={"error": "Key harus 16, 24, atau 32 bytes."})
        
        if file.content_type not in ["image/png", "image/jpeg"]:
            return JSONResponse(status_code=400, content={"error": "Hanya file PNG dan JPEG yang diizinkan."})

        text_enkrip = enkripsi(text, key_bit)
        if not text_enkrip:
            return JSONResponse(status_code=400, content={"error": "Enkripsi gagal."})

        imgae_enkrip = encode_lsb(image_bit, text_enkrip)

        encoded_base64 = base64.b64encode(imgae_enkrip).decode('utf-8')
        data_url = f"data:image/png;base64,{encoded_base64}"

        return {
            "preview": data_url,
            "filename": "test.png",
            "text_enkripsi": text_enkrip,
        }

    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

@router.post("/dekripsi")
async def aeslsbdekrip(
    file: UploadFile = File(...),
    key: str = Form(...)
):
    try:
        key_bit = key.encode('utf-8')
        image_bit = await file.read()

        if len(key_bit) not in {16, 24, 32}:
            return JSONResponse(status_code=400, content={"error": "Key harus 16, 24, atau 32 bytes."})
        
        if file.content_type not in ["image/png", "image/jpeg"]:
            return JSONResponse(status_code=400, content={"error": "Hanya file PNG dan JPEG yang diizinkan."})


        image_dekripsi = decode_lsb(image_bit).rstrip("ÿ")
        encode_text = dekripsi(image_dekripsi,key_bit)

        return{
            "text_enkripsi": image_dekripsi,
            "hasil_dekripsi": encode_text,
        }
    
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})
    