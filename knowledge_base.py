"""
Knowledge base for Fab's Salon & Bridal Lounge.
All salon information as structured constants — single source of truth.
"""

SALON_NAME = "Fab's Salon & Bridal Lounge"

BRANCHES = {
    "e11": {
        "name": "E-11/2 (Main Branch)",
        "address": "Nafees Mansion, F.E.C.H.S. PMCHS E-11/2, Islamabad",
        "phone": "0335-5593228",
        "hours": "Monday to Sunday, 11:00 AM to 8:00 PM",
    },
    "i8": {
        "name": "I-8 Markaz (Fabs Prestige)",
        "address": "I-8 Markaz, Islamabad",
        "phone": "0335-5593228",
        "hours": "Monday to Sunday, 11:00 AM to 8:00 PM",
    },
}

SERVICES = {
    "bridal": [
        "Nikkah makeup",
        "Barat makeup",
        "Valima makeup",
        "Mehndi",
        "Groom styling",
    ],
    "hair": [
        "Haircut",
        "Hair color",
        "Keratin treatment",
        "Hair rebounding",
        "L'Oreal Extenso",
        "Blow dry",
        "Hair HydraFacial",
    ],
    "skin": [
        "Facial",
        "HydraFacial",
        "Face polishing",
        "Waxing",
        "Cleansing",
    ],
    "nails_body": [
        "Manicure",
        "Pedicure",
        "Full body massage",
    ],
    "premium": [
        "Signature by Fabs",
        "Fabs Prestige packages",
    ],
}

STARTING_PRICE = "Rs. 6,900"
BOOKING_CONTACT = "0335-5593228"
TAGLINE = "We Believe in Enhancing your Beauty instead of making Fake Faces"
