def search_hotels(city, checkin_date, checkout_date, guests=1):
    """
    Mock function for searching hotels. Returns a dict with sample hotel info.
    """
    return {
        "hotels": [
            {
                "hotel_name": "Grand Hotel",
                "city": city,
                "checkin": checkin_date,
                "checkout": checkout_date,
                "price": 120,
                "currency": "USD",
                "stars": 4,
                "address": "123 Example St",
                "guests": guests
            }
        ]
    }