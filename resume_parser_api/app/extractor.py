import re
import spacy
import phonenumbers
def normalize_text_for_email(text):
    # Insert space after common TLDs if OCR glued text
    text = re.sub(r'(\.com)([A-Z])', r'\1 \2', text)
    text = re.sub(r'(\.in)([A-Z])', r'\1 \2', text)
    text = re.sub(r'(\.org)([A-Z])', r'\1 \2', text)
    text = re.sub(r'(\.net)([A-Z])', r'\1 \2', text)

    # Remove common language words if glued
    text = re.sub(
        r'(gmail\.com|yahoo\.com|outlook\.com)\s*(tamil|english|hindi|urdu)',
        r'\1',
        text,
        flags=re.IGNORECASE
    )

    return text

nlp = spacy.load("en_core_web_sm")

BLACKLIST = [
    "engineering", "college", "university", "institute",
    "technologies", "technology", "solutions", "systems",
    "pvt", "ltd", "limited", "company"
]

# ---------- EMAIL ----------
def extract_email(text):
    text = normalize_text_for_email(text)

    pattern = r'\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.(com|in|org|net|edu)\b'
    match = re.search(pattern, text, re.IGNORECASE)

    return match.group().lower() if match else None


# ---------- PHONE ----------
def extract_phone(text):
    for match in phonenumbers.PhoneNumberMatcher(text, "IN"):
        return phonenumbers.format_number(
            match.number,
            phonenumbers.PhoneNumberFormat.E164
        )
    return None


# ---------- EDUCATION ----------
def extract_education(text):
    text = text.lower()

    patterns = {
        "B.E": ["b.e", "be ", "bachelor of engineering"],
        "B.Tech": ["b.tech", "btech", "bachelor of technology"],
        "M.E": ["m.e", "master of engineering"],
        "M.Tech": ["m.tech", "mtech", "master of technology"],
        "MBA": ["mba", "master of business administration"],
        "MCA": ["mca", "master of computer applications"],
        "B.Sc": ["b.sc", "bsc", "bachelor of science"],
        "M.Sc": ["m.sc", "msc", "master of science"]
    }

    for degree, keys in patterns.items():
        for k in keys:
            if k in text:
                return degree
    return None


# ---------- NAME ----------
def looks_like_name(text):
    words = text.split()
    if not (2 <= len(words) <= 4):
        return False

    if re.search(r"\d|[@_]", text):
        return False

    for bad in BLACKLIST:
        if bad in text.lower():
            return False

    return True


def extract_name(text):
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    # Header priority
    for line in lines[:5]:
        if looks_like_name(line):
            return line.title()

    # Email username fallback
    email_match = re.search(r'([a-zA-Z0-9._%+-]+)@', text)
    if email_match:
        user = email_match.group(1).replace(".", " ").replace("_", " ")
        parts = user.split()
        if 1 <= len(parts) <= 3:
            return " ".join(p.capitalize() for p in parts)

    # NLP fallback
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ == "PERSON" and looks_like_name(ent.text):
            return ent.text.title()

    return None

def detect_pan(text):
    return bool(re.search(r'\b[A-Z]{5}[0-9]{4}[A-Z]\b', text))


def detect_aadhaar(text):
    return bool(re.search(r'\b\d{4}\s?\d{4}\s?\d{4}\b', text))

