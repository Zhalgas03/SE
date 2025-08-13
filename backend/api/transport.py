# transport.py
import os
import requests
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify

transport_bp = Blueprint("transport", __name__, url_prefix="/api/transport")

AMADEUS_CLIENT_ID = os.getenv("AMADEUS_CLIENT_ID")
AMADEUS_CLIENT_SECRET = os.getenv("AMADEUS_CLIENT_SECRET")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# простейший кэш токена Amadeus в памяти
_amadeus_token = {"token": None, "exp": None}

@transport_bp.route("/ping", methods=["GET"])
def transport_ping():
    return jsonify(ok=True, bp="transport"), 200


@transport_bp.route("/debug-locations", methods=["GET"])
def debug_locations():
    city = request.args.get("city", "")
    try:
        return jsonify({
            "city": city,
            "airports": _amadeus_locations(city),
            "cities": _amadeus_locations(city)
        }), 200
    except Exception as e:
        return jsonify(error=str(e)), 500


def _get_amadeus_token():
    from datetime import timezone
    now = datetime.now(tz=timezone.utc)
    if _amadeus_token["token"] and _amadeus_token["exp"] and now < _amadeus_token["exp"]:
        return _amadeus_token["token"]

    url = "https://test.api.amadeus.com/v1/security/oauth2/token"
    resp = requests.post(url, data={
        "grant_type": "client_credentials",
        "client_id": AMADEUS_CLIENT_ID,
        "client_secret": AMADEUS_CLIENT_SECRET
    }, timeout=12)
    resp.raise_for_status()
    data = resp.json()
    _amadeus_token["token"] = data["access_token"]
    _amadeus_token["exp"] = now + timedelta(seconds=int(data.get("expires_in", 1800)) - 30)
    return _amadeus_token["token"]


def _amadeus_locations(city: str):
    """Ищем город/аэропорты по ключевому слову."""
    token = _get_amadeus_token()
    url = "https://test.api.amadeus.com/v1/reference-data/locations"
    params = {
        "subType": "CITY,AIRPORT",
        "keyword": city,
        "page[limit]": 7,
        "sort": "analytics.travelers.score"
    }
    r = requests.get(url, headers={"Authorization": f"Bearer {token}"}, params=params, timeout=12)
    r.raise_for_status()
    return r.json().get("data", [])

def _amadeus_airports_nearby(lat: float, lon: float, radius_km: int = 300):
    """Ищем аэропорты рядом с координатами города."""
    token = _get_amadeus_token()
    url = "https://test.api.amadeus.com/v1/reference-data/locations/airports"
    params = {"latitude": lat, "longitude": lon, "radius": radius_km, "page[limit]": 5}
    r = requests.get(url, headers={"Authorization": f"Bearer {token}"}, params=params, timeout=12)
    r.raise_for_status()
    return r.json().get("data", [])


def _pick_airport_and_coords(city: str):
    """
    Возвращает (iata_code, (lat, lon)).
    Приоритет:
      1) Точно совпадающий CITY по имени → его код (напр. ALA для Almaty) + координаты
      2) AIRPORT в нужной стране/городе (если можем угадать страну по геокодингу)
      3) Если по keyword не нашли хорошее — Google геокодинг → Amadeus airports-nearby
    """
    target_city = (city or "").strip()
    code = None
    lat = lon = None

    # A) пробуем Amadeus locations (CITY/AIRPORT)
    try:
        data = _amadeus_locations(target_city)
    except Exception as e:
        print("[AMADEUS locations ERROR]", e)
        data = []

    # Попробуем получить подсказку по стране из Google (для фильтрации аэропортов)
    country_code = None
    gc = _google_geocode_city(target_city)
    if gc:
        lat, lon = gc  # координаты города
        # выдёргивать страну из geocode можно отдельной функцией (если нужно строго),
        # но для простоты оставим country_code=None — фильтрации по стране может и не быть.

    # 1) Ищем CITY с точным совпадением по имени (без регистра)
    city_exact = next(
        (d for d in data
         if d.get("subType") == "CITY"
         and isinstance(d.get("name"), str)
         and d["name"].strip().lower() == target_city.lower()
         and d.get("iataCode")),
        None
    )
    if city_exact:
        code = city_exact["iataCode"]
        geo = city_exact.get("geoCode") or {}
        lat = lat if lat is not None else geo.get("latitude")
        lon = lon if lon is not None else geo.get("longitude")

    # 2) Если нет — ищем AIRPORT, у которого есть привязка к этому городу по имени
    if not code:
        airport_in_city = next(
            (d for d in data
             if d.get("subType") == "AIRPORT"
             and d.get("iataCode")
             and (
                 (d.get("address") or {}).get("cityName", "").strip().lower() == target_city.lower()
                 or (d.get("name") or "").lower().startswith(target_city.lower())
             )),
            None
        )
        if airport_in_city:
            code = airport_in_city["iataCode"]
            geo = airport_in_city.get("geoCode") or {}
            if lat is None: lat = geo.get("latitude")
            if lon is None: lon = geo.get("longitude")

    # 3) Фолбэк: если кода нет — ищем ближайшие аэропорты вокруг города
    if not code:
        # координаты берём из Google (если ещё не взяли)
        if lat is None or lon is None:
            gc2 = _google_geocode_city(target_city)
            if gc2:
                lat, lon = gc2
        if lat is not None and lon is not None:
            try:
                nearby = _amadeus_airports_nearby(lat, lon, radius_km=400)
                # сначала аэропорты, где address.cityName совпадает
                airport_exact_city = next(
                    (a for a in nearby
                     if (a.get("address") or {}).get("cityName", "").strip().lower() == target_city.lower()
                     and a.get("iataCode")),
                    None
                )
                if airport_exact_city:
                    code = airport_exact_city["iataCode"]
                elif nearby:
                    # иначе берём самый популярный/первый
                    code = nearby[0].get("iataCode")
            except Exception as e:
                print("[AMADEUS airports-nearby ERROR]", e)

    # 4) Маленький «исправитель» частых кейсов (можно расширять при желании)
    overrides = {
        "almaty": "ALA",
        "alma-ata": "ALA",
        "almati": "ALA",
    }
    if not code:
        ov = overrides.get(target_city.lower())
        if ov:
            code = ov

    coords = (lat, lon) if (lat is not None and lon is not None) else None
    return code, coords




def _amadeus_flights(origin_code: str, dest_code: str, date_str: str | None):
    """
    Поиск 3 лучших предложений на выбранную дату.
    origin_code/dest_code — IATA (FCO/ALA/ROM и т.п.)
    """
    token = _get_amadeus_token()
    date = date_str or (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d")

    url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
    params = {
        "originLocationCode": origin_code,
        "destinationLocationCode": dest_code,
        "departureDate": date,
        "adults": 1,
        "currencyCode": "EUR",
        "max": 3
    }
    r = requests.get(url, headers={"Authorization": f"Bearer {token}"}, params=params, timeout=15)
    r.raise_for_status()
    data = r.json().get("data", [])

    options = []
    for it in data:
        price = it.get("price", {})
        itinerary = it.get("itineraries", [{}])[0]
        segs = []
        for s in itinerary.get("segments", []):
            dep = s.get("departure", {})
            arr = s.get("arrival", {})
            carrier = (s.get("carrierCode") or "") + ((" " + (s.get("number") or "")) if s.get("number") else "")
            segs.append({
                "from": dep.get("iataCode"),
                "to": arr.get("iataCode"),
                "dep": dep.get("at"),
                "arr": arr.get("at"),
                "carrier": carrier,
                "stops": None
            })
        duration = itinerary.get("duration")  # ISO8601, например "PT9H45M"
        options.append({
            "mode": "flight",
            "provider": "Amadeus",
            "price": {"amount": float(price.get("grandTotal")) if price.get("grandTotal") else None, "currency": price.get("currency")},
            "duration": duration,  # можно преобразовать позже в «9h 45m»
            "segments": segs,
            "booking_url": None  # Amadeus test не даёт прямую ссылку; можно проставить deeplink провайдера позже
        })
    return options


def _google_directions(origin_coords, dest_coords):
    """
    Простроим автомобильный маршрут (как справочную опцию).
    origin_coords/dest_coords = (lat, lon)
    """
    if not GOOGLE_MAPS_API_KEY or not origin_coords or not dest_coords:
        return None

    o = f"{origin_coords[0]},{origin_coords[1]}"  # lat,lon
    d = f"{dest_coords[0]},{dest_coords[1]}"
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {"origin": o, "destination": d, "mode": "driving", "key": GOOGLE_MAPS_API_KEY}
    r = requests.get(url, params=params, timeout=12)
    if r.status_code != 200:
        return None
    js = r.json()
    if not js.get("routes"):
        return None

    leg = js["routes"][0]["legs"][0]
    dist_txt = leg.get("distance", {}).get("text")
    dur_txt = leg.get("duration", {}).get("text")

    return {
        "mode": "car",
        "provider": "Google Directions",
        "price": None,
        "duration": dur_txt,
        "segments": [],
        "note": f"Approx. {dist_txt}"
    }

def _google_geocode_city(city: str):
    if not GOOGLE_MAPS_API_KEY:
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



@transport_bp.route("", methods=["GET"])
def get_transport():
    """
    GET /api/transport?from=Rome&to=Almaty&date=2025-09-01
    Принимает города/страны. Сам ищет IATA и координаты.
    Возвращает унифицированный список options[].
    """
    origin_city = request.args.get("from", "").strip()
    dest_city   = request.args.get("to", "").strip()
    date        = request.args.get("date")  # YYYY-MM-DD (optional)

    if not origin_city or not dest_city:
        return jsonify(success=False, message="from/to required"), 400

    try:
        orig_code, orig_coords = _pick_airport_and_coords(origin_city)
        dest_code, dest_coords = _pick_airport_and_coords(dest_city)
    
    except Exception as e:
        print("[AMADEUS LOCATIONS ERROR]", e)
        orig_code = dest_code = None
        orig_coords = dest_coords = None


    options = []

    # Полёты
    try:
        if orig_code and dest_code and AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET:
            options.extend(_amadeus_flights(orig_code, dest_code, date))
    except Exception as e:
        print("[AMADEUS FLIGHTS ERROR]", e)

    # Авто
    try:
        if orig_coords and dest_coords and GOOGLE_MAPS_API_KEY:
            options.append(_google_directions(orig_coords, dest_coords))
    except Exception as e:
        print("[GOOGLE DIRECTIONS ERROR]", e)

    # фильтр None
    options = [o for o in options if o]

    return jsonify({
        "success": True,
        "query": {"from": origin_city, "to": dest_city, "date": date,
                  "origin_code": orig_code, "dest_code": dest_code},
        "options": options
    }), 200


