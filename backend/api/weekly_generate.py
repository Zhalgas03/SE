# api/weekly_generate.py
import random, datetime as dt

DESTS = [
    ("Barcelona, Spain", "Sunny city break: beaches, Gaudí, tapas."),
    ("Lisbon, Portugal", "Hills, trams and ocean views. Pasteis time."),
    ("Prague, Czechia", "Old Town charm, bridges and cozy cafés."),
    ("Istanbul, Türkiye", "Bazaars, Bosphorus and layered history."),
    ("Amsterdam, Netherlands", "Canals, bikes and museums galore."),
    ("Rome, Italy", "Ruins, pasta, piazzas. La dolce vita."),
    ("Vienna, Austria", "Imperial elegance, coffeehouses, waltz."),
]

def _week_seed():
    today = dt.date.today()
    year, week, _ = today.isocalendar()
    return f"{year}-{week}"

def generate_weekly_trip():
    # детерминируем случайность на неделю
    random.seed(_week_seed())

    destination, teaser = random.choice(DESTS)
    duration = random.choice([3,4,5])

    # простая «универсальная» матрица активностей
    base_itin = [
        ("Day 1 — Old Town & Eats", [
            ("10:00","Old Town Walk","Streets & main square"),
            ("17:00","Local Tapas/Meze","Casual bites"),
        ]),
        ("Day 2 — Icons Day", [
            ("09:00","Top Landmark #1","Ticketed entry"),
            ("15:00","Top Park/Museum",""),
        ]),
        ("Day 3 — Chill & Viewpoints", [
            ("11:00","Waterfront / Canal / Beach",""),
            ("16:00","Viewpoint / Cable Car",""),
        ]),
    ]

    itinerary = []
    for i, (title, items) in enumerate(base_itin, start=1):
        itinerary.append({
            "day": i,
            "title": title,
            "items": [{"time": t, "place_name": p, "notes": n} for t,p,n in items]
        })

    return {
        "meta": {
            "title":"Trip of the Week",
            "generated_at":dt.datetime.utcnow().isoformat()+"Z",
            "duration_days":duration
        },
        "summary": {
            "destination": destination,
            "dates_text": f"{duration} days (flexible)",
            "teaser": teaser
        },
        "flights": [],
        "hotels":  [],
        "itinerary": itinerary,
        "tips":[
            "Book popular sights in advance",
            "Keep day 1 light after travel"
        ]
    }
