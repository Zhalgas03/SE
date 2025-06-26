import requests

def search_poi_mapbox(lat, lon, api_key, query=None, limit=10):
    """
    Search POIs using MapBox API by coordinates.
    Returns a dict with POI features.
    """
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{query or ''}.json"
    params = {
        "proximity": f"{lon},{lat}",
        "limit": limit,
        "access_token": api_key,
        "types": "poi"
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json() 