#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# AVR Resume Extractor v2 — deploy script
# Run on VPS as root: bash deploy_v2.sh
# v1 at /opt/resume_api is NEVER touched.
# ─────────────────────────────────────────────────────────────────────────────
set -e

echo "════════════════════════════════════"
echo " AVR Resume Extractor v2 — Deploy  "
echo "════════════════════════════════════"

V2_DIR=/opt/resume_v2

# 1. create dirs
mkdir -p $V2_DIR/uploads

# 2. copy source
cp -r app_v2/         $V2_DIR/app_v2/
cp    run_v2.py       $V2_DIR/
cp    requirements_v2.txt $V2_DIR/

# 3. venv
if [ ! -d $V2_DIR/venv ]; then
    python3 -m venv $V2_DIR/venv
    echo "  Created virtualenv"
fi
$V2_DIR/venv/bin/pip install --quiet --upgrade pip
$V2_DIR/venv/bin/pip install --quiet -r $V2_DIR/requirements_v2.txt
echo "  Dependencies installed"

# 4. permissions
chown -R www-data:www-data $V2_DIR
echo "  Permissions set"

# 5. systemd
cp resume_v2.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable resume_v2
systemctl restart resume_v2
sleep 2
systemctl is-active resume_v2 && echo "  Service: RUNNING ✓" || echo "  Service: FAILED ✗"

# 6. nginx
echo ""
echo "════ ACTION NEEDED ════"
echo "Add this to your nginx server{} block:"
echo "  cat nginx_v2_location.conf"
echo ""
echo "Then: nginx -t && systemctl reload nginx"
echo ""
echo "════════════════════════════════════"
echo " v2 LIVE at:"
echo " https://avrenergies.com/resume-extractor-v2"
echo " https://avrenergies.com/resume-extractor-v2/docs  ← Swagger"
echo "════════════════════════════════════"
