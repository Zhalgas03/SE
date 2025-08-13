# test_live_hotels.py
import os, sys, time, json, hashlib, requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

AMADEUS_CLIENT_ID = os.getenv("AMADEUS_CLIENT_ID")
AMADEUS_CLIENT_SECRET = os.getenv("AMADEUS_CLIENT_SECRET")
HOTELBEDS_API_KEY = os.getenv("HOTELBEDS_API_KEY")
HOTELBEDS_SECRET  = os.getenv("HOTELBEDS_SECRET")

# --- настройки по умолчанию ---
IATA_MAP = {
    "paris": ("PAR", (48.8566, 2.3522)),
    "london": ("LON", (51.5074, -0.1278)),
    "barcelona": ("BCN", (41.3851, 2.1734)),
    "rome": ("ROM", (41.9028, 12.4964)),
    "new york": ("NYC", (40.7128, -74.0060)),
}
CITY = (sys.argv[1] if len(sys.argv) > 1 else "paris").lower()
IATA, GEO = IATA_MAP.get(CITY, ("PAR", (48.8566, 2.3522)))

def dates(ahead_days=60, nights=2):
    d1 = (datetime.utcnow() + timedelta(days=ahead_days)).date()
    d2 = d1 + timedelta(days=nights)
    return d1.isoformat(), d2.isoformat()

CHECKIN, CHECKOUT = dates(60, 2)

def pretty(obj): return json.dumps(obj, ensure_ascii=False, indent=2)

# -------- Amadeus --------
def amadeus_token():
    r = requests.post("https://test.api.amadeus.com/v1/security/oauth2/token",
                      data={
                          "grant_type": "client_credentials",
                          "client_id": AMADEUS_CLIENT_ID,
                          "client_secret": AMADEUS_CLIENT_SECRET,
                      }, timeout=12)
    r.raise_for_status()
    return r.json()["access_token"]

def ama_offers_by_city(token, city_code, checkin, checkout):
    r = requests.get("https://test.api.amadeus.com/v2/shopping/hotel-offers",
                     headers={"Authorization": f"Bearer {token}"},
                     params={
                         "cityCode": city_code,
                         "checkInDate": checkin,
                         "checkOutDate": checkout,
                         "adults": 1, "bestRateOnly": True
                     }, timeout=15)
    if r.status_code == 404: return []
    r.raise_for_status()
    return r.json().get("data", [])

def ama_offers_by_geo(token, lat, lon, checkin, checkout, radius=20):
    r = requests.get("https://test.api.amadeus.com/v2/shopping/hotel-offers",
                     headers={"Authorization": f"Bearer {token}"},
                     params={
                         "latitude": lat, "longitude": lon,
                         "radius": radius, "radiusUnit": "KM",
                         "checkInDate": checkin, "checkOutDate": checkout,
                         "adults": 1, "bestRateOnly": True
                     }, timeout=15)
    if r.status_code == 404: return []
    r.raise_for_status()
    return r.json().get("data", [])

def pick_first_from_amadeus(data):
    for item in data or []:
        hotel = item.get("hotel") or {}
        offers = item.get("offers") or []
        if hotel and offers:
            off = min(offers, key=lambda o: float((o.get("price") or {}).get("total", "1e18")))
            return {
                "provider": "Amadeus",
                "hotel_id": hotel.get("hotelId"),
                "name": hotel.get("name"),
                "rating": hotel.get("rating"),
                "address": (hotel.get("address") or {}).get("lines"),
                "geo": (hotel.get("geoCode") or {}),
                "check_in": off.get("checkInDate"),
                "check_out": off.get("checkOutDate"),
                "price": off.get("price"),
                "room": off.get("room"),
            }
    return None

# -------- Hotelbeds --------
def hb_signature():
    if not (HOTELBEDS_API_KEY and HOTELBEDS_SECRET): return None, None
    epoch = str(int(time.time()))
    sig = hashlib.sha256((HOTELBEDS_API_KEY + HOTELBEDS_SECRET + epoch).encode()).hexdigest()
    return sig, epoch

def hb_offers_by_geo(lat, lon, checkin, checkout, radius=20):
    sig, _ = hb_signature()
    if not sig: return []
    r = requests.post("https://api.test.hotelbeds.com/hotel-api/1.0/hotels",
                      headers={
                          "Api-key": HOTELBEDS_API_KEY,
                          "X-Signature": sig,
                          "Accept": "application/json",
                          "Content-Type": "application/json",
                      },
                      json={
                          "stay": {"checkIn": checkin, "checkOut": checkout},
                          "occupancies": [{"rooms": 1, "adults": 1, "children": 0}],
                          "geolocation": {"latitude": lat, "longitude": lon, "radius": radius, "unit": "km"}
                      }, timeout=20)
    if r.status_code == 404: return []
    r.raise_for_status()
    js = r.json()
    return (js.get("hotels") or {}).get("hotels") or []

def pick_first_from_hotelbeds(hotels):
    for h in hotels or []:
        cheapest = None
        for room in (h.get("rooms") or []):
            for rate in (room.get("rates") or []):
                try:
                    val = float(rate.get("sellingRate") or rate.get("net"))
                except: 
                    continue
                if cheapest is None or val < cheapest[0]:
                    cheapest = (val, rate)
        if cheapest:
            return {
                "provider": "Hotelbeds",
                "hotel_id": str(h.get("code")),
                "name": h.get("name"),
                "rating": h.get("categoryCode") or h.get("categoryName"),
                "address": ", ".join([x for x in [h.get("address"), h.get("postalCode"), h.get("city")] if x]),
                "geo": h.get("coordinates"),
                "check_in": CHECKIN,
                "check_out": CHECKOUT,
                "price": {"amount": cheapest[0], "currency": (cheapest[1] or {}).get("currency", "EUR")},
                "room": {"boardName": (cheapest[1] or {}).get("boardName")},
            }
    return None

def main():
    print(f"[TEST] city={CITY}  IATA={IATA}  geo={GEO}  dates={CHECKIN}→{CHECKOUT}")

    # 1) Amadeus by city
    try:
        token = amadeus_token()
        data = ama_offers_by_city(token, IATA, CHECKIN, CHECKOUT)
        pick = pick_first_from_amadeus(data)
        if pick:
            print(pretty({"source":"amadeus:by-city","hotel":pick}))
            return 0
        print("[INFO] Amadeus by-city empty, trying by-geo…")
    except Exception as e:
        print(f"[WARN] Amadeus by-city failed: {e}")

    # 2) Amadeus by geo
    try:
        data = ama_offers_by_geo(token, GEO[0], GEO[1], CHECKIN, CHECKOUT, radius=22)
        pick = pick_first_from_amadeus(data)
        if pick:
            print(pretty({"source":"amadeus:by-geo","hotel":pick}))
            return 0
        print("[INFO] Amadeus by-geo empty, trying Hotelbeds…")
    except Exception as e:
        print(f"[WARN] Amadeus by-geo failed: {e}")

    # 3) Hotelbeds by geo
    try:
        data = hb_offers_by_geo(GEO[0], GEO[1], CHECKIN, CHECKOUT, radius=22)
        pick = pick_first_from_hotelbeds(data)
        if pick:
            print(pretty({"source":"hotelbeds:geo","hotel":pick}))
            return 0
        print("[INFO] Hotelbeds geo empty.")
    except Exception as e:
        print(f"[WARN] Hotelbeds geo failed: {e}")

    print(json.dumps({"error":"No offers found in sandbox for given params"}, ensure_ascii=False))
    return 2

if __name__ == "__main__":
    sys.exit(main())
