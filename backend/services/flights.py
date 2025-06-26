def search_flights(origin, destination, date_from, date_to, passengers=1):
    """
    Mock function for searching flights. Returns a dict with sample flight info.
    """
    return {
        "flights": [
            {
                "origin": origin,
                "destination": destination,
                "date_from": date_from,
                "date_to": date_to,
                "price": 15000,
                "currency": "USD",
                "airline": "MockAir",
                "flight_number": "MA123",
                "passengers": passengers
            }
        ]
    } 