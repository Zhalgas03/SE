def search_hotels(city, checkin_date, checkout_date, guests=1):
    """
    Поиск отелей (заглушка).
    :param city: str, город
    :param checkin_date: str, дата заезда (YYYY-MM-DD)
    :param checkout_date: str, дата выезда (YYYY-MM-DD)
    :param guests: int, количество гостей
    :return: list, найденные отели
    """
    # Здесь должен быть реальный вызов API бронирования отелей
    return [
        {
            "hotel_name": "Grand Hotel",
            "city": city,
            "checkin": checkin_date,
            "checkout": checkout_date,
            "price": 5000,
            "currency": "RUB",
            "stars": 4,
            "address": "ул. Примерная, 1"
        }
    ]
