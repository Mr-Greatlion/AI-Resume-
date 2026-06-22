import re
import spacy

# ================= SAFE SPACY LOAD =================
try:
    nlp = spacy.load("en_core_web_sm", disable=["parser", "tagger", "lemmatizer"])
except Exception:
    nlp = None

# ================= CONSTANTS =================

INDIAN_STATES = [
    "andhra pradesh", "arunachal pradesh", "assam", "bihar", "chhattisgarh",
    "goa", "gujarat", "haryana", "himachal pradesh", "jharkhand",
    "karnataka", "kerala", "madhya pradesh", "maharashtra", "manipur",
    "meghalaya", "mizoram", "nagaland", "odisha", "punjab",
    "rajasthan", "sikkim", "tamil nadu", "telangana", "tripura",
    "uttar pradesh", "uttarakhand", "west bengal",
    "andaman and nicobar", "chandigarh", "dadra and nagar haveli",
    "daman and diu", "delhi", "lakshadweep", "puducherry", "ladakh",
    "jammu and kashmir"
]

STATE_ABBREVIATIONS = {
    "ap": "Andhra Pradesh", "ar": "Arunachal Pradesh", "as": "Assam",
    "br": "Bihar", "cg": "Chhattisgarh", "ga": "Goa", "gj": "Gujarat",
    "hr": "Haryana", "hp": "Himachal Pradesh", "jh": "Jharkhand",
    "ka": "Karnataka", "kl": "Kerala", "mp": "Madhya Pradesh",
    "mh": "Maharashtra", "mn": "Manipur", "ml": "Meghalaya",
    "mz": "Mizoram", "nl": "Nagaland", "od": "Odisha", "pb": "Punjab",
    "rj": "Rajasthan", "sk": "Sikkim", "tn": "Tamil Nadu",
    "tg": "Telangana", "tr": "Tripura", "up": "Uttar Pradesh",
    "uk": "Uttarakhand", "wb": "West Bengal", "dl": "Delhi",
    "jk": "Jammu and Kashmir"
}

# ── NEW: Telangana short code (scenario 5) ────────────────────────────────────
STATE_SHORT_CODES = {
    "tg": "Telangana", "tn": "Tamil Nadu", "ap": "Andhra Pradesh",
    "ka": "Karnataka", "kl": "Kerala", "mh": "Maharashtra",
    "dl": "Delhi", "up": "Uttar Pradesh", "wb": "West Bengal",
    "br": "Bihar", "mp": "Madhya Pradesh", "gj": "Gujarat",
    "rj": "Rajasthan", "pb": "Punjab", "hr": "Haryana",
    "jk": "Jammu and Kashmir", "od": "Odisha", "cg": "Chhattisgarh",
    "jh": "Jharkhand", "as": "Assam", "hp": "Himachal Pradesh",
    "uk": "Uttarakhand", "tr": "Tripura",
}

INDIAN_DISTRICTS = [
    # Tamil Nadu
    "chennai", "coimbatore", "madurai", "tiruchirappalli", "trichy", "salem",
    "tirunelveli", "vellore", "erode", "theni", "dindigul", "thanjavur",
    "cuddalore", "kanchipuram", "villupuram", "namakkal", "karur",
    "tiruppur", "krishnagiri", "dharmapuri", "perambalur", "ariyalur",
    "pudukkottai", "ramanathapuram", "virudhunagar", "tenkasi",
    "chengalpattu", "ranipet", "tirupattur", "kallakurichi",
    # Karnataka
    "bangalore", "bengaluru", "mysuru", "mysore", "hubli", "dharwad",
    "mangalore", "mangaluru", "belagavi", "kalaburagi", "ballari",
    "davanagere", "shivamogga", "tumakuru", "udupi", "hassan",
    # Andhra Pradesh
    "visakhapatnam", "vizag", "vijayawada", "guntur", "nellore",
    "kurnool", "kakinada", "tirupati", "rajahmundry", "kadapa",
    "anantapur", "anakapalli", "anakaplli", "eluru", "ongole", "srikakulam",
    "vizianagaram",
    # Telangana
    "hyderabad", "warangal", "nizamabad", "karimnagar", "khammam",
    "ramagundam", "mahbubnagar", "nalgonda", "adilabad", "miryalguda",
    # Maharashtra
    "mumbai", "pune", "nagpur", "nashik", "aurangabad", "solapur",
    "amravati", "kolhapur", "akola", "latur", "jalgaon", "chandrapur",
    "thane", "nanded", "sangli", "satara", "ahmednagar",
    # Kerala
    "thiruvananthapuram", "kochi", "ernakulam", "kozhikode", "calicut",
    "thrissur", "kollam", "palakkad", "alappuzha", "kannur",
    "kasaragod", "malappuram", "pathanamthitta", "idukki", "wayanad",
    # Uttar Pradesh
    "lucknow", "kanpur", "agra", "varanasi", "meerut", "allahabad",
    "prayagraj", "ghaziabad", "noida", "bareilly", "aligarh", "gorakhpur",
    # Bihar
    "patna", "gaya", "bhagalpur", "muzaffarpur", "darbhanga", "purnia",
    "arrah", "begusarai", "katihar", "munger", "chapra", "samastipur",
    "hajipur", "sasaram", "bettiah", "motihari", "sitamarhi",
    "west champaran", "east champaran", "saran", "siwan", "gopalganj",
    "nawada", "jamui", "banka", "sheikhpura", "lakhisarai", "supaul",
    "madhepura", "saharsa", "madhubani", "supaul", "kishanganj",
    "araria", "sheohar", "vaishali", "nalanda",
    # Others
    "kolkata", "howrah", "ranchi", "bhopal", "indore",
    "jaipur", "jodhpur", "udaipur", "ahmedabad", "surat", "vadodara",
    "rajkot", "chandigarh", "ludhiana", "amritsar", "jalandhar",
    "dehradun", "guwahati", "bhubaneswar", "cuttack", "raipur",
    "jammu", "srinagar", "shimla", "gurugram", "gurgaon", "faridabad",
    "baniyapur",  # scenario 4
]

ADDRESS_HINT_WORDS = [
    "street", "road", "nagar", "colony", "layout", "lane", "block",
    "sector", "phase", "building", "apartment", "flat", "floor", "tower",
    "near", "opposite", "Village", "post", "district", "native place",
    "door no", "house no", "gate no", "residence", "permanent address",
    "present address", "current address", "mailing address",
    "correspondence address", "communication address",
    "taluk", "tehsil", "Mandal", "plot no", "room no", "survey no",
    "main road", "bypass", "highway", "industrial area", "civil lines",
    "housing board", "society", "compound", "complex", "enclave", "vihar",
    "garden", "park", "avenue", "market", "bazaar", "chowk",
    "p.o.", "po box", "c/o", "s/o", "d/o", "w/o", "care of",
    "ward no", "ward", "gali", "mohalla", "basti",
    "puram", "pet", "palya", "halli", "guda", "peta",
    "opp", "behind", "beside", "next to", "pincode", "pin code",
    "1st cross", "2nd cross", "3rd cross", "extension", "extn", "HO/NO",
    "at :-", "po :-", "ps :-", "dist :-", "at:", "po:", "ps:", "Dist",
    "at -", "po -", "ps -", "dist -", "tola", "majhaulia","H.No:","D.No:", "H.No-", "D.No-",
    "plot no","h.no", "d.no","(vi)", "(v)", "(m)", "(po)", "(ps)", "(dist)", "vi)", "v)", " m)", 
    "at/po", "at/p", "tq-", "tq –", "state-", "state –","add","tal-", "tal –",
]

NOISE_WORDS = [
    "resume", "curriculum vitae", "objective", "profile",
    "education", "experience", "skills", "certifications",
    "january", "february", "march", "april", "june", "july",
    "august", "september", "october", "november", "december",
    "challenging", "responsible", "position", "organization",
    "contribute", "client", "designation", "linkedin", "github",
    "hobbies", "interests", "marital", "nationality", "religion"
]

STOP_WORDS = [
    "declaration", "education", "academic", "experience", "skills",
    "objective", "strengths", "summary", "projects", "internship",
    "training", "certifications", "achievements", "awards",
    "publications", "references", "to obtain", "to work", "to utilize",
    "to contribute", "to secure", "to join", "seeking", "looking for",
    "i am seeking", "i wish", "i want", "bio", "career","i hereby", "i declare",
]

PERSONAL_FIELDS = [
    "name", "father", "mother", "dob", "date of birth",
    "age", "gender", "nationality", "marital", "blood group",
    "religion", "caste", "languages known", "hobbies"
]

TECH_BLACKLIST = [
    "react", "java", "python", "devops", "django", "flask",
    "aws", "azure", "node", "angular", "vue", "html", "css",
    "sql", "linux", "docker", "kubernetes", "git", "selenium",
    "spring", "mysql", "mongodb", "tensorflow", "pytorch", "php"
]

# Compiled regex patterns
PINCODE_RE      = re.compile(r"\b[1-9]\d{5}\b")
PHONE_RE        = re.compile(r"\b\d{10}\b")
YEAR_RANGE_RE   = re.compile(r"\b(19|20)\d{2}\s*[-–]\s*(19|20)\d{2}\b")
YEAR_END_RE     = re.compile(r"\b(19|20)\d{2}\s*$")
ALL_CAPS_RE     = re.compile(r"^[A-Z][A-Z\s.\-]{4,}$")
ADDR_LABEL_RE   = re.compile(
    r"(?i)[\W]*"
    r"(?:permanent\s*address|current\s*address|residential\s*address|"
    r"correspondence\s*address|present\s*address|address\s+for\s+communication|"
    r"communication\s*address|mailing\s*address|address)"
    r"\s*[:\-]?\s*",
    re.MULTILINE,
)
ADDRESS_LINE_LABEL_RE = re.compile(
    r"(?i)^\s*[-#]*\s*(?:permanent\s+address|current\s+address|"
    r"residential\s+address|correspondence\s+address|present\s+address|"
    r"address\s+for\s+communication|communication\s+address|"
    r"mailing\s+address|address)\s*[:\-]"
)

#Scenario 1 – door/plot number patterns (no hint words needed) ────────
# Matches: 12/27, 4B, No.14, D.No 5, H.No-3, 22A, etc.
DOOR_NUMBER_RE = re.compile(
    r"^\s*(?:"
    r"[A-Za-z]?\d+[/\\]\d+"        # 12/27, 4/B, A/12
    r"|[A-Za-z]{0,3}\.?\s*[Nn][Oo]\.?\s*[-:]?\s*\d+"   # No.14, D.No 5, H.No-3
    r"|\d+[-/][A-Za-z]\b"           # 22-A, 4/B
    r"|\d{1,4}[A-Za-z]\b"           # 22A, 4B  (short, not a year)
    r")",
    re.IGNORECASE,
)

# Scenario 2 – Bihar/rural AT/PO/PS/DIST pattern ──────────────────────
RURAL_ADDR_RE = re.compile(
     r"(?i)\b(?:at|po|p\.o|ps|p\.s|dist|tq|taluka?|state)\s*[:\-/]\s*\w"
     r"|at/p[os]?\s*[-–]",   # ← At/P, At/Po, At/Ps
)

VILLAGE_MANDAL_RE = re.compile(
    r'\b(?:vi|v|m|po|ps)\s*\)|'       # (VI), (M), (PO)
    r'\((?:vi|v|m|po|ps)\)',           
    re.IGNORECASE
)

# Scenario 3 – "Key : value" personal-info table (spaced colon) ───────
PERSONAL_INFO_LABEL_RE = re.compile(
    r"(?i)(?:permanent\s+address|current\s+address|residential\s+address|"
    r"address\s+for\s+communication|address)"
    r"\s{2,}:\s*(.+)",              # 2+ spaces before colon (tabular layout)
)

#Scenario 4 – state short code like TG-, AP-, KA- before pincode ─────
STATE_SHORTCODE_PINCODE_RE = re.compile(
    r"\b([A-Z]{2})-\s*(\d{6})\b"
)

# ============================================================
#  LINE-LEVEL HELPERS
# ============================================================

def _is_noise(line: str) -> bool:
    """True if this line is clearly NOT an address (email, phone, dates, etc.)."""
    lo = line.lower()
    without_contact = re.sub(
        r"(?i)\b(?:email|e-mail)\s*:?\s*[\w.+-]+@[\w.-]+\.[a-z]{2,}\b",
        "",
        line,
    )
    without_contact = re.sub(
        r"(?i)\b(?:cell(?:\s*no)?|mobile|phone|tel|ph)?\s*[-:.]?\s*"
        r"(?:\+?91[-\s]?)?[6-9]\d{9}\b",
        "",
        without_contact,
    ).strip(" ,.-|;:")
    return (
        not without_contact
        or bool(YEAR_RANGE_RE.search(line))
        or bool(YEAR_END_RE.search(line))
        or any(n in lo for n in NOISE_WORDS)
    )


def _is_stop(line: str) -> bool:
    lo = line.lower()
    if any(s in lo for s in STOP_WORDS):
        return True
    # Stop at declaration sentences
    if re.search(r"\bi\s+hereby\b|\bi\s+declare\b|\bto\s+the\s+best\s+of\b|\babove\s+mentioned\b", lo):
        return True
    return False


def _is_name_line(line: str) -> bool:
    """True if this line looks like a candidate name, not an address."""
    if ALL_CAPS_RE.match(line) and len(line.split()) <= 5:
        return True
    words = line.split()
    return (
        len(words) <= 5
        and all(w[0].isupper() for w in words if w and w[0].isalpha())
        and not _has_address_signal(line)
        and not any(c.isdigit() for c in line)
        and not any(c in line for c in ("@", "|", ","))
    )


def _has_address_signal(line: str) -> bool:
    """True if this line contains any address indicator."""
    lo = line.lower()
    if PINCODE_RE.search(line):
        return True
    # scenario 2 – AT/PO/PS/DIST pattern ──────────────────────────────
    if RURAL_ADDR_RE.search(line):
        return True
    if VILLAGE_MANDAL_RE.search(line):
        return True
    # scenario 1 – door/plot number pattern ───────────────────────────
    if DOOR_NUMBER_RE.search(line):
        return True
    # scenario 4 – TG-508207 style shortcode+pincode ─────────────────
    if STATE_SHORTCODE_PINCODE_RE.search(line):
        return True
    

    for state in INDIAN_STATES:
        pat = (r"\b" + re.escape(state) + r"\b") if len(state) <= 3 else re.escape(state)
        if re.search(pat, lo):
            return True
    for district in INDIAN_DISTRICTS:
        if re.search(r"\b" + re.escape(district) + r"\b", lo):
            return True
    return any(hint.lower() in lo for hint in ADDRESS_HINT_WORDS)


def _clean_line(line: str) -> str:
    """Strip address labels, pincode text, leading symbols, and extra spaces."""
    line = ADDR_LABEL_RE.sub("", line)
    line = re.sub(
        r"(?i)^.*?\b(?:s\s*/\s*o|d\s*/\s*o|w\s*/\s*o|c\s*/\s*o)\b"
        r"\s+[A-Za-z.'-]+(?:\s+[A-Za-z.'-]+)?\s*",
        "",
        line,
    )
    line = re.sub(r"(?i)\b(?:email|e-mail)\s*:?\s*[\w.+-]+@[\w.-]+\.[a-z]{2,}\b", "", line)
    line = re.sub(
        r"(?i)\b(?:cell(?:\s*no)?|mobile|phone|tel|ph)?\s*[-:.]?\s*"
        r"(?:\+?91[-\s]?)?[6-9]\d{9}\b",
        "",
        line,
    )
    line = re.sub(r"(?i)\b(pin\s*code|pincode|pin)\s*[-:]?\s*\d{6}\b", "", line)
    line = re.sub(PINCODE_RE, "", line)
    line = re.sub(r"^[\W_]+", "", line)
    line = re.sub(r"\s+", " ", line)
    line = re.sub(r"\s*,\s*", ", ", line)
    return line.strip(" ,.-|;:")

# ============================================================
#  PINCODE
# ============================================================

def extract_pincode(text: str) -> str:
    match = PINCODE_RE.search(text)
    return match.group() if match else ""

# ============================================================
#  STATE  (updated: handles TG-, AP- short codes from scenario 5)
# ============================================================

def extract_state(text: str) -> str:
    lo = text.lower()

    # Full state names (longest first)
    for state in sorted(INDIAN_STATES, key=len, reverse=True):
        pat = (r"\b" + re.escape(state) + r"\b") if len(state) <= 3 else re.escape(state)
        if re.search(pat, lo):
            return state.title()

    # ── NEW: short code before pincode e.g. "TG- 508207" ────────────────────
    m = STATE_SHORTCODE_PINCODE_RE.search(text)
    if m:
        code = m.group(1).lower()
        if code in STATE_SHORT_CODES:
            return STATE_SHORT_CODES[code]

    # 2-letter abbreviation in first 800 chars
    # Skip ambiguous abbreviations that are commonly used as non-location words
    _NON_LOCATION_ABBREVS = {"hr", "it", "or", "in", "at", "by", "is", "as"}
    for m in re.finditer(r"\b([A-Z]{2})\b", text[:800]):
        code = m.group(1).lower()
        if code in STATE_ABBREVIATIONS and code not in _NON_LOCATION_ABBREVS:
            return STATE_ABBREVIATIONS[code]

    return ""

# ============================================================
#  CITY
# ============================================================

def extract_city(text: str) -> str:
    lo = text.lower()
    for district in sorted(INDIAN_DISTRICTS, key=len, reverse=True):
        if re.search(r"\b" + re.escape(district) + r"\b", lo):
            return district.title()

    m = re.search(
        r"([A-Za-z][A-Za-z\s]{2,20}),?\s*(?:" + "|".join(re.escape(s) for s in INDIAN_STATES) + r")",
        text, re.IGNORECASE
    )
    if m:
        city = m.group(1).strip().split(",")[-1].strip()
        if city.lower() not in TECH_BLACKLIST and len(city) > 2:
            return city.title()

    m = re.search(r"([A-Za-z][A-Za-z\s]{2,25})[–\-]\s*(?=\d{6})", text)
    if m:
        city = m.group(1).strip().split(",")[-1].strip()
        if city.lower() not in TECH_BLACKLIST and city.lower() not in ("pin", "pincode", "pin code"):
            return city.title()

    if nlp:
        try:
            doc = nlp(text[:1000])
            for ent in doc.ents:
                if ent.label_ in ("GPE", "LOC"):
                    city = ent.text.strip().split("\n")[0].strip()
                    if (
                        city.lower() not in TECH_BLACKLIST
                        and city.lower() not in ("india", "bharat")
                        and not re.search(r"\d", city)
                        and len(city) > 2
                    ):
                        return city.title()
        except Exception:
            pass

    return ""

# ============================================================
#  HELPERS (new)
# ============================================================

def _strip_empty_pages(text: str) -> str:
    """
    Scenario 2: Remove trailing blank/empty pages from extracted PDF text.
    Many PDF-to-text tools insert form-feed \\f or repeated blank lines
    for blank pages. We strip everything after the last meaningful line.
    """
    # Split on form-feed (page break character common in pdfminer / PyMuPDF)
    pages = re.split(r"\f|\x0c", text)

    # Keep only pages that have at least one non-whitespace line
    meaningful_pages = [p for p in pages if p.strip()]
    return "\f".join(meaningful_pages) if meaningful_pages else text


def _try_personal_info_table(text: str) -> str:
    """
    Scenario 5: Handles tabular personal-info layouts where label and value
    are separated by lots of whitespace then a colon, e.g.:
        PermanentAddress                                 : Miryalguda, Nalgonda, TG- 508207
    Also handles ALL-CAPS label variants and concatenated labels (no space).
    """
    # Wide-spaced colon pattern (2+ spaces before colon)
    m = PERSONAL_INFO_LABEL_RE.search(text)
    if m:
        return m.group(1).strip()

    # Fallback: any line containing "address" (concatenated or spaced) and a colon
    # e.g. "PermanentAddress   : value"  or  "ADDRESS : value"
    for line in text.split("\n"):
        if re.search(r"(?i)(?:permanent|current|residential|present)?\s*address", line) and ":" in line:
            after_colon = line.split(":", 1)[-1].strip()
            if after_colon and len(after_colon) > 3 and not _is_noise(after_colon):
                return after_colon
    return ""


def _try_rural_address(text: str) -> str:
    """
    Scenario 3: Detects Bihar/rural style addresses using AT/PO/PS/DIST tokens.
    e.g.: AT :- PATBANDI TIWARI TOLA PO :- RATANMALA PS:- MAJHAULIA DIST :-WEST CHAMPARAN BIHAR, 845450
    Captures the whole line (or multi-token span) containing these markers.
    """
    for line in text.split("\n"):
        stripped = line.strip()
        if RURAL_ADDR_RE.search(stripped) and not _is_noise(stripped):
            return stripped
    return ""


def _try_door_number_line(lines: list[str]) -> str:
    """
    Scenario 1: Lines starting with door/plot numbers (no hint words).
    Collects that line + up to 2 continuation lines that look like address parts.
    """
    for i, line in enumerate(lines):
        if not DOOR_NUMBER_RE.search(line):
            continue
        if _is_noise(line) or _is_stop(line):
            continue
        # Must have at least one more address clue in the 3-line window
        window = " ".join(lines[i: i + 3])
        if not (PINCODE_RE.search(window) or _has_address_signal(window)):
            continue
        parts = []
        for part in lines[i: i + 3]:
            if _is_stop(part) or _is_noise(part):
                break
            cleaned = _clean_line(part)
            if cleaned:
                parts.append(cleaned)
        if parts:
            return ", ".join(parts)
    return ""


def _try_labeled_address_block(lines: list[str]) -> list[str]:
    """Scan the full document for a standalone labeled address block."""
    candidates = []

    for i, line in enumerate(lines):
        if not ADDRESS_LINE_LABEL_RE.search(line):
            continue

        parts = []
        has_pincode = False
        for part in lines[i: i + 10]:
            if part != line and _is_stop(part):
                break
            if part != line and ADDRESS_LINE_LABEL_RE.search(part):
                break
            if _is_noise(part):
                continue

            cleaned = _clean_line(part)
            if re.fullmatch(
                r"(?i)(?:s\s*/\s*o|d\s*/\s*o|w\s*/\s*o|c\s*/\s*o)"
                r"\s+[A-Za-z.'-]+(?:\s+[A-Za-z.'-]+)?",
                cleaned,
            ):
                continue
            if (
                cleaned
                and part == line
                and _is_name_line(cleaned)
                and not PINCODE_RE.search(part)
                and not STATE_SHORTCODE_PINCODE_RE.search(part)
            ):
                continue
            if (
                cleaned
                and _is_name_line(cleaned)
                and not _has_address_signal(cleaned)
                and not PINCODE_RE.search(part)
                and not STATE_SHORTCODE_PINCODE_RE.search(part)
            ):
                continue
            if cleaned and len(cleaned) <= 120:
                parts.append(cleaned)

            if PINCODE_RE.search(part):
                has_pincode = True
                break

        if parts:
            score = sum(_line_address_confidence(part) for part in parts)
            score += 3 if has_pincode else 0
            candidates.append((score, parts))

    return max(candidates, key=lambda item: item[0])[1] if candidates else []


def _address_scan_lines(text: str) -> list[str]:
    """Preserve OCR/PDF address blocks even when line breaks are collapsed."""
    text = re.sub(
        r"(?i)(?<!^)(?<!\n)(?=\s*[-#]*\s*(?:permanent\s+address|"
        r"current\s+address|residential\s+address|correspondence\s+address|"
        r"present\s+address|address\s+for\s+communication|"
        r"communication\s+address|mailing\s+address|address)\s*[:\-])",
        "\n",
        text,
    )
    return [line.strip() for line in re.split(r"[\r\n\f]+", text) if line.strip()]


# ============================================================
#  DEEP SCAN — full document, exhaustive last resort
# ============================================================

# Address-context keywords: presence of these near a line gives confidence
# it is a personal-details / contact section even with no explicit label.
_PERSONAL_SECTION_MARKERS = [
    "personal", "contact", "declaration", "details", "information",
    "profile", "bio", "about me",
]

# Lines whose ENTIRE content is just a section heading — skip them
_HEADING_ONLY_RE = re.compile(
    r"^(?:personal\s*(?:details|information|profile)|contact\s*(?:details|information)|"
    r"declaration|about\s*me|bio(?:data)?)$",
    re.IGNORECASE,
)


def _line_address_confidence(line: str) -> int:
    """
    Returns a confidence score 0-5 indicating how likely a line is an address.
    Used by the deep scanner to rank candidate lines across the full document.

    Score breakdown:
      +2  pincode present
      +2  any address hint word found
      +1  known state name present
      +1  known district present
      +1  door/plot number pattern at line start
      +1  rural AT/PO/PS/DIST marker
      +1  state short-code + pincode (TG-508207)
      -2  line is noise (phone, email, year range, noise words)
      -1  line looks like a name
    """
    if not line or not line.strip():
        return 0

    score = 0
    lo = line.lower()

    # Positive signals
    if PINCODE_RE.search(line):
        score += 2
    if any(hint.lower() in lo for hint in ADDRESS_HINT_WORDS):
        score += 2
    for state in INDIAN_STATES:
        pat = (r"" + re.escape(state) + r"") if len(state) <= 3 else re.escape(state)
        if re.search(pat, lo):
            score += 1
            break
    for district in INDIAN_DISTRICTS:
        if re.search(r"" + re.escape(district) + r"", lo):
            score += 1
            break
    if DOOR_NUMBER_RE.search(line):
        score += 1
    if RURAL_ADDR_RE.search(line):
        score += 1
    if STATE_SHORTCODE_PINCODE_RE.search(line):
        score += 1

    # Negative signals
    if _is_noise(line):
        score -= 2
    if _is_name_line(line):
        score -= 1

    return score


def _deep_scan_full_document(lines: list[str]) -> list[str]:
    """
    Strategy 10 — exhaustive full-document scan, called only after all earlier
    strategies have failed to find anything.

    Logic:
      1. Score every non-empty, non-noise line for address likelihood.
      2. Find the highest-scoring line with score >= 2 (confident threshold).
      3. Collect that line + up to 3 continuation lines that are also address-like.
      4. Additionally check lines that immediately follow known personal-section
         headings (e.g. "Personal Details", "Contact", "Declaration") anywhere
         in the document — those sections frequently hold address info buried
         after stop-word headings like "Education" or "Experience".
      5. Return empty list if nothing confident is found (truly no address).
    """
    if not lines:
        return []

    # Pass 1: score every line and find the best candidate
    best_score = 0
    best_idx   = -1
    for i, line in enumerate(lines):
        s = _line_address_confidence(line)
        if s > best_score:
            best_score = s
            best_idx   = i

    # Collect from best candidate if confident enough
    if best_score >= 2 and best_idx >= 0:
        parts = []
        for part in lines[best_idx: best_idx + 4]:
            if _is_noise(part):
                break
            cleaned = _clean_line(part)
            if cleaned and len(cleaned) > 2:
                parts.append(cleaned)
            # Stop if confidence drops sharply on continuation lines
            if _line_address_confidence(part) < 1 and len(parts) >= 1:
                break
        if parts:
            return parts

    # Pass 2: look for lines right after personal/contact section headings
    # (catches addresses that live after stop-word-blocked sections)
    for i, line in enumerate(lines):
        lo = line.lower().strip()
        if _HEADING_ONLY_RE.match(lo) or any(m in lo for m in _PERSONAL_SECTION_MARKERS):
            # Scan the next 10 lines for any address signal
            for j in range(i + 1, min(i + 11, len(lines))):
                candidate = lines[j]
                if _line_address_confidence(candidate) >= 2:
                    parts = []
                    for part in lines[j: j + 4]:
                        if _is_noise(part):
                            break
                        cleaned = _clean_line(part)
                        if cleaned and len(cleaned) > 2:
                            parts.append(cleaned)
                        if _line_address_confidence(part) < 1 and len(parts) >= 1:
                            break
                    if parts:
                        return parts

    return []

# ============================================================
#  LABELED ADDRESS DETECTOR
# ============================================================

def find_labeled_address(text: str) -> str | None:
    m = re.search(
        r"(?i)(?:permanent\s+address|current\s+address|residential\s+address|"
        r"address\s+for\s+communication|address)\s*[:\-]\s*(.+)",
        text,
    )
    if not m:
        return None

    block = text[m.start():]
    lines = [l.strip() for l in block.split("\n") if l.strip()][:3]
    return " ".join(lines)

# ============================================================
#  SMART ADDRESS DETECTOR  (header-area scan)
# ============================================================

def find_address_near_contact_info(text: str) -> str:
    lines = [l.strip() for l in text.split("\n") if l.strip()][:25]

    for i, line in enumerate(lines):
        if _is_stop(line):
            break
        if _is_noise(line) or _is_name_line(line):
            continue
        if not _has_address_signal(line):
            continue

        address_parts = []
        for part in lines[i: i + 4]:
            if _is_stop(part) or _is_noise(part):
                break
            cleaned = _clean_line(part)
            if cleaned:
                address_parts.append(cleaned)

        if address_parts:
            return ", ".join(address_parts)

    return ""

# ============================================================
#  MAIN EXTRACT ADDRESS
# ============================================================

def extract_address(text: str) -> dict:
    """
    Full address extractor. Tries strategies in order:
      1. Top-of-resume header scan (contact info area)
      2. Pipe-separated inline contact line
      3. Labeled address block ("Address: ..." / "Permanent Address: ...")
      4. Scenario 5: tabular personal-info table (wide-spaced colon)
      5. Scenario 3: rural AT/PO/PS/DIST pattern
      6. Scenario 1: door/plot number lines (no hint words)
      7. spaCy NER on header block
      8. Pincode line fallback
      9. State / district fallback
    Returns: { address, city, state, country, pincode }
    """
    # ── Scenario 2: strip trailing empty pages before any processing ──────────
    text = _strip_empty_pages(text)

    lines = _address_scan_lines(text)
    address_parts = _try_labeled_address_block(lines)

    # ── STRATEGY 1: top-of-resume header scan (first 20 lines) ──────────────
    for i, line in enumerate(lines[:20]):
        if address_parts:
            break
        lower = line.lower()

        if _is_stop(line):
            break
        if _is_noise(line) or _is_name_line(line):
            continue
        if "|" in line and not PINCODE_RE.search(line):
            if not any(s in lower for s in INDIAN_STATES):
                continue

        if (
            PINCODE_RE.search(line)
            or "india" in lower
            or any(state in lower for state in INDIAN_STATES)
            or any(word.lower() in lower for word in ADDRESS_HINT_WORDS)
            or DOOR_NUMBER_RE.search(line)          # scenario 1
            or RURAL_ADDR_RE.search(line)           # scenario 3
            or STATE_SHORTCODE_PINCODE_RE.search(line)  # scenario 5
        ):
            cleaned = _clean_line(line)
            if cleaned and len(cleaned) > 2:
                address_parts.append(cleaned)
                for cont in lines[i + 1: i + 4]:
                    if _is_stop(cont):
                        break
                    if _is_noise(cont):
                        continue
                    if any(p in cont.lower() for p in PERSONAL_FIELDS):
                        break
                    cont_clean = _clean_line(cont)
                    if cont_clean and len(cont_clean) > 2:
                        address_parts.append(cont_clean)
                break

    # ── STRATEGY 2: pipe-separated inline contact line ───────────────────────
    if not address_parts:
        for line in lines[:10]:
            if "|" not in line:
                continue
            for segment in line.split("|"):
                seg = segment.strip()
                if not _is_noise(seg) and _has_address_signal(seg) and len(seg) > 3:
                    cleaned = _clean_line(seg)
                    if cleaned:
                        address_parts.append(cleaned)
                    break
            if address_parts:
                break

    # ── STRATEGY 3: labeled address block anywhere in document ───────────────
    if not address_parts:
        for i, line in enumerate(lines):
            if not ADDR_LABEL_RE.search(line):
                 continue
       

            inline = _clean_line(line)
            if inline and not _is_noise(inline) and len(inline) > 2:
                address_parts.append(inline)

            for part in lines[i + 1: i + 5]:
                lower_part = part.lower()
                if _is_stop(part):
                    break
                if any(p in lower_part for p in PERSONAL_FIELDS):
                    if not re.search(r"(?i)\baddress\b", part):
                        break
                if _is_noise(part):
                    continue
                if ":" in part and not _has_address_signal(part):
                    continue
                part_clean = _clean_line(part)
                if part_clean and len(part_clean) > 120:
                    address_parts.append(part_clean)
                if len(address_parts) >= 4:
                    break
            break

    # ── STRATEGY 4 (NEW): tabular personal-info table (scenario 5) ───────────
    # Handles:  PermanentAddress                   : Miryalguda, Nalgonda, TG- 508207
    if not address_parts:
        tabular = _try_personal_info_table(text)
        if tabular:
            address_parts.append(tabular)

    # ── STRATEGY 5 (NEW): rural AT/PO/PS/DIST pattern (scenario 3) ───────────
    if not address_parts:
        rural = _try_rural_address(text)
        if rural:
            address_parts.append(rural)

    # ── STRATEGY 6 (NEW): door/plot number lines (scenario 1) ────────────────
    if not address_parts:
        door_addr = _try_door_number_line(lines)
        if door_addr:
            address_parts.append(door_addr)

    # ── STRATEGY 7: spaCy NER on the header block ────────────────────────────
    if not address_parts and nlp:
        try:
            header = text[:1200]
            doc = nlp(header)
            geo_lines = []
            for ent in doc.ents:
                if ent.label_ in ("GPE", "LOC") and ent.text.lower() not in ("india", "bharat"):
                    geo_lines.append(ent.text.strip())
            if geo_lines:
                for line in lines[:20]:
                    if _is_noise(line) or _is_name_line(line):
                        continue
                    hits = sum(1 for g in geo_lines if g.lower() in line.lower())
                    if hits >= 1 and _has_address_signal(line):
                        address_parts.append(_clean_line(line))
                        break
        except Exception:
            pass

    # ── STRATEGY 8: pincode line fallback ────────────────────────────────────
    if not address_parts:
        for line in lines:
            if PINCODE_RE.search(line) and not _is_noise(line):
                cleaned = _clean_line(line)
                if cleaned and len(cleaned) > 3:
                    address_parts.append(cleaned)
                    break

    # ── STRATEGY 9: state / district scan — full document, no stop-word block ─
    # Deliberately skips _is_stop() check so personal-details sections buried
    # after headings like "Education" / "Experience" are still reachable.
    if not address_parts:
        for line in lines:
            if _is_noise(line) or _is_name_line(line):
                continue
            lo = line.lower()
            if any(s in lo for s in INDIAN_STATES) or \
               any(re.search(r"\b" + re.escape(d) + r"\b", lo) for d in INDIAN_DISTRICTS):
                address_parts.append(line.strip())
                break

    # ── STRATEGY 10: exhaustive deep scan — last resort before giving up ──────
    # Scores every line in the full document for address likelihood.
    # Also checks lines following personal/contact section headings anywhere.
    # "Address not found in resume" is only emitted when THIS also returns empty,
    # ensuring we never give up prematurely on a resume that has address content.
    if not address_parts:
        address_parts = _deep_scan_full_document(lines)

    # ── Build result ──────────────────────────────────────────────────────────
    seen, unique_parts = set(), []
    for p in address_parts:
        key = p.lower().strip()
        if key and key not in seen:
            seen.add(key)
            unique_parts.append(p)

    full_address = ", ".join(unique_parts)

    city    = extract_city(full_address) if full_address else extract_city(text[:2000])
    state   = extract_state(full_address) if full_address else extract_state(text[:2000])
    pincode = extract_pincode(text)

    # ── Scenario 6: only after ALL 10 strategies are exhausted ───────────────
    # Emitted only when the resume truly contains no address information.
    # Do NOT change this to empty string — downstream callers use this message
    # to distinguish "not found" from "found but blank".
    ADDRESS_NOT_FOUND = "Address not found in resume"
    return {
        "address": full_address if full_address else ADDRESS_NOT_FOUND,
        "city":    city,
        "state":   state,
        "country": "India",
        "pincode": pincode,
    }

# ============================================================
#  CURRENT LOCATION  (lightweight — city+state from header)
# ============================================================

def extract_current_location(text: str) -> dict | None:
    header = text[:1200]
    city  = extract_city(header)
    state = extract_state(header)

    if not city and not state:
        return None

    return {
        "city":    city,
        "state":   state,
        "country": "India",
    }
