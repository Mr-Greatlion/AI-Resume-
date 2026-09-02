"""Embedded reference UI for v2 — served at API_PREFIX. Pure HTML/CSS/JS, no build step."""

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Add Candidate — Resume Data Extractor v2</title>
<style>
:root{--bg:#0f1115;--card:#161920;--card2:#1b1f28;--line:#262b36;--text:#e6e8ee;--muted:#8b93a7;--muted2:#5d6578;
 --blue:#2f7cf6;--blue2:#2668d0;--green:#22c55e;--amber:#f59e0b;--red:#ef4444;--input:#11141b;--radius:10px}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Inter,system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--text);font-size:13px}
.page{max-width:1500px;margin:0 auto;padding:26px 28px 40px}
h1{font-size:22px;font-weight:700;letter-spacing:-.2px}
.sub{color:var(--muted);margin-top:4px;font-size:12.5px}
.card{margin-top:18px;background:var(--card);border:1px solid var(--line);border-radius:12px;overflow:hidden}
.card-h{display:flex;align-items:center;justify-content:space-between;padding:13px 18px;border-bottom:1px solid var(--line)}
.card-h h2{font-size:14px;font-weight:600}
.chip{font-size:11.5px;padding:4px 10px;border-radius:6px;border:1px solid var(--line);background:var(--card2);color:var(--muted);display:inline-flex;align-items:center;gap:6px}
.chip.ok{color:#b7f5cd;border-color:#1f6b3d;background:#0f2a1c}
.chip.busy{color:#bcd6ff;border-color:#2b4c8c;background:#101d33}
.chip.err{color:#ffc9c9;border-color:#7a2a2a;background:#2b1212}
.iconbtn{background:none;border:1px solid var(--line);color:var(--muted);border-radius:6px;width:28px;height:26px;cursor:pointer;margin-left:8px}
.iconbtn:hover{color:var(--text);border-color:var(--muted2)}
.split{display:grid;grid-template-columns:1fr 1fr;min-height:640px}
.split.swap .left{order:2}.split.swap .right{order:1;border-right:0;border-left:1px solid var(--line)}
.left{border-right:1px solid var(--line);display:flex;flex-direction:column}
.thead{display:grid;grid-template-columns:34% 66%;padding:11px 16px;border-bottom:1px solid var(--line);font-weight:600;font-size:12.5px}
.rows{flex:1;overflow:auto;max-height:70vh}
.sec{background:var(--card2);color:var(--muted);font-size:10.5px;font-weight:700;letter-spacing:.8px;padding:8px 16px;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.row{display:grid;grid-template-columns:34% 66%;border-bottom:1px solid var(--line);align-items:start}
.row.missing{background:rgba(239,68,68,.05)}
.row.low{background:rgba(245,158,11,.04)}
.cell-l{padding:12px 14px 12px 16px;display:flex;gap:10px;align-items:flex-start}
.cell-r{padding:10px 14px}
.dot{width:20px;height:20px;border-radius:50%;flex-shrink:0;border:1.5px solid var(--line);background:var(--input);display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;margin-top:1px}
.dot.ok{border-color:#1f6b3d;background:#0f2a1c;color:var(--green)}
.dot.low{border-color:#6b4a0f;background:#2a200f;color:var(--amber)}
.dot.miss{border-color:#7a2a2a;background:#2b1212;color:var(--red)}
.lbl{font-weight:600;font-size:12.5px}
.lbl .req{color:var(--red);margin-left:3px}
.val{color:var(--muted);font-size:12px;margin-top:3px;word-break:break-word;line-height:1.45}
.val.miss{color:#f87171}.val.src{color:var(--muted2);font-size:10.5px;margin-top:2px}
input,select,textarea{width:100%;background:var(--input);border:1px solid var(--line);color:var(--text);border-radius:8px;padding:8px 10px;font-size:12.5px;outline:none;font-family:inherit}
input:focus,select:focus,textarea:focus{border-color:var(--blue)}
input::placeholder,textarea::placeholder{color:var(--muted2)}
select{appearance:none;background-image:linear-gradient(45deg,transparent 50%,var(--muted) 50%),linear-gradient(135deg,var(--muted) 50%,transparent 50%);background-position:calc(100% - 15px) 55%,calc(100% - 10px) 55%;background-size:5px 5px,5px 5px;background-repeat:no-repeat;padding-right:28px}
textarea{min-height:58px;resize:vertical}
.inline{display:flex;gap:6px;align-items:center;margin-bottom:6px}
.inline:last-child{margin-bottom:0}
.inline .cc{width:82px;flex-shrink:0}
.btn{border:none;border-radius:8px;padding:8px 12px;font-size:12.5px;font-weight:600;cursor:pointer;font-family:inherit;white-space:nowrap}
.btn.blue{background:var(--blue);color:#fff}.btn.blue:hover{background:var(--blue2)}
.btn.blue:disabled{background:#2a3a5a;color:#7e8aa3;cursor:not-allowed}
.btn.ghost{background:transparent;border:1px solid var(--line);color:var(--text)}.btn.ghost:hover{border-color:var(--muted2)}
.btn.red{background:transparent;border:1px solid #7a2a2a;color:#f87171}.btn.red:hover{background:#2b1212}
.btn.sq{width:34px;padding:8px 0;flex-shrink:0}
.btn.sq.del{background:transparent;border:1px solid var(--line);color:#f87171}
.foot{display:flex;flex-direction:column;gap:10px;padding:12px 16px;border-top:1px solid var(--line);background:var(--card)}
.foot .secure{color:var(--muted);font-size:12px}
.foot .actions{display:flex;gap:10px;align-items:center}
.right{display:flex;flex-direction:column}
.right .ph{padding:11px 16px;border-bottom:1px solid var(--line);font-weight:600;font-size:12.5px;display:flex;justify-content:space-between;align-items:center}
.drop{flex:1;margin:14px;border:1.5px dashed var(--line);border-radius:12px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;color:var(--muted);min-height:420px;cursor:pointer;text-align:center;padding:20px}
.drop.over{border-color:var(--blue);background:#101827}
.drop .big{font-size:15px;font-weight:600;color:var(--text)}
.drop small{color:var(--muted2);font-size:11px}
.fileinfo{display:flex;gap:10px;align-items:center;margin:14px 14px 0;padding:10px 12px;border:1px solid var(--line);border-radius:10px;background:var(--card2)}
.fileinfo .fn{font-weight:600;font-size:12.5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.fileinfo .fs{color:var(--muted);font-size:11px}
.fileinfo .grow{flex:1;min-width:0}
.preview{flex:1;margin:12px 14px 0;border:1px solid var(--line);border-radius:10px;overflow:hidden;background:#fff;min-height:420px;position:relative}
.preview iframe,.preview img{width:100%;height:100%;border:0;display:block;object-fit:contain;background:#fff}
.preview .nopv{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;background:var(--card2);color:var(--muted);gap:8px}
.tip{margin:12px 14px 14px;border:1px solid var(--line);border-radius:10px;padding:10px 12px;display:flex;gap:10px;background:var(--card2)}
.tip b{display:block;font-size:12.5px;margin-bottom:2px}
.tip span{color:var(--muted);font-size:12px}
.toast{position:fixed;right:22px;bottom:22px;max-width:420px;background:#111827;border:1px solid var(--line);border-left:4px solid var(--green);border-radius:10px;padding:12px 14px;box-shadow:0 10px 30px rgba(0,0,0,.5);display:none;z-index:99}
.toast.err{border-left-color:var(--red)}
.toast b{display:block;margin-bottom:4px}
.toast small{color:var(--muted);display:block;line-height:1.5}
.spin{width:14px;height:14px;border:2px solid #2b4c8c;border-top-color:#bcd6ff;border-radius:50%;animation:sp .7s linear infinite;display:inline-block}
@keyframes sp{to{transform:rotate(360deg)}}
.certlist{margin-top:6px;display:flex;flex-direction:column;gap:4px}
.certlist .ci{display:flex;align-items:center;gap:8px;background:var(--card2);border:1px solid var(--line);border-radius:8px;padding:6px 8px;font-size:12px}
.certlist .ci .n{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.certlist .ci .f{color:var(--muted);font-size:11px}
.certlist .ci .x{cursor:pointer;color:#f87171;font-weight:700}
.hidden{display:none!important}
@media(max-width:1000px){.split{grid-template-columns:1fr}.left{border-right:0;border-bottom:1px solid var(--line)}}
</style>
</head>
<body>
<div class="page">
  <h1>Add Candidate</h1>
  <div class="sub">Review extracted information from resume and update if needed.</div>

  <div class="card">
    <div class="card-h">
      <h2>Resume Data Extractor Results</h2>
      <div><span class="chip" id="chip">Waiting for upload</span><button class="iconbtn" id="swap" title="Swap panels">⇄</button></div>
    </div>
    <div class="split" id="split">
      <div class="left">
        <div class="thead"><div>Extracted Information</div><div>Review &amp; Edit</div></div>
        <div class="rows" id="rows"></div>
        <div class="foot">
          <div class="secure">🛡 Your data is secure and confidential.</div>
          <div class="actions">
            <button class="btn blue" id="submit" disabled>Submit for Data Training</button>
            <button class="btn red" id="reset">Reset</button>
            <span id="submitmsg" class="sub"></span>
          </div>
        </div>
      </div>
      <div class="right">
        <div class="ph"><span>Resume Preview</span><button class="btn ghost hidden" id="remove" style="padding:5px 10px">✕ Remove</button></div>
        <div class="drop" id="drop">
          <div style="font-size:32px">☁</div>
          <div class="big">No file uploaded</div>
          <div>Drag and drop your resume here, or click to browse</div>
          <button class="btn blue" type="button" id="browse">⇧ Upload Resume</button>
          <small>PDF, DOC, DOCX, RTF, TXT or image (Max 10MB)</small>
        </div>
        <input type="file" id="fi" class="hidden" accept=".pdf,.doc,.docx,.rtf,.txt,.jpg,.jpeg,.png,.webp,.bmp,.tif,.tiff">
        <div class="fileinfo hidden" id="fileinfo">
          <div style="font-size:20px">📄</div>
          <div class="grow"><div class="fn" id="fname"></div><div class="fs" id="fsize"></div></div>
          <button class="btn ghost" id="replace" style="padding:6px 10px">Replace</button>
        </div>
        <div class="preview hidden" id="preview"></div>
        <div class="tip"><div>ⓘ</div><div><b>Tip</b><span>Review all extracted fields carefully. Edit any incorrect information before adding the candidate.</span></div></div>
      </div>
    </div>
  </div>
</div>
<div class="toast" id="toast"><b id="toast-t"></b><small id="toast-b"></small></div>

<script>
const BASE = "__API_PREFIX__";
const $ = id => document.getElementById(id);
let OPTS = null, REC = null, FILE = null, CERTS = [];

// ── field definitions (order = UI order) ────────────────────────────────────
const SECTIONS = [
  {title:"CANDIDATE DETAILS", fields:[
    {k:"fullName", label:"Full Name", req:true, type:"text", ph:"Full Name"},
    {k:"surname", label:"Surname", type:"text", ph:"Surname"},
    {k:"emails", label:"Primary Email", req:true, type:"emails"},
    {k:"mobileNumbers", label:"Phone Number", type:"phones"},
  ]},
  {title:"WORK EXPERIENCE", fields:[
    {k:"jobTitle", label:"Job Title", req:true, type:"select", opts:"jobTitles", ph:"Select Job Title"},
    {k:"yearsOfExperience", label:"Years of Experience", type:"select", opts:"experience", ph:"Select Years of Experience"},
    {k:"educationQualification", label:"Education Qualification", type:"select", opts:"education", ph:"Select Education Qualification"},
    {k:"certificates", label:"Certificates", type:"certs"},
  ]},
  {title:"CURRENT WORK LOCATION", fields:[
    {k:"currentWorkLocation.country", label:"Country", type:"country", ph:"Select Country"},
    {k:"currentWorkLocation.state", label:"State", type:"state", of:"currentWorkLocation.country", ph:"Select State"},
    {k:"currentWorkLocation.city", label:"City", type:"text", ph:"City"},
  ]},
  {title:"PERMANENT ADDRESS", fields:[
    {k:"permanentAddress.country", label:"Country", req:true, type:"country", ph:"Select Country"},
    {k:"permanentAddress.state", label:"State", type:"state", of:"permanentAddress.country", ph:"Select State"},
    {k:"permanentAddress.city", label:"City", type:"text", ph:"City"},
    {k:"permanentAddress.address", label:"Address", type:"textarea", ph:"House no, street, area"},
    {k:"permanentAddress.pinCode", label:"Pin Code", type:"text", ph:"Pin Code"},
  ]},
  {title:"IDENTITY (OPTIONAL)", fields:[
    {k:"pan", label:"PAN", type:"text", ph:"ABCDE1234F"},
    {k:"aadhar", label:"Aadhaar", type:"text", ph:"12 digit number"},
  ]},
];

const esc = s => String(s ?? "").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
const get = (o, path) => path.split(".").reduce((a,k)=>a==null?undefined:a[k], o);

function selectHtml(id, list, ph, value, extra="") {
  let h = `<select id="${id}" ${extra}><option value="">${esc(ph)}</option>`;
  let inList = false;
  for (const o of list||[]) { const sel = value && o===value; if (sel) inList = true; h += `<option value="${esc(o)}"${sel?" selected":""}>${esc(o)}</option>`; }
  if (value && !inList) h += `<option value="${esc(value)}" selected>${esc(value)} (from resume)</option>`;
  return h + `</select>`;
}

function buildRows() {
  let h = "";
  for (const s of SECTIONS) {
    h += `<div class="sec">${s.title}</div>`;
    for (const f of s.fields) h += rowHtml(f);
  }
  $("rows").innerHTML = h;
  for (const s of SECTIONS) for (const f of s.fields) wireField(f);
}

function rowHtml(f) {
  const id = "f_" + f.k.replace(/\./g,"_");
  let ctl = "";
  if (f.type==="text") ctl = `<input id="${id}" placeholder="${esc(f.ph)}">`;
  else if (f.type==="textarea") ctl = `<textarea id="${id}" placeholder="${esc(f.ph)}"></textarea>`;
  else if (f.type==="select") ctl = selectHtml(id, OPTS ? OPTS[f.opts] : [], f.ph, "");
  else if (f.type==="country") ctl = selectHtml(id, OPTS ? OPTS.countries : [], f.ph, "");
  else if (f.type==="state") ctl = selectHtml(id, [], f.ph, "");
  else if (f.type==="emails") ctl = `<div id="${id}_list"></div>`;
  else if (f.type==="phones") ctl = `<div id="${id}_list"></div>`;
  else if (f.type==="certs") ctl = `<div class="inline">${selectHtml(id+"_name", OPTS?OPTS.certificates:[], "Certificate Name", "")}<button class="btn ghost" id="${id}_up" type="button">⇧ Upload</button><button class="btn blue sq" id="${id}_add" type="button">+</button></div><input type="file" id="${id}_file" class="hidden" accept=".pdf,.jpg,.jpeg,.png,.webp,.doc,.docx"><div class="certlist" id="${id}_list"></div>`;
  return `<div class="row" id="row_${id}">
    <div class="cell-l"><div class="dot" id="${id}_dot"></div><div><div class="lbl">${esc(f.label)}${f.req?'<span class="req">*</span>':""}</div><div class="val" id="${id}_val">—</div><div class="val src" id="${id}_src"></div></div></div>
    <div class="cell-r">${ctl}</div></div>`;
}

function wireField(f) {
  const id = "f_" + f.k.replace(/\./g,"_");
  if (f.type==="country") {
    $(id).addEventListener("change", () => {
      for (const s of SECTIONS) for (const g of s.fields) if (g.type==="state" && g.of===f.k) refillState(g, $(id).value, "");
    });
  }
  if (f.type==="emails") { renderList(id, []); }
  if (f.type==="phones") { renderPhones(id, []); }
  if (f.type==="certs") {
    $(id+"_up").onclick = () => $(id+"_file").click();
    $(id+"_file").onchange = () => { if ($(id+"_file").files[0]) addCert($(id+"_name").value, $(id+"_file").files[0]); $(id+"_file").value=""; };
    $(id+"_add").onclick = () => { const n=$(id+"_name").value; if(!n){toast("Pick a certificate name first","",true);return;} addCert(n, null); };
  }
}

function refillState(f, country, value) {
  const id = "f_" + f.k.replace(/\./g,"_");
  const list = (OPTS && OPTS.states[country]) || [];
  $(id).outerHTML = selectHtml(id, list, f.ph, value);
}

// emails
function renderList(id, items) {
  const box = $(id+"_list");
  if (!items.length) items = [{emailAddress:"", isPrimary:true}];
  box.innerHTML = items.map((e,i)=>`<div class="inline"><input class="em" placeholder="Email" value="${esc(e.emailAddress)}">${items.length>1?`<button class="btn sq del" type="button" data-i="${i}">🗑</button>`:""}${i===items.length-1?`<button class="btn blue sq addem" type="button">+</button>`:""}</div>`).join("");
  box.querySelectorAll(".del").forEach(b=>b.onclick=()=>{const cur=readEmails(id);cur.splice(+b.dataset.i,1);renderList(id,cur);});
  const add = box.querySelector(".addem"); if (add) add.onclick=()=>{const cur=readEmails(id);cur.push({emailAddress:"",isPrimary:false});renderList(id,cur);};
}
function readEmails(id){ return [...$(id+"_list").querySelectorAll(".em")].map((i,idx)=>({emailAddress:i.value.trim(), isPrimary:idx===0})); }

// phones
function renderPhones(id, items) {
  const box = $(id+"_list");
  const dc = (REC && REC.meta && REC.meta.defaultDialCode) || "+91";
  if (!items.length) items = [{countryCode:dc, mobileNumber:"", isPrimary:true}];
  const codes = (OPTS && OPTS.countryCodes) || ["+91","+234"];
  box.innerHTML = items.map((p,i)=>`<div class="inline">${selectHtml("", codes, "+", p.countryCode||dc, 'class="cc"')}<input class="pn" placeholder="Phone Number" value="${esc(p.mobileNumber)}">${items.length>1?`<button class="btn sq del" type="button" data-i="${i}">🗑</button>`:""}${i===items.length-1?`<button class="btn blue sq addph" type="button">+</button>`:""}</div>`).join("");
  box.querySelectorAll(".del").forEach(b=>b.onclick=()=>{const cur=readPhones(id);cur.splice(+b.dataset.i,1);renderPhones(id,cur);});
  const add = box.querySelector(".addph"); if (add) add.onclick=()=>{const cur=readPhones(id);cur.push({countryCode:dc,mobileNumber:"",isPrimary:false});renderPhones(id,cur);};
}
function readPhones(id){ return [...$(id+"_list").querySelectorAll(".inline")].map((row,idx)=>({countryCode:row.querySelector(".cc").value, mobileNumber:row.querySelector(".pn").value.trim(), isPrimary:idx===0})); }

// certificates
async function addCert(name, file) {
  const id = "f_certificates";
  let fileId = null, fileName = null;
  if (file) {
    if (!REC) { toast("Upload the resume first", "", true); return; }
    const fd = new FormData(); fd.append("file", file); fd.append("name", name||file.name);
    try {
      const r = await fetch(`${BASE}/certificates/${REC.uid}`, {method:"POST", body:fd});
      const d = await r.json();
      if (!r.ok) { toast("Certificate upload failed", d.detail||"", true); return; }
      fileId = d.fileId; fileName = d.fileName; if (!name) name = d.name || file.name;
    } catch (e) { toast("Certificate upload failed", e.message, true); return; }
  }
  CERTS.push({name, fileId, fileName});
  renderCerts();
}
function renderCerts() {
  const box = $("f_certificates_list");
  box.innerHTML = CERTS.map((c,i)=>`<div class="ci"><span class="n">${esc(c.name||"(unnamed)")}</span><span class="f">${c.fileName?"📎 "+esc(c.fileName):"no file"}</span><span class="x" data-i="${i}">✕</span></div>`).join("");
  box.querySelectorAll(".x").forEach(x=>x.onclick=()=>{CERTS.splice(+x.dataset.i,1);renderCerts();});
}

// ── status rendering ────────────────────────────────────────────────────────
function setStatus(f, status, text, src) {
  const id = "f_" + f.k.replace(/\./g,"_");
  const dot = $(id+"_dot"), val = $(id+"_val"), row = $("row_"+id);
  row.classList.remove("missing","low");
  dot.className = "dot"; val.className = "val";
  if (status==="extracted") { dot.classList.add("ok"); dot.textContent="✓"; }
  else if (status==="low_confidence") { dot.classList.add("low"); dot.textContent="!"; row.classList.add("low"); }
  else if (status==="not_extracted") { dot.classList.add("miss"); dot.textContent="✕"; row.classList.add("missing"); val.classList.add("miss"); }
  else { dot.textContent=""; }
  val.textContent = text;
  $(id+"_src").textContent = src || "";
}

function displayValue(f, v) {
  if (v==null || v==="" ) return "";
  if (f.type==="emails") return v.map(e=>e.emailAddress).join(", ");
  if (f.type==="phones") return v.map(p=>`${p.countryCode} ${p.mobileNumber}`).join(", ");
  if (f.type==="certs") return v.map(c=>c.name).join(", ");
  return String(v);
}

function fillFromRecord(rec) {
  REC = rec; CERTS = [];
  const F = rec.fields || {};
  for (const s of SECTIONS) for (const f of s.fields) {
    const id = "f_" + f.k.replace(/\./g,"_");
    const top = f.k.split(".")[0];
    const desc = F[top] || {status:"not_extracted", value:"", confidence:0, source:""};
    let v = f.k.includes(".") ? get(desc.value||{}, f.k.split(".").slice(1).join(".")) : desc.value;
    let status = desc.status;
    if (f.k.includes(".")) status = v ? (desc.status==="not_extracted"?"low_confidence":desc.status) : "not_extracted";
    const shown = displayValue(f, v);
    const conf = desc.confidence ? ` · ${Math.round(desc.confidence*100)}%` : "";
    setStatus(f, status, shown || "Not extracted", status!=="not_extracted" ? (desc.source||"") + conf : "");
    // fill control
    if (f.type==="text" || f.type==="textarea") $(id).value = shown;
    else if (f.type==="select") $(id).outerHTML = selectHtml(id, OPTS[f.opts], f.ph, shown);
    else if (f.type==="country") { $(id).outerHTML = selectHtml(id, OPTS.countries, f.ph, shown); wireField(f); }
    else if (f.type==="state") { const c = get(F[top]?.value||{}, "country") || ""; refillState(f, c, shown); }
    else if (f.type==="emails") renderList(id, Array.isArray(v)?v:[]);
    else if (f.type==="phones") renderPhones(id, Array.isArray(v)?v:[]);
    else if (f.type==="certs") { CERTS = (Array.isArray(v)?v:[]).map(c=>({name:c.name,fileId:c.fileId||null,fileName:null})); renderCerts(); }
  }
  $("submit").disabled = false;
}

function readForm() {
  const g = k => { const el = $("f_"+k.replace(/\./g,"_")); return el ? el.value.trim() : ""; };
  return {
    fullName: g("fullName"), surname: g("surname"),
    emails: readEmails("f_emails").filter(e=>e.emailAddress),
    mobileNumbers: readPhones("f_mobileNumbers").filter(p=>p.mobileNumber),
    jobTitle: g("jobTitle"), yearsOfExperience: g("yearsOfExperience"),
    educationQualification: g("educationQualification"),
    certificates: CERTS.map(c=>({name:c.name, fileId:c.fileId})),
    currentWorkLocation: {country:g("currentWorkLocation.country"), state:g("currentWorkLocation.state"), city:g("currentWorkLocation.city")},
    permanentAddress: {address:g("permanentAddress.address"), city:g("permanentAddress.city"), state:g("permanentAddress.state"), country:g("permanentAddress.country"), pinCode:g("permanentAddress.pinCode")},
    pan: g("pan"), aadhar: g("aadhar"),
  };
}

// ── upload / extract ────────────────────────────────────────────────────────
function chip(cls, text, spin) { const c=$("chip"); c.className="chip "+cls; c.innerHTML=(spin?'<span class="spin"></span>':"")+esc(text); }
function fmtSize(b){ return b>1048576 ? (b/1048576).toFixed(1)+" MB" : (b/1024).toFixed(1)+" KB"; }

async function upload(file) {
  if (!file) return;
  FILE = file;
  $("drop").classList.add("hidden"); $("fileinfo").classList.remove("hidden"); $("remove").classList.remove("hidden");
  $("fname").textContent = file.name; $("fsize").textContent = fmtSize(file.size)+" · Uploading…";
  chip("busy","Extracting…",true);
  $("submit").disabled = true; $("submitmsg").textContent="";
  showPreview(file);
  const fd = new FormData(); fd.append("file", file);
  try {
    const r = await fetch(`${BASE}/extract`, {method:"POST", body:fd});
    const d = await r.json();
    if (!r.ok) { chip("err","Extraction failed"); toast("Extraction failed", d.detail||d.error||"Unknown error", true); $("fsize").textContent = fmtSize(file.size)+" · Failed"; return; }
    fillFromRecord(d);
    $("fsize").textContent = `${fmtSize(file.size)} · Uploaded · ${d.extractMethod} · ${d.durationMs} ms`;
    if (d.status==="failed") { chip("err","Extraction failed"); toast("Could not read this file", d.error||"", true); }
    else { chip("ok","✓ Extraction completed"); const m=d.meta||{}; toast("Extraction completed", `${m.fieldsExtracted} fields extracted, ${m.fieldsLowConfidence} need checking, ${m.fieldsMissing} missing · country: ${m.detectedCountry||"unknown"}`); }
  } catch (e) { chip("err","Network error"); toast("Network error", e.message, true); }
}

function showPreview(file) {
  const pv = $("preview"); pv.classList.remove("hidden"); pv.innerHTML = "";
  const ext = file.name.split(".").pop().toLowerCase();
  const url = URL.createObjectURL(file);
  if (ext==="pdf") pv.innerHTML = `<iframe src="${url}#toolbar=0"></iframe>`;
  else if (["jpg","jpeg","png","webp","bmp","gif"].includes(ext)) pv.innerHTML = `<img src="${url}">`;
  else if (ext==="txt") { file.text().then(t=>{ pv.innerHTML = `<pre style="padding:14px;white-space:pre-wrap;font-size:12px;color:#222;height:100%;overflow:auto">${esc(t)}</pre>`; }); }
  else pv.innerHTML = `<div class="nopv"><div style="font-size:30px">📄</div><div>Preview not available for .${esc(ext)}</div><small>The extracted text is shown in the left column</small></div>`;
}

function resetAll(keepFile) {
  REC = null; CERTS = [];
  buildRows();
  $("submit").disabled = true; $("submitmsg").textContent="";
  if (!keepFile) {
    FILE = null; $("fi").value="";
    $("drop").classList.remove("hidden"); $("fileinfo").classList.add("hidden"); $("preview").classList.add("hidden"); $("preview").innerHTML=""; $("remove").classList.add("hidden");
    chip("","Waiting for upload");
  }
}

async function submit() {
  if (!REC) return;
  const payload = {uid: REC.uid, fields: readForm(), reviewer: localStorage.getItem("reviewer") || null};
  if (!payload.fields.fullName) { toast("Full Name is required","",true); return; }
  if (!payload.fields.emails.length) { toast("Primary Email is required","",true); return; }
  if (!payload.fields.jobTitle) { toast("Job Title is required","",true); return; }
  $("submit").disabled = true; $("submitmsg").innerHTML = '<span class="spin"></span> Saving…';
  try {
    const r = await fetch(`${BASE}/review`, {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(payload)});
    const d = await r.json();
    if (!r.ok) { const det = Array.isArray(d.detail) ? d.detail.map(x=>x.loc.slice(1).join(".")+": "+x.msg).join("; ") : (d.detail||d.error); toast("Not saved", det, true); $("submitmsg").textContent=""; $("submit").disabled=false; return; }
    $("submitmsg").textContent = `Saved (review #${d.reviewId}) · extraction accuracy ${d.extractionAccuracyPct}% · ${d.fieldsChanged} of ${d.fieldsTotal} fields corrected`;
    toast("Submitted for data training", `Stored in ${d.storedIn} database · accuracy ${d.extractionAccuracyPct}%` + (d.changedFields.length ? ` · corrected: ${d.changedFields.join(", ")}` : " · no corrections needed"));
    chip("ok","✓ Saved to database");
  } catch (e) { toast("Network error", e.message, true); $("submit").disabled=false; $("submitmsg").textContent=""; }
}

let toastT;
function toast(t, b, err) { const el=$("toast"); el.className="toast"+(err?" err":""); $("toast-t").textContent=t; $("toast-b").textContent=b||""; el.style.display="block"; clearTimeout(toastT); toastT=setTimeout(()=>el.style.display="none", err?7000:5000); }

// ── init ────────────────────────────────────────────────────────────────────
async function init() {
  try { const r = await fetch(`${BASE}/options`); OPTS = await r.json(); }
  catch (e) { OPTS = {jobTitles:[],experience:[],education:[],certificates:[],countries:["India"],states:{},countryCodes:["+91"]}; toast("Could not load dropdown options", e.message, true); }
  buildRows();
  const fi=$("fi"), drop=$("drop");
  $("browse").onclick = e => { e.stopPropagation(); fi.click(); };
  drop.onclick = () => fi.click();
  $("replace").onclick = () => fi.click();
  fi.onchange = () => { if (fi.files[0]) { resetAll(true); upload(fi.files[0]); } };
  drop.ondragover = e => { e.preventDefault(); drop.classList.add("over"); };
  drop.ondragleave = () => drop.classList.remove("over");
  drop.ondrop = e => { e.preventDefault(); drop.classList.remove("over"); if (e.dataTransfer.files[0]) { resetAll(true); upload(e.dataTransfer.files[0]); } };
  $("remove").onclick = () => resetAll(false);
  $("reset").onclick = () => resetAll(false);
  $("submit").onclick = submit;
  $("swap").onclick = () => $("split").classList.toggle("swap");
}
init();
</script>
</body>
</html>"""
