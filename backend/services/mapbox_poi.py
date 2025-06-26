import requests


def search_poi_mapbox(lat, lon, api_key, query=None, limit=10):
    """
    Поиск POI через MapBox API по координатам.

    :param lat: float, широта
    :param lon: float, долгота
    :param api_key: str, ваш MapBox API ключ
    :param query: str, опционально — фильтр по типу/названию POI (например, 'cafe', 'museum')
    :param limit: int, максимальное число результатов
    :return: list, найденные POI
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
    data = response.json()
    return data.get("features", [])
