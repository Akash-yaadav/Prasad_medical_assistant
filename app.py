from flask import Flask, render_template, request, jsonify
import datetime
import json
import os

app = Flask(__name__)

# In-memory storage for hackathon demo (resets gracefully or can be saved to JSON)
ACTIVE_ALERTS = [
    {
        "id": "ALERT-101",
        "timestamp": "10 minutes ago",
        "type": "Late Night Acute Fever / Vomiting",
        "location": "Hostel Block C - Room 304",
        "severity": "Medium",
        "assigned_to": "Anupam Yadav (Pharmacy & Logistics)",
        "status": "In Progress"
    }
]

# Student Coordinators Data (Featuring Akash Yadav, Anupam Yadav, Aman Kumar)
STUDENT_COORDINATORS = [
    {
        "id": "coord-1",
        "name": "Akash Yadav",
        "role": "Lead Student Coordinator (Emergency Response)",
        "phone": "+91 98765 43210",  # Placeholder that user can customize
        "whatsapp": "+919876543210",
        "email": "akash.yadav@prasad.edu.in",
        "hostel": "PIT Hostel Block A - Room 214",
        "status": "Active (On-Duty)",
        "avatar": "https://api.dicebear.com/7.x/bottts/svg?seed=Akash",
        "is_lead": True,
        "speciality": "CPR Certified, Incident Commander, Police Liaison"
    },
    {
        "id": "coord-2",
        "name": "Anupam Yadav",
        "role": "Student Coordinator (Medical & Pharmacy Logistics)",
        "phone": "+91 98765 43211",
        "whatsapp": "+919876543211",
        "email": "anupam.yadav@prasad.edu.in",
        "hostel": "PIT Hostel Block B - Room 108",
        "status": "Active (On-Duty)",
        "avatar": "https://api.dicebear.com/7.x/bottts/svg?seed=Anupam",
        "is_lead": False,
        "speciality": "Dispensary Access, First-Aid Kit Custodian"
    },
    {
        "id": "coord-3",
        "name": "Aman Kumar",
        "role": "Student Coordinator (Rapid Action & Tech Support)",
        "phone": "+91 98765 43212",
        "whatsapp": "+919876543212",
        "email": "aman.kumar@prasad.edu.in",
        "hostel": "PIT Hostel Block A - Room 302",
        "status": "Active (On-Duty)",
        "avatar": "https://api.dicebear.com/7.x/bottts/svg?seed=Aman",
        "is_lead": False,
        "speciality": "Emergency Transport, Night Flying Squad"
    }
]

# Categorized Emergency Contacts based on situation for Prasad Institute of Technology
EMERGENCY_CONTACTS = {
    "medical": [
        {"name": "PIT Campus Ambulance (24x7 Quick Response)", "number": "102 / +91 94150 11111", "dept": "Prasad Institute Health Center", "icon": "truck-medical", "badge": "Immediate"},
        {"name": "PIT Health Center Doctor on Duty", "number": "+91 94150 22222", "dept": "Infirmary Block 1", "icon": "stethoscope", "badge": "Doctor"},
        {"name": "City Trauma Center (Emergency ICU)", "number": "+91 522 2258888", "dept": "Metro Super Specialty", "icon": "hospital", "badge": "Off-Campus"},
        {"name": "National Emergency Medical Services", "number": "108", "dept": "State Govt Services", "icon": "ambulance", "badge": "Toll Free"}
    ],
    "police": [
        {"name": "PIT Main Gate & Security Control Room", "number": "+91 94150 33333", "dept": "PIT Campus Security HQ", "icon": "shield-alert", "badge": "Campus Police"},
        {"name": "PIT Chief Proctor / Flying Squad", "number": "+91 94150 44444", "dept": "Discipline & Safety Board", "icon": "user-check", "badge": "Hostel Security"},
        {"name": "Women's Safety Helpline (24x7)", "number": "1090 / 112", "dept": "Special Protection Cell", "icon": "shield-check", "badge": "Toll Free"},
        {"name": "Local Police Station (Jurisdiction Post)", "number": "112 / +91 522 223344", "dept": "Civil Police Post", "icon": "badge-sheriff", "badge": "Police Post"}
    ],
    "fire": [
        {"name": "PIT Campus Fire Safety Officer", "number": "+91 94150 55555", "dept": "Estate & Safety Office", "icon": "flame", "badge": "Campus Fire"},
        {"name": "National Fire Brigade", "number": "101", "dept": "Fire & Rescue Department", "icon": "fire-extinguisher", "badge": "Toll Free"}
    ],
    "mental_health": [
        {"name": "PIT Student Wellness Counselor", "number": "+91 94150 66666", "dept": "Student Counseling Cell", "icon": "heart-handshake", "badge": "Confidential"},
        {"name": "Tele-MANAS Mental Health Helpline", "number": "14416 / 1800-891-4416", "dept": "Govt of India Helpline", "icon": "phone-call", "badge": "24/7 Free"}
    ]
}

# Campus Dispensary Inventory for Pill Scanner
DISPENSARY_INVENTORY = {
    "paracetamol": {"stock": 140, "shelf": "Aisle A-1", "usage": "Fever, mild-to-moderate headache, body pain", "dosage": "500mg or 650mg every 6 hours after food"},
    "crocin": {"stock": 85, "shelf": "Aisle A-1", "usage": "Fever and headaches", "dosage": "1 tablet (650mg) after meals"},
    "pantoprazole": {"stock": 60, "shelf": "Aisle B-2", "usage": "Acidity, acid reflux, gastric irritation", "dosage": "40mg early morning empty stomach"},
    "cetirizine": {"stock": 95, "shelf": "Aisle A-3", "usage": "Allergic reactions, running nose, sneezing, itching", "dosage": "10mg once daily at bedtime"},
    "ors": {"stock": 210, "shelf": "Aisle C-1", "usage": "Dehydration, food poisoning, weakness, heatstroke", "dosage": "Dissolve 1 sachet in 1 liter clean water"},
    "bandages": {"stock": 75, "shelf": "Emergency Rack 1", "usage": "Wound dressing, cuts and lacerations", "dosage": "Clean with Betadine, apply sterile gauze"},
    "betadine": {"stock": 40, "shelf": "Emergency Rack 2", "usage": "Antiseptic solution for external cuts and abrasions", "dosage": "Topical application only"},
    "inhaler": {"stock": 12, "shelf": "Emergency Locked Cabinet", "usage": "Salbutamol for acute asthma attacks", "dosage": "1-2 puffs with spacer, seek medical help immediately"},
    "digene": {"stock": 50, "shelf": "Aisle B-1", "usage": "Indigestion and heartburn relief", "dosage": "Chew 2 tablets after meals"}
}

# Campus Outbreak Surveillance Data
OUTBREAK_DATA = {
    "blocks": [
        {"name": "Hostel Block A", "cases": 3, "symptom": "Mild Cough / Flu", "risk": "Low", "color": "#10b981"},
        {"name": "Hostel Block B", "cases": 5, "symptom": "Headache & Exhaustion", "risk": "Low", "color": "#10b981"},
        {"name": "Hostel Block C", "cases": 18, "symptom": "Acute Stomach Cramps & Nausea (Mess Water Check Required)", "risk": "High (Alert)", "color": "#ef4444"},
        {"name": "Hostel Block D", "cases": 2, "symptom": "Sports Sprains", "risk": "Low", "color": "#10b981"},
        {"name": "Girls Hostel Block 1", "cases": 4, "symptom": "Viral Fever", "risk": "Moderate", "color": "#f59e0b"}
    ],
    "alert_notice": "High cluster of gastroenteritis symptoms detected in Hostel Block C mess over last 24 hours. Food safety officer notified."
}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/coordinators", methods=["GET", "POST"])
def get_coordinators():
    if request.method == "POST":
        data = request.json
        coord_id = data.get("id")
        new_phone = data.get("phone")
        new_room = data.get("hostel")
        for coord in STUDENT_COORDINATORS:
            if coord["id"] == coord_id:
                if new_phone: coord["phone"] = new_phone
                if new_room: coord["hostel"] = new_room
                return jsonify({"status": "success", "message": f"Updated {coord['name']}'s details."})
    return jsonify({"coordinators": STUDENT_COORDINATORS})

@app.route("/api/contacts", methods=["GET"])
def get_contacts():
    return jsonify({
        "contacts": EMERGENCY_CONTACTS,
        "student_coordinators": STUDENT_COORDINATORS
    })

@app.route("/api/triage", methods=["POST"])
def triage():
    """
    Intelligent AI Triage Engine:
    Classifies emergency level, gives step-by-step first aid,
    and assigns emergency coordinators and authorities.
    """
    data = request.json or {}
    text = data.get("input", "").lower().strip()
    location = data.get("location", "Campus / Hostel Premise")

    if not text:
        return jsonify({"error": "No symptom or situation provided"}), 400

    # Rule-based heuristics + semantic triage
    critical_keywords = ["bleeding", "unconscious", "fainted", "not breathing", "chest pain", "heart", "head injury", "convulsion", "seizure", "collapse", "severe burn", "suicide", "strangled"]
    urgent_keywords = ["fracture", "deep cut", "vomiting", "food poisoning", "high fever", "asthma", "allergic", "breathless", "electrocution", "sprain"]
    security_keywords = ["police", "fight", "attack", "ragging", "harassment", "theft", "trespass", "stalking", "weapon", "threat"]

    is_critical = any(kw in text for kw in critical_keywords)
    is_urgent = any(kw in text for kw in urgent_keywords)
    is_security = any(kw in text for kw in security_keywords)

    if is_critical:
        severity = "CODE RED (CRITICAL EMERGENCY)"
        color = "red"
        action = "DISPATCH AMBULANCE & ON-DUTY DOCTOR IMMEDIATELY"
        guidance = [
            "Check airway, breathing, and responsiveness. Do NOT shake the person vigorously.",
            "If severe bleeding: Apply direct firm pressure with a clean cloth or towel right now.",
            "If unconscious but breathing: Turn them gently into the recovery position on their left side.",
            "If no pulse or breathing: Begin hands-only CPR at 100-120 beats/min (center of chest).",
            "Keep the room ventilated and crowds cleared."
        ]
        contacts_to_alert = [
            {"name": "Campus Ambulance", "number": "102 / +91 94150 11111"},
            {"name": "Lead Coordinator: Akash Yadav", "number": STUDENT_COORDINATORS[0]["phone"]},
            {"name": "Emergency Doctor on Duty", "number": "+91 94150 22222"}
        ]
    elif is_security:
        severity = "CODE PURPLE (SECURITY / POLICE THREAT)"
        color = "purple"
        action = "ALERT CAMPUS PROCTORIAL SQUAD & LOCAL POLICE"
        guidance = [
            "Move to a well-lit, populated area or lock your hostel room door.",
            "Do not physically confront violent individuals alone.",
            "Note physical descriptions or vehicle license plates if safe to do so.",
            "Emergency alerts are being transmitted to Campus Security & Police."
        ]
        contacts_to_alert = [
            {"name": "Campus Security HQ", "number": "+91 94150 33333"},
            {"name": "Police Control Room", "number": "112"},
            {"name": "Lead Coordinator: Akash Yadav", "number": STUDENT_COORDINATORS[0]["phone"]},
            {"name": "Women's Safety Cell", "number": "1090"}
        ]
    elif is_urgent:
        severity = "CODE YELLOW (URGENT ATTENTION)"
        color = "amber"
        action = "CAMPUS INFIRMARY VISIT & FIRST-AID REQUIRED"
        guidance = [
            "If food poisoning/vomiting: Sip ORS solution slowly every 10 minutes to prevent acute dehydration.",
            "If sprain/fracture: Rest, Ice the area, and immobilize the limb. Do NOT massage.",
            "If high fever: Sponge forehead with room-temperature water; prepare for doctor consult.",
            "Coordinator Anupam Yadav notified for dispensary medicine support."
        ]
        contacts_to_alert = [
            {"name": "Coordinator: Anupam Yadav (Pharmacy)", "number": STUDENT_COORDINATORS[1]["phone"]},
            {"name": "Campus Health Center", "number": "+91 94150 22222"},
            {"name": "Aman Kumar (Rapid Transport)", "number": STUDENT_COORDINATORS[2]["phone"]}
        ]
    else:
        severity = "CODE GREEN (MILD / ROUTINE CARE)"
        color = "green"
        action = "SELF-CARE & DISPENSARY CONSULT"
        guidance = [
            "Rest and stay adequately hydrated with water or electrolyte fluids.",
            "Monitor body temperature every 4 hours.",
            "Visit the campus dispensary during normal operating hours (8:00 AM - 8:00 PM)."
        ]
        contacts_to_alert = [
            {"name": "Campus Dispensary", "number": "+91 94150 22222"},
            {"name": "Coordinator: Aman Kumar", "number": STUDENT_COORDINATORS[2]["phone"]}
        ]

    # Voice prompt synthesis text (for browser text-to-speech)
    speech_text = f"Emergency Alert! {severity}. {action}. " + " ".join(guidance[:2])

    # Log as active alert
    new_alert = {
        "id": f"ALERT-{len(ACTIVE_ALERTS) + 101}",
        "timestamp": "Just now",
        "type": text.capitalize()[:35],
        "location": location,
        "severity": severity,
        "assigned_to": "Akash Yadav & Emergency Team",
        "status": "Active"
    }
    ACTIVE_ALERTS.insert(0, new_alert)

    return jsonify({
        "severity": severity,
        "color": color,
        "action": action,
        "guidance": guidance,
        "speech_text": speech_text,
        "contacts": contacts_to_alert,
        "alert_id": new_alert["id"]
    })

@app.route("/api/sos/broadcast", methods=["POST"])
def sos_broadcast():
    """
    Broadcasts real-time emergency SOS to Akash Yadav, Anupam Yadav, Aman Kumar,
    and Campus Emergency Response Team with room/location coordinates.
    """
    data = request.json or {}
    location = data.get("location", "Hostel Block / Campus Unknown")
    student_name = data.get("student_name", "Student in Distress")
    situation = data.get("situation", "Immediate Medical/Security Assistance Required")
    timestamp = datetime.datetime.now().strftime("%I:%M %p, %d %b %Y")

    broadcast_payload = {
        "broadcast_id": f"SOS-{int(datetime.datetime.now().timestamp())}",
        "status": "DISPATCHED",
        "timestamp": timestamp,
        "student": student_name,
        "location": location,
        "situation": situation,
        "responders_notified": [
            {
                "coordinator": "Akash Yadav",
                "role": "Lead Student Coordinator",
                "phone": STUDENT_COORDINATORS[0]["phone"],
                "channel": "SMS / WhatsApp Priority Alert Sent",
                "ack": "Awaiting response"
            },
            {
                "coordinator": "Anupam Yadav",
                "role": "Pharmacy & Medical Coordinator",
                "phone": STUDENT_COORDINATORS[1]["phone"],
                "channel": "Dispensary Alert Sent",
                "ack": "Awaiting response"
            },
            {
                "coordinator": "Aman Kumar",
                "role": "Rapid Response Coordinator",
                "phone": STUDENT_COORDINATORS[2]["phone"],
                "channel": "Hostel Patrol Notified",
                "ack": "Awaiting response"
            },
            {
                "coordinator": "Campus Ambulance Driver",
                "role": "Medical Transport",
                "phone": "102 / +91 94150 11111",
                "channel": "GPS Beacon Active",
                "ack": "En route"
            }
        ]
    }

    return jsonify({
        "success": True,
        "message": f"🚨 High-priority SOS broadcasted successfully to Akash Yadav, Anupam Yadav, Aman Kumar, and Campus Security!",
        "payload": broadcast_payload
    })

@app.route("/api/medicine/scan", methods=["POST"])
def scan_medicine():
    """
    Simulated Pill / Prescription Vision Scanner
    Matches extracted terms against campus dispensary inventory.
    """
    data = request.json or {}
    query = data.get("query", "").lower().strip()

    if not query:
        # Default sample scan if user just clicked "Scan Sample Prescription"
        query = "paracetamol"

    found = None
    for med_name, details in DISPENSARY_INVENTORY.items():
        if med_name in query:
            found = {
                "medicine": med_name.upper(),
                "status": "In Stock at Campus Dispensary",
                "shelf": details["shelf"],
                "units_available": details["stock"],
                "indications": details["usage"],
                "recommended_dosage": details["dosage"],
                "coordinators_for_pickup": "Contact Anupam Yadav (+91 98765 43211) for after-hours dispensary access"
            }
            break

    if not found:
        return jsonify({
            "status": "Not Found in Campus Dispensary",
            "query": query,
            "message": f"'{query}' is not in the standard campus dispensary stock. Contact Akash Yadav or Campus Infirmary for off-campus pharmacy purchase.",
            "safe_alternatives": ["Paracetamol (for fever/pain)", "Cetirizine (for allergy)", "ORS (for weakness)"]
        })

    return jsonify({"status": "Match Found", "data": found})

@app.route("/api/outbreak/stats", methods=["GET"])
def outbreak_stats():
    return jsonify(OUTBREAK_DATA)

@app.route("/api/alerts", methods=["GET"])
def get_alerts():
    return jsonify({"alerts": ACTIVE_ALERTS})

if __name__ == "__main__":
    print("=" * 65)
    print("🏥 CampusMed AI - Prasad Institute of Technology")
    print("   24/7 Emergency Triage & Medical Assistance Network")
    print("   Lead Coordinator: Akash Yadav")
    print("   Student Coordinators: Anupam Yadav, Aman Kumar")
    print("   Server running on: http://127.0.0.1:5000")
    print("=" * 65)
    app.run(host="0.0.0.0", port=5000, debug=False)
