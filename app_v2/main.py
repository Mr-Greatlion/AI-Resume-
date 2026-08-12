"""
AVR Resume Extractor — v2
=========================
Route prefix : /resume-extractor-v2
Port         : 8001  (v1 stays on 8000 — never touched)
Swagger      : /resume-extractor-v2/docs

Sits in the same GitHub repo under app_v2/
v1 code in app/ is 100% untouched.
"""
from __future__ import annotations

import os, shutil, uuid
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from app_v2.config  import (
    API_KEY, ALLOWED_EXT, MAX_FILE_MB, MAX_RECORDS,
    UPLOAD_DIR, API_PREFIX
)
from app_v2.database import init_db, save_record, list_records, get_record
from app_v2 import extractor


# ── lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    if API_KEY in ("avr_v2_change_me", "avr_dev_key"):
        print("[WARN] RESUME_V2_KEY is not set — using insecure default key!")
    yield


# ── app ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title       = "AVR Resume Extractor v2",
    description = (
        "Upload a resume (PDF / DOCX / image / TXT) and get 16 structured "
        "fields back instantly.\n\n"
        "**Auth**: pass `x-api-key` header for admin endpoints.\n\n"
        "**Storage**: last 5 records kept on VPS — older ones auto-deleted.\n\n"
        "**v1 is untouched** — this runs on port 8001 alongside v1 on 8000."
    ),
    version     = "2.0.0",
    docs_url    = f"{API_PREFIX}/docs",
    openapi_url = f"{API_PREFIX}/openapi.json",
    redoc_url   = None,
    lifespan    = lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins  = ["https://avrenergies.com",
                      "https://www.avrenergies.com",
                      "http://localhost", "http://localhost:8001"],
    allow_credentials = True,
    allow_methods  = ["*"],
    allow_headers  = ["*"],
)


@app.exception_handler(Exception)
async def _global_err(request: Request, exc: Exception):
    return JSONResponse(
        status_code = 500,
        content     = {
            "error":  type(exc).__name__,
            "detail": str(exc),
        },
    )


def _require_key(x_api_key: str | None = None):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


# ── 1. Health ─────────────────────────────────────────────────────────────────

@app.get(
    f"{API_PREFIX}/health",
    tags=["Health"],
    summary="Health check — no auth needed",
)
def health():
    """
    Returns server status, version, accepted file formats, and
    how many records are currently stored on the VPS.
    """
    return {
        "status":          "running",
        "version":         "2.0.0",
        "port":            8001,
        "v1_port":         8000,
        "accepted_formats": sorted(ALLOWED_EXT),
        "max_records_kept": MAX_RECORDS,
        "upload_dir":      UPLOAD_DIR,
    }


# ── 2. Extract (the main endpoint) ───────────────────────────────────────────

@app.post(
    f"{API_PREFIX}/extract",
    tags=["Extract"],
    summary="Upload resume → get 16 extracted fields",
)
async def extract_resume(
    file: Annotated[UploadFile, File(description="Resume file: PDF, DOCX, JPG, PNG, TXT")]
):
    """
    **Upload a resume and get structured data back.**

    No API key needed — this is the public-facing endpoint.

    ### Response fields
    | Field | Description |
    |---|---|
    | `uid` | Unique ID for this record (use to fetch later) |
    | `status` | `success` / `partial` / `failed` |
    | `duration_ms` | How long extraction took |
    | `extract_method` | `pdf` / `pdf-ocr` / `docx` / `image` / `txt` |
    | `fields` | All 16 extracted fields |
    | `error` | Error message if status is failed |

    ### Field status colours (for UI)
    - **Green** = regex match (email, phone, PAN, Aadhaar, pincode) — high confidence
    - **Yellow** = heuristic match (name, job title, education, city) — please verify
    - **Red** = not found — fill manually
    """
    # validate
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(
            status_code = 400,
            detail      = f"Unsupported format '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXT))}"
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file uploaded")
    if len(content) > MAX_FILE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File exceeds {MAX_FILE_MB} MB limit")

    # save to disk
    uid         = uuid.uuid4().hex
    stored_name = f"{uid}{ext}"
    stored_path = os.path.join(UPLOAD_DIR, stored_name)
    with open(stored_path, "wb") as fh:
        fh.write(content)

    # extract
    fields, status, method, ms, error = extractor.run(stored_path, file.filename or stored_name)

    # persist (auto-purges old records)
    save_record(uid, file.filename or stored_name, stored_path,
                fields, status, ms, error)

    return {
        "uid":            uid,
        "filename":       file.filename,
        "status":         status,
        "duration_ms":    ms,
        "extract_method": method,
        "error":          error,
        "stored_on_vps":  True,
        "fields":         fields,
    }


# ── 3. List stored records (admin) ───────────────────────────────────────────

@app.get(
    f"{API_PREFIX}/records",
    tags=["Admin"],
    summary="List last 5 stored records — requires API key",
)
def records(x_api_key: str | None = Query(default=None, description="Admin API key")):
    """
    Returns the last **5** parsed records stored on the VPS.
    Older records are automatically purged when a new one comes in.

    **Auth**: pass `x_api_key` as a query param or header.
    """
    _require_key(x_api_key)
    rows = list_records()
    return {
        "total":       len(rows),
        "max_kept":    MAX_RECORDS,
        "records": [
            {
                "uid":        r["uid"],
                "filename":   r["filename"],
                "status":     r["proc_status"],
                "duration_ms":r["extract_ms"],
                "created_at": r["created_at"],
                "fields":     r["fields"],
            }
            for r in rows
        ],
    }


# ── 4. Get one record (admin) ─────────────────────────────────────────────────

@app.get(
    f"{API_PREFIX}/records/{'{uid}'}",
    tags=["Admin"],
    summary="Get one stored record by UID — requires API key",
)
def get_one(
    uid: str,
    x_api_key: str | None = Query(default=None, description="Admin API key"),
):
    """Fetch a single stored record by its UID."""
    _require_key(x_api_key)
    r = get_record(uid)
    if not r:
        raise HTTPException(status_code=404, detail=f"Record '{uid}' not found")
    return {
        "uid":          r["uid"],
        "filename":     r["filename"],
        "status":       r["proc_status"],
        "duration_ms":  r["extract_ms"],
        "error":        r["error_msg"],
        "created_at":   r["created_at"],
        "fields":       r["fields"],
    }


# ── 5. Frontend UI ────────────────────────────────────────────────────────────

@app.get(f"{API_PREFIX}", response_class=HTMLResponse, include_in_schema=False)
@app.get(f"{API_PREFIX}/", response_class=HTMLResponse, include_in_schema=False)
def frontend():
    return _HTML

# ── Embedded frontend HTML ────────────────────────────────────────────────────

_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Resume Extractor v2 — AVR Energies</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,-apple-system,sans-serif;background:#f0f2f5;color:#222}
header{background:#1a3f6f;color:#fff;padding:14px 32px;display:flex;align-items:center;gap:16px}
.logo{font-size:20px;font-weight:700;letter-spacing:.5px}
.logo span{color:#e05a2b}
.v2tag{background:#e05a2b;color:#fff;font-size:11px;font-weight:700;padding:2px 8px;border-radius:10px;margin-left:8px;vertical-align:middle}
.sub{font-size:12px;opacity:.7;margin-top:2px}
.wrap{max-width:980px;margin:28px auto;padding:0 16px;display:grid;grid-template-columns:1fr 1fr;gap:20px}
@media(max-width:640px){.wrap{grid-template-columns:1fr}}
.card{background:#fff;border-radius:12px;border:1px solid #dde1e7;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.06)}
.ch{padding:13px 18px;border-bottom:1px solid #eee;font-size:13px;font-weight:600;color:#1a3f6f;display:flex;align-items:center;gap:8px}
.cb{padding:18px}
.drop{border:2px dashed #c5cae9;border-radius:10px;padding:36px 16px;text-align:center;cursor:pointer;transition:all .2s}
.drop:hover,.drop.over{border-color:#1a3f6f;background:#f0f4ff}
.drop-icon{font-size:34px;margin-bottom:10px}
.drop p{color:#555;font-size:14px}
.drop small{color:#999;font-size:11px;display:block;margin-top:5px}
#fi{display:none}
.fname{text-align:center;font-size:12px;color:#555;margin:8px 0;min-height:18px}
.btn{width:100%;padding:11px;background:#1a3f6f;color:#fff;border:none;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;transition:background .2s;margin-top:4px}
.btn:hover{background:#15305a}
.btn:disabled{background:#aaa;cursor:not-allowed}
.sbar{display:none;align-items:center;gap:8px;padding:9px 12px;border-radius:8px;margin-top:12px;font-size:12px;font-weight:500}
.sbar.show{display:flex}
.sbar.loading{background:#e3f2fd;color:#1565c0;border:1px solid #90caf9}
.sbar.success{background:#e8f5e9;color:#1b5e20;border:1px solid #a5d6a7}
.sbar.partial{background:#fffde7;color:#f57f17;border:1px solid #fff176}
.sbar.failed{background:#ffebee;color:#b71c1c;border:1px solid #ef9a9a}
.spin{width:14px;height:14px;border:2px solid #90caf9;border-top-color:#1565c0;border-radius:50%;animation:sp .7s linear infinite;flex-shrink:0}
@keyframes sp{to{transform:rotate(360deg)}}
.empty{text-align:center;padding:36px 16px;color:#bbb}
.empty-icon{font-size:36px;margin-bottom:8px}
.empty p{font-size:13px}
.fgrid{display:grid;grid-template-columns:1fr 1fr;gap:0}
.fr{display:flex;align-items:flex-start;gap:7px;padding:7px 0;border-bottom:1px solid #f5f5f5;font-size:12px}
.fr:last-child{border-bottom:none}
.fd{width:7px;height:7px;border-radius:50%;flex-shrink:0;margin-top:3px}
.ok{background:#43a047}
.low{background:#ffa000}
.miss{background:#e53935}
.fl{color:#777;min-width:90px;flex-shrink:0}
.fv{color:#111;font-weight:500;word-break:break-all}
.fv.empty{color:#ccc;font-style:italic;font-weight:400}
.meta{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px}
.mtag{background:#f5f5f5;border:1px solid #e0e0e0;border-radius:10px;font-size:11px;padding:3px 9px;color:#555}
.mtag.ok{background:#e8f5e9;border-color:#a5d6a7;color:#1b5e20}
.mtag.partial{background:#fffde7;border-color:#fff176;color:#f57f17}
.mtag.failed{background:#ffebee;border-color:#ef9a9a;color:#b71c1c}
.api-note{margin-top:16px;padding:10px 12px;background:#f5f5f5;border-radius:8px;font-size:11px;color:#666;line-height:1.6}
.api-note a{color:#1a3f6f;text-decoration:none;font-weight:600}
</style>
</head>
<body>
<header>
  <div>
    <div class="logo">AVR <span>Energies</span> <span class="v2tag">v2</span></div>
    <div class="sub">Resume Data Extractor — Upload once, get structured fields instantly</div>
  </div>
</header>

<div class="wrap">
  <div class="card">
    <div class="ch">📤 Upload Resume</div>
    <div class="cb">
      <div class="drop" id="drop" onclick="document.getElementById('fi').click()">
        <div class="drop-icon">📄</div>
        <p>Click or drag &amp; drop a resume</p>
        <small>PDF · DOCX · JPG · PNG · TXT &nbsp;·&nbsp; Max 10 MB</small>
      </div>
      <input type="file" id="fi" accept=".pdf,.docx,.jpg,.jpeg,.png,.txt">
      <div class="fname" id="fname"></div>
      <button class="btn" id="btn" disabled onclick="doUpload()">Extract Data</button>
      <div class="sbar" id="sbar">
        <div class="spin" id="spin" style="display:none"></div>
        <span id="smsg"></span>
      </div>
      <div class="api-note">
        🔗 <a href="/resume-extractor-v2/docs" target="_blank">Open Swagger API docs</a>
        &nbsp;·&nbsp; POST <code>/resume-extractor-v2/extract</code>
      </div>
    </div>
  </div>

  <div class="card">
    <div class="ch">📋 Extracted Fields</div>
    <div class="cb" id="res">
      <div class="empty">
        <div class="empty-icon">🔍</div>
        <p>Upload a resume to see extracted fields</p>
      </div>
    </div>
  </div>
</div>

<script>
const BASE="/resume-extractor-v2";
let sel=null;
const fi=document.getElementById("fi");
const drop=document.getElementById("drop");
const btn=document.getElementById("btn");
const fname=document.getElementById("fname");
const sbar=document.getElementById("sbar");
const smsg=document.getElementById("smsg");
const spin=document.getElementById("spin");
const res=document.getElementById("res");

const LABELS={
  name:"Name",job_title:"Job Title",education:"Education",
  experience:"Experience",emails:"Email(s)",phones:"Phone(s)",
  address:"Address",city:"City",state:"State",country:"Country",
  pincode:"Pincode",pan:"PAN",aadhaar:"Aadhaar",
  current_location:"Location",is_employee:"Type",applied_date:"Applied"
};
const STRONG=new Set(["emails","phones","pan","aadhaar","pincode"]);

fi.onchange=()=>pick(fi.files[0]);
drop.ondragover=e=>{e.preventDefault();drop.classList.add("over")};
drop.ondragleave=()=>drop.classList.remove("over");
drop.ondrop=e=>{e.preventDefault();drop.classList.remove("over");if(e.dataTransfer.files[0])pick(e.dataTransfer.files[0])};

function pick(f){
  sel=f;
  fname.textContent=f.name+" ("+(f.size/1024).toFixed(0)+" KB)";
  btn.disabled=false;
  setS("","");
}
function setS(type,msg){
  sbar.className="sbar"+(type?" show "+type:"");
  smsg.textContent=msg;
  spin.style.display=type==="loading"?"block":"none";
}
function dot(k,v){
  if(!v||(Array.isArray(v)&&!v.length))return"miss";
  return STRONG.has(k)?"ok":"low";
}
function disp(v){
  if(!v)return["not found",true];
  if(Array.isArray(v))return v.length?[v.join(", "),false]:["not found",true];
  return[v,false];
}
function esc(s){return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")}

async function doUpload(){
  if(!sel)return;
  btn.disabled=true;
  setS("loading","Uploading and extracting — please wait…");
  res.innerHTML='<div class="empty"><div class="spin" style="width:32px;height:32px;border-width:3px;margin:0 auto 16px"></div><p>Processing…</p></div>';
  try{
    const fd=new FormData();fd.append("file",sel);
    const r=await fetch(BASE+"/extract",{method:"POST",body:fd});
    const d=await r.json();
    if(!r.ok){setS("failed","Error: "+(d.detail||d.error||"Unknown"));res.innerHTML='<div class="empty"><p style="color:#b71c1c">'+esc(d.detail||"Extraction failed")+'</p></div>';btn.disabled=false;return;}
    const cls=d.status==="success"?"success":d.status==="partial"?"partial":"failed";
    const lbl={success:"✓ Parsed successfully",partial:"⚠ Partial result",failed:"✗ Could not extract"}[d.status]||d.status;
    setS(cls,lbl+" · "+d.duration_ms+"ms · "+d.extract_method);
    renderFields(d);
  }catch(e){setS("failed","Network error: "+e.message);}
  btn.disabled=false;
}

function renderFields(d){
  const f=d.fields||{};
  let h='<div class="meta">';
  h+='<span class="mtag '+d.status+'">'+d.status.toUpperCase()+'</span>';
  h+='<span class="mtag">'+d.duration_ms+'ms</span>';
  h+='<span class="mtag">'+d.extract_method+'</span>';
  h+='<span class="mtag">UID: '+d.uid.slice(0,8)+'…</span>';
  h+='<span class="mtag ok">Stored on VPS ✓</span>';
  h+='</div><div class="fgrid">';
  for(const[k,lbl]of Object.entries(LABELS)){
    const[v,empty]=disp(f[k]);
    h+='<div class="fr"><div class="fd '+dot(k,f[k])+'"></div>';
    h+='<div class="fl">'+lbl+'</div>';
    h+='<div class="fv'+(empty?" empty":"")+'">'+esc(v)+'</div></div>';
  }
  h+='</div>';
  res.innerHTML=h;
}
</script>
</body>
</html>"""
