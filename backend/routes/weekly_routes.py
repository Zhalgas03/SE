# api/weekly_routes.py
import io
import os
import base64
import textwrap
import datetime as dt

from flask import Blueprint, request, jsonify, render_template_string, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from psycopg2.extras import RealDictCursor
import requests
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from api.weekly_token import decode_weekly_payload, encode_weekly_payload
from api.weekly_generate import generate_weekly_trip
from db import get_db_connection

weekly_bp = Blueprint("weekly", __name__, url_prefix="/weekly")

PREVIEW_TMPL = """
<!doctype html>
<meta charset="utf-8" />
<title>Trip of the Week</title>

<style>
  body {
    font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
    background: #f8f9fa;
    margin: 0;
    padding: 0;
  }
  .container {
    max-width: 940px;
    margin: 24px auto;
    padding: 20px;
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.06);
  }
  h1 {
    font-size: 2.2rem;
    text-align: center;
    margin-bottom: 6px;
  }
  h2 {
    font-size: 1.4rem;
    text-align: center;
    margin-top: 0;
    color: #333;
  }
  p.teaser {
    text-align: center;
    color: #666;
    font-size: 1rem;
    margin-bottom: 28px;
  }
  h3 {
    text-align: center;
    margin-top: 0;
    margin-bottom: 20px;
  }
  .cards {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
  .card {
    background: #fafafa;
    border-radius: 10px;
    padding: 16px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    width: 100%;
  }
  .card-title {
    font-weight: bold;
    margin-bottom: 10px;
    color: #222;
  }
  .card ul {
    padding-left: 16px;
    margin: 0;
  }
  .card li {
    margin-bottom: 6px;
    font-size: 0.95rem;
    color: #444;
  }
  .save-btn {
    display: block;
    margin: 28px auto 0 auto;
    padding: 12px 22px;
    font-size: 1rem;
    background: linear-gradient(90deg, #ff7b54, #ff3c6a);
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-weight: bold;
    box-shadow: 0 4px 10px rgba(0,0,0,0.15);
    transition: background 0.3s ease, transform 0.2s ease;
  }
  .save-btn:hover {
    transform: translateY(-2px);
    background: linear-gradient(90deg, #ff9068, #ff5a85);
  }
</style>

<div class="container">
  <h1>{{ offer.meta.title }}</h1>
  <h2>{{ offer.summary.destination }} — {{ offer.meta.duration_days }} days</h2>
  <p class="teaser">{{ offer.summary.teaser }}</p>

  <h3>Itinerary</h3>
  <div class="cards">
    {% for day in offer.itinerary %}
      <div class="card">
        <div class="card-title">Day {{ day.day }} — {{ day.title }}</div>
        <ul>
          {% for it in day["items"] %}
            <li>{{ it.time }} · {{ it.place_name }}{% if it.notes %} — {{ it.notes }}{% endif %}</li>
          {% endfor %}
        </ul>
      </div>
    {% endfor %}
  </div>

  <button id="btnSave" onclick="saveFav()" class="save-btn">Save to favorites</button>
</div>

<script>
  // фронт для логина (передаётся из Flask в render_template_string)
  const FE_ORIGIN = "{{ front_origin or 'http://localhost:3000' }}";
  const INTENT_KEY = "weekly_save_intent_v2";

  // 1) Если пришёл #rt=..., кладём JWT в localStorage и чистим hash
  (function bootstrap() {
    try {
      const hash = new URLSearchParams(location.hash.slice(1));
      const rt = hash.get("rt");
      if (rt) {
        localStorage.setItem("token", rt);
        history.replaceState(null, "", location.pathname + location.search);
      }
    } catch (e) {}

    // 2) Автосохранение после логина, если intent=save и есть флаг
    const params = new URLSearchParams(location.search);
    const intent = params.get("intent");
    const intentData = sessionStorage.getItem(INTENT_KEY);
    if (intent === "save" && intentData) {
      try { sessionStorage.removeItem(INTENT_KEY); } catch (e) {}
      setTimeout(() => saveFav(true), 80); // silent=true
    }
  })();

  function redirectToLoginWithIntent() {
    const u = new URL(location.href);
    u.searchParams.set("intent", "save");
    const next = encodeURIComponent(u.toString());
    window.location.href = `${FE_ORIGIN}/login?next=${next}`;
  }

  async function saveFav(silent = false) {
    const btn = document.getElementById("btnSave");
    const token = localStorage.getItem("token");

    if (!token) {
      // пользователь нажал Save → фиксируем намерение и ведём на логин
      try { sessionStorage.setItem(INTENT_KEY, JSON.stringify({ t: "{{ token }}", ts: Date.now() })); } catch (e) {}
      redirectToLoginWithIntent();
      return;
    }

    try {
      if (!silent && btn) { btn.disabled = true; btn.textContent = "Saving…"; }

      const res = await fetch("/weekly/save-favorite", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ t: "{{ token }}" })
      });

      if (res.status === 401) {
        // токен протух → чистим и ведём на логин (если это не silent)
        localStorage.removeItem("token");
        if (!silent) {
          try { sessionStorage.setItem(INTENT_KEY, JSON.stringify({ t: "{{ token }}", ts: Date.now() })); } catch (e) {}
          redirectToLoginWithIntent();
        }
        return;
      }

      const j = await res.json().catch(() => ({}));
      if (j && j.success) {
        // сохраняем превью-URL для вкладки избранного
        try { sessionStorage.setItem("weekly_last_preview", j.preview_url || ""); } catch (e) {}
        window.location.href = `${FE_ORIGIN}/favorites?just_saved=1`;
      } else {
        if (!silent) alert((j && j.message) || "Failed to save");
        if (!silent && btn) { btn.disabled = false; btn.textContent = "Save to favorites"; }
      }
    } catch (e) {
      if (!silent) alert("Server error");
      if (!silent && btn) { btn.disabled = false; btn.textContent = "Save to favorites"; }
    }
  }
</script>
"""

# ---------- Public API ----------

@weekly_bp.route("/current", methods=["GET"])
def weekly_current():
    """
    Детеминированный оффер на текущую неделю, но с возможностью вариативности через salt.
    Query: ?mode=auto|llm|basic&destination=Rome,%20Italy&duration=4&salt=foo
    Возвращает: {success, token, preview_url, summary, meta, mode, seed}
    """
    mode        = (request.args.get("mode") or "auto").lower()
    destination = request.args.get("destination") or None
    duration    = request.args.get("duration") or None
    salt        = request.args.get("salt") or None

    offer = generate_weekly_trip(mode=mode, destination=destination, duration=duration, salt=salt)

    token = encode_weekly_payload(offer, current_app.config["JWT_SECRET_KEY"], exp_days=14)
    base_url = current_app.config.get("BASE_URL", "http://localhost:5001")
    preview_url = f"{base_url}/weekly/preview?t={token}"

    # seed покажем для дебага
    seed = offer.get("meta", {}).get("generated_at", "")

    return jsonify(
        success=True,
        mode=mode,
        seed=seed,
        token=token,
        preview_url=preview_url,
        summary=offer.get("summary", {}),
        meta=offer.get("meta", {})
    )


@weekly_bp.route("/preview", methods=["GET"])
def preview():
    t = request.args.get("t")
    if not t:
        return jsonify(success=False, message="Missing token"), 400
    try:
        offer = decode_weekly_payload(t, current_app.config["JWT_SECRET_KEY"])
    except Exception as e:
        return jsonify(success=False, message=f"Invalid token: {e}"), 400

    front_origin = current_app.config.get("FRONT_ORIGIN", "http://localhost:3000")
    return render_template_string(PREVIEW_TMPL, offer=offer, token=t, front_origin=front_origin)

@weekly_bp.route("/create-trip", methods=["POST"])
@jwt_required()
def create_trip_from_token():
    data = request.get_json(silent=True) or {}
    t = data.get("t") or request.args.get("t")
    if not t:
        return jsonify(success=False, message="Missing token"), 400

    try:
        offer = decode_weekly_payload(t, current_app.config["JWT_SECRET_KEY"])
    except Exception as e:
        return jsonify(success=False, message=f"Invalid token: {e}"), 400

    username = get_jwt_identity()  # из JWT -> users.username
    conn = get_db_connection()
    with conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        # 1) найдём автора (uuid)
        cur.execute("SELECT id FROM users WHERE username=%s", (username,))
        u = cur.fetchone()
        if not u:
            return jsonify(success=False, message="User not found"), 404
        user_id = u["id"]

        # 2) значения под твою схему trips
        duration_days = int(offer.get("meta", {}).get("duration_days", 3))
        trip_name = offer.get("summary", {}).get("destination") or offer.get("meta", {}).get("title", "Trip")
        teaser = offer.get("summary", {}).get("teaser", "")
        desc = f"{trip_name} — {duration_days} days. {teaser}".strip()

        # 3) вставка в trips
        cur.execute(
            """
            INSERT INTO trips (creator_id, name, date_start, date_end, description)
            VALUES (%s, %s, NOW(), NOW() + (%s || ' day')::interval, %s)
            RETURNING id
            """,
            (user_id, trip_name, duration_days, desc)
        )
        trip_id = cur.fetchone()["id"]

    return jsonify(success=True, trip_id=str(trip_id))

# --- Save to favorites (создаём запись в trips С PDF) ---
@weekly_bp.route("/save-favorite", methods=["POST"])
@jwt_required()
def save_favorite_from_token():
    data = request.get_json(silent=True) or {}
    tok = data.get("t")
    if not tok:
        return jsonify(success=False, message="Missing token"), 400

    # 1) Декодируем оффер из weekly-токена
    try:
        offer = decode_weekly_payload(tok, current_app.config["JWT_SECRET_KEY"])
    except Exception as e:
        return jsonify(success=False, message=f"Invalid token: {e}"), 400

    # 2) Рендерим PDF сервер-сайд (ReportLab)
    try:
        pdf_bytes = _render_offer_pdf(offer)
    except Exception:
        current_app.logger.exception("PDF render failed")
        return jsonify(success=False, message="Failed to render PDF"), 500

    # 3) Метаданные для trips
    try:
        duration = int(offer.get("meta", {}).get("duration_days") or 5)
    except Exception:
        duration = 5
    name = (
        offer.get("meta", {}).get("title")
        or offer.get("summary", {}).get("destination")
        or "Trip of the Week"
    )
    today = dt.date.today()
    # date_end включительно на duration дней
    date_start = today.isoformat()
    date_end = (today + dt.timedelta(days=max(0, duration - 1))).isoformat()

    # 4) Вызываем уже существующий API, который пишет в БД и сохраняет PDF на диск
    #    Важно: прокидываем Authorization из исходного запроса
    try:
        result = _call_save_with_pdf(name=name, date_start=date_start, date_end=date_end, pdf_bytes=pdf_bytes)
    except requests.HTTPError as err:
        status = getattr(err.response, "status_code", 500)
        # если токен протух — дадим фронту понять, что надо перелогиниться
        return jsonify(success=False, message="Save failed", status=status), status
    except Exception:
        current_app.logger.exception("Save favorite (save-with-pdf) failed")
        return jsonify(success=False, message="Server error"), 500

    # 5) Возвращаем то, что отдал save-with-pdf
    if not result.get("success"):
        return jsonify(success=False, message=result.get("message") or "Failed to create trip"), 502

    base_url = current_app.config.get("BASE_URL", "http://localhost:5001")
    preview_url = f"{base_url}/weekly/preview?t={tok}"

    return jsonify(
        success=True,
        trip_id=result.get("trip_id"),
        pdf_path=result.get("pdf_path"),
        preview_url=preview_url
    ), 201

@weekly_bp.route("/ping", methods=["GET"])
def weekly_ping():
    return jsonify(ok=True)

# ---------- Dev helpers (guarded by ALLOW_WEEKLY_DEV) ----------
@weekly_bp.route("/test-generate", methods=["GET"])
def weekly_test_generate():
    """
    DEV-ручка для генерации оффера.
    Query: ?mode=auto|llm|basic&destination=...&duration=3..5&salt=...
    Возвращает: {success, token, preview_url, summary, mode, salt}
    """
    if os.getenv("ALLOW_WEEKLY_DEV", "1") != "1":
        return jsonify(success=False, message="Forbidden"), 403

    mode        = (request.args.get("mode") or "auto").lower()
    destination = request.args.get("destination") or None
    duration    = request.args.get("duration") or None
    salt        = request.args.get("salt") or None

    offer = generate_weekly_trip(mode=mode, destination=destination, duration=duration, salt=salt)

    token = encode_weekly_payload(offer, current_app.config["JWT_SECRET_KEY"], exp_days=14)
    base_url = current_app.config.get("BASE_URL", "http://localhost:5001")
    preview_url = f"{base_url}/weekly/preview?t={token}"

    return jsonify(
        success=True,
        mode=mode,
        salt=salt,
        token=token,
        preview_url=preview_url,
        summary=offer.get("summary", {})
    )


# ---------- Helpers ----------

def _call_save_with_pdf(name: str, date_start: str, date_end: str, pdf_bytes: bytes) -> dict:
    base_url = current_app.config.get("BASE_URL", "http://localhost:5001")
    url = f"{base_url}/api/trips/save-with-pdf"
    headers = {
        "Authorization": request.headers.get("Authorization", ""),
        "Content-Type": "application/json"
    }
    pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")
    data_url = f"data:application/pdf;base64,{pdf_b64}"
    payload = {
        "name": name,
        "date_start": date_start,
        "date_end": date_end,
        "pdf_base64": data_url
    }
    r = requests.post(url, headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()

def _wrap_lines(text, width=95):
    return textwrap.wrap(text, width=width) if text else [""]

def _render_offer_pdf(offer: dict) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    w, h = letter
    margin = 56  # ~0.78"
    y = h - margin

    # Header
    title = f"Trip of the Week — {offer.get('summary', {}).get('destination','')}"
    subtitle = f"{offer.get('meta', {}).get('duration_days','?')} days — {offer.get('summary', {}).get('teaser','')}"
    c.setFont("Helvetica-Bold", 16); c.drawString(margin, y, title); y -= 20
    c.setFont("Helvetica", 11); c.drawString(margin, y, subtitle); y -= 24

    # Optional samples
    if offer.get("flights"):
        c.setFont("Helvetica-Bold", 11); c.drawString(margin, y, "Flights sample:"); y -= 14
        c.setFont("Helvetica", 10)
        fs = offer["flights"][0]
        for line in _wrap_lines(f"{fs.get('origin','')} → {fs.get('destination','')} · {fs.get('price','')}"):
            if y < margin: c.showPage(); y = h - margin
            c.drawString(margin, y, line); y -= 12
        y -= 6
    if offer.get("hotels"):
        c.setFont("Helvetica-Bold", 11); c.drawString(margin, y, "Hotel sample:"); y -= 14
        c.setFont("Helvetica", 10)
        hs = offer["hotels"][0]
        for line in _wrap_lines(f"{hs.get('name','')} · {hs.get('price','')}"):
            if y < margin: c.showPage(); y = h - margin
            c.drawString(margin, y, line); y -= 12
        y -= 6

    # Itinerary
    c.setFont("Helvetica-Bold", 12); c.drawString(margin, y, "Itinerary"); y -= 16
    for day in offer.get("itinerary", []):
        if y < margin + 40: c.showPage(); y = h - margin
        c.setFont("Helvetica-Bold", 11)
        c.drawString(margin, y, f"Day {day.get('day','?')} — {day.get('title','')}"); y -= 14
        c.setFont("Helvetica", 10)
        for item in day.get("items", []):
            line = f"{item.get('time','')}  {item.get('place_name','')}"
            notes = item.get("notes","")
            for chunk in _wrap_lines(line, 95):
                if y < margin: c.showPage(); y = h - margin
                c.drawString(margin, y, f"• {chunk}"); y -= 12
            if notes:
                for chunk in _wrap_lines(f"   {notes}", 95):
                    if y < margin: c.showPage(); y = h - margin
                    c.drawString(margin, y, chunk); y -= 12
        y -= 6

    # Tips
    if offer.get("tips"):
        if y < margin + 40: c.showPage(); y = h - margin
        c.setFont("Helvetica-Bold", 11); c.drawString(margin, y, "Tips"); y -= 14
        c.setFont("Helvetica", 10)
        for tip in offer["tips"]:
            for chunk in _wrap_lines(f"• {tip}", 95):
                if y < margin: c.showPage(); y = h - margin
                c.drawString(margin, y, chunk); y -= 12

    c.showPage(); c.save()
    pdf_bytes = buf.getvalue(); buf.close()
    return pdf_bytes
