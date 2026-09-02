"""
Static dropdown option lists. Served by GET /options and used by the
extractor to normalise values so they always match a dropdown entry.
"""
from __future__ import annotations

# ── Experience buckets (exactly what the UI dropdown shows) ──────────────────
EXPERIENCE_BUCKETS = ["Fresher", "0-1 years", "1-3 years", "3-5 years", "5-10 years", "10+ years"]


def experience_bucket(years: float | None) -> str:
    if years is None:
        return ""
    if years < 0.5:
        return "Fresher"
    if years <= 1:
        return "0-1 years"
    if years <= 3:
        return "1-3 years"
    if years <= 5:
        return "3-5 years"
    if years <= 10:
        return "5-10 years"
    return "10+ years"


# ── Education options ────────────────────────────────────────────────────────
EDUCATION_OPTIONS = [
    "10th / SSC", "Intermediate / 12th", "ITI", "Diploma", "Diploma (Mechanical)",
    "Diploma (Electrical & Electronics)", "Diploma (ECE)", "Diploma (Civil)",
    "Diploma (Computer Science)", "Diploma (Textile Technology)",
    "OND", "HND", "B.E", "B.Tech", "B.Eng", "B.Sc", "BCA", "B.A", "B.Com",
    "M.E", "M.Tech", "M.Eng", "M.Sc", "MCA", "M.A", "M.Com", "MBA", "PhD", "Other",
]

# Keyword → option. Checked in order; first hit wins (specific before generic).
EDUCATION_KEYWORDS = [
    (r"\bph\.?\s?d\b|doctor of philosophy", "PhD"),
    (r"\bmba\b|master of business administration", "MBA"),
    (r"\bm\.?\s?tech\b|master of technology", "M.Tech"),
    (r"\bm\.?\s?eng\b|master of engineering", "M.Eng"),
    (r"\bm\.?\s?e\b(?!\w)", "M.E"),
    (r"\bmca\b|master of computer application", "MCA"),
    (r"\bm\.?\s?sc\b|master of science", "M.Sc"),
    (r"\bm\.?\s?com\b|master of commerce", "M.Com"),
    (r"\bm\.?\s?a\b(?![\w.])|master of arts", "M.A"),
    (r"\bhnd\b|higher national diploma", "HND"),
    (r"\bond\b|ordinary national diploma", "OND"),
    (r"\bb\.?\s?tech\b|bachelor of technology", "B.Tech"),
    (r"\bb\.?\s?eng\b", "B.Eng"),
    (r"\bb\.?\s?e\b(?![\w.])|bachelor of engineering", "B.E"),
    (r"\bbca\b|bachelor of computer application", "BCA"),
    (r"\bb\.?\s?sc\b|bachelor of science", "B.Sc"),
    (r"\bb\.?\s?com\b|bachelor of commerce", "B.Com"),
    (r"\bb\.?\s?a\b(?![\w.])|bachelor of arts", "B.A"),
    (r"diploma.{0,25}(electrical|eee)", "Diploma (Electrical & Electronics)"),
    (r"diploma.{0,25}(mechanical)|\bd\.?m\.?e\b", "Diploma (Mechanical)"),
    (r"diploma.{0,25}(ece|electronics)", "Diploma (ECE)"),
    (r"diploma.{0,25}civil", "Diploma (Civil)"),
    (r"diploma.{0,25}computer", "Diploma (Computer Science)"),
    (r"diploma.{0,25}textile", "Diploma (Textile Technology)"),
    (r"\bdiploma\b", "Diploma"),
    (r"\bi\.?t\.?i\b", "ITI"),
    (r"\b12th\b|\bhsc\b|intermediate|higher secondary|\b\+2\b|\bwaec\b|\bssce\b|\bneco\b", "Intermediate / 12th"),
    (r"\b10th\b|\bsslc\b|\bssc\b|matriculation", "10th / SSC"),
]

# ── Certificates (common in O&M / power-plant hiring) ────────────────────────
CERTIFICATE_OPTIONS = [
    "Boiler Operation Engineer (BOE)", "First Class Boiler Attendant", "Second Class Boiler Attendant",
    "Electrical Supervisor License", "Electrical Wireman License", "HSE Level 1", "HSE Level 2",
    "HSE Level 3", "NEBOSH IGC", "IOSH Managing Safely", "OSHA 30", "First Aid / CPR",
    "Fire Safety", "Work at Height", "Confined Space Entry", "Rigging & Lifting",
    "Welding Certificate (6G)", "ISO 9001 Internal Auditor", "ISO 45001 Internal Auditor",
    "PLC / SCADA Training", "DCS Training", "AutoCAD", "Driving License", "Passport", "Other",
]

# ── Fallback job titles (used only when the live AVR API is unreachable) ─────
JOB_TITLE_FALLBACK = [
    "AHP Operator", "Admin / Store Keeper", "Automation Engineer", "Bagasse Operator",
    "Boiler DCS Operator", "Boiler Field Operator", "Boiler Operator", "Bull Driver",
    "CHP Operator", "Chemist", "Commissioning Engineer - Turbine", "Control Room Operator",
    "Cooling Tower Operator", "DCS Engineer", "DM Chemist", "DM Operator", "E&I Engineer",
    "Electrical Engineer", "Electrical Supervisor", "Electrical Technician", "Electrician",
    "FHS Operator", "Field Operator", "Finance Executive", "Fitter", "Fresher", "HR Executive",
    "HR Manager", "IT Admin", "Instrumentation Engineer", "Instrumentation Incharge",
    "Instrumentation Technician", "Maintenance Engineer", "Mechanical Engineer",
    "Mechanical Fitter", "Mechanical Helper", "Mechanical Incharge", "Mechanical Technician",
    "Mechanical Welder", "O&M Engineer", "Operations Manager", "Operator", "Plant Manager",
    "Power Plant Maintenance", "Power Plant Operations", "Project Engineer", "RO Plant Chemist",
    "RO Plant Operator", "Safety Officer", "Senior Chemist", "Shift Engineer", "Shift Incharge",
    "Software Engineer", "Supervisor", "Turbine DCS Operator", "Turbine Field Operator",
    "WTP Chemist", "WTP Incharge", "Welder",
]

# Role words that make a phrase look like a job title
ROLE_WORDS = (
    "engineer", "technician", "operator", "manager", "chemist", "fitter", "incharge",
    "in-charge", "supervisor", "officer", "executive", "electrician", "welder", "helper",
    "driver", "admin", "administrator", "analyst", "developer", "consultant", "specialist",
    "coordinator", "lead", "head", "assistant", "attendant", "mechanic", "foreman", "trainee",
    "apprentice", "inspector", "planner", "scheduler", "controller", "accountant",
)

# ── Countries + states ───────────────────────────────────────────────────────
COUNTRIES = [
    "India", "Nigeria", "Ghana", "Kenya", "Tanzania", "Uganda", "Zambia", "Ethiopia",
    "South Africa", "Saudi Arabia", "United Arab Emirates", "Qatar", "Oman", "Kuwait", "Bahrain",
    "Bangladesh", "Nepal", "Sri Lanka", "Indonesia", "Malaysia", "Philippines", "Vietnam",
    "Thailand", "United Kingdom", "United States", "Other",
]

STATES: dict[str, list[str]] = {
    "India": [
        "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat",
        "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh",
        "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
        "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh",
        "Uttarakhand", "West Bengal", "Andaman and Nicobar Islands", "Chandigarh",
        "Dadra and Nagar Haveli and Daman and Diu", "Delhi", "Jammu and Kashmir", "Ladakh",
        "Lakshadweep", "Puducherry",
    ],
    "Nigeria": [
        "Abia", "Adamawa", "Akwa Ibom", "Anambra", "Bauchi", "Bayelsa", "Benue", "Borno",
        "Cross River", "Delta", "Ebonyi", "Edo", "Ekiti", "Enugu", "Gombe", "Imo", "Jigawa",
        "Kaduna", "Kano", "Katsina", "Kebbi", "Kogi", "Kwara", "Lagos", "Nasarawa", "Niger",
        "Ogun", "Ondo", "Osun", "Oyo", "Plateau", "Rivers", "Sokoto", "Taraba", "Yobe",
        "Zamfara", "Federal Capital Territory",
    ],
    "Ghana": ["Ahafo", "Ashanti", "Bono", "Bono East", "Central", "Eastern", "Greater Accra",
              "North East", "Northern", "Oti", "Savannah", "Upper East", "Upper West", "Volta",
              "Western", "Western North"],
    "Kenya": ["Nairobi", "Mombasa", "Kisumu", "Nakuru", "Kiambu", "Uasin Gishu", "Machakos", "Other"],
    "Tanzania": ["Dar es Salaam", "Dodoma", "Arusha", "Mwanza", "Mbeya", "Other"],
    "Uganda": ["Central", "Eastern", "Northern", "Western"],
    "Zambia": ["Lusaka", "Copperbelt", "Southern", "Central", "Eastern", "Other"],
    "Ethiopia": ["Addis Ababa", "Oromia", "Amhara", "Tigray", "Other"],
    "South Africa": ["Gauteng", "KwaZulu-Natal", "Western Cape", "Eastern Cape", "Free State",
                     "Limpopo", "Mpumalanga", "North West", "Northern Cape"],
    "Saudi Arabia": ["Riyadh", "Makkah", "Eastern Province", "Madinah", "Other"],
    "United Arab Emirates": ["Abu Dhabi", "Dubai", "Sharjah", "Ajman", "Ras Al Khaimah",
                             "Fujairah", "Umm Al Quwain"],
    "Qatar": ["Doha", "Al Rayyan", "Al Wakrah", "Other"],
    "Oman": ["Muscat", "Dhofar", "Al Batinah", "Other"],
    "Kuwait": ["Kuwait City", "Al Ahmadi", "Hawalli", "Other"],
    "Bahrain": ["Capital", "Muharraq", "Northern", "Southern"],
    "Bangladesh": ["Dhaka", "Chittagong", "Khulna", "Rajshahi", "Sylhet", "Other"],
    "Nepal": ["Bagmati", "Gandaki", "Lumbini", "Other"],
    "Sri Lanka": ["Western", "Central", "Southern", "Northern", "Other"],
}

# City → (state, country) lookup for common cities that resumes mention.
CITY_LOOKUP: dict[str, tuple[str, str]] = {
    # India
    "chennai": ("Tamil Nadu", "India"), "madras": ("Tamil Nadu", "India"),
    "coimbatore": ("Tamil Nadu", "India"), "madurai": ("Tamil Nadu", "India"),
    "trichy": ("Tamil Nadu", "India"), "tiruchirappalli": ("Tamil Nadu", "India"),
    "salem": ("Tamil Nadu", "India"), "tirunelveli": ("Tamil Nadu", "India"),
    "vellore": ("Tamil Nadu", "India"), "erode": ("Tamil Nadu", "India"),
    "tiruppur": ("Tamil Nadu", "India"), "thanjavur": ("Tamil Nadu", "India"),
    "bangalore": ("Karnataka", "India"), "bengaluru": ("Karnataka", "India"),
    "mysore": ("Karnataka", "India"), "mysuru": ("Karnataka", "India"),
    "hubli": ("Karnataka", "India"), "mangalore": ("Karnataka", "India"),
    "hyderabad": ("Telangana", "India"), "secunderabad": ("Telangana", "India"),
    "warangal": ("Telangana", "India"),
    "visakhapatnam": ("Andhra Pradesh", "India"), "vizag": ("Andhra Pradesh", "India"),
    "vijayawada": ("Andhra Pradesh", "India"), "guntur": ("Andhra Pradesh", "India"),
    "tirupati": ("Andhra Pradesh", "India"), "nellore": ("Andhra Pradesh", "India"),
    "kochi": ("Kerala", "India"), "cochin": ("Kerala", "India"),
    "thiruvananthapuram": ("Kerala", "India"), "trivandrum": ("Kerala", "India"),
    "kozhikode": ("Kerala", "India"), "calicut": ("Kerala", "India"), "thrissur": ("Kerala", "India"),
    "mumbai": ("Maharashtra", "India"), "bombay": ("Maharashtra", "India"),
    "pune": ("Maharashtra", "India"), "nagpur": ("Maharashtra", "India"),
    "nashik": ("Maharashtra", "India"), "aurangabad": ("Maharashtra", "India"),
    "new delhi": ("Delhi", "India"), "delhi": ("Delhi", "India"),
    "gurgaon": ("Haryana", "India"), "gurugram": ("Haryana", "India"), "faridabad": ("Haryana", "India"),
    "noida": ("Uttar Pradesh", "India"), "lucknow": ("Uttar Pradesh", "India"),
    "kanpur": ("Uttar Pradesh", "India"), "ghaziabad": ("Uttar Pradesh", "India"),
    "varanasi": ("Uttar Pradesh", "India"), "agra": ("Uttar Pradesh", "India"),
    "kolkata": ("West Bengal", "India"), "calcutta": ("West Bengal", "India"),
    "howrah": ("West Bengal", "India"), "durgapur": ("West Bengal", "India"),
    "ahmedabad": ("Gujarat", "India"), "surat": ("Gujarat", "India"),
    "vadodara": ("Gujarat", "India"), "rajkot": ("Gujarat", "India"),
    "jaipur": ("Rajasthan", "India"), "jodhpur": ("Rajasthan", "India"), "kota": ("Rajasthan", "India"),
    "bhopal": ("Madhya Pradesh", "India"), "indore": ("Madhya Pradesh", "India"),
    "jabalpur": ("Madhya Pradesh", "India"),
    "patna": ("Bihar", "India"), "ranchi": ("Jharkhand", "India"), "jamshedpur": ("Jharkhand", "India"),
    "bhubaneswar": ("Odisha", "India"), "cuttack": ("Odisha", "India"), "rourkela": ("Odisha", "India"),
    "raipur": ("Chhattisgarh", "India"), "bhilai": ("Chhattisgarh", "India"),
    "chandigarh": ("Chandigarh", "India"), "ludhiana": ("Punjab", "India"), "amritsar": ("Punjab", "India"),
    "dehradun": ("Uttarakhand", "India"), "guwahati": ("Assam", "India"),
    "panaji": ("Goa", "India"), "shimla": ("Himachal Pradesh", "India"),
    "srinagar": ("Jammu and Kashmir", "India"), "jammu": ("Jammu and Kashmir", "India"),
    "puducherry": ("Puducherry", "India"), "pondicherry": ("Puducherry", "India"),
    # Nigeria
    "lagos": ("Lagos", "Nigeria"), "ikeja": ("Lagos", "Nigeria"), "lekki": ("Lagos", "Nigeria"),
    "abuja": ("Federal Capital Territory", "Nigeria"),
    "port harcourt": ("Rivers", "Nigeria"), "kano": ("Kano", "Nigeria"), "ibadan": ("Oyo", "Nigeria"),
    "kaduna": ("Kaduna", "Nigeria"), "benin city": ("Edo", "Nigeria"), "enugu": ("Enugu", "Nigeria"),
    "owerri": ("Imo", "Nigeria"), "aba": ("Abia", "Nigeria"), "umuahia": ("Abia", "Nigeria"),
    "onitsha": ("Anambra", "Nigeria"), "awka": ("Anambra", "Nigeria"), "abakaliki": ("Ebonyi", "Nigeria"),
    "unwana": ("Ebonyi", "Nigeria"), "afikpo": ("Ebonyi", "Nigeria"), "warri": ("Delta", "Nigeria"),
    "asaba": ("Delta", "Nigeria"), "uyo": ("Akwa Ibom", "Nigeria"), "calabar": ("Cross River", "Nigeria"),
    "jos": ("Plateau", "Nigeria"), "ilorin": ("Kwara", "Nigeria"), "abeokuta": ("Ogun", "Nigeria"),
    "akure": ("Ondo", "Nigeria"), "osogbo": ("Osun", "Nigeria"), "yenagoa": ("Bayelsa", "Nigeria"),
    "makurdi": ("Benue", "Nigeria"), "maiduguri": ("Borno", "Nigeria"), "sokoto": ("Sokoto", "Nigeria"),
    "bauchi": ("Bauchi", "Nigeria"), "minna": ("Niger", "Nigeria"), "lokoja": ("Kogi", "Nigeria"),
    "gombe": ("Gombe", "Nigeria"), "yola": ("Adamawa", "Nigeria"), "zaria": ("Kaduna", "Nigeria"),
    # Others
    "accra": ("Greater Accra", "Ghana"), "kumasi": ("Ashanti", "Ghana"), "tema": ("Greater Accra", "Ghana"),
    "nairobi": ("Nairobi", "Kenya"), "mombasa": ("Mombasa", "Kenya"),
    "dar es salaam": ("Dar es Salaam", "Tanzania"), "kampala": ("Central", "Uganda"),
    "lusaka": ("Lusaka", "Zambia"), "addis ababa": ("Addis Ababa", "Ethiopia"),
    "johannesburg": ("Gauteng", "South Africa"), "cape town": ("Western Cape", "South Africa"),
    "durban": ("KwaZulu-Natal", "South Africa"),
    "riyadh": ("Riyadh", "Saudi Arabia"), "jeddah": ("Makkah", "Saudi Arabia"),
    "dammam": ("Eastern Province", "Saudi Arabia"), "jubail": ("Eastern Province", "Saudi Arabia"),
    "dubai": ("Dubai", "United Arab Emirates"), "abu dhabi": ("Abu Dhabi", "United Arab Emirates"),
    "sharjah": ("Sharjah", "United Arab Emirates"), "doha": ("Doha", "Qatar"),
    "muscat": ("Muscat", "Oman"), "kuwait city": ("Kuwait City", "Kuwait"), "manama": ("Capital", "Bahrain"),
    "dhaka": ("Dhaka", "Bangladesh"), "chittagong": ("Chittagong", "Bangladesh"),
    "kathmandu": ("Bagmati", "Nepal"), "colombo": ("Western", "Sri Lanka"),
}

COUNTRY_ALIASES = {
    "india": "India", "bharat": "India",
    "nigeria": "Nigeria",
    "ghana": "Ghana", "kenya": "Kenya", "tanzania": "Tanzania", "uganda": "Uganda", "zambia": "Zambia",
    "ethiopia": "Ethiopia", "south africa": "South Africa",
    "saudi arabia": "Saudi Arabia", "ksa": "Saudi Arabia",
    "united arab emirates": "United Arab Emirates", "uae": "United Arab Emirates",
    "qatar": "Qatar", "oman": "Oman", "kuwait": "Kuwait", "bahrain": "Bahrain",
    "bangladesh": "Bangladesh", "nepal": "Nepal", "sri lanka": "Sri Lanka",
    "indonesia": "Indonesia", "malaysia": "Malaysia", "philippines": "Philippines",
    "vietnam": "Vietnam", "thailand": "Thailand",
    "united kingdom": "United Kingdom", "uk": "United Kingdom", "england": "United Kingdom",
    "united states": "United States", "usa": "United States",
}

# Phone dial code per country (default for the country-code dropdown)
DIAL_CODES = {
    "India": "+91", "Nigeria": "+234", "Ghana": "+233", "Kenya": "+254", "Tanzania": "+255",
    "Uganda": "+256", "Zambia": "+260", "Ethiopia": "+251", "South Africa": "+27",
    "Saudi Arabia": "+966", "United Arab Emirates": "+971", "Qatar": "+974", "Oman": "+968",
    "Kuwait": "+965", "Bahrain": "+973", "Bangladesh": "+880", "Nepal": "+977", "Sri Lanka": "+94",
    "Indonesia": "+62", "Malaysia": "+60", "Philippines": "+63", "Vietnam": "+84", "Thailand": "+66",
    "United Kingdom": "+44", "United States": "+1",
}

COUNTRY_CODE_OPTIONS = sorted({v for v in DIAL_CODES.values()}, key=lambda s: (len(s), s))

# Fields the review form sends. Used for diffing extracted vs reviewed.
FIELD_KEYS = [
    "fullName", "surname", "emails", "mobileNumbers",
    "jobTitle", "yearsOfExperience", "educationQualification", "certificates",
    "currentWorkLocation", "permanentAddress", "pan", "aadhar",
]
