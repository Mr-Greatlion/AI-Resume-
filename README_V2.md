# Resume Extractor v2

Sits in the same repo as v1. **v1 is untouched.**

## What's new in v2
- Clean structured output (16 fields)
- Processing status: `success` / `partial` / `failed`
- Stores last 5 records on VPS (auto-purges older ones)
- Full Swagger docs at `/resume-extractor-v2/docs`
- Runs on port 8001 (v1 stays on 8000)

## URLs (once deployed)
| URL | What |
|---|---|
| `avrenergies.com/resume-extractor` | v1 — unchanged |
| `avrenergies.com/resume-extractor-v2` | v2 UI |
| `avrenergies.com/resume-extractor-v2/docs` | Swagger |
| `avrenergies.com/resume-extractor-v2/health` | Health check |
| `avrenergies.com/resume-extractor-v2/records?x_api_key=KEY` | Last 5 records |

## Local run (Swagger)
```bash
pip install -r requirements_v2.txt
set RESUME_V2_KEY=avr_dev_123
uvicorn app_v2.main:app --port 8001 --reload
# open http://localhost:8001/resume-extractor-v2/docs
```

## Deploy on VPS
```bash
bash deploy_v2.sh
# then add nginx_v2_location.conf into nginx server{} block
```
