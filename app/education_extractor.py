import re
from typing import List, Optional

# ================= EDUCATION =================

DEGREE_PATTERNS = {
    # Postgraduate
    "PhD":    ["phd", "ph.d", "doctor of philosophy"],
    "MBA":    ["mba", "master of business administration"],
    "M.Tech": ["m.tech", "mtech", "master of technology"],
    "MCA":    ["mca", "master of computer applications"],
    "M.Sc":   ["m.sc", "msc", "master of science"],
    "M.E":    ["master of engineering"],
    "M.A":    ["m.a", "master of arts"],

    # Undergraduate
    "B.Tech": ["b.tech", "btech", "B-tech", "bachelor of technology","b-tech","b tech"],
    "BCA":    ["bca", "bachelor of computer applications"],
    "B.Sc":   ["b.sc", "b.s.c", "bsc", "bachelor of science"],
    "B.E":    ["bachelor of engineering","b.e", "b e", "b.e.", "b-e", "bachelorofengineering"],
    "B.A":    ["bachelor of arts"],

    # Diploma specific (order matters — specific before generic)
    "Diploma (Electrical & Electronics)": [
        "diploma in electrical & electronics engineering",
        "diploma in electrical and electronics engineering",
        "diploma in electrical engineering",
        "diploma in eee",
        "diploma (eee)",
        "diploma(eee)",
        "diploma electrical & electronics",
        "diploma electrical and electronics",
        "diploma electrical",
        "eee diploma",
        "diploma eee",
    ],
    "Diploma (Textile Technology)": [
        "diploma in textile technology",
    ],
    "Diploma (ECE)": [
        "diploma in ece",
        "diploma in electronics and communication",
        "diploma in electronics & communication",
        "diploma in electronics engineering",
        "diploma(ece)",
        "diploma (ece)",
        "diploma ece",
        "ece diploma",
        "diploma electronics",
        "diploma in electronics",
    ],
    "Diploma (Mechanical)": [
        "diploma in mechanical engineering",
        "diploma in mechanical",
        "diploma (mechanical)",
        "diploma mechanical",
        "mechanical diploma",
        "d.m.e",
        "dme",
    ],
    "Diploma (Civil)": [
        "diploma in civil engineering",
        "diploma in civil",
        "diploma (civil)",
        "diploma civil",
        "civil diploma",
    ],
    "Diploma (Computer Science)": [
        "diploma in computer science",
        "diploma in cs",
        "diploma (cs)",
        "diploma cs",
    ],
    # Generic diploma LAST — only catches bare "diploma" with no stream
    "Diploma": ["diploma"],

    # ITI specific only
    "ITI": ["iti (electrician)", "iti(electrician)", "iti electrician",
            "iti (fitter)",      "iti(fitter)",      "iti fitter",
            "iti (welder)",      "iti(welder)",      "iti welder",
            "iti (mechanic)",    "iti(mechanic)",
            "i.t.i","ITI", "I T I","I.T.I FITTER","I.T.I","i.t.i  fitter","iti",
            ],

    # Standalone engineering streams -> B.E (only when no diploma keyword)
    "BE (Mechanical)_stream": [
        "mechanical engineering",
        "mechanical engg",
    ],
    "BE (Electrical & Electronics)_stream": [
        "electrical engineering",
        "electrical and electronics engineering",
        "electrical & electronics engineering",
        "electrical and electronics",
        "electrical & electronics",
        "eee",
    ],
    "BE (ECE)_stream": [
        "electronics and communication engineering",
        "electronics & communication engineering",
        "electronics engineering",
        "electronics and communication",
        "electronics & communication",
        "ece",
    ],
    "BE (Civil)_stream": [
        "civil engineering",
        "civil engg",
    ],

    # School
    "Intermediate / 12th": [
        "intermediate", "12th", "hsc", "higher secondary",
        "plus two", "+2", "10+2", "pre-university", "junior college",
    ],
}

STREAM_ALIAS = {
    "BE (Mechanical)_stream": "B.E",
    "BE (Electrical & Electronics)_stream": "B.E",
    "BE (ECE)_stream": "B.E",
    "BE (Civil)_stream": "B.E",
    "B.Tech Electronics & Instrumentation_stream":  "B.Tech",
    "B.E Mechanical Engineering_stream": "B.E"
}

BOUNDARY_ONLY = {
    r"m\.tech": "M.Tech",
    r"b[\s.]?\s*tech": "B.Tech",
    r"m\.e":    "M.E",
    r"b\.e\.?": "B.E",
    r"m\.a":    "M.A",
    r"b\.a":    "B.A",
    r"m\.sc":   "M.Sc",
    r"b\.sc":   "B.Sc",
}

PRIORITY = [
    "PhD", "MBA", "M.Tech", "MCA", "M.Sc", "M.E", "M.A",
    "B.Tech", "BCA", "B.Sc", "B.A",
    "Diploma (Electrical & Electronics)",
    "Diploma (ECE)",
    "Diploma (Mechanical)",
    "Diploma (Civil)",
    "Diploma (Computer Science)",
    "Diploma (Textile Technology)",
    "Diploma",
    "B.E", "B.Tech",
    "ITI",
    "Intermediate / 12th",
    "10th / SSC",
]

EDUCATION_HEADINGS = [
    "academic profile", "educational qualification", "educational qualifications",
    "academic qualifications",
    "education", "qualification", "qualifications", "qualification personal details",
    "academic background", "academic details", "basic academic credentials",
    "educational details", "academics",
]

PROFILE_HEADINGS = [
    "professional profile", "career objective", "objective",
    "summary", "profile", "about me", "professional summary",
]

NOSPACE_PATTERNS = [
    ("diplomainmechanicalengineering",                "Diploma (Mechanical)"),
    ("diplomainmechanical",                           "Diploma (Mechanical)"),
    ("mechanicaldiploma",                             "Diploma (Mechanical)"),
    ("d.m.e",                                         "Diploma (Mechanical)"),
    ("dme",                                           "Diploma (Mechanical)"),
    ("diplomainelectricalandelectronicsengineering",  "Diploma (Electrical & Electronics)"),
    ("diplomainelectricalelectronicsengineering",     "Diploma (Electrical & Electronics)"),
    ("diplomainelectricalengineering",                "Diploma (Electrical & Electronics)"),
    ("diplomainelectrical",                           "Diploma (Electrical & Electronics)"),
    ("diplomaineee",                                  "Diploma (Electrical & Electronics)"),
    ("diplomaelectrical",                             "Diploma (Electrical & Electronics)"),
    ("eeediploma",                                    "Diploma (Electrical & Electronics)"),
    ("diplomainelectronicsandcommunication",          "Diploma (ECE)"),
    ("diplomainelectronicsengineering",               "Diploma (ECE)"),
    ("diplomainece",                                  "Diploma (ECE)"),
    ("diplomaelectronics",                            "Diploma (ECE)"),
    ("ecediploma",                                    "Diploma (ECE)"),
    ("diplomaincivilengineering",                     "Diploma (Civil)"),
    ("diplomaincivil",                                "Diploma (Civil)"),
    ("civildiploma",                                  "Diploma (Civil)"),
    ("diplomaincomputerscience",                      "Diploma (Computer Science)"),
    ("btech",                                         "B.Tech"),
    ("bsc",                                           "B.Sc"),
    ("bca",                                           "BCA"),
    ("mtech",                                         "M.Tech"),
    ("diploma",                                       "Diploma"),
    ("b.e(mechanicalengineering)",   "B.E"),
    ("b.e(mechanical)",              "B.E"),
    ("b.e(electrical)",              "B.E"),
    ("b.e(civil)",                   "B.E"),
    ("b.e(ece)",                     "B.E"),
    ("bachelorofengineering", "B.E"),
    ("bacheloroftechnology", "B.Tech"),
    ("masteroftechnology", "M.Tech"),
    ("masterofengineering", "M.E"),
    ("bacheloroftechnology", "B.Tech"),
    ("btech", "B.Tech"),
    ("i.t.ifitter",     "ITI"),
    ("i.t.ielectrician","ITI"),
    ("i.t.iwelder",     "ITI"),
    ("i.t.imechanic",   "ITI"),
]


def _normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[ \t]+", " ", text)
    return text


def _dejunk(text: str) -> str:
    return re.sub(r"\s+", "", text.lower())


def _join_lines(text: str) -> str:
    return re.sub(r"\n+", " ", text)


def _has_bsc_variant(t_norm: str, t_joined: str, t_nospace: str) -> bool:
    pat = r"(?<![a-z0-9])b[\s.]*s[\s.]*c(?![a-z0-9])"
    return (
        re.search(pat, t_norm) is not None
        or re.search(pat, t_joined) is not None
        or "degree(bsc)" in t_nospace
        or "bsc" in t_nospace
    )


def _has_diploma_evidence(t_norm: str, t_joined: str, t_nospace: str) -> bool:
    if "diploma" in t_norm or "diploma" in t_joined or "diploma" in t_nospace:
        return True
    if re.search(r"(?<![a-z0-9])d\.m\.e(?![a-z0-9])", t_norm):
        return True
    if re.search(r"(?<![a-z0-9])d\.m\.e(?![a-z0-9])", t_joined):
        return True
    if "dme" in t_nospace:
        return True
    return False


def _scan(text: str, stream_ok: bool = False, global_diploma: bool = False) -> Optional[str]:
    t_norm    = _normalize(text)
    t_joined  = _normalize(_join_lines(text))
    t_nospace = _dejunk(text)

    found = set()

    diploma_present = global_diploma or _has_diploma_evidence(t_norm, t_joined, t_nospace)

    if _has_bsc_variant(t_norm, t_joined, t_nospace):
        found.add("B.Sc")

    # FIX: removed the misplaced early-return inside this loop.
    # It was firing before any other degree could be checked.
    # "Diploma (Mechanical)" is already handled by DEGREE_PATTERNS patterns below.
    for degree, patterns in DEGREE_PATTERNS.items():
        if degree in STREAM_ALIAS and not stream_ok:
            continue
        for p in patterns:
            if p in t_norm or p in t_joined:
                found.add(degree)
                break

    best_nospace = None
    for pat, degree in NOSPACE_PATTERNS:
        # Avoid false DME detection when ITI exists
        if pat == "dme" and "ITI" in found:
            continue    
        if pat in t_nospace:
            if best_nospace is None:
                best_nospace = degree
            if degree != "Diploma":
                break
    if best_nospace:
        found.add(best_nospace)

    if re.search(r'b[\.\-]e\s*\(', t_nospace.replace(" ", "")):
        found.add("B.E")

    diploma_present = diploma_present or any(d.startswith("Diploma") for d in found)

    dme_present = (
        bool(re.search(r"(?<![a-z0-9])d\.m\.e(?![a-z0-9])", t_norm))
        or bool(re.search(r"(?<![a-z0-9])d\.m\.e(?![a-z0-9])", t_joined))
        or "dme" in t_nospace
    )

    # Strip university/institute names to avoid false matches
    text_for_scan = re.sub(
        r'\b(?:university|institute|college|board|deemed|from)\b.*',
        '', t_norm
    )

    text_for_iti = re.sub(
    r'\b(?:university|institute|college|board|deemed|from|private|school|polytechnic)\b.*',
    '', t_norm
  )

    for pattern, degree in BOUNDARY_ONLY.items():
        if diploma_present and degree in {"M.E", "B.E", "M.A"}:
            continue
        if dme_present and degree == "M.E":
            continue
        if re.search(r"(?<![a-z0-9.])" + pattern + r"(?![a-z0-9.])", text_for_scan):
            found.add(degree)

    if stream_ok and not diploma_present:
        if re.search(r"\b(mechanical|civil|electrical|electronics)\s+engineering\b", t_norm):
            found.add("B.E")
        elif re.search(r"\b(ece|eee)\b", t_norm):
            found.add("B.E")

    if re.search(r'i\.?t\.?i', t_norm, re.IGNORECASE) and re.search(r'\b(fitter|electrician|welder|mechanic)\b',
        t_norm,
        re.IGNORECASE
        ):
        found.add("ITI")
    
    resolved = {STREAM_ALIAS.get(d, d) for d in found}

    has_non_iti = any(d != "ITI" for d in resolved)
    if not has_non_iti:
        if re.search(
            r"\bi\.?t\.?i\.?\b(?!\s*(college|polytechnic|school|university|institute))",
            t_norm
        ):
            if re.search(
                r"\bi\.?t\.?i\.?\b(?!\s*(college|polytechnic|school|university|institute|private))",
                text_for_iti   # ← was t_norm
                ):
                    resolved.add("ITI")           
            
        elif any(x in t_norm or x in t_joined for x in DEGREE_PATTERNS.get("ITI", [])):
            resolved.add("ITI")

    if not resolved:
        if "bachelor of engineering" in t_norm:
            return "B.E"
        if "bachelorofengineering" in t_nospace:
            return "B.E"
        if "bachelor of technology" in t_norm:
            return "B.Tech"
        if "bacheloroftechnology" in t_nospace:
            return "B.Tech"
        return None

    for degree in PRIORITY:
        if degree in resolved:
            return degree
    return next(iter(resolved))


def _get_section(lines: List[str], headings: List[str], window: int = 25) -> List[str]:
    stripped_headings = [re.sub(r"\s+", "", h) for h in headings]
    for i, line in enumerate(lines):
        line_s = re.sub(r"[:\-_*]+$", "", line.strip()).strip()
        line_ns = re.sub(r"\s+", "", line_s)
        if (any(h in line_s for h in headings) or
                any(h in line_ns for h in stripped_headings)):
            section = []
            # FIX: the stop-word check and break were outside the for loop
            # due to wrong indentation — the section never stopped at headings
            # like "Experience" or "Skills". Fixed indentation below.
            for part in lines[i + 1:]:
                l = part.lower().strip()
                if l in ["experience", "languages", "skills", "projects",
                         "personal details", "job profile", "declaration"]:
                    break
                section.append(part)
                if len(section) >= window:
                    break
            return section
    return []


def extract_education(text: str) -> str:
    t_norm    = _normalize(text)
    t_joined  = _normalize(_join_lines(text))
    t_nospace = _dejunk(text)
    lines     = t_norm.splitlines()

    if (
        re.search(r"\bindustrial\s+training\s+course\b", t_joined)
        and re.search(r"\bfitter\s+trade\b", t_joined)
    ):
        return "ITI"

    global_diploma = _has_diploma_evidence(t_norm, t_joined, t_nospace)

    # 1) Education / qualification section
    edu_lines = _get_section(lines, EDUCATION_HEADINGS, window=10)
    if edu_lines:
        degree = _scan("\n".join(edu_lines), stream_ok=True, global_diploma=global_diploma)
        if degree:
            return degree

    # 2) Profile / summary section
    profile_lines = _get_section(lines, PROFILE_HEADINGS, window=12)
    if profile_lines:
        degree = _scan("\n".join(profile_lines), stream_ok=False, global_diploma=global_diploma)
        if degree:
            return degree

    # 3) Full text fallback
    degree = _scan(t_norm, stream_ok=True, global_diploma=global_diploma)
    if degree:
        return degree

    return "Intermediate / 12th"
