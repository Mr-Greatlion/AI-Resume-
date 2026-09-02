"""
Local entry point for v2.
    python run_v2.py
    or: uvicorn app_v2.main:app --port 8001 --reload
Swagger: http://localhost:8001/resume-extractor-v2/docs
UI:      http://localhost:8001/resume-extractor-v2/
"""
import os
import uvicorn

if __name__ == "__main__":
    os.environ.setdefault("V2_BASE_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "v2_data"))
    uvicorn.run("app_v2.main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8001")), reload=True)
