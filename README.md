# Resume Parsing API

Production-ready Resume Parsing API using FastAPI.

## Features

- Resume parsing via S3 URL
- OCR + Rule-based extraction
- Experience calculation
- Location & Address detection
- PAN / Aadhaar presence detection
- Safe auto-fill JSON output

## Tech Stack

- Python 3.10
- FastAPI
- EasyOCR + PaddleOCR
- Ubuntu 22.04

## Run Locally

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
