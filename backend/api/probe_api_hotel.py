# probe_api_hotel.py
import json
from dotenv import load_dotenv
from flask import Flask
from hotel import hotel_bp  # импорт твоего блюпринта

load_dotenv()  # подтянуть .env

app = Flask(__name__)
app.register_blueprint(hotel_bp)

def probe(city, checkin, checkout, radius=25, maxn=10):
    with app.test_client() as client:
        qs = {
            "city": city,
            "checkin": checkin,
            "checkout": checkout,
            "adults": 1,
            "rooms": 1,
            "radius_km": radius,
            "max": maxn
        }
        resp = client.get("/api/hotel", query_string=qs)
        print(f"\n=== {city} {checkin}→{checkout} (radius={radius}) ===")
        print("HTTP:", resp.status_code)
        data = resp.get_json()
        if not data:
            print("NO JSON")
            return
        print("meta:", data.get("meta"))
        opts = data.get("options") or []
        print(f"options: {len(opts)}")
        if opts:
            print(json.dumps(opts[0], ensure_ascii=False, indent=2))

if __name__ == "__main__":
    # Попробуем несколько «живых» сетов для sandbox
    probe("Paris",    "2025-10-10", "2025-10-12", radius=25)
    probe("London",   "2025-11-12", "2025-11-14", radius=25)
    probe("Barcelona","2025-10-07", "2025-10-09", radius=25)
    probe("Rome",     "2025-10-15", "2025-10-17", radius=25)
