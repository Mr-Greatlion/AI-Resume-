#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# AVR Resume Extractor v2 — deploy / update script
# Run on the VPS from the repo folder, as root:   bash deploy_v2.sh
# v1 (/opt/resume_api, port 8000, resume_api.service) is NEVER touched.
# ─────────────────────────────────────────────────────────────────────────────
set -e

V2_DIR=/opt/resume_v2
echo "════════════════════════════════════════"
echo " AVR Resume Extractor v2 — Deploy"
echo "════════════════════════════════════════"

# 1. system packages (optional helpers; skipped silently if apt is missing)
if command -v apt-get >/dev/null 2>&1; then
    apt-get install -y -qq poppler-utils antiword tesseract-ocr >/dev/null 2>&1 || true
fi

# 2. folders
mkdir -p $V2_DIR/uploads $V2_DIR/certificates

# 3. copy source (v2 gets its own private copy of the v1 extractor package `app/`)
rm -rf $V2_DIR/app_v2 $V2_DIR/app
cp -r app_v2/            $V2_DIR/app_v2/
cp -r app/               $V2_DIR/app/
cp    run_v2.py          $V2_DIR/
cp    requirements_v2.txt $V2_DIR/
[ -f $V2_DIR/.env ] || { cp .env.v2.example $V2_DIR/.env; echo "  Created $V2_DIR/.env — EDIT RESUME_V2_KEY and DATABASE_URL"; }

# 4. virtualenv + dependencies
if [ ! -d $V2_DIR/venv ]; then
    python3 -m venv $V2_DIR/venv
    echo "  Created virtualenv"
fi
$V2_DIR/venv/bin/pip install --quiet --upgrade pip
$V2_DIR/venv/bin/pip install --quiet -r $V2_DIR/requirements_v2.txt
$V2_DIR/venv/bin/python -m spacy download en_core_web_sm --quiet >/dev/null 2>&1 || echo "  (spaCy model download failed — v2 falls back to its own extractors)"
echo "  Dependencies installed"

# 5. permissions
chown -R www-data:www-data $V2_DIR
chmod 640 $V2_DIR/.env

# 6. systemd
cp resume_v2.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable resume_v2 >/dev/null 2>&1
systemctl restart resume_v2
sleep 3
if systemctl is-active --quiet resume_v2; then
    echo "  Service: RUNNING ✓"
    curl -s http://127.0.0.1:8001/resume-extractor-v2/health && echo
else
    echo "  Service: FAILED ✗   → journalctl -u resume_v2 -n 50"
fi

# 7. nginx
echo ""
echo "════ ACTION NEEDED (first deploy only) ════"
echo "Add nginx_v2_location.conf inside your avrenergies.com server{} block, then:"
echo "  nginx -t && systemctl reload nginx"
echo ""
echo "════════════════════════════════════════"
echo " v2 LIVE at:"
echo "   https://avrenergies.com/resume-extractor-v2         ← review UI"
echo "   https://avrenergies.com/resume-extractor-v2/docs    ← Swagger"
echo "   https://avrenergies.com/resume-extractor-v2/health"
echo "════════════════════════════════════════"
