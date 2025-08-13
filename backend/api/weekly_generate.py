# api/weekly_generate.py
import os
import json
import random
import datetime as dt
import requests
from flask import Blueprint, request, jsonify

weekly_bp = Blueprint("weekly", __name__, url_prefix="/api/weekly")

# ---------- данные ----------
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

# ---------- BASIC ----------
def _generate_basic(destination=None, teaser=None, duration=None):
    rnd = random.Random(_week_seed())

    if destination is None or teaser is None:
        d, t = rnd.choice(DESTS)
        destination = destination or d
        teaser = teaser or t

    duration = int(duration or rnd.choice([3, 4, 5]))
    duration = max(3, min(5, duration))

    base_itin = [
        ("Day 1 — Old Town & Eats", [
            ("10:00", "Old Town Walk", "Streets & main square"),
            ("17:00", "Local Tapas/Meze", "Casual bites"),
        ]),
        ("Day 2 — Icons Day", [
            ("09:00", "Top Landmark #1", "Ticketed entry"),
            ("15:00", "Top Park/Museum", ""),
        ]),
        ("Day 3 — Chill & Viewpoints", [
            ("11:00", "Waterfront / Canal / Beach", ""),
            ("16:00", "Viewpoint / Cable Car", ""),
        ]),
    ]
    if duration > 3:
        for d in range(4, duration + 1):
            base_itin.append((f"Day {d} — Local Life & Food", [
                ("10:30", "Market / Food Hall", "Try local bites"),
                ("18:00", "Neighborhood Walk", "Cafés & street vibes"),
            ]))

    itinerary = []
    for i, (title, items) in enumerate(base_itin[:duration], start=1):
        itinerary.append({
            "day": i,
            "title": title,
            "items": [{"time": t, "place_name": p, "notes": n} for t, p, n in items]
        })

    return {
        "meta": {
            "title": "Trip of the Week",
            "generated_at": dt.datetime.utcnow().isoformat() + "Z",
            "duration_days": duration
        },
        "summary": {
            "destination": destination,
            "dates_text": f"{duration} days (flexible)",
            "teaser": teaser
        },
        "flights": [],
        "hotels": [],
        "itinerary": itinerary,
        "tips": [
            "Book popular sights in advance",
            "Keep day 1 light after travel"
        ]
    }

# ---------- LLM (Perplexity) ----------
_LLM_SYSTEM = {
    "role": "system",
    "content": """
You are a travel content generator that outputs STRICT JSON ONLY (no markdown, no comments).
Goal: produce a weekly "Trip of the Week" object in the exact JSON schema below. Do not include extra keys.

Schema:
{
  "meta": {
    "title": "Trip of the Week",
    "generated_at": "<UTC ISO8601 with Z>",
    "duration_days": <integer 3..5>
  },
  "summary": {
    "destination": "<City, Country>",
    "dates_text": "<X days (flexible)>",
    "teaser": "<short catchy one-line teaser>"
  },
  "flights": [],
  "hotels": [],
  "itinerary": [
    {
      "day": <1-based integer>,
      "title": "<string>",
      "items": [
        {"time":"HH:MM","place_name":"<string>","notes":"<string or empty>"}
      ]
    }
  ],
  "tips": ["<string>", "<string>"]
}

Hard rules:
- Output valid JSON (no trailing commas, no comments).
- Exactly the keys shown above, nothing else.
- "generated_at" must be UTC ISO8601 with trailing 'Z'.
- duration_days must be 3..5 inclusive.
- itinerary must have exactly duration_days entries, day = 1..duration_days.
- Each itinerary day must have 2–4 items with realistic times.
- Be specific with place_name (real sights/areas/foods). Avoid generic words.
- Keep flights and hotels arrays as empty lists for now.
"""
}

def _perplexity_generate(destination, duration_days, api_key):
    user_prompt = f"""
Generate the STRICT JSON object for Trip of the Week using the schema.
Destination: {destination}
Duration days: {duration_days}
Seed: {_week_seed()}
Remember: output JSON only. No markdown. No comments.
""".strip()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": "sonar",
        "temperature": 0,
        "top_p": 1,
        "messages": [
            _LLM_SYSTEM,
            {"role": "user", "content": user_prompt},
        ],
    }

    res = requests.post(
        "https://api.perplexity.ai/chat/completions",
        headers=headers,
        json=body,
        timeout=60,
    )
    res.raise_for_status()
    content = res.json()["choices"][0]["message"]["content"].strip()

    # снять возможные ```json обёртки
    if content.startswith("```"):
        content = content.strip("`")
        if content.lower().startswith("json"):
            content = content[4:].strip()

    data = json.loads(content)
    required = {"meta", "summary", "flights", "hotels", "itinerary", "tips"}
    if not isinstance(data, dict) or not required.issubset(data.keys()):
        raise ValueError("LLM JSON schema mismatch")

    return data

# ---------- Публичная функция ----------
def generate_weekly_trip(mode="auto", destination=None, duration=None, api_key=None):
    """
    :param mode: "auto" | "llm" | "basic"
    :param destination: str | None
    :param duration: int 3..5 | None
    :param api_key: str | None (если None — возьмём PERPLEXITY_API_KEY)
    """
    # нормализуем вход
    if duration is not None:
        try:
            duration = int(duration)
        except Exception:
            duration = None
    if duration is not None:
        duration = max(3, min(5, duration))

    seed_rnd = random.Random(_week_seed())
    if not destination:
        destination = seed_rnd.choice([d for d, _ in DESTS])

    if mode == "basic":
        teaser = next((t for d, t in DESTS if d == destination), None)
        return _generate_basic(destination=destination, teaser=teaser, duration=duration)

    # auto/llm
    key = api_key or os.getenv("PERPLEXITY_API_KEY")
    if mode == "llm" or (mode == "auto" and key):
        try:
            dur = duration or seed_rnd.choice([3, 4, 5])
            return _perplexity_generate(destination, dur, key)
        except Exception as e:
            # Фоллбэк на basic
            print("Perplexity failed, fallback to basic:", e)

    teaser = next((t for d, t in DESTS if d == destination), None)
    return _generate_basic(destination=destination, teaser=teaser, duration=duration)

# ---------- HTTP эндпоинт ----------
@weekly_bp.route("", methods=["GET"])
def get_weekly_trip():
    """
    GET /api/weekly?mode=auto|llm|basic&destination=Rome,%20Italy&duration=4
    """
    mode = (request.args.get("mode") or "auto").lower()
    destination = request.args.get("destination") or None
    duration = request.args.get("duration") or None
    data = generate_weekly_trip(mode=mode, destination=destination, duration=duration)
    return jsonify(success=True, mode=mode, seed=_week_seed(), data=data)
