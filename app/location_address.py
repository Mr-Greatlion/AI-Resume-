import re

INDIAN_STATES = [
    "tamil nadu", "karnataka", "kerala", "andhra pradesh",
    "telangana", "maharashtra", "delhi", "west bengal",
    "uttar pradesh", "rajasthan", "gujarat"
]

def extract_pincode(text):
    match = re.search(r'\b\d{6}\b', text)
    return match.group() if match else None


def extract_state(text):
    text_lower = text.lower()
    for state in INDIAN_STATES:
        if state in text_lower:
            return state.title()
    return None


def extract_current_location(text):
    state = extract_state(text)
    if state:
        return {
            "country": "India",
            "state": state
        }
    return None


def extract_address(text):
    lines = text.split("\n")
    address_lines = []

    for line in lines:
        if any(k in line.lower() for k in ["address", "street", "road", "nagar"]):
            address_lines.append(line.strip())

    address = " ".join(address_lines) if address_lines else None
    pincode = extract_pincode(text)
    state = extract_state(text)

    if address or pincode or state:
        return {
            "address": address,
            "state": state,
            "country": "India",
            "pincode": pincode
        }

    return None
