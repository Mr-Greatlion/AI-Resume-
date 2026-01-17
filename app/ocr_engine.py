from pdfminer.high_level import extract_text
from pdf2image import convert_from_path
import easyocr
import os
import uuid
import shutil

reader = easyocr.Reader(['en'], gpu=False)

TEMP_DIR = "temp_images"

def pdf_to_text(pdf_path):
    # 1️⃣ Try digital text first (FAST)
    try:
        text = extract_text(pdf_path)
        if text and len(text.strip()) > 100:
            return text
    except:
        pass

    # 2️⃣ OCR fallback (IMAGE-BASED PDF)
    os.makedirs(TEMP_DIR, exist_ok=True)
    text = ""

    images = convert_from_path(pdf_path, dpi=300)

    for img in images:
        img_name = f"{TEMP_DIR}/{uuid.uuid4()}.jpg"
        img.save(img_name, "JPEG")

        result = reader.readtext(img_name, detail=0, paragraph=True)
        text += " ".join(result) + " "

        os.remove(img_name)

    # Cleanup folder if empty
    if not os.listdir(TEMP_DIR):
        shutil.rmtree(TEMP_DIR, ignore_errors=True)

    return text
