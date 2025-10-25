from fastapi import APIRouter, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse
from pathlib import Path
import os, uuid, cv2, time, pickle
import numpy as np
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes

router = APIRouter()

BASE_STORAGE = Path("static")
ENCRYPTED_DIR = BASE_STORAGE / "encrypted"
DECRYPTED_DIR = BASE_STORAGE / "decrypted"

ENCRYPTED_DIR.mkdir(parents=True, exist_ok=True)
DECRYPTED_DIR.mkdir(parents=True, exist_ok=True)


def encrypt_bytes_to_file_visual(image_bytes: bytes, key: bytes, output_path: str):
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        raise ValueError("Gagal decode image")
    
    height, width, channels = img.shape
    pixel_data = img.flatten()
    
    # Generate IV
    iv = get_random_bytes(16)
    
    # Enkripsi pixel data
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted_data = cipher.encrypt(pad(pixel_data.tobytes(), AES.block_size))
    
    # Convert ke array
    encrypted_array = np.frombuffer(encrypted_data, dtype=np.uint8)
    
    # Adjust size ke ukuran original
    target_size = height * width * channels
    if len(encrypted_array) > target_size:
        encrypted_array = encrypted_array[:target_size]
    elif len(encrypted_array) < target_size:
        padding_arr = np.random.randint(0, 256, target_size - len(encrypted_array), dtype=np.uint8)
        encrypted_array = np.concatenate([encrypted_array, padding_arr])
    
    # Reshape ke bentuk gambar
    encrypted_img = encrypted_array.reshape(height, width, channels)
    
    # Save sebagai PNG (agar tidak ada kompresi)
    cv2.imwrite(output_path, encrypted_img)
    
    # Save metadata (IV dan shape)
    metadata = {
        'iv': iv,
        'shape': (height, width, channels),
        'mode': 'visual'
    }
    
    metadata_path = output_path + '.meta'
    with open(metadata_path, 'wb') as f:
        pickle.dump(metadata, f)
    
    return metadata_path


def decrypt_file_to_bytes_visual(encrypted_path: str, key: bytes) -> bytes:
    # Load metadata
    metadata_path = encrypted_path + '.meta'
    if not os.path.exists(metadata_path):
        raise ValueError("Metadata file tidak ditemukan")
    
    with open(metadata_path, 'rb') as f:
        metadata = pickle.load(f)
    
    iv = metadata['iv']
    original_shape = metadata['shape']
    
    # Load encrypted image
    encrypted_img = cv2.imread(encrypted_path)
    if encrypted_img is None:
        raise ValueError("Gagal membaca gambar terenkripsi")
    
    # Flatten
    encrypted_data = encrypted_img.flatten().tobytes()
    
    # Decrypt
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_padded = cipher.decrypt(encrypted_data)
    
    # Unpad
    try:
        decrypted_data = unpad(decrypted_padded, AES.block_size)
    except:
        decrypted_data = decrypted_padded
    
    # Reconstruct image
    height, width, channels = original_shape
    target_size = height * width * channels
    
    decrypted_array = np.frombuffer(decrypted_data[:target_size], dtype=np.uint8)
    decrypted_img = decrypted_array.reshape(height, width, channels)
    
    # Encode ke bytes
    _, buffer = cv2.imencode('.png', decrypted_img)
    return buffer.tobytes()


def calculate_correlation_coefficient(image, direction='horizontal'):
    if len(image.shape) == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    h, w = image.shape
    if direction == 'horizontal':
        x = image[:, :-1].flatten()
        y = image[:, 1:].flatten()
    elif direction == 'vertical':
        x = image[:-1, :].flatten()
        y = image[1:, :].flatten()
    elif direction == 'diagonal':
        x = image[:-1, :-1].flatten()
        y = image[1:, 1:].flatten()
    
    return float(np.corrcoef(x, y)[0, 1])


def calculate_entropy(image):
    if len(image.shape) == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    hist, _ = np.histogram(image.flatten(), bins=256, range=(0, 256))
    hist = hist / hist.sum()
    hist = hist[hist > 0]
    entropy = -np.sum(hist * np.log2(hist))
    return float(entropy)


def calculate_npcr_uaci(original, encrypted):
    if len(original.shape) == 3:
        original = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
    if len(encrypted.shape) == 3:
        encrypted = cv2.cvtColor(encrypted, cv2.COLOR_BGR2GRAY)
    
    h, w = original.shape
    total_pixels = h * w
    
    # NPCR - Number of Pixels Change Rate
    diff_pixels = np.sum(original != encrypted)
    npcr = (diff_pixels / total_pixels) * 100
    
    # UACI - Unified Average Changing Intensity
    uaci = np.sum(np.abs(original.astype(float) - encrypted.astype(float))) / (total_pixels * 255) * 100
    
    return float(npcr), float(uaci)


def calculate_mse_psnr(original, encrypted):
    if len(original.shape) == 3:
        original = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
    if len(encrypted.shape) == 3:
        encrypted = cv2.cvtColor(encrypted, cv2.COLOR_BGR2GRAY)
    
    mse = np.mean((original.astype(float) - encrypted.astype(float)) ** 2)
    
    if mse == 0:
        psnr = float('inf')
    else:
        max_pixel = 255.0
        psnr = 20 * np.log10(max_pixel / np.sqrt(mse))
    
    return float(mse), float(psnr)


def comprehensive_encryption_evaluation(original_bytes, encrypted_path):
    try:
        # Load original
        original_array = np.frombuffer(original_bytes, dtype=np.uint8)
        original_img = cv2.imdecode(original_array, cv2.IMREAD_COLOR)
        
        # Load encrypted (bisa dibuka karena masih format image)
        encrypted_img = cv2.imread(encrypted_path)
        
        if original_img is None or encrypted_img is None:
            return {"error": "Failed to load images"}
        
        # Convert to grayscale untuk analisis
        original_gray = cv2.cvtColor(original_img, cv2.COLOR_BGR2GRAY)
        encrypted_gray = cv2.cvtColor(encrypted_img, cv2.COLOR_BGR2GRAY)
        
        # metrik
        npcr, uaci = calculate_npcr_uaci(original_gray, encrypted_gray)
        mse, psnr = calculate_mse_psnr(original_gray, encrypted_gray)
        
        # Korelasi
        enc_corr_h = calculate_correlation_coefficient(encrypted_gray, 'horizontal')
        enc_corr_v = calculate_correlation_coefficient(encrypted_gray, 'vertical')
        enc_corr_d = calculate_correlation_coefficient(encrypted_gray, 'diagonal')
        
        # Entropy
        enc_entropy = calculate_entropy(encrypted_gray)
        orig_entropy = calculate_entropy(original_gray)
        
        # Generate assessment
        assessment_scores = []
        
        # Entropy assessment
        if enc_entropy >= 7.9:
            assessment_scores.append("✓ EXCELLENT - Entropy sangat tinggi")
        elif enc_entropy >= 7.5:
            assessment_scores.append("✓ GOOD - Entropy tinggi")
        else:
            assessment_scores.append("✗ WEAK - Entropy kurang optimal")
        
        # NPCR assessment
        if npcr >= 99.5:
            assessment_scores.append("✓ EXCELLENT - NPCR mendekati ideal")
        elif npcr >= 95:
            assessment_scores.append("✓ GOOD - NPCR baik")
        else:
            assessment_scores.append("✗ WEAK - NPCR kurang optimal")
        
        # Correlation assessment
        avg_corr = (abs(enc_corr_h) + abs(enc_corr_v) + abs(enc_corr_d)) / 3
        if avg_corr <= 0.1:
            assessment_scores.append("✓ EXCELLENT - Korelasi sangat rendah")
        elif avg_corr <= 0.3:
            assessment_scores.append("✓ GOOD - Korelasi rendah")
        else:
            assessment_scores.append("✗ WEAK - Korelasi masih tinggi")
        
        # Overall assessment
        excellent_count = len([s for s in assessment_scores if "EXCELLENT" in s])
        good_count = len([s for s in assessment_scores if "GOOD" in s])
        
        if excellent_count >= 2:
            overall = "🔒 HIGHLY SECURE"
        elif (excellent_count + good_count) >= 2:
            overall = "🔐 SECURE"
        else:
            overall = "⚠️ NEEDS IMPROVEMENT"
        
        evaluation = {
            "encryption_mode": "VISUAL AES-CBC",
            "description": "Gambar terenkripsi dapat dibuka sebagai file image dengan tampilan noise/static",
            
            "security_metrics": {
                "correlation_coefficient": {
                    "encrypted_horizontal": enc_corr_h,
                    "encrypted_vertical": enc_corr_v,
                    "encrypted_diagonal": enc_corr_d,
                    "average": avg_corr,
                    "original_horizontal": calculate_correlation_coefficient(original_gray, 'horizontal'),
                    "interpretation": "Nilai mendekati 0 menunjukkan enkripsi yang baik"
                },
                "information_entropy": {
                    "encrypted": enc_entropy,
                    "original": orig_entropy,
                    "max_possible": 8.0,
                    "interpretation": "Nilai mendekati 8 menunjukkan keacakan maksimum"
                },
                "differential_analysis": {
                    "npcr_percentage": npcr,
                    "uaci_percentage": uaci,
                    "npcr_ideal": 99.6094,
                    "uaci_ideal": 33.4635,
                    "interpretation": "NPCR mengukur persentase piksel yang berubah, UACI mengukur intensitas perubahan"
                },
                "quality_metrics": {
                    "mse": mse,
                    "psnr_db": psnr,
                    "interpretation": "MSE tinggi dan PSNR rendah menunjukkan perbedaan besar (enkripsi kuat)"
                }
            },
            
            "visual_properties": {
                "can_open_as_image": True,
                "appearance": "Random noise/static berwarna (seperti TV tanpa sinyal)",
                "format": "PNG (tanpa kompresi lossy)",
                "original_dimensions": f"{original_img.shape[1]}x{original_img.shape[0]}",
                "encrypted_dimensions": f"{encrypted_img.shape[1]}x{encrypted_img.shape[0]}"
            },
            
            "security_assessment": {
                "overall_rating": overall,
                "details": assessment_scores,
                "recommendation": "Enkripsi visual cocok untuk visualisasi dan demonstrasi, namun untuk keamanan maksimum gunakan enkripsi full binary."
            }
        }
        
        return evaluation
        
    except Exception as e:
        return {"error": str(e)}


# ============= API ROUTES =============
@router.post("/encrypt-image")
async def encrypt_image_route(
    request: Request,
    file: UploadFile = File(...),
    key: str = Form(...)
):
    """
    Enkripsi gambar dengan metode visual AES-CBC
    Hasil: File PNG yang bisa dibuka tapi tampilannya noise/static
    """
    try:
        key_bytes = key.encode("utf-8")
        if len(key_bytes) not in {16, 24, 32}:
            return JSONResponse(status_code=400, content={
                "error": "Key harus 16, 24, atau 32 bytes (karakter)."
            })

        if file.content_type not in ["image/png", "image/jpeg", "image/jpg"]:
            return JSONResponse(status_code=400, content={
                "error": "Hanya file PNG dan JPEG yang diizinkan."
            })

        image_bytes = await file.read()
        start_time = time.time()

        # Generate unique filename dengan extension .png
        unique_name = f"{uuid.uuid4().hex}_{file.filename}"
        unique_name = unique_name.rsplit('.', 1)[0] + '.png'
        
        out_path = ENCRYPTED_DIR / unique_name

        # Enkripsi visual
        encrypt_bytes_to_file_visual(image_bytes, key_bytes, str(out_path))
        
        # Evaluasi hasil enkripsi
        eval_result = comprehensive_encryption_evaluation(image_bytes, str(out_path))

        encryption_time = time.time() - start_time

        # efficiency metrics
        eval_result["efficiency_metrics"] = {
            "encryption_time_seconds": round(encryption_time, 4),
            "file_size_original_bytes": len(image_bytes),
            "file_size_encrypted_bytes": os.path.getsize(out_path),
            "throughput_kbps": round(len(image_bytes) / encryption_time / 1024, 2),
            "size_increase_percentage": round((os.path.getsize(out_path) - len(image_bytes)) / len(image_bytes) * 100, 2)
        }

        base_url = str(request.base_url).rstrip("/")
        file_url = f"{base_url}/static/encrypted/{unique_name}"

        return {
            "success": True,
            "message": "Gambar berhasil dienkripsi dengan AES Visual Mode",
            "encrypted_url": file_url,
            "filename": unique_name,
            "key_length": len(key_bytes) * 8,
            "algorithm": "AES-CBC",
            "evaluation": eval_result
        }
        
    except Exception as e:
        return JSONResponse(status_code=400, content={
            "success": False,
            "error": str(e)
        })


@router.post("/decrypt-image")
async def decrypt_image_route(
    request: Request,
    filename: str = Form(...),
    key: str = Form(...)
):
    try:
        key_bytes = key.encode("utf-8")
        if len(key_bytes) not in {16, 24, 32}:
            return JSONResponse(status_code=400, content={
                "error": "Key harus 16, 24, atau 32 bytes (karakter)."
            })

        enc_path = ENCRYPTED_DIR / filename
        if not enc_path.exists():
            return JSONResponse(status_code=404, content={
                "error": "File terenkripsi tidak ditemukan."
            })

        start_time = time.time()

        # Dekripsi
        plain_bytes = decrypt_file_to_bytes_visual(str(enc_path), key_bytes)

        decryption_time = time.time() - start_time

        # Save decrypted file
        decrypted_name = f"dec_{uuid.uuid4().hex}_{filename}"
        out_decrypted_path = DECRYPTED_DIR / decrypted_name
        with open(out_decrypted_path, "wb") as f:
            f.write(plain_bytes)

        # Evaluation
        eval_result = {
            "status": "success",
            "message": "Gambar berhasil didekripsi dan dipulihkan",
            "file_size_bytes": len(plain_bytes),
            "efficiency_metrics": {
                "decryption_time_seconds": round(decryption_time, 4),
                "file_size_encrypted_bytes": os.path.getsize(enc_path),
                "file_size_decrypted_bytes": len(plain_bytes),
                "throughput_kbps": round(len(plain_bytes) / decryption_time / 1024, 2)
            }
        }

        base_url = str(request.base_url).rstrip("/")
        decrypted_url = f"{base_url}/static/decrypted/{decrypted_name}"

        return {
            "success": True,
            "message": "Dekripsi berhasil! Gambar telah dipulihkan.",
            "decrypted_url": decrypted_url,
            "filename": decrypted_name,
            "evaluation": eval_result
        }
        
    except ValueError as e:
        return JSONResponse(status_code=400, content={
            "success": False,
            "error": f"Dekripsi gagal: {str(e)}. Pastikan key yang digunakan benar."
        })
    except Exception as e:
        return JSONResponse(status_code=400, content={
            "success": False,
            "error": str(e)
        })