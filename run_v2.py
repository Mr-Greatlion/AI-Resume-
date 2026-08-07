"""
Entry point for v2.
Run: python run_v2.py
  or: uvicorn app_v2.main:app --port 8001 --reload
"""
import uvicorn
if __name__ == "__main__":
    uvicorn.run("app_v2.main:app", host="0.0.0.0", port=8001, reload=True)
