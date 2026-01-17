import re
from datetime import datetime
import math

MONTHS = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12
}

# ---------- DATE PARSER ----------
def parse_date_safe(text):
    text = text.lower().strip()
    parts = text.split()

    if len(parts) == 2 and parts[0] in MONTHS:
        return datetime(int(parts[1]), MONTHS[parts[0]], 1)

    if text.isdigit() and len(text) == 4:
        return datetime(int(text), 1, 1)

    return None


# ---------- LAYER 1: DIRECT EXPERIENCE ----------
def extract_direct_experience(text):
    patterns = [
        r'(\d{1,2}\.\d+)\s*\+?\s*years?',
        r'(\d{1,2})\s*\+?\s*years?',
        r'(\d{1,2}\.\d+)\s*yrs?',
        r'(\d{1,2})\s*yrs?'
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1))

    return None


# ---------- LAYER 2: DATE RANGE ----------
def calculate_from_dates(text):
    pattern = r'([A-Za-z]+ \d{4}|\d{4})\s*[-–]\s*(Present|[A-Za-z]+ \d{4}|\d{4})'
    matches = re.findall(pattern, text, re.IGNORECASE)

    total_months = 0
    used = set()

    for start, end in matches:
        start_date = parse_date_safe(start)
        if not start_date:
            continue

        end_date = datetime.now() if end.lower() == "present" else parse_date_safe(end)
        if not end_date:
            continue

        key = (start_date, end_date)
        if key in used:
            continue
        used.add(key)

        months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
        if months > 0:
            total_months += months

    if total_months == 0:
        return None

    return total_months / 12


# ---------- FINAL EXPERIENCE ----------
def calculate_experience(text):
    # 1️⃣ Direct experience mention
    direct = extract_direct_experience(text)
    if direct:
        return math.floor(direct)

    # 2️⃣ Date-based calculation
    calculated = calculate_from_dates(text)
    if calculated:
        return math.floor(calculated)

    # 3️⃣ Fallback
    return 0
