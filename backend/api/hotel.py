# api/hotel.py
import os
import time
import hashlib
import requests
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify

# <<< ВАЖНО: грузим .env до чтения os.getenv >>>
from dotenv import load_dotenv
load_dotenv()

hotel_bp = Blueprint("hotel", __name__, url_prefix="/api/hotel")

# Amadeus
AMADEUS_CLIENT_ID = os.getenv("AMADEUS_CLIENT_ID")
AMADEUS_CLIENT_SECRET = os.getenv("AMADEUS_CLIENT_SECRET")

# Google (только для геокодинга, опционально)
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# Hotelbeds
HOTELBEDS_API_KEY = os.getenv("HOTELBEDS_API_KEY")
HOTELBEDS_SECRET  = os.getenv("HOTELBEDS_SECRET")

# простейший кэш токена Amadeus в памяти
_amadeus_token = {"token": None, "exp": None}


@hotel_bp.route("/ping", methods=["GET"])
def hotel_ping():
    return jsonify(ok=True, bp="hotel"), 200


@hotel_bp.route("/debug-city", methods=["GET"])
def debug_city():
    city = request.args.get("city", "")
    try:
        code, coords = _amadeus_city_info(city)
        gcoords = _google_geocode_city(city)
        return jsonify(city=city, amadeusCityCode=code, amadeusCoords=coords, googleCoords=gcoords), 200
    except Exception as e:
        return jsonify(error=str(e)), 500


# =========================
# Amadeus (self-service)
# =========================
def _get_amadeus_token():
    from datetime import timezone, timedelta
    now = datetime.now(tz=timezone.utc)
    if _amadeus_token["token"] and _amadeus_token["exp"] and now < _amadeus_token["exp"]:
        return _amadeus_token["token"]

    url = "https://test.api.amadeus.com/v1/security/oauth2/token"
    resp = requests.post(
        url,
        data={
            "grant_type": "client_credentials",
            "client_id": AMADEUS_CLIENT_ID,
            "client_secret": AMADEUS_CLIENT_SECRET,
        },
        timeout=12,
    )
    resp.raise_for_status()
    data = resp.json()
    _amadeus_token["token"] = data["access_token"]
    _amadeus_token["exp"] = now + timedelta(seconds=int(data.get("expires_in", 1800)) - 30)
    return _amadeus_token["token"]


def _amadeus_locations(keyword: str):
    token = _get_amadeus_token()
    url = "https://test.api.amadeus.com/v1/reference-data/locations"
    params = {
        "subType": "CITY,AIRPORT",
        "keyword": keyword,
        "page[limit]": 7,
        "sort": "analytics.travelers.score",
    }
    r = requests.get(url, headers={"Authorization": f"Bearer {token}"}, params=params, timeout=12)
    r.raise_for_status()
    return r.json().get("data", [])


def _amadeus_city_info(city: str):
    """Возвращает (city_code, (lat, lon)) из Amadeus CITY (если есть)."""
    city = (city or "").strip()
    if not city:
        return None, None
    try:
        data = _amadeus_locations(city)
    except Exception as e:
        print("[AMADEUS locations ERROR]", e)
        data = []

    exact = next(
        (d for d in data
         if d.get("subType") == "CITY"
         and isinstance(d.get("name"), str)
         and d["name"].strip().lower() == city.lower()
         and d.get("iataCode")),
        None
    )
    any_city = next((d for d in data if d.get("subType") == "CITY" and d.get("iataCode")), None)
    chosen = exact or any_city
    if not chosen:
        overrides = {
            "beijing": ("BJS", None),
            "shanghai": ("SHA", None),
            "rome": ("ROM", None),
            "paris": ("PAR", None),
            "london": ("LON", None),
            "new york": ("NYC", None),
            "tokyo": ("TYO", None),
            "los angeles": ("LAX", None),
            "barcelona": ("BCN", None),
        }
        return overrides.get(city.lower(), (None, None))

    code = chosen.get("iataCode")
    geo = chosen.get("geoCode") or {}
    coords = (geo.get("latitude"), geo.get("longitude")) if geo.get("latitude") is not None else None
    return code, coords


def _amadeus_hotel_offers_by_city(city_code: str, checkin: str, checkout: str,
                                  adults: int = 1, room_qty: int = 1,
                                  currency: str = "EUR",
                                  price_min: float | None = None,
                                  price_max: float | None = None,
                                  max_results: int = 20):
    token = _get_amadeus_token()
    url = "https://test.api.amadeus.com/v2/shopping/hotel-offers"
    params = {
        "cityCode": city_code,
        "checkInDate": checkin,
        "checkOutDate": checkout,
        "adults": adults,
        "roomQuantity": room_qty,
        "currency": currency,
        "bestRateOnly": True,
        "radius": 10,
        "radiusUnit": "KM",
        "includeClosed": False
    }
    if price_min is not None or price_max is not None:
        low = 0 if price_min is None else int(price_min)
        high = 99999 if price_max is None else int(price_max)
        params["priceRange"] = f"{low}-{high}"

    try:
        r = requests.get(url, headers={"Authorization": f"Bearer {token}"}, params=params, timeout=15)
        if r.status_code == 404:
            return []
        r.raise_for_status()
    except requests.HTTPError as e:
        if getattr(e, "response", None) and e.response.status_code == 404:
            return []
        raise
    data = r.json().get("data", [])
    return _normalize_amadeus_offers(data, checkin, checkout, currency, max_results)


def _amadeus_hotel_offers_by_geocode(lat: float, lon: float, checkin: str, checkout: str,
                                     adults: int = 1, room_qty: int = 1,
                                     currency: str = "EUR",
                                     radius_km: int = 15,
                                     price_min: float | None = None,
                                     price_max: float | None = None,
                                     max_results: int = 20):
    token = _get_amadeus_token()
    url = "https://test.api.amadeus.com/v2/shopping/hotel-offers"
    params = {
        "latitude": lat,
        "longitude": lon,
        "radius": radius_km,
        "radiusUnit": "KM",
        "checkInDate": checkin,
        "checkOutDate": checkout,
        "adults": adults,
        "roomQuantity": room_qty,
        "currency": currency,
        "bestRateOnly": True,
        "includeClosed": False
    }
    if price_min is not None or price_max is not None:
        low = 0 if price_min is None else int(price_min)
        high = 99999 if price_max is None else int(price_max)
        params["priceRange"] = f"{low}-{high}"

    try:
        r = requests.get(url, headers={"Authorization": f"Bearer {token}"}, params=params, timeout=15)
        if r.status_code == 404:
            return []
        r.raise_for_status()
    except requests.HTTPError as e:
        if getattr(e, "response", None) and e.response.status_code == 404:
            return []
        raise
    data = r.json().get("data", [])
    return _normalize_amadeus_offers(data, checkin, checkout, currency, max_results)


def _normalize_amadeus_offers(data, checkin: str, checkout: str, currency: str, max_results: int):
    by_hotel = {}
    for item in data or []:
        hotel = item.get("hotel", {}) or {}
        offers = item.get("offers", []) or []
        if not hotel or not offers:
            continue

        cheapest = None
        cheapest_total = None
        for off in offers:
            pr = off.get("price", {})
            total = pr.get("total")
            try:
                val = float(total) if total is not None else None
            except Exception:
                val = None
            if val is None:
                continue
            if cheapest is None or val < cheapest_total:
                cheapest = off
                cheapest_total = val

        if not cheapest:
            continue

        addr = hotel.get("address") or {}
        lines = addr.get("lines", [])
        addr_line = ", ".join([*lines, addr.get("postalCode", ""), addr.get("cityName", ""), addr.get("countryCode", "")]).strip(", ").replace(" ,", ",")
        geo = hotel.get("geoCode") or {}

        normalized = {
            "mode": "stay",
            "provider": "Amadeus",
            "hotel_id": hotel.get("hotelId"),
            "name": hotel.get("name"),
            "rating": hotel.get("rating"),
            "address": addr_line or None,
            "geo": {"lat": geo.get("latitude"), "lon": geo.get("longitude")},
            "distance": (hotel.get("distance") if hotel.get("distance") else None),
            "check_in": cheapest.get("checkInDate") or checkin,
            "check_out": cheapest.get("checkOutDate") or checkout,
            "price": {
                "amount": cheapest_total,
                "currency": (cheapest.get("price") or {}).get("currency") or currency,
            },
            "room": {
                "description": ((cheapest.get("room") or {}).get("description") or {}).get("text"),
                "type": (cheapest.get("room") or {}).get("type"),
                "category": (cheapest.get("room") or {}).get("typeEstimated", {}),
            },
            "board_type": cheapest.get("boardType"),
            "cancellation": (cheapest.get("policies") or {}).get("cancellations"),
            "booking_url": None,
        }

        hid = hotel.get("hotelId") or hotel.get("name")
        prev = by_hotel.get(hid)
        if not prev or (prev["price"]["amount"] is None) or (cheapest_total is not None and cheapest_total < prev["price"]["amount"]):
            by_hotel[hid] = normalized

    options = list(by_hotel.values())
    options = [o for o in options if o.get("price", {}).get("amount") is not None]
    options.sort(key=lambda x: x["price"]["amount"])
    if max_results:
        options = options[:max_results]
    return options


# =========================
# Hotelbeds (fallback)
# =========================
def _hb_signature():
    """
    X-Signature = SHA256( apiKey + secret + epoch )
    """
    if not HOTELBEDS_API_KEY or not HOTELBEDS_SECRET:
        return None
    epoch = str(int(time.time()))
    raw = f"{HOTELBEDS_API_KEY}{HOTELBEDS_SECRET}{epoch}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest(), epoch


def _hotelbeds_availability_by_geo(lat: float, lon: float, checkin: str, checkout: str,
                                   adults: int = 1, rooms: int = 1,
                                   radius_km: int = 15, currency: str = "EUR",
                                   max_results: int = 20):
    sig = _hb_signature()
    if not sig:
        return []
    signature, epoch = sig  # epoch можно не использовать, но пусть будет для дебага

    url = "https://api.test.hotelbeds.com/hotel-api/1.0/hotels"
    headers = {
        "Api-key": HOTELBEDS_API_KEY,
        "X-Signature": signature,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    body = {
        "stay": {"checkIn": checkin, "checkOut": checkout},
        "occupancies": [{"rooms": rooms, "adults": adults, "children": 0}],
        "geolocation": {"latitude": lat, "longitude": lon, "radius": radius_km, "unit": "km"},
    }
    r = requests.post(url, json=body, headers=headers, timeout=20)
    if r.status_code == 404:
        return []
    r.raise_for_status()
    data = r.json().get("hotels", {}).get("hotels", [])
    return _normalize_hotelbeds_offers(data, checkin, checkout, currency, max_results)


def _normalize_hotelbeds_offers(hotels, checkin: str, checkout: str, currency: str, max_results: int):
    options = []
    for h in hotels or []:
        cheapest_total = None
        cheapest_rate = None
        for room in (h.get("rooms") or []):
            for rate in (room.get("rates") or []):
                val_str = rate.get("sellingRate") or rate.get("net")
                try:
                    val = float(str(val_str)) if val_str is not None else None
                except Exception:
                    val = None
                if val is None:
                    continue
                if cheapest_total is None or val < cheapest_total:
                    cheapest_total = val
                    cheapest_rate = rate

        if cheapest_rate is None:
            continue

        lat = (h.get("coordinates") or {}).get("latitude")
        lon = (h.get("coordinates") or {}).get("longitude")

        rating = None
        cat = h.get("categoryCode") or h.get("categoryName") or ""
        if isinstance(cat, str):
            for ch in cat:
                if ch.isdigit():
                    rating = ch
                    break

        address_parts = []
        if h.get("address"): address_parts.append(h["address"])
        if h.get("postalCode"): address_parts.append(h["postalCode"])
        if h.get("city"): address_parts.append(h["city"])
        addr_line = ", ".join([p for p in address_parts if p])

        options.append({
            "mode": "stay",
            "provider": "Hotelbeds",
            "hotel_id": str(h.get("code")),
            "name": h.get("name"),
            "rating": rating,
            "address": addr_line or None,
            "geo": {"lat": lat, "lon": lon},
            "distance": None,
            "check_in": checkin,
            "check_out": checkout,
            "price": {
                "amount": cheapest_total,
                "currency": cheapest_rate.get("currency") or currency,
            },
            "room": {
                "description": cheapest_rate.get("boardName"),
                "type": None,
                "category": {"code": cheapest_rate.get("boardCode")},
            },
            "board_type": cheapest_rate.get("boardName"),
            "cancellation": cheapest_rate.get("cancellationPolicies"),
            "booking_url": None,
        })

    options = [o for o in options if o["price"]["amount"] is not None]
    options.sort(key=lambda x: x["price"]["amount"])
    if max_results:
        options = options[:max_results]
    return options


# =========================
# Google geocode (optional)
# =========================
def _google_geocode_city(city: str):
    if not GOOGLE_MAPS_API_KEY or not city:
        return None
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    r = requests.get(url, params={"address": city, "key": GOOGLE_MAPS_API_KEY}, timeout=10)
    if r.status_code != 200:
        return None
    js = r.json()
    if not js.get("results"):
        return None
    loc = js["results"][0]["geometry"]["location"]
    return (loc["lat"], loc["lng"])


# =========================
# HTTP endpoint
# =========================
@hotel_bp.route("", methods=["GET"])
def get_hotels():
    """
    GET /api/hotel?city=Paris&checkin=2025-10-01&checkout=2025-10-03&adults=1&rooms=1&radius_km=15&max=20
    """
    city = request.args.get("city", "").strip()
    checkin = request.args.get("checkin")
    checkout = request.args.get("checkout")
    
    
    adults = int(request.args.get("adults", 1))
    room_qty = int(request.args.get("rooms", 1))
    currency = (request.args.get("currency") or "EUR").upper()

    budget_min = request.args.get("budget_min")
    budget_max = request.args.get("budget_max")
    price_min = float(budget_min) if budget_min not in (None, "",) else None
    price_max = float(budget_max) if budget_max not in (None, "",) else None

    radius_km = int(request.args.get("radius_km", 15))
    max_results = int(request.args.get("max", 20))

    if not city or not checkin or not checkout:
        return jsonify(success=False, message="city/checkin/checkout required", options=[]), 400

    options = []
    meta = {"sources_tried": [], "source": None, "notes": []}

    # --- 1) Amadeus v2: by cityCode ---
    if AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET:
        city_code, amadeus_coords = None, None
        try:
            city_code, amadeus_coords = _amadeus_city_info(city)
        except Exception as e:
            print("[CITY INFO ERROR]", e)

        if city_code:
            try:
                am_opts = _amadeus_hotel_offers_by_city(
                    city_code=city_code,
                    checkin=checkin, checkout=checkout,
                    adults=adults, room_qty=room_qty,
                    currency=currency,
                    price_min=price_min, price_max=price_max,
                    max_results=max_results
                )
                meta["sources_tried"].append("amadeus:v2/by-city")
                if am_opts:
                    options = am_opts
                    meta["source"] = "amadeus:v2/by-city"
            except Exception as e:
                print("[AMADEUS by-city ERROR]", e)
                meta["notes"].append("amadeus by-city failed")

        # --- 1b) Amadeus v2: by geocode (from Amadeus coords) ---
        if not options and amadeus_coords and all(amadeus_coords):
            try:
                am_geo = _amadeus_hotel_offers_by_geocode(
                    lat=amadeus_coords[0], lon=amadeus_coords[1],
                    checkin=checkin, checkout=checkout,
                    adults=adults, room_qty=room_qty, currency=currency,
                    radius_km=radius_km,
                    price_min=price_min, price_max=price_max,
                    max_results=max_results
                )
                meta["sources_tried"].append("amadeus:v2/by-geo(amadeus)")
                if am_geo:
                    options = am_geo
                    meta["source"] = "amadeus:v2/by-geo(amadeus)"
            except Exception as e:
                print("[AMADEUS by-geocode(amadeus) ERROR]", e)
                meta["notes"].append("amadeus by-geocode(amadeus) failed")

    # --- 2) Hotelbeds fallback: by geocode ---
    if not options and HOTELBEDS_API_KEY and HOTELBEDS_SECRET:
        lat = lon = None
        try:
            _, acoords = _amadeus_city_info(city)
            if acoords and all(acoords):
                lat, lon = acoords
        except Exception:
            pass
        if (lat is None or lon is None):
            g = _google_geocode_city(city)
            if g:
                lat, lon = g

        if lat is not None and lon is not None:
            try:
                hb_opts = _hotelbeds_availability_by_geo(
                    lat=lat, lon=lon,
                    checkin=checkin, checkout=checkout,
                    adults=adults, rooms=room_qty,
                    radius_km=max(radius_km, 12),
                    currency=currency, max_results=max_results
                )
                meta["sources_tried"].append("hotelbeds:geo")
                if hb_opts:
                    options = hb_opts
                    meta["source"] = "hotelbeds:geo"
            except Exception as e:
                print("[HOTELBEDS geo ERROR]", e)
                meta["notes"].append("hotelbeds geo failed")

    return jsonify(
        success=True,
        query={
            "city": city,
            "checkin": checkin,
            "checkout": checkout,
            "adults": adults,
            "rooms": room_qty,
            "currency": currency,
            "budget_min": price_min,
            "budget_max": price_max,
            "radius_km": radius_km,
        },
        options=options,
        meta=meta,
    ), 200
